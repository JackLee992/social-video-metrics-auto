#!/usr/bin/env python3
"""
Collect rolling 7-day creator video metrics from platform dashboards and publish a daily report.

This script uses Playwright storage state files for login persistence and a JSON config file
to keep fragile selectors outside the code path.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import plistlib
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib import error, parse, request


CONFIG_FILENAME = "config.json"
DEFAULT_REPORT_DIR = "reports"
DEFAULT_RAW_DIR = "raw"
DEFAULT_AUTH_DIR = "auth"
DEFAULT_OUTPUT_BASENAME = "video_metrics"
DEFAULT_FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"
REQUIRED_PYTHON_PACKAGES = ("playwright",)


class SkillError(RuntimeError):
    pass


@dataclass
class RunArtifacts:
    report_markdown: Path
    normalized_json: Path
    normalized_csv: Path
    raw_json: Path


def utc_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def today_slug() -> str:
    return date.today().isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_subprocess(cmd: list[str]) -> None:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise SkillError(f"Command failed: {' '.join(cmd)}\n{result.stdout.strip()}")


def ensure_python_package(package_name: str) -> None:
    try:
        __import__(package_name)
        return
    except ImportError:
        pass
    print(f"Installing missing Python package: {package_name}", file=sys.stderr)
    run_subprocess([sys.executable, "-m", "pip", "install", "--user", package_name])


def ensure_playwright_runtime() -> None:
    cache_root = Path.home() / "Library" / "Caches" / "ms-playwright"
    if cache_root.exists() and any(cache_root.glob("chromium-*")):
        return
    print("Installing Playwright Chromium runtime", file=sys.stderr)
    run_subprocess([sys.executable, "-m", "playwright", "install", "chromium"])


def ensure_browser_environment() -> None:
    for package_name in REQUIRED_PYTHON_PACKAGES:
        ensure_python_package(package_name)
    ensure_playwright_runtime()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def default_config(root: Path) -> dict[str, Any]:
    return {
        "version": 1,
        "created_at": utc_timestamp(),
        "report": {
            "days": 7,
            "timezone": "Asia/Shanghai",
            "title_template": "Daily Video Metrics - {date}",
            "top_n": 5,
        },
        "publish": {
            "enabled": False,
            "mode": "append",
            "document_id": "",
            "space_id": "",
            "title_template": "Daily Video Metrics - {date}",
        },
        "platforms": {
            "xiaohongshu": {
                "enabled": True,
                "display_name": "Xiaohongshu",
                "login_url": "https://creator.xiaohongshu.com/login",
                "data_url": "",
                "storage_state": "auth/xiaohongshu.json",
                "ready_selector": "body",
                "date_range_selector": "",
                "row_selector": "",
                "max_pages": 1,
                "next_page_selector": "",
                "wait_after_open_ms": 2500,
                "columns": {
                    "video_title": {"selector": ""},
                    "publish_time": {"selector": ""},
                    "views": {"selector": ""},
                    "likes": {"selector": ""},
                    "comments": {"selector": ""},
                    "shares": {"selector": ""},
                    "favorites": {"selector": ""},
                    "followers": {"selector": ""},
                },
            },
            "douyin": {
                "enabled": True,
                "display_name": "Douyin",
                "login_url": "https://creator.douyin.com/",
                "data_url": "",
                "storage_state": "auth/douyin.json",
                "ready_selector": "body",
                "date_range_selector": "",
                "row_selector": "",
                "max_pages": 1,
                "next_page_selector": "",
                "wait_after_open_ms": 2500,
                "columns": {
                    "video_title": {"selector": ""},
                    "publish_time": {"selector": ""},
                    "views": {"selector": ""},
                    "likes": {"selector": ""},
                    "comments": {"selector": ""},
                    "shares": {"selector": ""},
                    "favorites": {"selector": ""},
                    "followers": {"selector": ""},
                },
            },
            "wechat_channels": {
                "enabled": True,
                "display_name": "WeChat Channels",
                "login_url": "https://channels.weixin.qq.com/platform/login",
                "data_url": "",
                "storage_state": "auth/wechat_channels.json",
                "ready_selector": "body",
                "date_range_selector": "",
                "row_selector": "",
                "max_pages": 1,
                "next_page_selector": "",
                "wait_after_open_ms": 2500,
                "columns": {
                    "video_title": {"selector": ""},
                    "publish_time": {"selector": ""},
                    "views": {"selector": ""},
                    "likes": {"selector": ""},
                    "comments": {"selector": ""},
                    "shares": {"selector": ""},
                    "favorites": {"selector": ""},
                    "followers": {"selector": ""},
                },
            },
        },
    }


def load_config(root: Path) -> dict[str, Any]:
    config_path = root / CONFIG_FILENAME
    if not config_path.exists():
        raise SkillError(f"Missing config: {config_path}. Run `init` first.")
    return read_json(config_path)


def resolve_path(root: Path, path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else root / path


def parse_metric(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip().lower()
    if not text:
        return None

    text = text.replace(",", "").replace("+", "")
    multiplier = 1.0
    if text.endswith("w"):
        multiplier = 10000.0
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1000.0
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1000000.0
        text = text[:-1]
    elif text.endswith("万"):
        multiplier = 10000.0
        text = text[:-1]
    elif text.endswith("千"):
        multiplier = 1000.0
        text = text[:-1]

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return int(float(match.group(0)) * multiplier)


def normalize_row(platform_key: str, platform_name: str, row: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "platform": platform_key,
        "platform_name": platform_name,
        "video_title": str(row.get("video_title", "")).strip(),
        "publish_time": str(row.get("publish_time", "")).strip(),
        "views": parse_metric(row.get("views")),
        "likes": parse_metric(row.get("likes")),
        "comments": parse_metric(row.get("comments")),
        "shares": parse_metric(row.get("shares")),
        "favorites": parse_metric(row.get("favorites")),
        "followers": parse_metric(row.get("followers")),
        "source_url": str(row.get("source_url", "")).strip(),
        "captured_at": utc_timestamp(),
    }
    return normalized


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    fieldnames = [
        "platform",
        "platform_name",
        "video_title",
        "publish_time",
        "views",
        "likes",
        "comments",
        "shares",
        "favorites",
        "followers",
        "source_url",
        "captured_at",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_report(config: dict[str, Any], rows: list[dict[str, Any]], errors: list[str]) -> str:
    report_cfg = config["report"]
    top_n = int(report_cfg.get("top_n", 5))
    today = today_slug()
    title = report_cfg.get("title_template", "Daily Video Metrics - {date}").format(date=today)

    lines = [f"# {title}", "", f"- Generated: {utc_timestamp()}", f"- Window: last {report_cfg.get('days', 7)} days", ""]

    if errors:
        lines.append("## Collection Errors")
        lines.append("")
        for item in errors:
            lines.append(f"- {item}")
        lines.append("")

    if not rows:
        lines.append("## Summary")
        lines.append("")
        lines.append("No rows were collected. Check platform selectors and login state.")
        lines.append("")
        return "\n".join(lines)

    by_platform: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_platform.setdefault(row["platform_name"], []).append(row)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Platforms with data: {len(by_platform)}")
    lines.append(f"- Total videos captured: {len(rows)}")
    lines.append("")

    for platform_name, platform_rows in sorted(by_platform.items()):
        lines.append(f"## {platform_name}")
        lines.append("")
        total_views = sum(item.get("views") or 0 for item in platform_rows)
        total_likes = sum(item.get("likes") or 0 for item in platform_rows)
        lines.append(f"- Videos: {len(platform_rows)}")
        lines.append(f"- Total views: {total_views}")
        lines.append(f"- Total likes: {total_likes}")
        lines.append("")

        top_rows = sorted(platform_rows, key=lambda item: item.get("views") or 0, reverse=True)[:top_n]
        lines.append(f"Top {len(top_rows)} by views:")
        for row in top_rows:
            lines.append(
                f"- {row.get('video_title') or '(untitled)'} | views={row.get('views') or 0} "
                f"likes={row.get('likes') or 0} comments={row.get('comments') or 0}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def feishu_request_json(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{DEFAULT_FEISHU_BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SkillError(f"Feishu HTTP {exc.code} for {path}: {detail}") from exc
    except error.URLError as exc:
        raise SkillError(f"Feishu network error for {path}: {exc}") from exc
    result = json.loads(body)
    if result.get("code") != 0:
        raise SkillError(f"Feishu API error: {json.dumps(result, ensure_ascii=False)}")
    return result


def get_feishu_token() -> str:
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        raise SkillError("Missing FEISHU_APP_ID or FEISHU_APP_SECRET in the environment.")
    result = feishu_request_json(
        "POST",
        "/auth/v3/tenant_access_token/internal",
        payload={"app_id": app_id, "app_secret": app_secret},
    )
    return result["tenant_access_token"]


def split_text_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for line in text.splitlines():
        blocks.append(
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": line,
                                "text_element_style": {
                                    "bold": False,
                                    "inline_code": False,
                                    "italic": False,
                                    "strikethrough": False,
                                    "underline": False,
                                },
                            }
                        }
                    ]
                },
            }
        )
    if not blocks:
        blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": ""}}]}})
    return blocks


def feishu_append_text(token: str, document_id: str, text: str) -> None:
    blocks = split_text_blocks(text)
    for start in range(0, len(blocks), 50):
        batch = blocks[start : start + 50]
        feishu_request_json(
            "POST",
            f"/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            token=token,
            payload={"index": start, "children": batch},
        )


def feishu_create_doc(token: str, title: str) -> str:
    result = feishu_request_json("POST", "/docx/v1/documents", token=token, payload={"title": title})
    return result["data"]["document"]["document_id"]


def feishu_create_wiki_page(token: str, space_id: str, title: str, text: str) -> str:
    result = feishu_request_json(
        "POST",
        f"/wiki/v2/spaces/{space_id}/nodes",
        token=token,
        payload={"node_type": "origin", "obj_type": "docx", "title": title},
    )
    document_id = result["data"]["node"]["obj_token"]
    feishu_append_text(token, document_id, text)
    return document_id


def import_playwright() -> Any:
    ensure_browser_environment()
    from playwright.sync_api import TimeoutError, sync_playwright
    return sync_playwright, TimeoutError


def extract_rows(page: Any, platform_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    row_selector = platform_cfg.get("row_selector", "").strip()
    if not row_selector:
        raise SkillError("Missing row_selector in config.")
    columns = platform_cfg.get("columns", {})
    rows = page.locator(row_selector)
    count = rows.count()
    data: list[dict[str, Any]] = []
    for idx in range(count):
        row_locator = rows.nth(idx)
        item: dict[str, Any] = {}
        for field, field_cfg in columns.items():
            selector = str(field_cfg.get("selector", "")).strip()
            index = field_cfg.get("index")
            text = ""
            if selector:
                locator = row_locator.locator(selector).first
                if locator.count() > 0:
                    text = locator.inner_text().strip()
            elif index is not None:
                locator = row_locator.locator(":scope > *").nth(int(index))
                if locator.count() > 0:
                    text = locator.inner_text().strip()
            item[field] = text

        link_selector = platform_cfg.get("link_selector", "").strip()
        if link_selector:
            link = row_locator.locator(link_selector).first
            if link.count() > 0:
                href = link.get_attribute("href") or ""
                item["source_url"] = href.strip()
        data.append(item)
    return data


def maybe_click(page: Any, selector: str) -> None:
    selector = selector.strip()
    if not selector:
        return
    locator = page.locator(selector).first
    if locator.count() == 0:
        raise SkillError(f"Selector not found: {selector}")
    locator.click()


def collect_platform(root: Path, platform_key: str, platform_cfg: dict[str, Any], headed: bool) -> list[dict[str, Any]]:
    if not platform_cfg.get("enabled", True):
        return []
    if not platform_cfg.get("data_url", "").strip():
        raise SkillError(f"{platform_key}: missing data_url in config.")

    storage_state = resolve_path(root, platform_cfg["storage_state"])
    if not storage_state.exists():
        raise SkillError(f"{platform_key}: missing login state {storage_state}. Run `login --platform {platform_key}`.")

    sync_playwright, timeout_error = import_playwright()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        context = browser.new_context(storage_state=str(storage_state))
        page = context.new_page()
        try:
            page.goto(platform_cfg["data_url"], wait_until="load")
            ready_selector = str(platform_cfg.get("ready_selector", "body")).strip() or "body"
            page.wait_for_selector(ready_selector, timeout=30000)

            wait_after_open_ms = int(platform_cfg.get("wait_after_open_ms", 0))
            if wait_after_open_ms > 0:
                page.wait_for_timeout(wait_after_open_ms)

            date_range_selector = str(platform_cfg.get("date_range_selector", "")).strip()
            if date_range_selector:
                maybe_click(page, date_range_selector)
                page.wait_for_timeout(1500)

            platform_rows: list[dict[str, Any]] = []
            max_pages = int(platform_cfg.get("max_pages", 1))
            next_page_selector = str(platform_cfg.get("next_page_selector", "")).strip()
            for page_number in range(max_pages):
                extracted = extract_rows(page, platform_cfg)
                platform_rows.extend(extracted)
                if page_number >= max_pages - 1 or not next_page_selector:
                    break
                next_locator = page.locator(next_page_selector).first
                if next_locator.count() == 0 or next_locator.is_disabled():
                    break
                next_locator.click()
                page.wait_for_timeout(1500)

            return [normalize_row(platform_key, platform_cfg["display_name"], row) for row in platform_rows]
        except timeout_error as exc:
            raise SkillError(f"{platform_key}: timed out waiting for dashboard elements.") from exc
        finally:
            context.close()
            browser.close()


def run_collection(root: Path, config: dict[str, Any], headed: bool = False, platform_filter: str | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    platforms = config.get("platforms", {})
    selected = [platform_filter] if platform_filter else list(platforms.keys())
    for platform_key in selected:
        platform_cfg = platforms.get(platform_key)
        if not platform_cfg:
            errors.append(f"Unknown platform: {platform_key}")
            continue
        try:
            rows.extend(collect_platform(root, platform_key, platform_cfg, headed=headed))
        except SkillError as exc:
            errors.append(str(exc))
    return rows, errors


def persist_outputs(root: Path, config: dict[str, Any], rows: list[dict[str, Any]], errors: list[str]) -> RunArtifacts:
    report_dir = root / DEFAULT_REPORT_DIR / today_slug()
    raw_dir = root / DEFAULT_RAW_DIR / today_slug()
    ensure_dir(report_dir)
    ensure_dir(raw_dir)

    base = DEFAULT_OUTPUT_BASENAME
    normalized_json = raw_dir / f"{base}.json"
    normalized_csv = raw_dir / f"{base}.csv"
    raw_json = raw_dir / f"{base}_raw.json"
    report_markdown = report_dir / f"{base}.md"

    write_json(raw_json, {"generated_at": utc_timestamp(), "errors": errors, "rows": rows})
    write_json(normalized_json, {"generated_at": utc_timestamp(), "rows": rows})
    write_csv(normalized_csv, rows)
    report_markdown.write_text(render_report(config, rows, errors), encoding="utf-8")

    return RunArtifacts(
        report_markdown=report_markdown,
        normalized_json=normalized_json,
        normalized_csv=normalized_csv,
        raw_json=raw_json,
    )


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    ensure_dir(root)
    ensure_dir(root / DEFAULT_REPORT_DIR)
    ensure_dir(root / DEFAULT_RAW_DIR)
    ensure_dir(root / DEFAULT_AUTH_DIR)

    config_path = root / CONFIG_FILENAME
    if config_path.exists() and not args.force:
        raise SkillError(f"Config already exists: {config_path}. Use --force to overwrite.")

    config = default_config(root)
    write_json(config_path, config)
    print(config_path)


def cmd_login(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    config = load_config(root)
    platform_cfg = config["platforms"].get(args.platform)
    if not platform_cfg:
        raise SkillError(f"Unknown platform: {args.platform}")

    sync_playwright, _ = import_playwright()
    storage_state = resolve_path(root, platform_cfg["storage_state"])
    ensure_dir(storage_state.parent)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(platform_cfg["login_url"], wait_until="load")
        prompt = textwrap.dedent(
            f"""
            Finish login in the opened browser window for {args.platform}.
            After the dashboard is visibly logged in, return here and press Enter.
            """
        ).strip()
        print(prompt)
        input()
        context.storage_state(path=str(storage_state))
        context.close()
        browser.close()
    print(storage_state)


def cmd_collect(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    config = load_config(root)
    rows, errors = run_collection(root, config, headed=args.headed, platform_filter=args.platform)
    artifacts = persist_outputs(root, config, rows, errors)
    print(json.dumps({"rows": len(rows), "errors": errors, "report": str(artifacts.report_markdown)}, ensure_ascii=False, indent=2))


def cmd_report(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    config = load_config(root)
    raw_json = root / DEFAULT_RAW_DIR / today_slug() / f"{DEFAULT_OUTPUT_BASENAME}.json"
    if not raw_json.exists():
        raise SkillError(f"Missing normalized output: {raw_json}. Run `collect` first.")
    payload = read_json(raw_json)
    report_path = root / DEFAULT_REPORT_DIR / today_slug() / f"{DEFAULT_OUTPUT_BASENAME}.md"
    report_path.write_text(render_report(config, payload.get("rows", []), []), encoding="utf-8")
    print(report_path)


def publish_report(config: dict[str, Any], markdown: str) -> str:
    publish_cfg = config.get("publish", {})
    token = get_feishu_token()
    title = publish_cfg.get("title_template", "Daily Video Metrics - {date}").format(date=today_slug())

    document_id = str(publish_cfg.get("document_id", "")).strip()
    space_id = str(publish_cfg.get("space_id", "")).strip()
    mode = str(publish_cfg.get("mode", "append")).strip()

    if mode == "append":
        if not document_id:
            raise SkillError("publish.document_id is required for append mode.")
        feishu_append_text(token, document_id, markdown)
        return document_id
    if mode == "create-doc":
        document_id = feishu_create_doc(token, title)
        feishu_append_text(token, document_id, markdown)
        return document_id
    if mode == "create-wiki":
        if not space_id:
            raise SkillError("publish.space_id is required for create-wiki mode.")
        return feishu_create_wiki_page(token, space_id, title, markdown)
    raise SkillError(f"Unsupported publish mode: {mode}")


def cmd_publish_feishu(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    config = load_config(root)
    report_path = root / DEFAULT_REPORT_DIR / today_slug() / f"{DEFAULT_OUTPUT_BASENAME}.md"
    if not report_path.exists():
        raise SkillError(f"Missing report: {report_path}. Run `collect` first.")
    document_id = publish_report(config, report_path.read_text(encoding="utf-8"))
    print(document_id)


def cmd_run_daily(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    config = load_config(root)
    rows, errors = run_collection(root, config, headed=args.headed)
    artifacts = persist_outputs(root, config, rows, errors)

    result: dict[str, Any] = {
        "rows": len(rows),
        "errors": errors,
        "report": str(artifacts.report_markdown),
        "csv": str(artifacts.normalized_csv),
        "json": str(artifacts.normalized_json),
    }

    if config.get("publish", {}).get("enabled"):
        result["feishu_document_id"] = publish_report(config, artifacts.report_markdown.read_text(encoding="utf-8"))

    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_launch_agent_plist(python_bin: str, script_path: Path, root: Path, hour: int, minute: int) -> dict[str, Any]:
    return {
        "Label": "com.codex.social-video-metrics-auto",
        "ProgramArguments": [python_bin, str(script_path), "run-daily", "--root", str(root)],
        "RunAtLoad": False,
        "StartCalendarInterval": {"Hour": hour, "Minute": minute},
        "StandardOutPath": str(root / "logs" / "launchd.out.log"),
        "StandardErrorPath": str(root / "logs" / "launchd.err.log"),
        "WorkingDirectory": str(root),
    }


def cmd_install_launch_agent(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    ensure_dir(root / "logs")

    hour_text, minute_text = args.time.split(":", 1)
    hour = int(hour_text)
    minute = int(minute_text)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise SkillError("Time must be HH:MM in 24-hour format.")

    script_path = Path(__file__).resolve()
    plist = build_launch_agent_plist(args.python_bin, script_path, root, hour, minute)
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.codex.social-video-metrics-auto.plist"
    ensure_dir(plist_path.parent)
    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle)
    print(plist_path)
    print("Run `launchctl unload ~/Library/LaunchAgents/com.codex.social-video-metrics-auto.plist 2>/dev/null; launchctl load ~/Library/LaunchAgents/com.codex.social-video-metrics-auto.plist` to apply.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and publish 7-day video metrics from creator dashboards.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_p = subparsers.add_parser("init", help="Create a workspace config for the automation.")
    init_p.add_argument("--root", required=True, help="Workspace directory for config, auth, and reports.")
    init_p.add_argument("--force", action="store_true", help="Overwrite an existing config.json.")
    init_p.set_defaults(func=cmd_init)

    login_p = subparsers.add_parser("login", help="Open a browser and save a platform login state.")
    login_p.add_argument("--root", required=True, help="Workspace directory created by init.")
    login_p.add_argument("--platform", required=True, choices=["xiaohongshu", "douyin", "wechat_channels"])
    login_p.set_defaults(func=cmd_login)

    collect_p = subparsers.add_parser("collect", help="Collect dashboard rows and write raw + normalized outputs.")
    collect_p.add_argument("--root", required=True, help="Workspace directory created by init.")
    collect_p.add_argument("--platform", choices=["xiaohongshu", "douyin", "wechat_channels"])
    collect_p.add_argument("--headed", action="store_true", help="Run browsers in headed mode for debugging.")
    collect_p.set_defaults(func=cmd_collect)

    report_p = subparsers.add_parser("report", help="Render the markdown report from the latest normalized rows.")
    report_p.add_argument("--root", required=True, help="Workspace directory created by init.")
    report_p.set_defaults(func=cmd_report)

    publish_p = subparsers.add_parser("publish-feishu", help="Publish the latest markdown report to Feishu.")
    publish_p.add_argument("--root", required=True, help="Workspace directory created by init.")
    publish_p.set_defaults(func=cmd_publish_feishu)

    run_p = subparsers.add_parser("run-daily", help="Run collection, report generation, and optional Feishu publish.")
    run_p.add_argument("--root", required=True, help="Workspace directory created by init.")
    run_p.add_argument("--headed", action="store_true", help="Run browsers in headed mode for debugging.")
    run_p.set_defaults(func=cmd_run_daily)

    launch_p = subparsers.add_parser("install-launch-agent", help="Write a macOS launchd plist for daily execution.")
    launch_p.add_argument("--root", required=True, help="Workspace directory created by init.")
    launch_p.add_argument("--time", default="08:30", help="Daily run time in HH:MM.")
    launch_p.add_argument("--python-bin", default=sys.executable or "python3", help="Python interpreter to use.")
    launch_p.set_defaults(func=cmd_install_launch_agent)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except SkillError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
