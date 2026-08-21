# hearingtheamericas.org

*Hearing the Americas* explores the early decades of the recording industry
(1898–1925), posing new questions about the origins of popular music. A project
of the Roy Rosenzweig Center for History and New Media at George Mason
University, with funding from the National Endowment for the Humanities, it is
built around 374 items — recordings, sheet music, advertisements, catalogues,
photographs — and 46 written pages that argue through them: 23 "Spins"
(questions with answers), 8 "Styles", 9 "Notes", and a browse of the artists.

## Retrofit

This is the second **Omeka S** site in the set, after
iowmaterialhistorieswebinar.org, so the URL vocabulary is `/s/<site-slug>/item/4`
rather than Omeka Classic's `/items/show/4`. The failure modes are the ones the
siblings had, plus three this site owns.

The crawled mirror still behaved like a live install. The search box on all 384
captured pages posted to a database endpoint. Every media file was hot-linked to
the origin — 3,428 absolute references across the export. The theme fetched its
two typefaces from Google on every page view and its jQuery from Google's CDN,
with no fallback, and `default.js` is entirely inside `(function($){…})(jQuery)`.
The content-warning banner was injected by a script that first pulled a third
typeface from Google. Every one of the 4,912 images carried `alt=""` or no `alt`
at all.

It was also **badly incomplete**, which was the more urgent problem. The crawl
captured 382 of the 961 URLs the origin serves. Nothing in the site's navigation
points at the item browse, the item-set browse or any media page, so wget never
found them, and through them never found 55 items, 523 media pages or one item
set. The origin was still up when this work started, so all of it was fetched
rather than reconstructed.

And three things on it were not archives of anything — they were live
applications:

- **Artists**, one of the five items on the main menu, was an empty `<div>` and
  three `data-url` attributes naming server endpoints. It rendered a hero image,
  a heading, and nothing else.
- **The home page timeline** was an iframe into KnightLab's CDN with a Google
  Sheet id in the query string.
- **The Victor Recording Expeditions map** drew its country outlines from a live
  API on another host, and built its links and audio players from absolute URLs
  to the origin baked into a 300 KB JavaScript bundle.

This directory holds only what gets served. The transformations were made by a
set of one-off scripts that are **not kept here** — this repository is
deployment artifacts, and `context_root` is copied to the web root wholesale, so
anything else in this directory would be served publicly. What they did is
recorded below in enough detail to redo it. They were idempotent and took a
`--check` flag, so a second run left `git diff` empty; the archive as committed
is a fixed point.

Order mattered in three places. The origin data had to come first, because
everything downstream would otherwise emit dead links, and because the site goes
away the moment the DNS moves. The 961 pages were then rebuilt from the
*pristine* origin HTML rather than patched from the crawl, so that a single
template governs the head, the header, the navigation, the footer and the Matomo
block on every one of them and they cannot drift apart. And the Pagefind index
was built last, because it indexes the HTML as committed.

| what | where |
|---|---|
| Static search | `pagefind/` (committed — the deploy only copies files), `pagefind.yml`, `themes/hearing_americas/asset/js/search.js`, `search.html` |
| Accessibility | `themes/hearing_americas/asset/css/a11y.css`, plus the markup itself |
| Artists browse | `s/the-americas/faceted-browse/1.html`, `themes/hearing_americas/asset/js/artist-facets.js` |
| Timeline | `timeline/` — `index.html` is generated from `timeline.json`; `timeline.js` + `timeline.css`, no dependencies |
| Maps | `basemap/protomaps-basemap.pmtiles`, `modules/Mapping/asset/js/omeka-basemap.js`, `modules/Mapping/asset/vendor/protomaps-leaflet.js` |
| Expeditions geometry | `data/ne/globe-{north,south}-america.json` |
| Fonts | `themes/hearing_americas/asset/css/fonts.css` + `fonts/*.woff2` — Crimson Text, Montserrat; `modules/bannerMessage/asset/fonts/` — Open Sans; `themes/…/asset/font/` — League Spartan; `application/asset/fonts/` — Font Awesome 5 |
| Vendored JS | `application/asset/js/vendor/jquery.min.js`, `vendor/soundcite/` |
| Recovered audio | `audio/` — the 23 clips the pages played from a third-party host |
| Media | referenced as `/files/…`; the objects themselves live in the bucket |
| URL repair | `redirects.caddy` |

### What the crawl missed

