# social-video-metrics-auto

Codex skill for building and operating a browser-driven workflow that collects creator video metrics from Xiaohongshu, Douyin, and WeChat Channels, normalizes the outputs, generates daily reports, and optionally publishes the result to Feishu.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/JackLee992/social-video-metrics-auto.git ~/.codex/skills/social-video-metrics-auto
```

If the directory already exists, update it in place:

```bash
git -C ~/.codex/skills/social-video-metrics-auto pull
```

Restart Codex after installing or updating the skill.

## Repository Layout

- `SKILL.md`: skill instructions used by Codex
- `agents/openai.yaml`: display and invocation metadata
- `references/`: schema and reporting references
- `scripts/bootstrap_workspace.py`: helper script to scaffold a local automation workspace

## What This Skill Covers

- initialize a local project workspace for daily metrics collection
- preserve per-platform login state outside version control
- collect and normalize dashboard data from multiple creator backends
- generate Markdown daily reports
- optionally publish reports to Feishu
- prepare a macOS `launchd` schedule after local validation

## Notes

- Keep `config.json`, auth state, raw data, reports, and credentials out of version control.
- The automation project itself should live in a separate workspace; this repository is the reusable skill package.
