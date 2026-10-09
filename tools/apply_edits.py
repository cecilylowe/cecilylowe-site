#!/usr/bin/env python3
"""Apply edits saved in the Site Editor artifact to the real pages.

The editor stores one document per page in its `edits` collection:
  {page, items: [{sel, dx?, dy?, scale?, hidden?, html?}], savedAt}
`sel` is a `body > tag:nth-child(n) > ...` path to the element, computed on the page as published.
Claude reads the documents (ArtifactData, out_dir) and runs:

  python3 tools/apply_edits.py path/to/edits/            # folder of <page>.json files
  python3 tools/apply_edits.py path/to/edits/ --dry-run  # show what would change

Moves and resizes become inline `translate` / `scale` styles, hidden items `display:none`,
text edits replace the element's inner HTML. Afterwards the editor's edits for that page
should be cleared, because the page itself now contains them.
"""
import argparse, json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

SITE = Path(__file__).resolve().parent.parent
FILES = {"home": "index.html", "about": "about.html", "research": "work.html", "work": "work.html", "news": "news.html",
         "curious": "about.html", "thoughts": "about.html", "newsletter": "about.html", "question": "question.html"}


def set_style(el, prop, value):
    rules = [r for r in (el.get("style") or "").split(";") if r.strip() and r.split(":")[0].strip() != prop]
    if value is not None:
        rules.append(f"{prop}: {value}")
    if rules:
        el["style"] = "; ".join(r.strip() for r in rules)
    elif el.has_attr("style"):
        del el["style"]


def apply(page, items, dry):
    path = SITE / FILES[page]
    src = path.read_text()
    soup = BeautifulSoup(src, "html.parser")
    changed = 0
    for it in items:
        el = soup.select_one(it["sel"])
        if el is None:
            print(f"  {page}: not found (page changed since the edit?): {it['sel']}")
            continue
        dx, dy = it.get("dx") or 0, it.get("dy") or 0
        set_style(el, "translate", f"{dx}px {dy}px" if (dx or dy) else None)
        s = it.get("scale")
        set_style(el, "scale", str(s) if s and s != 1 else None)
        if it.get("hidden"):
            set_style(el, "display", "none")
        if isinstance(it.get("html"), str):
            html = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", it["html"])
            html = re.sub(r'\son\w+="[^"]*"', "", html)
            el.clear()
            el.append(BeautifulSoup(html, "html.parser"))
        changed += 1
        print(f"  {page}: {it['sel']}  " + ", ".join(k for k in ("dx", "dy", "scale", "hidden", "html") if it.get(k) not in (None, 0, False)))
    if changed and not dry:
        out = soup.decode(formatter="html5")
        path.write_text(out)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    total = 0
    for f in sorted(a.folder.rglob("*.json")):
        d = json.loads(f.read_text())
        page = d.get("page") or f.stem
        if page not in FILES:
            continue
        total += apply(page, d.get("items") or [], a.dry_run)
    print(f"{total} edit(s) {'would be ' if a.dry_run else ''}applied")


if __name__ == "__main__":
    sys.exit(main())
