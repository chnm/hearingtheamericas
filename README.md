# hearingtheamericas.org

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://hearingtheamericas.org/`

**Run**

- started:   2026-05-27 16:12:03
- finished:  2026-05-27 16:21:17
- duration:  554s (wrapper) · 9m 15s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 585 files, 78M (43.5 MB/s)
- links converted: 394 files in 0.2s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 585 | 24 | 14 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (14)

| status | url |
|--------|-----|
| 404 | https://hearingtheamericas.org/s/the-americas/item/23 |
| 404 | https://hearingtheamericas.org/s/the-americas/page/jazz |
| 404 | https://hearingtheamericas.org/s/the-americas/item/334 |
| 404 | https://hearingtheamericas.org/s/the-americas/item/378 |
| 404 | https://hearingtheamericas.org/s/the-americas/page/okeh-records |
| 404 | https://hearingtheamericas.org/s/the-americas/item/235' |
| 404 | https://hearingtheamericas.org/s/the-americas/page/popular-band |
| 404 | https://hearingtheamericas.org/s/the-americas/page/$%7Bt.recordings_url%7D |
| 404 | https://hearingtheamericas.org/s/the-americas/page/$%7Bt.omeka_item_url%7D |
| 404 | https://hearingtheamericas.org/s/the-americas/page/$%7Bt.item_url%7D |
| 404 | https://hearingtheamericas.org/s/the-americas/item/739 |
| 404 | https://hearingtheamericas.org/s/the-americas/item/28 |
| 404 | https://hearingtheamericas.org/s/the-americas/item/%20https:/www.loc.gov/pictures/item/96521549 |
| 404 | https://hearingtheamericas.org/hearing/s/the-americas/page/minstrelsy |

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  |   285 |
| `href=` |   365 |

**Top broken path prefixes**

| count | prefix                          |
| ----: | ------------------------------- |
|   674 | `files/original/`               |
|   384 | `s/the-americas/index/`         |
|    30 | `s/the-americas/item/`          |
|     9 | `s/the-americas/page/`          |
|     6 | `s/the-americas/item-set/67`    |

Locally surviving under `files/`: `asset/` (this site is Omeka S, not classic — `theme_uploads/` doesn't apply). All Omeka media-derivative dirs were excluded at crawl time.
