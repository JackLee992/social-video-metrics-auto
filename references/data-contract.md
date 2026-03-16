# Data Contract

## Normalized Record

Each normalized video row should use the following fields:

```json
{
  "platform": "xiaohongshu | douyin | wechat_channels",
  "video_id": "string | null",
  "title": "string",
  "publish_time": "ISO-8601 string | null",
  "views_7d": "number | null",
  "likes": "number | null",
  "comments": "number | null",
  "shares": "number | null",
  "favorites": "number | null",
  "followers_gained": "number | null",
  "collected_at": "ISO-8601 string",
  "source_url": "string | null"
}
```

## Platform Mapping Notes

- Xiaohongshu: map "分享" into `shares`, "收藏" into `favorites`.
- Douyin: map "转发" into `shares`; use the closest available interaction metric when labels differ.
- WeChat Channels: if a metric is not exposed in the backend view, keep it as `null`.

## Output Files

For each run, prefer this layout:

```text
workspace/
  config.json
  .env.example
  auth/
    xiaohongshu.json
    douyin.json
    wechat_channels.json
  raw/
    2026-03-16/
      xiaohongshu.raw.json
      xiaohongshu.normalized.json
      douyin.raw.json
      douyin.normalized.json
      wechat_channels.raw.json
      wechat_channels.normalized.json
      merged.normalized.json
      merged.normalized.csv
  reports/
    2026-03-16.md
  logs/
```

## Config Shape

The project should keep collector settings in `config.json` with keys similar to:

```json
{
  "outputRoot": ".",
  "timezone": "Asia/Shanghai",
  "platforms": {
    "xiaohongshu": {
      "enabled": true,
      "loginUrl": "",
      "dataUrl": "",
      "storageStatePath": "auth/xiaohongshu.json",
      "selectors": {}
    },
    "douyin": {
      "enabled": true,
      "loginUrl": "",
      "dataUrl": "",
      "storageStatePath": "auth/douyin.json",
      "selectors": {}
    },
    "wechat_channels": {
      "enabled": true,
      "loginUrl": "",
      "dataUrl": "",
      "storageStatePath": "auth/wechat_channels.json",
      "selectors": {}
    }
  },
  "feishu": {
    "enabled": false,
    "appIdEnv": "FEISHU_APP_ID",
    "appSecretEnv": "FEISHU_APP_SECRET",
    "spaceId": "",
    "parentNodeToken": ""
  },
  "schedule": {
    "hour": 9,
    "minute": 0,
    "label": "com.codex.social-video-metrics-auto"
  }
}
```

## Command Expectations

- `init`: create the standard folder tree and local config template.
- `login --platform <name>`: launch headed browser, finish login, save storage state.
- `collect --platform <name|all> [--headed]`: output raw and normalized files.
- `report [--date YYYY-MM-DD]`: generate one Markdown report from normalized files.
- `publish-feishu [--date YYYY-MM-DD]`: publish the report only when Feishu is enabled.
- `run-daily`: execute collection, merge, report, and optional publish.
- `install-launch-agent`: install a plist that calls `run-daily`.

## Validation Checklist

- One platform can complete `login` and `collect --headed`.
- Normalized rows always match the schema.
- Markdown report can be generated from stored normalized data without recollecting.
- Missing platform metrics do not break merge or report generation.
