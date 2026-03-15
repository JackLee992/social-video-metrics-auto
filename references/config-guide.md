# Config Guide

`config.json` lives in the workspace you pass to `init --root ...`.

## Workflow

1. Run `init` to create the workspace.
2. Fill in each platform's `data_url`, `row_selector`, and `columns`.
3. Run `login --platform <name>` once per platform to save browser state.
4. Run `collect --headed` while tuning selectors.
5. When the output looks correct, install the launch agent for the morning schedule.

## Platform Config Fields

- `login_url`: page used for the first interactive login.
- `data_url`: analytics page that already shows the last 7 days or can be switched with `date_range_selector`.
- `storage_state`: path to the Playwright session file.
- `ready_selector`: a stable selector that appears after the dashboard is fully loaded.
- `date_range_selector`: optional button or tab selector for "last 7 days".
- `row_selector`: selector that matches one table row or card per video.
- `next_page_selector`: optional selector for pagination.
- `max_pages`: number of pages to crawl before stopping.
- `columns.<field>.selector`: selector relative to each row for the desired metric.
- `columns.<field>.index`: fallback cell index when the row is table-like and selectors are not practical.

## Required Output Fields

These normalized fields are emitted into CSV/JSON:

- `video_title`
- `publish_time`
- `views`
- `likes`
- `comments`
- `shares`
- `favorites`
- `followers`

If a platform does not expose one field, leave the selector blank.

## Tuning Tips

- Use Chromium devtools to copy selectors, then replace fragile generated classes with stable attributes when possible.
- Start with one platform and one page before enabling pagination.
- Keep `--headed` on during selector tuning so you can see where the script is waiting.
- If the dashboard shows cards instead of tables, point `row_selector` at the card container and set field selectors relative to the card.

## Feishu Publishing

The `publish` section controls whether `run-daily` pushes the markdown report to Feishu.

- `enabled=true` turns on publishing.
- `mode="append"` appends to an existing doc.
- `mode="create-doc"` creates a new doc each day.
- `mode="create-wiki"` creates a new wiki-backed page each day.

Set `FEISHU_APP_ID` and `FEISHU_APP_SECRET` in the environment before using publish commands.