Omeka S serves `/s/<site>/item`, `/s/<site>/item-set` and a page for every
media object, but this site's navigation is Spins / Styles / Notes / Artists /
About, and none of those is on it. Everything reachable only through them was
invisible to wget.

The gap was closed from the origin's own REST API (`/api/items`, `/api/media`,
`/api/site_pages`, `/api/item_sets`, `/api/assets`, `/api/mapping_markers`),
which is the authoritative list and which also supplied the file inventory, the
map markers and the alt text below.

| | origin serves | crawl captured | recovered |
|---|---:|---:|---:|
| Home page | 1 | 1 | — |
| Site pages | 45 | 45 | — |
| Items | 374 | 319 | **55** |
| Media | 529 | 6 | **523** |
| Item sets | 11 | 10 | **1** |
| Artists browse | 1 | 1 (empty) | rebuilt |
| **Total** | **961** | **382** | **579** |

Three browse listings are built that the origin only produced as database
queries: `s/the-americas/item.html` (all 374 items on one page, in the origin's
default created-descending order), `s/the-americas/item-set.html`, and the
Artists page below. Their server-side pagination, sort forms and advanced-search
links are dropped rather than left as controls that do nothing. `search.html`
links to all three, so the 228 items that belong to no item set and appear on no
menu are now reachable by browsing as well as by searching.

### The Artists page

`/s/the-americas/faceted-browse/1` is one of the five entries on the main
navigation. In the crawl it was this:

```html
<div id="container"
    data-url-categories="/s/the-americas/faceted-browse/1/categories"
    data-url-facets="/s/the-americas/faceted-browse/1/facets"
    data-url-browse="/s/the-americas/faceted-browse/1/browse">
    <div id="section-sidebar"></div>
    <div id="section-content"></div>
</div>
```

Three XHR calls to endpoints a static host cannot answer, into two empty divs.

The endpoints were still live when this was built, so the page is rebuilt from
what they actually returned: the 49 items of item set 55 in the category's own
created-ascending order, and the single **Style** facet the category defined — a
single-select list over `dcterms:subject` with nine values. The facet is applied
in the page now instead of by a database query, and reproduces Omeka's
`query_type: "in"` substring match rather than switching to equality, so the
same artists come back for the same choice as they did on the live site. Without
JavaScript all 49 artists are listed and the facet is hidden, which is more than
the original page managed *with* JavaScript.

Its hero image was hot-linked to `github.com/chnm/hearing-the-americas`, through
the `?raw=true` redirect. It is in the theme's own image directory now.

### The timeline

The home page carried this:

```html
<iframe src="https://cdn.knightlab.com/libs/timeline3/latest/embed/index.html?source=1QA4375O8BUp5pUas5Yr0duph-Pg5fRYmHJ0ZcKLLuDE&…">
```

— which made a headline feature of the site depend on KnightLab's CDN, on
Google Sheets, and on one spreadsheet's sharing settings never changing. All
three were still answering, so the sheet was exported and committed as
`timeline/timeline.json`: 1 title slide and 19 events, 1877 to 1926. Eight
slide images that the sheet hot-linked to Wikimedia Commons, the Library of
Congress and one third-party site are mirrored in `timeline/media/`; see the
`PROVENANCE.txt` there. The rest come from the bucket.

TimelineJS itself was vendored at first, and then removed. Keeping it meant
carrying 1.4 MB — 224 KB of library, 976 KB of PT Sans and PT Serif, an icon
font, and media handlers for fifteen services this archive does not use, three
of them holding KnightLab's own Flickr, Google Maps and Facebook credentials —
to draw twenty slides. `timeline/timeline.js` and `timeline/timeline.css` are
13 KB together and have no dependencies.

`timeline/index.html` is **generated from `timeline.json`** by the same script
that builds the rest of the archive, so the markup and the data cannot drift
apart. Two things follow from generating it as static HTML rather than building
it in the browser:

- **Without JavaScript the timeline still reads.** Every slide is in the page,
  one after another, as a document. TimelineJS rendered an empty box.
- **It is searchable.** Those twenty slides were the only prose in the archive
  Pagefind could not index; `/timeline/` is a search result now.

`timeline.js` turns that stack into one-slide-at-a-time with a navigation strip
below: two lanes, one per group, earliest first; a marker per event positioned
by year; decade ticks; previous and next; and arrow keys, Home and End. Four
events share 1917 and two each share 1912 and 1920, so markers are packed into
as many rows per lane as they need — every one at its true date, none within
28px of another, which is also what keeps them 24px apart for 2.5.8. The
packing is redone on resize.

