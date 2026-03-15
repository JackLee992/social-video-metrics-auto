# Platform Notes

This skill intentionally uses browser automation instead of assuming official analytics APIs exist for every platform.

## Xiaohongshu

- Expect to tune selectors in the creator center analytics pages.
- Login persistence is handled with a Playwright storage state file.

## Douyin

- If you already have an internal API integration, you can replace the browser path later.
- The first usable version keeps Douyin on the same browser-driven workflow as the other platforms.

## WeChat Channels

- The analytics surface can differ between video account types; keep selectors account-specific if needed.
- If a QR login expires often, rerun the `login` command to refresh the storage state.

## Validation Standard

A platform is considered "ready" when:

1. `login --platform ...` saves a storage state file.
2. `collect --platform ... --headed` writes at least one normalized row.
3. The generated markdown report lists sane totals for that platform.
