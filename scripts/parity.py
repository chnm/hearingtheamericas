#!/usr/bin/env python3
"""Compare a Hugo build with the static archive it replaced.

Usage: parity.py BASELINE_DIR PUBLIC_DIR [-v]

Both trees are normalised the same way before comparing: every URL is
resolved to root-absolute (the archive used relative URLs, the Hugo build
root-absolute ones; both resolve to the same address at the domain root),
and whitespace runs and whitespace between tags are collapsed, since HTML
renders them alike. Comments are dropped, "/index.html" is "/", and character references are
spelled one way. Anything else that differs is reported, page by page.
Every other file must be byte-identical. Exits 1 on any difference.
"""
import difflib
import html
import filecmp
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert import rewrite  # noqa: E402

SKIP = ("pagefind/", "README.md", "pagefind.yml", ".git")


ENTITY = re.compile(r"&(?:#[0-9]+|#x[0-9a-fA-F]+|[A-Za-z]+);")
ESCAPED = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def canonical(m):
    """One spelling per character: &#039;, &#x27;, &apos; and ' are all '."""
    c = html.unescape(m[0])
    return ESCAPED.get(c, c) if len(c) == 1 else m[0]


def normalise(text, page):
    text = rewrite(text, page)
    # Hugo's templates drop comments, HTML and JS alike; neither renders or runs.
    text = re.sub(r"<!--.*?-->|//<!--|//-->|/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r'(href|action)="/index\.html"', r'\1="/"', text)
    text = ENTITY.sub(canonical, text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r">\s+<", "><", text).replace("> ", ">").replace(" <", "<")


def tags(text):
    return re.sub(r"(<[^/])", r"\n\1", text).splitlines()


def main(baseline, public, verbose=False):
    baseline, public = Path(baseline), Path(public)
    a = {p.relative_to(baseline).as_posix() for p in baseline.rglob("*") if p.is_file()}
    b = {p.relative_to(public).as_posix() for p in public.rglob("*") if p.is_file()}
    a = {p for p in a if not p.startswith(SKIP) and not p.endswith(".DS_Store")}
    b = {p for p in b if not p.startswith(SKIP)}
    bad = 0
    for p in sorted(a - b):
        print(f"missing  {p}")
        bad += 1
    for p in sorted(b - a):
        print(f"extra    {p}")
        bad += 1
    for p in sorted(a & b):
        if not p.endswith(".html"):
            if not filecmp.cmp(baseline / p, public / p, shallow=False):
                print(f"bytes    {p}")
                bad += 1
            continue
        x = normalise((baseline / p).read_text(), p)
        y = normalise((public / p).read_text(), p)
        if x != y:
            bad += 1
            print(f"differs  {p}")
            if verbose:
                for line in list(difflib.unified_diff(tags(x), tags(y), lineterm="", n=1))[2:40]:
                    print("    " + line[:240])
    print(f"{len(a & b)} common files, {bad} differences")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], "-v" in sys.argv))
