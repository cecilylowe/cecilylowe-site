#!/usr/bin/env python3
"""Copy text edited in the published preview back into the real site pages.

Every editable region carries data-edit="key" in both the preview and the source pages. This
reads the preview HTML (saved from the artifact), finds each key, and replaces the inner HTML of
the element with the same key in whichever source page holds it. Nothing else is touched.

Usage:  python3 tools/sync_from_preview.py path/to/preview-index.html [--dry-run]

Rule for authors: an editable element must not contain another element of its own tag
(no <p> inside a <p data-edit>, no <span> inside a <span data-edit>), or the match ends early.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
PAGES = ["index", "publications", "outreach", "cv"]
EL = r'<(\w+)([^>]*?)\sdata-edit="%s"([^>]*)>(.*?)</\1>'


def regions(html):
    out = {}
    for m in re.finditer(r'<(\w+)([^>]*?)\sdata-edit="([^"]+)"([^>]*)>(.*?)</\1>', html, re.S):
        out[m.group(3)] = m.group(5)
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def anchor_homes():
    """Which source page holds each id, so a preview link like #charge maps back to work.html#charge."""
    homes = {}
    for name in PAGES:
        src = (SITE / (name + ".html")).read_text(encoding="utf-8")
        for m in re.finditer(r'\sid="([\w-]+)"', src):
            homes.setdefault(m.group(1), name)
    return homes


def unhash_hrefs(html, homes):
    """The preview is one document with hash links; the site is many pages. Reverse the build's rewrite."""
    def fix(m):
        target = m.group(1)
        if target == "top":
            return m.group(0)
        if target in PAGES:
            return 'href="%s.html"' % target
        if target in homes:
            return 'href="%s.html#%s"' % (homes[target], target)
        return m.group(0)
    return re.sub(r'href="#([\w-]*)"', fix, html)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    preview = Path(sys.argv[1]).read_text(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    homes = anchor_homes()
    edited = {k: unhash_hrefs(v, homes) for k, v in regions(preview).items()}
    if not edited:
        raise SystemExit("no data-edit regions found in " + sys.argv[1])

    changed_total = 0
    for name in PAGES:
        path = SITE / (name + ".html")
        src = path.read_text(encoding="utf-8")
        current = regions(src)
        new = src
        changed = []
        for key, html in edited.items():
            if key not in current or norm(current[key]) == norm(html):
                continue
            pat = re.compile(EL % re.escape(key), re.S)
            m = pat.search(new)
            if not m:
                continue
            new = new[: m.start(4)] + html + new[m.end(4):]
            changed.append(key)
        if changed:
            changed_total += len(changed)
            print("%s: %s" % (path.name, ", ".join(changed)))
            if not dry:
                path.write_text(new, encoding="utf-8")
    missing = sorted(k for k in edited if not any(k in regions((SITE / (p + ".html")).read_text(encoding="utf-8")) for p in PAGES))
    if missing:
        print("keys in the preview with no home in the source pages: " + ", ".join(missing))
    print("%d region(s) %s" % (changed_total, "would change" if dry else "updated"))


if __name__ == "__main__":
    main()
