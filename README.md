# social-video-metrics-auto

Codex skill for automating rolling 7-day creator analytics collection across Xiaohongshu, Douyin, and WeChat Channels.

## What It Does

This skill provides a browser-driven workflow for:

- saving login state for creator dashboards
- collecting per-video metrics from the last 7 days
- normalizing output to JSON and CSV
- generating a daily Markdown report
- optionally publishing the report to Feishu
- installing a macOS `launchd` task for scheduled runs

It is designed for cases where platform dashboards are the source of truth and stable public analytics APIs are not available for every platform.

## Included Files

- `SKILL.md`: Codex-facing skill instructions
- `scripts/social_video_metrics.py`: main CLI entry point
- `references/config-guide.md`: selector and config guidance
- `references/platform-notes.md`: platform-specific notes
- `references/todo.md`: remaining implementation work

## Quick Start

1. Initialize a workspace:

```bash
python3 scripts/social_video_metrics.py init --root ~/social-video-metrics
```

2. Save login state for each platform:

```bash
python3 scripts/social_video_metrics.py login --root ~/social-video-metrics --platform xiaohongshu
python3 scripts/social_video_metrics.py login --root ~/social-video-metrics --platform douyin
python3 scripts/social_video_metrics.py login --root ~/social-video-metrics --platform wechat_channels
```

3. Fill in the generated `config.json` with:

- `data_url`
- `row_selector`
- field selectors under `columns`

4. Run a headed debug collection:

```bash
python3 scripts/social_video_metrics.py collect --root ~/social-video-metrics --headed
```

5. Run the daily pipeline:

```bash
python3 scripts/social_video_metrics.py run-daily --root ~/social-video-metrics
```

## Auto-Install Behavior

Browser-based commands automatically install missing runtime dependencies when needed:

- Python package: `playwright`
- Browser runtime: Playwright Chromium

That means first use may take longer on a fresh machine.

## Feishu Publishing

If you enable publishing in `config.json`, set these environment variables first:

```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
```

The script supports:

- append to an existing Feishu doc
- create a new Feishu doc
- create a new wiki-backed page

## Repository Safety

This repository is set up to avoid committing sensitive local runtime files.

Ignored content includes:

- `config.json`
- `auth/`
- `raw/`
- `reports/`
- `logs/`

Keep secrets only in environment variables, not in the repository.

## Current Status

This is a usable first version. The main remaining work is tuning real dashboard selectors for each platform and validating one full scheduled run with live accounts.
