# hearingtheamericas.org

*Hearing the Americas* explores the early decades of the recording industry
(1898–1925), posing new questions about the origins of popular music. A project
of the Roy Rosenzweig Center for History and New Media at George Mason
University, with funding from the National Endowment for the Humanities.

It was an Omeka S site. It was flattened to a static archive and brought to
WCAG 2.2 AA in August 2026 (see [docs/retrofit.md](docs/retrofit.md)), and is
now a Hugo site so that it can be added to. The Hugo build reproduces that
archive page for page: `scripts/parity.py` compares the two and reports two
differences across all 964 pages and 225 other files, both on purpose. Item
set pages list every item, where the archive kept only Omeka's first page of
50 (so item set 56, Songs, was missing 22). `timeline.json` carries `alt`
text for the three timeline images that have no caption or credit.

## Layout

| what | where |
|---|---|
| Items (374) | `content/s/the-americas/item/<id>.md` → `layouts/item/single.html` |
| Media (529) | `content/s/the-americas/media/<id>.md` → `layouts/media/single.html` |
| Item sets (11) | `content/s/the-americas/item-set/<id>.md` → `layouts/item-set/single.html` |
| Written pages (45), home, search, Artists | `content/**/*.html`: the HTML the Omeka page-block editor produced, inside the site's templates |
| Timeline | `static/timeline/timeline.json` → `layouts/timeline/single.html` |
| Navigation | `[[menus.main]]` in `hugo.toml` |
| Theme, modules, fonts, maps, audio | `static/`, unchanged from the archive |
| Omeka's JSON-LD records | `assets/jsonld/`, emitted verbatim on each resource's page |
| Property labels for "Related to" lists | `data/properties.yaml` |
| URL repairs | `static/redirects.caddy`, imported by the host's Caddy |

URLs are the Omeka S ones (`/s/the-americas/item/4.html`), so links,
bookmarks and the redirects keep working.

## Adding content

**An item.** Copy an item file and give it a new `id` (and file name). Front
matter:

```yaml
title: The Laughing Song
id: 1
class: recording        # the Omeka resource class: recording, person, primary Source, …
resource_class: Sound   # the label shown when other items link here
created: '2017-10-05T21:46:26+00:00'   # orders browse and item-set listings, newest first
item_sets: [56]
media: [1134, 1136]     # media ids, in display order
role: Coon Song         # optional, shown under the title
properties:
- term: dcterms:title
  label: Title
  values:
  - text: The Laughing Song
- term: bibo:performer
  label: Performer
  values:
  - item: 6             # or item-set: 55, media: 938
- term: dcterms:source
  label: Source
  values:
  - uri: https://example.org/record
    label: Example Archive
```

A value is `text:` (escaped), `html:` (as is), `uri:` with an optional
`label:`, or a reference to an `item:`, `item-set:` or `media:` by id. The
"Related to" list on the item a reference points at, item-set pages, the item
and item-set browse pages and the Artists page (item set 55) are all built from
these, so a new item appears everywhere it belongs.

Items that are `class: recording` show their audio first, each followed by the
media's `dcterms:source`; other items show images and embeds only, as the Omeka
theme did.

**A media file.** `item:` is the parent item's id. `kind: image` or `kind: audio`
with `file:` naming the original under `/files/original/`, plus `alt:` and
`link_title:` for an image, or `label:` (the player's accessible name) for
audio. Derivatives are expected at `/files/{large,medium,square}/<hash>.jpg`,
as Omeka made them. `kind: html` with `html:` is for embeds.

The media files themselves are not in this repository. They live in the file
store, and the host serves them at `/files/{original,large,medium,square}/`.
Images placed in written pages are the exception: `static/files/asset/`.

**A written page.** A Markdown or HTML file under `content/s/the-americas/page/`
with `title:` and `body_class: "page <slug> content-warning-banner"`. To put it
in the navigation, add a `[[menus.main]]` entry to `hugo.toml`.

**A timeline event.** An entry in `static/timeline/timeline.json`, in the
TimelineJS sheet's shape. An image's alt text is its `media.alt`, falling back
to the caption and then the credit.

Optional front matter the templates honour: `thumbnail:` (an image path; the
default is the first media's square derivative), `thumbnail_alt:`,
`description:` (default: the first `dcterms:description`), `hide_media:`,
`linked_order:`, `head_title:`, and `head_css` / `head_js` / `head_tail`
(extra tags for the page's `<head>`, as the map pages use).

## Building

```sh
npm ci
hugo
npx pagefind      # search index into public/pagefind, per pagefind.yml
```

`hugo server` previews the site, but media and search won't work there: media
is served by the host, and the search index is built after Hugo.

Deployment is not set up yet: hearingtheamericas.org and
hearamerica.dev.chnm.gmu.edu are still served by chnm/sustainability's static
deploy of its `hearingtheamericas/` directory. The workflow here runs only by
hand and builds without deploying. At cutover it gets the push trigger and
hostnames that chnm/hurricanearchive has (see the comment in the workflow), and
then builds the Docker image in `Dockerfile` (Hugo, then Pagefind) and deploys
through `chnm/.github/.github/workflows/hugo--build-release-deploy.yml`.

## Checking a change against the archive

`scripts/parity.py` compares a build with the static archive, as it stood
once the untitled media were described (chnm/sustainability#142):

```sh
git -C ../sustainability archive c760bd5695 hearingtheamericas | tar -x -C /tmp
hugo -d /tmp/hta-public
python3 scripts/parity.py /tmp/hearingtheamericas /tmp/hta-public -v
```

It resolves URLs, collapses whitespace and normalises comments and character
references, then reports any page that still differs. A content change will
show up there, as it should; it's for checking that template changes don't
change anything else.

`scripts/convert.py` is the one-off migration that produced `content/` from
that archive. It refuses to run once `content/` exists.

## Known deviations from Omeka

- **"Related to" order** for eleven items is kept in `linked_order:`. Omeka
  ordered those lists by database row, which no longer exists. Everywhere else
  the order is computed.
- The known gaps in [docs/retrofit.md](docs/retrofit.md#known-gaps) (untitled
  media, the six Library of Congress recordings, eight links to things the
  origin had already deleted) are unchanged.
