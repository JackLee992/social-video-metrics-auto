---
name: social-video-metrics-auto
description: Use this skill when the user wants to build, scaffold, or operate a browser-automation workflow that collects recent video metrics from Xiaohongshu, Douyin, and WeChat Channels, normalizes the data, generates daily reports, and optionally publishes the report to Feishu or installs a macOS launchd schedule.
---

# Social Video Metrics Auto

## Overview

Use this skill to create or maintain a local automation project that:

- logs into Xiaohongshu, Douyin, and WeChat Channels with saved browser state
- collects recent video performance metrics from creator backends
- normalizes cross-platform fields into one schema
- outputs JSON, CSV, and Markdown daily reports
- optionally publishes the report to Feishu
- optionally installs a macOS `launchd` schedule for daily runs

This skill is optimized for the pragmatic path: browser automation first, API replacement later when a platform exposes a stable official interface.

## When To Use

Use this skill when the user asks to:

- build the first version of a multi-platform video metrics automation
- scaffold a Playwright-based project for creator backend scraping
- define selectors, login persistence, report generation, or daily scheduling
- wire up commands such as `init`, `login`, `collect`, `report`, `publish-feishu`, `run-daily`, or `install-launch-agent`
- standardize metrics across Xiaohongshu, Douyin, and WeChat Channels

Do not use this skill for:

- pure public web scraping without login state
- one-off manual spreadsheet cleanup
- deep BI modeling unrelated to the collection pipeline

## Working Style

Follow this sequence unless the user asks for a narrower slice:

1. Confirm the workspace shape and whether a project already exists.
2. Initialize the working directory with the helper script in `scripts/bootstrap_workspace.py` if needed.
3. Read [references/data-contract.md](references/data-contract.md) before designing collectors or reports.
4. Implement platform collectors one by one, starting with Xiaohongshu.
5. Keep login state, raw data, reports, and secrets out of version control.
6. Verify a single-platform `collect --headed` flow before wiring the full `run-daily` chain.
7. Add `launchd` scheduling only after at least one end-to-end local run succeeds.

## Command Contract

The target automation project should expose these commands:

- `init`: create directories, config template, and local project files
- `login`: open one platform in headed mode and save browser state
- `collect`: fetch raw metrics and normalized records for one or more platforms
- `report`: generate a Markdown daily report from normalized data
- `publish-feishu`: publish the latest report to Feishu doc or wiki
- `run-daily`: run collection, reporting, and optional publish in sequence
- `install-launch-agent`: write and install a macOS launch agent plist

If the current repo does not already implement these commands, scaffold them first and keep each command callable independently.

## Implementation Rules

- Prefer Playwright with persistent or reusable storage state per platform.
- Keep selectors and URLs in configuration, not hard-coded in collector logic.
- Preserve both raw records and normalized records for debugging.
- Normalize output fields even when a platform lacks a metric; use `null` rather than inventing values.
- Timestamp all runs with an explicit collection time.
- Default to Markdown reports that summarize the latest run and highlight top-performing videos.
- Treat Feishu publish and `launchd` install as optional extensions behind config flags.

## Platform Rollout Order

Implement and verify in this order:

1. Xiaohongshu
2. Douyin
3. WeChat Channels

This reduces moving parts while selectors and schema are still stabilizing.

## References

- Read [references/data-contract.md](references/data-contract.md) for the normalized schema, directory layout, and command expectations.
- Read [references/report-spec.md](references/report-spec.md) when generating daily Markdown summaries or Feishu-ready content.

## Scripts

- Run `scripts/bootstrap_workspace.py` to scaffold a new automation workspace.
- The script is for project setup only; it does not replace collector implementation.

## Guardrails

- Never commit `config.json`, `auth/`, `raw/`, `reports/`, or Feishu credentials.
- Expect selectors and backend URLs to change; keep them configurable and easy to patch.
- If browser dependencies are missing, install Playwright and Chromium as part of first-run setup.
- If a platform flow becomes stable through an official API later, replace only that collector and keep the normalized schema unchanged.
