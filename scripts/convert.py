#!/usr/bin/env python3
"""Convert the flattened hearingtheamericas.org archive into Hugo content.

Usage: convert.py BASELINE_DIR

BASELINE_DIR is the static archive as it stood before the Hugo conversion
(`git archive <rev> hearingtheamericas`). Every page becomes a file under
content/ whose front matter carries what the shared templates need (title,
body class, extra head tags) and whose body is the page's <main>, with every
relative URL rewritten root-absolute so it reads the same from any file.

Idempotent: a second run leaves `git diff` empty.
"""
import html
import json
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SITE = " · Hearing the Americas"

# Every page's <head> is this list plus page-specific extras; see head.html.
BASE_HEAD = [
    "themes/hearing_americas/asset/css/fonts.css",
    "application/asset/css/iconfonts.css",
    "themes/hearing_americas/asset/css/style.css",
    "modules/MetadataBrowse/asset/css/metadata-browse.css",
    "modules/bannerMessage/asset/warning-style.css",
    "s/the-americas/css-editor.css",
    "application/asset/js/vendor/jquery.min.js",
    "application/asset/js/global.js",
    "themes/hearing_americas/asset/js/default.js",
    "themes/hearing_americas/asset/css/a11y.css",
]

URL_ATTR = re.compile(r'\b(href|src|action|poster|data-[\w-]*url[\w-]*)="([^"]*)"')
CSS_URL = re.compile(r"url\((['\"]?)([^)'\"]+)\1\)")


def absolute(url, page):
    """Resolve a URL found on PAGE (a root-relative path) to root-absolute."""
    if not url or re.match(r"^(?:[a-z][\w+.-]*:|/|#|\?|\$\{)", url, re.I):
        return url
    base = posixpath.dirname("/" + page)
    path, sep, rest = re.match(r"([^?#]*)([?#]?)(.*)", url).groups()
    out = posixpath.normpath(posixpath.join(base, path)) if path else "/" + page
    if path.endswith("/") and not out.endswith("/"):
        out += "/"
    return out + sep + rest


def rewrite(fragment, page):
    fragment = URL_ATTR.sub(lambda m: f'{m[1]}="{absolute(m[2], page)}"', fragment)
    return CSS_URL.sub(lambda m: f"url({m[1]}{absolute(m[2], page)}{m[1]})", fragment)


def head_extras(head, page):
    """The page's head tags that are not in BASE_HEAD, by the slot head.html puts
    them in (after style.css, after default.js, or last), and the base ones it omits."""
    slots = {"head_css": [], "head_js": [], "head_tail": []}
    seen = []
    for tag in re.findall(r"<(?:link|script)\b[^>]*>(?:</script>)?", head):
        url = re.search(r'(?:href|src)="([^"]+)"', tag)
        ref = url and absolute(url[1], page).lstrip("/")
        if ref in BASE_HEAD:
            seen.append(ref)
        elif ref:
            slot = "head_tail" if BASE_HEAD[-1] in seen else "head_js" if BASE_HEAD[-2] in seen else "head_css"
            slots[slot].append(rewrite(tag, page))
    slots["head_omit"] = [r for r in BASE_HEAD if r not in seen]
    return slots


def front_matter(fields):
    return "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in fields.items() if v not in (None, [], "")) + "---\n"


def target(page):
    """Where PAGE's content file goes so Hugo (uglyURLs) renders it at PAGE."""
    if page == "index.html":
        return CONTENT / "_index.html"
    p = Path(page)
    # item.html and item-set.html are the listings of the item/ and item-set/ sections.
    if (CONTENT / p.with_suffix("")).is_dir() or p.stem in ("item", "item-set") and p.parent.name == "the-americas":
        return CONTENT / p.with_suffix("") / "_index.html"
    return CONTENT / p


def convert(src, page):
    s = src.read_text()
    head = re.search(r"<head>(.*?)</head>", s, re.S)[1]
    title = html.unescape(re.search(r"<title>(.*?)</title>", head, re.S)[1])
    body_class = re.search(r'<body class="([^"]*)"', s)[1]
    main_open, main = re.search(r"(<main[^>]*>)(.*?)</main>", s, re.S).groups()
    fields = {
        "title": title.removesuffix(SITE),
        "body_class": body_class,
        **head_extras(head, page),
        "pagefind": "ignore" if "data-pagefind-ignore" in main_open else None,
    }
    out = target(page)
    if out.name == "_index.html" and page != "index.html":
        fields["url"] = "/" + page  # uglyURLs does not apply to section listings
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(front_matter(fields) + rewrite(main, page))


def main(baseline):
    baseline = Path(baseline)
    pages = sorted(p.relative_to(baseline).as_posix() for p in baseline.rglob("*.html"))
    pages = [p for p in pages if not p.startswith(("pagefind/", "timeline/"))]
    # Sections first, so target() can tell item.html is a listing.
    for p in pages:
        if (baseline / p).with_suffix("").is_dir():
            (CONTENT / p).with_suffix("").mkdir(parents=True, exist_ok=True)
    for p in pages:
        convert(baseline / p, p)
    print(f"{len(pages)} pages")


if __name__ == "__main__":
    main(sys.argv[1])
