#!/usr/bin/env python3
"""Convert the flattened hearingtheamericas.org archive into Hugo content.

Usage: convert.py BASELINE_DIR

BASELINE_DIR is the static archive as it stood before the Hugo conversion
(`git archive <rev> hearingtheamericas`). Every page becomes a file under
content/ whose front matter carries what the shared templates need (title,
body class, extra head tags) and whose body is the page's <main>, with every
relative URL rewritten root-absolute so it reads the same from any file.

This was the one-time migration. content/ is the source now, and a second
run would overwrite edits made since, so it refuses to run once content/
exists unless given --force. Run against a fresh checkout it is idempotent.
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


# ---------------------------------------------------------------------------
# Items, media and item sets become data: front matter the templates in
# layouts/item, layouts/media and layouts/item-set render. Their JSON-LD
# records are kept verbatim in assets/jsonld/, since they are Omeka's
# identifiers rather than content.

S = "s/the-americas/"
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
PROPERTY = re.compile(
    r'<div class="property" data-term="([^"]+)">\s*<h\d class="heading-4">\s*(.*?)\s*</h\d>\s*'
    r'<div class="values">(.*?)\n                </div>\n    </div>', re.S)
VALUE = re.compile(r'<div class="value([^"]*)"((?: [\w-]+="[^"]*")*)>\n\s*(.*?)\s*            </div>', re.S)
RESOURCE_LINK = re.compile(
    r'<a class="resource-link" href="([^"]+)">(?:<img src="([^"]+)" alt="([^"]*)">)?'
    r'<span class="resource-name">(.*?)</span></a>')
URI_LINK = re.compile(r'<a class="uri-value-link" target="_blank" href="([^"]*)">(.*?)</a>', re.S)
RENDER = re.compile(r'<div class="media-render[^"]*">(.*?)</div>(?=\s*(?:<div|<script|</div>|<h|\s))', re.S)
IMAGE = re.compile(r'<a href="/files/original/([^"]+)" title="([^"]*)"><img src="([^"]+)" alt="([^"]*)"></a>')
AUDIO = re.compile(r'<audio src="/files/original/([^"]+)" controls title="([^"]*)"><a href="/files/original/\1">\2</a></audio>')
DEFAULT_CLASS = {"text": "", "uri": " uri", "item": " resource items", "item-set": " resource item_sets", "media": " resource media"}


def ref(url):
    """'/s/the-americas/item/6.html' -> ('item', 6)."""
    m = re.fullmatch(r"/s/the-americas/(item|item-set|media)/(\d+)\.html", url)
    return (m[1], int(m[2])) if m else None


def text(fragment):
    return html.unescape(fragment.strip())


def properties(main, page):
    props = []
    for term, label, values in PROPERTY.findall(main):
        vals = []
        for cls, attrs, inner in VALUE.findall(values):
            inner = rewrite(inner, page)
            v = {}
            link = RESOURCE_LINK.fullmatch(inner)
            uri = URI_LINK.fullmatch(inner)
            if link and ref(link[1]):
                kind, rid = ref(link[1])
                v = {kind: rid}
                if not link[2]:
                    v["thumbnail"] = False
            elif uri:
                v = {"uri": html.unescape(uri[1])}
                if text(uri[2]) != v["uri"]:
                    v["label"] = text(uri[2])
                kind = "uri"
            else:
                v = {"text": text(inner)} if "<" not in inner else {"html": inner.strip()}
                kind = "text"
            if cls != DEFAULT_CLASS[kind]:
                v["class"] = cls.strip()
            if attrs:
                v["attrs"] = attrs.strip()
            vals.append(v)
        props.append({"term": term, "label": text(label), "values": vals})
    return props


def media_render(fragment):
    image, audio = IMAGE.fullmatch(fragment), AUDIO.fullmatch(fragment)
    if image:
        f = {"kind": "image", "file": image[1], "link_title": text(image[2]), "alt": text(image[4])}
        stem = image[1].rsplit(".", 1)[0]
        if image[3] != f"/files/large/{stem}.jpg":
            f["display"] = image[3]
        return f
    if audio:
        return {"kind": "audio", "file": audio[1], "label": text(audio[2])}
    return {"kind": "html", "html": fragment}


class Archive:
    """What the structured pages share: thumbnails and listing alts, gathered
    from every page that links to or lists a resource."""

    def __init__(self, baseline):
        self.thumbs, self.list_alt = {}, {}
        self.records, self.vocab, class_label, self.linked, self.render = {}, {}, {}, {}, {}
        for p in sorted(baseline.glob(S + "*/*.html")):
            m = re.fullmatch(r"(item|media)/(\d+)\.html", p.relative_to(baseline / S).as_posix())
            ld = m and LD.search(p.read_text())
            if ld:
                self.records[(m[1], int(m[2]))] = json.loads(ld[1])
            if m and m[1] == "media":
                self.render[int(m[2])] = RENDER.search(rewrite(p.read_text(), (S + m[0])))[1]
        for (kind, rid), j in self.records.items():
            for term, values in j.items():
                for v in values if isinstance(values, list) else []:
                    if isinstance(v, dict) and "property_label" in v:
                        self.vocab[term] = v["property_label"]
        for p in baseline.rglob("*.html"):
            page = p.relative_to(baseline).as_posix()
            if page.startswith(("pagefind/", "timeline/")):
                continue
            s = rewrite(p.read_text(), page)
            for h, cls in re.findall(r'<a class="resource-link" href="([^"]+)">.*?</a>\s*<span class="resource-class">(.*?)</span>', s):
                j = ref(h) and self.records.get(ref(h))
                if j and j.get("o:resource_class"):
                    class_label[j["o:resource_class"]["o:id"]] = html.unescape(cls)
            if re.fullmatch(S + r"item/\d+\.html", page):
                self.linked[ref("/" + page)] = [
                    ref(h) for h in re.findall(r'<div class="linked-resource">\s*<h3 class="heading-4">.*?</h3>\s*<a class="resource-link" href="([^"]+)">', s)]
            for href, img, _alt, _name in RESOURCE_LINK.findall(s):
                if img and ref(href):
                    self.thumbs.setdefault(ref(href), img.replace("/medium/", "/square/"))
            for href, img, alt in re.findall(r'<a href="([^"]+)" tabindex="-1" aria-hidden="true"><img src="([^"]+)" alt="([^"]*)">', s):
                if ref(href):
                    self.thumbs.setdefault(ref(href), img.replace("/medium/", "/square/"))
                    if "/medium/" in img and alt:
                        self.list_alt[ref(href)] = html.unescape(alt)
        self.class_label = {k: class_label.get(j["o:resource_class"]["o:id"])
                            for k, j in self.records.items() if j.get("o:resource_class")}

    def linked_rule(self, rid):
        """layouts/partials/linked.html's order: resources linking to item RID,
        by id, grouped by property in order of first appearance."""
        subjects = []
        for (kind, sid), j in self.records.items():
            for term, values in j.items():
                for v in values if isinstance(values, list) else []:
                    if isinstance(v, dict) and v.get("value_resource_name") == "items" and v.get("value_resource_id") == rid:
                        subjects.append((sid, kind, v["property_label"]))
        subjects = sorted(set(subjects))
        groups = list(dict.fromkeys(label for _, _, label in subjects))
        return [(kind, sid) for g in groups for sid, kind, label in subjects if label == g]


def save_jsonld(kind, rid, record):
    out = ROOT / "assets" / "jsonld" / kind / f"{rid}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(record)


def write_yaml(path, fields, body=""):
    import yaml  # uv run --with pyyaml

    class Dumper(yaml.SafeDumper):
        pass

    Dumper.add_representer(str, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|" if "\n" in s else None))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.dump(fields, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=1000) + "---\n" + body)


def common(kind, rid, page, s, archive, title):
    head = re.search(r"<head>(.*?)</head>", s, re.S)[1]
    f = {"id": rid}
    head_title = html.unescape(re.search(r"<title>(.*?)</title>", head, re.S)[1]).removesuffix(SITE)
    if head_title != title:
        f["head_title"] = head_title
    body_class = re.search(r'<body class="([^"]*)"', s)[1]
    default = {"item": "item resource show", "media": "media resource show", "item-set": "item resource browse item-set"}[kind]
    cls = body_class.removeprefix(default + " ").removesuffix(" content-warning-banner").removesuffix("content-warning-banner")
    if kind == "item":
        f["class"] = cls.strip()
    elif cls.strip():
        f["body_class"] = body_class
    if (kind, rid) in archive.thumbs:
        f["thumbnail"] = archive.thumbs[(kind, rid)]
    if (kind, rid) in archive.list_alt:
        f["thumbnail_alt"] = archive.list_alt[(kind, rid)]
    if archive.class_label.get((kind, rid)):
        f["resource_class"] = archive.class_label[(kind, rid)]
    if kind == "item" and archive.linked.get((kind, rid)) != archive.linked_rule(rid):
        f["linked_order"] = [f"{k}/{i}" for k, i in archive.linked[(kind, rid)]]
    f.update({k: v for k, v in head_extras(head, page).items() if v})
    return f


def convert_item(rid, page, s, archive):
    main = rewrite(re.search(r"<main[^>]*>(.*?)</main>", s, re.S)[1], page)
    record = LD.search(main)[1]
    save_jsonld("item", rid, record)
    j = json.loads(record)
    f = {"title": text(re.search(r'<div class="item-head">\s*<h1 class="heading-2"><span class="title">(.*?)</span>', main, re.S)[1])}
    f.update(common("item", rid, page, s, archive, f["title"]))
    f["created"] = j["o:created"]["@value"]
    if j.get("o:item_set"):
        f["item_sets"] = [x["o:id"] for x in j["o:item_set"]]
    shown = [mid for mid in (m["o:id"] for m in j["o:media"]) if archive.render.get(mid) in RENDER.findall(main)]
    f["media"] = [m["o:id"] for m in j["o:media"]]
    role = re.search(r'<span class="role">(.*?)</span>', main, re.S)
    if role:
        f["role"] = text(role[1])
    props = properties(main, page)
    f["properties"] = props
    desc = re.search(r'<div class="item-description">(.*?)</div>', main, re.S)
    first = next((p["values"][0] for p in props if p["term"] == "dcterms:description"), None)
    first = first and (first.get("html") or html.escape(first.get("text", ""), quote=True))
    if (desc[1] if desc else None) != first:
        f["description"] = desc[1] if desc else False
    tail = main[main.index(LD.search(main)[0]) + len(LD.search(main)[0]):].strip()
    if tail:
        f["after"] = tail  # the Mapping module's map and marker popups
    return f, shown


def convert_media(rid, page, s, archive):
    main = rewrite(re.search(r"<main[^>]*>(.*?)</main>", s, re.S)[1], page)
    record = LD.search(main)
    if record:
        save_jsonld("media", rid, record[1])
    f = {"title": text(re.search(r'<h1 class="heading-2"><span class="title">(.*?)</span>', main, re.S)[1])}
    f.update(common("media", rid, page, s, archive, f["title"]))
    f["item"] = int(re.search(r'Part of <a href="/s/the-americas/item/(\d+)\.html">', main)[1])
    f.update(media_render(RENDER.search(main)[1]))
    f["properties"] = properties(main, page)
    return f


def convert_item_set(rid, page, s, archive):
    main = re.search(r"<main[^>]*>(.*?)</main>", s, re.S)[1]
    f = {"title": text(re.search(r'<span class="title">(.*?)</span>', main, re.S)[1])}
    f.update(common("item-set", rid, page, s, archive, f["title"]))
    return f


def main(baseline):
    baseline = Path(baseline)
    archive = Archive(baseline)
    pages = sorted(p.relative_to(baseline).as_posix() for p in baseline.rglob("*.html"))
    pages = [p for p in pages if not p.startswith(("pagefind/", "timeline/"))]
    # Sections first, so target() can tell item.html is a listing.
    for p in pages:
        if (baseline / p).with_suffix("").is_dir():
            (CONTENT / p).with_suffix("").mkdir(parents=True, exist_ok=True)
    hidden = {}
    for p in pages:
        m = re.fullmatch(S + r"(item|media|item-set)/(\d+)\.html", p)
        if not m:
            convert(baseline / p, p)
            continue
        kind, rid, s = m[1], int(m[2]), (baseline / p).read_text()
        out = CONTENT / S / kind / f"{rid}.md"
        if kind == "item":
            f, shown = convert_item(rid, p, s, archive)
            hidden[rid] = (f, shown, out)
        elif kind == "media":
            write_yaml(out, convert_media(rid, p, s, archive))
        else:
            write_yaml(out, convert_item_set(rid, p, s, archive))
        (CONTENT / p).unlink(missing_ok=True)
    # Drop thumbnails layouts/partials/thumb.html would derive anyway.
    def derived(kind, rid):
        if kind == "media":
            r = archive.render.get(rid, "")
            img = IMAGE.fullmatch(r)
            if img:
                return f"/files/square/{img[1].rsplit('.', 1)[0]}.jpg"
            return "/application/asset/thumbnails/audio.png" if r.startswith("<audio") else None
        first = hidden[rid][0]["media"][:1] if kind == "item" else []
        return (archive.thumbs.get(("media", first[0])) or derived("media", first[0])) if first else None
    for rid, (f, shown, out) in hidden.items():
        if f.get("thumbnail") and f["thumbnail"] == (derived("item", rid) or "/application/asset/thumbnails/default.png"):
            del f["thumbnail"]
    for mf in (CONTENT / S / "media").glob("*.md"):
        t = mf.read_text()
        m = re.search(r"^thumbnail: (\S+)\n", t, re.M)
        if m and m[1] == derived("media", int(mf.stem)):
            mf.write_text(t.replace(m[0], ""))
    # Media an item's page leaves out (Omeka skips some; see layouts/item).
    for rid, (f, shown, out) in hidden.items():
        skip = [mid for mid in f["media"] if mid not in shown
                and (f["class"] == "recording" or not archive.render[mid].startswith("<audio"))]
        if skip:
            f["hide_media"] = skip
        write_yaml(out, f)
    write_yaml(ROOT / "data" / "properties.yaml", dict(sorted(archive.vocab.items())))
    for listing in ("item", "item-set"):
        write_yaml(CONTENT / S / listing / "_index.md", {
            "title": {"item": "Items", "item-set": "Item Sets"}[listing],
            "url": f"/{S}{listing}.html",
            "body_class": f"{listing} resource browse content-warning-banner",
            "type": listing, "cascade": {"type": listing}})
        (CONTENT / S / listing / "_index.html").unlink(missing_ok=True)
    write_yaml(CONTENT / S / "media" / "_index.md", {
        "build": {"render": "never", "list": "local"}, "type": "media", "cascade": {"type": "media"}})
    print(f"{len(pages)} pages")


if __name__ == "__main__":
    if CONTENT.exists() and "--force" not in sys.argv:
        sys.exit("content/ exists; this would overwrite it (use --force)")
    main(sys.argv[1])
