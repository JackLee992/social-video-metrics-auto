---
name: social-video-metrics-auto
description: Automate daily collection of rolling 7-day video metrics from Xiaohongshu, Douyin, and WeChat Channels creator dashboards using Playwright login sessions, normalized CSV/JSON outputs, markdown reports, Feishu publishing, and macOS launchd scheduling. Use when a user needs recurring creator analytics reporting instead of manual dashboard exports.
---

# Social Video Metrics Auto

## Overview

Use this skill when the user needs a reusable automation for daily creator analytics pulls across Xiaohongshu, Douyin, and WeChat Channels.

The workflow is:

1. Initialize a local workspace with `config.json`, auth state files, raw exports, and reports.
2. Log into each platform once with Playwright and save the browser session.
3. Configure each platform's dashboard URL and selectors in `config.json`.
4. Run collection, report generation, and optional Feishu publishing from one command.
5. Install a macOS launch agent for a fixed morning schedule.

Read [references/config-guide.md](references/config-guide.md) when tuning selectors or configuring Feishu publishing. Read [references/platform-notes.md](references/platform-notes.md) when a platform needs special handling.

## Quick Start

Create a workspace:

```bash
python scripts/social_video_metrics.py init --root ~/social-video-metrics
```

The script will auto-install browser dependencies on first use. Manual install is only needed if you want to prepare the machine in advance:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

Save login state for each platform:

```bash
python scripts/social_video_metrics.py login --root ~/social-video-metrics --platform xiaohongshu
python scripts/social_video_metrics.py login --root ~/social-video-metrics --platform douyin
python scripts/social_video_metrics.py login --root ~/social-video-metrics --platform wechat_channels
```

Tune `config.json`, then run a debug collection:

```bash
python scripts/social_video_metrics.py collect --root ~/social-video-metrics --headed
```

Run the full daily pipeline:

```bash
python scripts/social_video_metrics.py run-daily --root ~/social-video-metrics
```

## Commands

Use the bundled script at [scripts/social_video_metrics.py](scripts/social_video_metrics.py).

- `init`
  Creates the workspace and a starter `config.json`.
- `login`
  Opens a real Chromium window so the user can sign in and save a storage state file. If the browser environment is missing, it installs it first.
- `collect`
  Visits each configured analytics page, extracts per-video rows, and writes raw + normalized outputs. If the browser environment is missing, it installs it first.
- `report`
  Renders a markdown summary from the latest normalized JSON file.
- `publish-feishu`
  Publishes the latest markdown report to Feishu using environment credentials.
- `run-daily`
  Runs collection, report generation, and optional Feishu publishing in one step.
- `install-launch-agent`
  Writes a macOS `launchd` plist for a fixed daily schedule.

## Execution Rules

- Prefer `collect --headed` while tuning selectors.
- The script auto-installs missing Python/browser runtime dependencies before browser-based commands.
- Do not hardcode cookies or tokens into the skill; keep them in Playwright storage state files under the workspace.
- Keep platform selectors in `config.json`, not in the script.
- Treat this as browser automation first; only replace a platform with a direct API if the user already has that integration working.
- If publishing is enabled, require `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.

## Outputs

Each run writes:

- `raw/<date>/video_metrics_raw.json`
- `raw/<date>/video_metrics.json`
- `raw/<date>/video_metrics.csv`
- `reports/<date>/video_metrics.md`

## Validation

Representative checks:

```bash
python scripts/social_video_metrics.py --help
python scripts/social_video_metrics.py init --root /tmp/social-video-metrics-smoke --force
python scripts/social_video_metrics.py install-launch-agent --root /tmp/social-video-metrics-smoke --time 08:30
```

For a real end-to-end validation, the user still needs to:

1. Fill in platform selectors and analytics URLs in `config.json`.
2. Run `login` once per platform.
3. Run `collect --headed` and confirm non-empty rows.
