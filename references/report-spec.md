# Report Spec

## Goal

The daily Markdown report should help a human quickly compare recent performance across platforms without reopening each creator backend.

## Recommended Sections

1. Title with report date and collection time
2. Short summary of platforms included
3. Per-platform table of normalized rows
4. Top videos section sorted by `views_7d`
5. Exceptions section for failed collection or missing metrics

## Example Skeleton

```md
# Social Video Metrics Daily Report - 2026-03-16

Collected at: 2026-03-16T09:00:00+08:00
Platforms: Xiaohongshu, Douyin, WeChat Channels

## Overview

- Total videos collected: 12
- Top platform by 7-day views: Douyin
- Collection issues: none

## Xiaohongshu

| Title | Publish Time | 7d Views | Likes | Comments | Shares | Favorites | Followers Gained |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |

## Douyin

| Title | Publish Time | 7d Views | Likes | Comments | Shares | Favorites | Followers Gained |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |

## WeChat Channels

| Title | Publish Time | 7d Views | Likes | Comments | Shares | Favorites | Followers Gained |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |

## Top Videos

| Platform | Title | 7d Views | Likes | Publish Time |
| --- | --- | ---: | ---: | --- |

## Exceptions

- None
```

## Feishu Notes

- Prefer simple Markdown-compatible structure because it is easier to transform into Feishu content blocks later.
- Avoid embedding local image paths in the default report.
- Include failure notes instead of silently skipping a platform.