The slides carry the backgrounds the sheet specified: seventeen a colour, three
a photograph. White text on the four colours in use runs from 6.02:1 to
17.39:1. The photographs get a 0.65 black scrim, which puts white text at 7:1
even over a pure white image — a floor, not an average.

### Maps

There are two kinds of map here and both were somebody else's service.

**The Mapping module** draws four Leaflet maps — one on the African-American
Theater Circuits page, showing three circuits, and one on each of the three
items behind them — from 48 markers. It fetched tiles through leaflet-providers:
`OpenStreetMap.Mapnik` by default, with `CartoDB.Positron`, `Esri.WorldImagery`
and `Esri.WorldShadedRelief` in the layer control. OSM's tile CDN has a usage
policy a public archive should not lean on and CARTO's basemaps are an
Enterprise product.

`basemap/protomaps-basemap.pmtiles` replaces all four: 34 MB of
OpenStreetMap-derived vector tiles (ODbL), served out of static storage over
HTTP range requests, with no API key and no account. The world at z0–5 and the
eastern and central United States at z6–8, which is where all 48 markers are.
See `basemap/PROVENANCE.txt` for how it was built and why it stops where it
does. The four-entry layer control is gone: there is one basemap now, and a
control offering four copies of it would say nothing.

**The Victor Recording Expeditions map** is a bundled D3 visualisation with its
own data inlined — 300 KB of JavaScript in a `<script>` tag on the page. Three
things in it pointed off the archive, all of them in JavaScript string literals
that no `href`/`src` rewrite would have touched:

- two calls to `https://data.chnm.org/ne/globe?location=…` for the country
  outlines it draws. Both responses are committed under `data/ne/`.
- twelve `https://hearingtheamericas.org/files/original/*.mp3` recordings, now
  root-absolute so they reach the bucket.
- one item permalink, now an archive-relative link.

Its year slider was an `<input type="range">` with no label — the two labels
beside it read "1902" and "1926" and point at ids that do not exist on the page.

### Audio

Recordings are what this site is about, and they came from three places.

**The bucket.** 136 audio files are Omeka media and are in object storage with
everything else.

**SoundCite**, KnightLab's inline-clip player, is used in 66 places across 23
pages — the device the site uses to say "listen to this bar, now listen to this
one". It was loaded from `cdn.knightlab.com`, and it in turn fetched Popcorn
from the same CDN at run time. Both are vendored under `vendor/soundcite/`, with
the loader's hard-coded CDN path repointed at the local copy.

**spokeshave.net.** 21 of the clips SoundCite plays, and two more that pages
link directly, were mp3s on a third-party host, 22 of the 24 references over
plain `http://`. All 23 files are recovered into `audio/`, preserving their
paths so the mapping is legible. Two repairs while doing it:
`crave melody.mp3` had a space in its filename that was never URL-encoded, so
that clip had never played at all — it is `crave-melody.mp3` now; and
`music/joplinflat.mp3` and `music/hta/joplinflat.mp3` are byte-identical, so one
copy serves both references.

**The Library of Congress**, on six media records, through a Flash player:

```html
<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000">
  <param name="movie" value="http://media.loc.gov/player/flowplayer.commercial.swf?0.108…">
  <param name="flashvars" value="config=http://media.loc.gov/media/embed/id/A2671ACD7E0C…">
```

Flash was removed from every browser in 2020, and both the player and every one
of the six config addresses now answer 404 — these had been rendering as nothing
at all for years. They are replaced by a note that says what the recording was
and why it cannot be played, keeping the National Jukebox id in a data
attribute. The six are tango recordings; the audio is not in the archive, and
recovering it from the Library's current catalogue is a curatorial job.

### Static search

Omeka S ran search at `/s/the-americas/index/search`, a database query. The
theme put a search box in the header of every page, so **all 384 captured pages
carried a form posting to an endpoint a static host does not have** — and
`wget --convert-links` had rewritten its `action` to the absolute origin URL, so
after the DNS moves it would not even have failed locally.

