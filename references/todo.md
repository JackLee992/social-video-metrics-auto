# TODO

## Remaining Work

- Tune stable selectors for Xiaohongshu, Douyin, and WeChat Channels against real creator dashboards.
- Add one verified example `config.json` template per platform after selectors are confirmed.
- Add optional per-platform extractor hooks for card-based layouts that do not map cleanly to table rows.
- Validate the end-to-end flow with real platform logins and one successful `run-daily` execution.
- Add stronger duplicate prevention when multiple pages contain the same video row.
- Add support for alternate output targets such as Feishu Sheets or database storage if needed later.
- Add alerting for failed scheduled runs so broken selectors are visible before the next morning report.

## Safety Notes

- Do not commit local `config.json`, browser storage state files, or generated reports.
- Keep `FEISHU_APP_ID` and `FEISHU_APP_SECRET` only in the environment.