It is re-implemented client-side with [Pagefind](https://pagefind.app):

- **`search.html`** reads `?fulltext_search=`, the parameter name Omeka S itself
  used, so links and bookmarks of the old shape still land on a real result set
  (`?q=` and `?query=` are accepted too).
- **The header form on every other page** now targets it, in the slot the theme
  already had. On `search.html` that same header form *is* the search form —
  there is no second box.
- `pagefind/` — the prebuilt index, committed, so the site stays a pure static
  deploy with no build step. `pagefind.yml` regenerates it.

Built on Pagefind's **core API** rather than its Default UI, which renders its
own input: that would be a second search box on a page whose header already has
one, and the sibling archives work around it by hiding Pagefind's input and
driving it from the header, leaving an invisible control in the DOM.

**Index scope.** 963 pages, 8,881 words. Only `<main data-pagefind-body>` is
indexed: the header, the 40-link navigation, the content-warning banner and the
footer are byte-identical on every page, and indexing them would make every
page a hit for every word on the menu. The three browse listings are indexed for their own
text, but their link lists are not — every word in them is a title indexed on
the page it points at. `search.html` indexes nothing of its own.

**Search recall is bounded by the data.** 8,881 words across 963 pages. The 46
written pages carry most of the prose; a typical item page is a title, a
performer, a label, a date and a one-line description.

### Accessibility (WCAG 2.2 AA)

The archive was a raw crawl with no remediation. Verified with **axe-core**
(`wcag2a`/`2aa`/`21a`/`21aa`/`22aa`) → **0 violations**, across a 154-URL sample
covering every page type — the home page, all 45 written pages, all 11 item
sets, the three browse listings, the search page empty and with a query, the
timeline, and 45 items and 45 media pages drawn at random — at 1280px, 375px and
320px, plus a keyboard pass and a horizontal-overflow check at each width, all
driven through real headless Chromium. jsdom would not do: it cannot compute
colour contrast or target size, and it cannot run Pagefind's WebAssembly index,
Leaflet's canvas renderer or the D3 bundle, so the pages that matter most here
would audit as empty shells.

- **Headings (1.3.1)**: the theme made the site title the `<h1>` of all 963
  pages, so no page's `<h1>` said anything about that page, and content started
  at `<h2>`. Beneath that the page-block editor skipped levels freely: `h2 → h4`
  on 377 pages, which is every item and media page. The site title is a `<p>`
  now, and the content headings are renumbered so no level is skipped.

  **The rendering is unchanged, and that is measured rather than asserted.**
  Each renumbered heading carries a `heading-N` class naming the level it used
  to be. `a11y.css` restates what that level rendered as — the theme's
  font-family, font-size and line-height, and the browser's default margins,
  which are expressed in `em` and so have to move with the font-size rather
  than be inherited from whatever tag the heading now uses.

  That is not sufficient on its own, because the theme also styles headings
  *contextually* — `.div-banner h2`, `.property h4`, `.file h3`, `.shelf2 h3`,
  `#content>h1:first-child` and 29 more, several of them per breakpoint. Every
  one of those selectors now has two halves: `X hN:not([class*="heading-"])`,
  which matches a heading that was always level N, and `X .heading-N`, which
  matches one that merely rendered as it. The `:not()` matters as much as the
  twin: without it, the 529 media pages — whose first content child is their
  title heading — would newly match `#content>h1:first-child` and pick up a
  centred layout and a decorative rule the origin never drew there.

  Verified by building the whole archive a second time with renumbering
  switched off, rendering both copies in headless Chromium at 1280px and 375px,
  and comparing every element in the content region on thirteen computed
  properties and its bounding box, and separately by asserting the invariants
  themselves over all 965 pages: the site title is never a heading, `<main>`
  opens at `h1`, no level is skipped, no heading carries a `heading-N` class
  naming its own level, and no heading is empty.

  That second check exists because the first one was, for a while, lying. The
  variant builder symlinked the repo's directories into its output and then
  wrote through them, so it clobbered the real archive with un-renumbered pages
  and compared that tree against itself: 16,086 comparisons, zero differences,
  and the renumbering silently reverted across all 961 pages in the process.
  Nothing else caught it, because axe's `heading-order` rule is in its
  best-practice tag set rather than the WCAG tags the sweep filtered on, so a
  document with `h2 → h4` skips and a site-title `<h1>` on every page audits
  clean. The builder now refuses to write outside its own directory, the sweep
  includes `best-practice`, and the invariants are asserted directly rather
  than inferred from a comparison. The comparison, re-run against two trees
  that genuinely differ, reports zero differences over 3,884 element/viewport
  comparisons. The check found three real regressions
  while it was being written: the missing `line-height` restatement, which gave
  every property label on 377 item pages a 45px line box instead of 30px; the
  `.div-banner h2` case, which had left the Artists heading unstyled; and the
  multi-line selectors that a first, line-based rewrite had missed.
- **Images (1.1.1)**: all 4,912 of them carried `alt=""`, or no `alt` attribute
  at all, which is not the same thing and is worse. 3,525 are described now,
  from the `dcterms:title` of the media object the image depicts, keyed on the
  file hash in the URL; ten Omeka assets carry authored `o:alt_text` and that is
  used where it exists. The remaining 1,387 are marked decorative on purpose:
  the theme's record sleeves, spinning discs and shelves, and Omeka's
  media-type placeholders. The two logos in the footer credit are named, because
  they say who made this and who paid for it.
- **Use of colour (1.4.1)**: links are `#b13a1a` with `text-decoration: none`,
  against `#3a2e2e` body text — 2.16:1, well under the 3:1 that colour alone
  needs. Underlines are restored across the content region, the footer and both
  content-warning banner, and taken back off where a link sits among nothing
  but other links,
  wraps an image, or is drawn as a button. Restoring them only in `<p>` and
  `<li>` would not have been enough: this site puts prose straight into styled
  `<div>`s and its bibliographies into `<cite>`.
- **Contrast (1.4.3)**: `a:hover` was `#dd4921`, 4.16:1 on white — under the
  4.5:1 that 20px non-bold text needs. Contrast applies in every state, and no
  automated checker tests hover, so this is a repair the audit above cannot
  report. `#d0451f` is the same hue and saturation three points darker: 4.61:1.
- **Reflow (1.4.10)**: five pages scrolled horizontally at 320px and four still
  did at 1280px, hidden by a `body { overflow-x: hidden }` the theme applies
  only above 1200px. Every one was a fixed pixel width: 300px audio players in
  130px columns, a 290px callout, four 300px cards with 50px margins, 250px flip
  cards inside 100px margins, and a hero image drawn at `calc(100% + 1.25%)` to
  negate padding that a later rule in the same media block sets to zero. No page
  scrolls horizontally now at 320, 375, 800, 1000, 1150, 1280 or 1600px.
- **Focus (2.4.7, 2.4.11)**: the theme defines no focus styling anywhere except
  the skip link. Worse, the spin discs flip on hover to reveal their answer and
  a "learn more" link, and both faces are `backface-visibility: hidden` — so a
  keyboard user tabbing through 23 cards put focus on 23 links they could not
  see. Focus flips the card now, exactly as hover does.
- **Link purpose (2.4.4)**: those same 23 links were all named "learn more".
  Each carries the question from the front of its own card now.
- **Link name (4.1.2)**: browse listings render each resource twice — a
  thumbnail link and a title link to the same page — and the thumbnail link's
  accessible name was an empty `alt`. Those are hidden from assistive technology
  and from the tab order.
- **Landmarks (1.3.1)**: `<div id="content" role="main">` is a `<main>`, the
  navigation is named, and the header search form is a `search` landmark.
- **Labels (1.3.1, 4.1.2)**: the year slider on the Expeditions map had none;
  every `<audio controls>` was announced as nothing but "audio player", and this
  site puts three of them on one page. Each is named after the recording it
  plays, and where the media is titled with nothing but its cylinder or matrix
  number the parent item's title carries it: *The Laughing Song — 14568*.
- **Target size (2.5.8)**: the genre tags under each record on the Style pages
  are 12.5px uppercase links on a 15px line. At 375px and below that is a
  53×15px touch target where WCAG 2.2 asks for 24×24. Padding on an inline box
  grows the hit area without moving the line.
- **Frame title (4.1.2)**: the timeline and YouTube iframes had no `title`.
- **Parsing**: `lang=""` on every metadata value whose language Omeka did not
  know, and `id="explore-cards"` on all four cards on the home page. The theme
  styled that id; it styles a class now.
- WCAG 2.2's other AA additions are satisfied without change and were confirmed:
  2.5.7 Dragging Movements and 3.3.8 Accessible Authentication (neither exists
  here), 3.2.6 Consistent Help and 3.3.7 Redundant Entry (no help mechanism, no
  multi-step flows).

**The content warning.** It is real markup now rather than something a script
prepends, so it survives with JavaScript off and is visible to an indexer; it
carries `data-pagefind-ignore` so it does not make every page a search hit. The
skip link stays ahead of it in `<body>`: a keyboard user should not have to tab
past a link to reach the one that exists to save them the trouble.

### Robustness

Nothing outside the archive is fetched any more except Matomo. Verified in real
headless Chromium with every other host blocked at the network layer: across the
home page, the map pages, the SoundCite pages, the Expeditions map, the search
page and the Artists page, the only outbound request is `stats.rrchnm.org`.

- **Crimson Text and Montserrat are self-hosted.** Every page's `<head>` loaded
  them from `fonts.googleapis.com`. The `@font-face` blocks in `fonts.css` are
  Google's own, taken from the stylesheet it returns for exactly the request the
  theme made. Of the three subsets Google offers for Crimson Text and the five
  for Montserrat, only `latin` and `latin-ext` are kept: the archive's text is
  99.9% basic Latin, and every exception — the macrons in Hawaiian words, the
  accents in Spanish and Portuguese titles — is latin-ext. The theme asked for
  weight 400 only, so bold text was synthesized by the browser; that is
  preserved, because a real 700 face would change the rendering.
- **Open Sans is self-hosted too.** `warning-style.css` opened with
  `@import url('https://fonts.googleapis.com/css?family=Open+Sans&display=swap')`,
  which made all 962 pages carrying the content-warning banner fetch a
  stylesheet and then a font from Google for one sentence of English.
- **jQuery 3.5.1 is vendored** (sha256 `f7f6a589…`, matching the published SRI).
  Every page loaded it from `ajax.googleapis.com` with no fallback, and
  `default.js` is entirely inside `(function($) {…})(jQuery)` — so a blocked CDN
  took the theme's JavaScript with it.
- **Font Awesome 5 and League Spartan are self-hosted already**, but the crawl
  had saved each `.eot` twice, once under the literal filenames
  `fa-solid-900.eot?` and `leaguespartan-bold.eot?` — names no web server can
  return, because the `?` starts a query string. Both `@font-face` blocks are
  trimmed to `woff2` + `woff`; the `.eot`, `.ttf` and `.svg` sources only ever
  served IE8 and Android 4.
- **Two Leaflet marker images were missing.** `marker-icon-2x.png` and
  `marker-shadow.png` are requested by `L.Icon.Default` at run time, not named
  in any stylesheet, so the crawl never saw them. Fetched from the origin.
- The crawl's asset filenames carried their cache-busting query strings into the
  *filenames* (`style.css?v=0.0.3.css`, `global.js?v=3.1.2`). They are named
  plainly now.
- Every `href`, `src` and `action` is relative, except `/files/…`, which is
  root-absolute so it reaches the bucket.
- Text is NFC-normalised. Two strings in the archive carried decomposed accents —
  *première* with a combining grave, *Gaitán* with a combining acute — which are
  the only two characters that would have needed a third font subset, and which
  no search index would have matched against their composed spellings.

### Chrome

**The footer credit carries three logos**, not two. The sentence beside them
says the site is "a project of the George Mason University with funding from
the National Endowment for the Humanities", but only RRCHNM and the NEH were
pictured; the GMU Department of History and Art History mark goes between them,
in the gap the theme's `space-between` flex row already left for it. It is
byte-identical to the copy the `iowmaterialhistorieswebinar.org` archive ships
(sha256 `497b803e…`), so the two sets of credits stay consistent.

That row sizes its logos at a fixed 300px with no `max-width`, so below the
width at which they all fit the flex algorithm shrank them rather than
wrapping: at 375px each was 92px across and the fine print on the GMU mark was
unreadable. Two fitted in a 1280px viewport, three do not below about 1170px,
so from there down the row wraps and each mark keeps its size.

**There is no "this is a static copy" banner.** The sibling archives put one
across the top of every page; this site does not need it. The footer already
credits RRCHNM by name and wordmark on all 964 pages, and a banner would have
been saying a second time what the page already says — above the skip link and
above the site's own content warning, which is the one notice here that a
reader does need to see first.

The theme nested `<footer>` inside `<footer>`; the wrapper is gone. `<title>` on
every page read *Hearing the Americas · X · Hearing the Americas*, because
Omeka's `headTitle` appends the site name and the theme had already prepended
it — one is enough, and it is what a bookmark, a browser tab and a search result
all show.

### Media

The 1,640 objects under `files/{original,large,medium,square}` (886 MB) were
excluded at crawl time and are **not in this repo** (`.gitignore` blocks them).
They were fetched from the origin into a staging tree outside this repository,
with a `manifest.tsv` recording each object's URL, path, size and sha256, for
loading into the object bucket. The list came from the API (`o:original_url` and
`o:thumbnail_urls` on each of the 529 media records), not from a crawl, so it is
complete by construction: 521 originals — eight media are HTML or YouTube
embeds and have no file — and 373 each of `large`, `medium` and `square`.

`files/asset/` is different: those are the images editors dropped into page
blocks, they are small, and they are committed here. Three of the 66 were
missing from the crawl and were fetched from the origin.

Until the bucket and the web server's `/files/` handler are live on the deployed
host, every image and every recording 404s; they previously rendered only by
hot-linking the origin. Check with:

```sh
curl -sIL https://hearamerica.dev.chnm.gmu.edu/files/square/ddfc4293857e8580722178c993faf6a8e3ff1ee0.jpg
```

### Analytics

Matomo, site id **11**, at `https://stats.rrchnm.org/`. All 963 origin pages
already carried it; the block is normalised to one identical copy across all 964
content pages. `timeline/index.html` deliberately does not carry it — it is an
iframe inside a page that already counts the view.

### Redirects

`redirects.caddy` repairs the extensionless URLs the export renamed
(`/s/the-americas/item/4` → `…/4.html`), sends the site root and
`/s/the-americas/page/welcome` to `/` — Omeka served the home page at three URLs
and the archive keeps one — carries the old `fulltext_search` query on to
`search.html`, collapses the server-side browse pagination and the advanced
search onto the one-page listings, points the three dead FacetedBrowse endpoints
at the page that replaced them, and answers `410` for `/api`, `/admin` and
`/login`, which no static host can stand in for. Every rule was checked with
`caddy validate` and exercised against a running Caddy 2.10.2; every redirect
was followed to a 200.

**Two things about the deployed environment, observed on the live hosts.** None
of these rules fires on `hearamerica.dev.chnm.gmu.edu` — not even the `410`
block — although the build itself is deployed; the sibling archives' rules do
fire on their prod hosts, so importing `redirects.caddy` looks like a per-vhost
step rather than something the build carries. And on those prod hosts `redir`
works but `respond` does not: `iowmaterialhistorieswebinar.org/api` answers 404
rather than the 410 its own file asks for. That does not change what belongs in
this file. `/api`, `/admin` and `/login` stay excluded from `@needs_html` either
way, because without the exclusion `/admin` would 301 to `/admin.html` and 404
there instead — which is what mallhistory.org does today.

### Deployment note

The archive must be served **at a domain root**: `/files/…`, the basemap, the
vendored SoundCite loader and the Pagefind result links are all root-absolute,
as they are on the sibling archives. It is at `hearamerica.dev.chnm.gmu.edu`
today, for both dev and prod
(`.github/workflows/hearingtheamericas--deploy.yml`). Flipping
`website-prod-fqdn` to `hearingtheamericas.org` is the cutover and is
deliberately **not** part of this work — the origin is still live and still
serving the real site.

That flip is what makes one loose end resolve: the `@id` permalinks Omeka wrote
into the JSON-LD block on all 914 resource pages still read
`https://hearingtheamericas.org/api/items/4`, which is what an identifier minted
before the migration should keep saying. Nothing in the archive *fetches* from
that host — those are text. Of the 3,428 `href`/`src`/`action` references to
`hearingtheamericas.org` in the pristine export, zero remain; what is left is
12,786 plain-text mentions across 932 pages, all of them inside those JSON-LD
blocks.

### Known gaps

- **188 media objects carry no `dcterms:title`**, so the images that depict them
  are marked decorative on 405 pages. Their filenames are not descriptions
  (`Screen Shot 2021-07-23 at 6.00.28 PM.png`), and inventing alt text from them
  would be worse than none. In every case a heading or a link beside the image
  names the resource. Writing real descriptions is a curatorial pass.
- **Media pages with no title show their filename as the page heading** —
  `Frank_Ferera.jpg` — because that is Omeka's fallback and what the origin
  serves. They are at least all distinct, so no two pages share a title.
- **Eight internal links point at things the origin itself 404s on.** Five
  items were deleted since publication (23, 28, 334, 378, 739 — Len Spencer,
  Sherman H. Dudley, John McCormack, and two others), and two page slugs were
  never created (`page/jazz`, linked from Samba and Syncopation, and
  `page/okeh-records`, linked from "Where do the blues come from?"). They were
  written in good faith and are left as the authors wrote them; supplying
  targets is a curatorial call, not a migration one.
- **Five other links were repaired**, because each was a slip in the URL rather
  than a page that moved: two `/admin/item/…` addresses written while logged in
  to the Omeka back end, a `/hearing/` staging prefix, a stray apostrophe on an
  item id, and `page/popular-band` for `page/q-popular-band`. One
  `dcterms:source` value on item 512 had a book title where its URI should be,
  so Omeka rendered a citation as a link to a page of that name; it reads as a
  citation now.
- **The six Library of Congress recordings** cannot be played — see *Audio*.
- **Two pages have a flat outline.** The page-block editor put every section
  heading at the same level as the page's own title, so Styles has eight `<h1>`s
  and Notes has ten. The renumbering preserves the sibling relationship the
  source expresses rather than inventing a hierarchy it does not: the theme
  draws the page title larger than the sections, but nothing in the markup ever
  said one contained the other. It is valid HTML5, `heading-order` and
  `page-has-heading-one` both pass, and each page's `<h1>` is its own title.
  Nesting the sections under it would be a content edit.
- **Three Omeka back-end URLs appear as visible text** in the description on
  item 588 — `…/admin/item/937`, `…/admin/media/942`, `…/admin/item/939`,
  pasted into the prose in parentheses. They are text, not links, so nothing
  follows them, and rewriting them would be editing what the author wrote. The
  three that *were* links are repaired above.
- **Outbound links have not been link-checked.** The archive points at 87
  external hosts, many of them library catalogues and newspaper archives that
  have reorganised since 2021.

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

Every one of these is the origin's, not the crawler's, and all of them are
accounted for above. The three `${t.…}` entries are not URLs at all: they are
JavaScript template literals inside the Expeditions bundle, which wget read as
`href` attributes and dutifully tried to fetch. The Library of Congress one is a
URL pasted after a stray space into an item id.

## Surviving absolute URLs to dead origin

In-tree HTML scan. `--convert-links` only rewrites refs to files wget actually
downloaded — anything filtered stayed as the absolute origin URL and would 404
once the live site is gone.

Measured across the 963 pristine origin pages, and again across the 965 rebuilt
ones.

| attr      | at crawl | after retrofit |
| --------- | -------: | -------------: |
| `src=`    |    1,825 | 0 |
| `action=` |      384 | 0 |
| `href=`   |    1,603 | 0 |

No `href`, `src` or `action` anywhere in the archive resolves to
`hearingtheamericas.org` now. What remains is 12,786 plain-text mentions across
932 pages: the JSON-LD block Omeka wrote into each resource page, whose `@id`
and `thumbnail_display_urls` are identifiers rather than links, and are not
fetched.

## Rebuilding

The origin was live while this was done, and the API is what everything was
built from. To redo the harvest while it still answers:

```sh
for n in items media site_pages item_sets sites assets mapping_markers; do
  curl -s "https://hearingtheamericas.org/api/$n?per_page=100&page=1" -o "api-$n.json"
done
```

`items` and `media` need pagination — 374 and 529 records against a 100-per-page
cap. Every page URL in the archive is derivable from those files, and every media
object from `o:original_url` and `o:thumbnail_urls` in `api-media.json`.

Three things came from endpoints that are not part of the REST API and that only
exist while the application is running:

```sh
curl -s "https://hearingtheamericas.org/s/the-americas/faceted-browse/1/categories"
curl -s "https://hearingtheamericas.org/s/the-americas/faceted-browse/1/facets?category_id=1"
curl -s "https://hearingtheamericas.org/s/the-americas/faceted-browse/1/browse?item_set_id%5B%5D=55&faceted_browse_category_id=1"
```

and the timeline from
`https://docs.google.com/spreadsheets/d/1QA4375O8BUp5pUas5Yr0duph-Pg5fRYmHJ0ZcKLLuDE/export?format=csv`.

The media staging tree and its `manifest.tsv` are at
`~/media-staging/hearingtheamericas.org/` on the machine this was run on; all
1,640 objects verify against the manifest's sha256 sums. The pristine origin
HTML is at `~/origin-cache/hearingtheamericas.org/`, 963 files.
