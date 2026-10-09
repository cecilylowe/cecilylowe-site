#!/bin/bash
# Publish the site to GitHub Pages (cecilylowe.com).
# Copies only the public files into .deploy/ and force-pushes that folder, on its own, to the
# gh-pages branch of github.com/cecilylowe/cecilylowe-site. GitHub serves that branch at the
# custom domain. Nothing else in this folder (tools, notes, email drafts, _unused, _private,
# subscribers) is ever published. No build service, no credits, no limits.
#   tools/deploy.sh "what changed"
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=https://github.com/cecilylowe/cecilylowe-site.git
rm -rf .deploy && mkdir .deploy
cp ./*.html style.css favicon.ico .deploy/
cp -R assets .deploy/assets
rm -f .deploy/assets/cover.jpg            # not used by the current pages
# clean addresses: links point at /about, /work … and / instead of about.html, index.html.
# (GitHub serves /about from about.html.) The source pages keep .html so local previews still work.
STAMP=$(date +%s)
python3 - .deploy "$STAMP" <<'PY'
import re, sys, pathlib
for f in pathlib.Path(sys.argv[1]).glob("*.html"):
    s = f.read_text()
    s = re.sub(r'href="index\.html(#[^"]*)?"', lambda m: f'href="/{m.group(1) or ""}"', s)
    s = re.sub(r'href="([a-z0-9-]+)\.html(#[^"]*)?"', lambda m: f'href="/{m.group(1)}{m.group(2) or ""}"', s)
    # a version stamp on the stylesheet and pictures, so browsers fetch the new ones at once
    # instead of mixing in copies they saved from an earlier publish
    s = re.sub(r'(href|src)="(style\.css|assets/[^"?]+)"', lambda m: f'{m.group(1)}="{m.group(2)}?v={sys.argv[2]}"', s)
    f.write_text(s)
PY
echo "cecilylowe.com" > .deploy/CNAME     # the custom domain
touch .deploy/.nojekyll                   # serve files exactly as they are
cd .deploy
git init -q -b gh-pages
git add -A
git -c user.name="Cecily Lowe" -c user.email="cecily.lowe@yale.edu" commit -qm "${1:-update}"
git push -qf "$REPO" gh-pages
echo "Published to gh-pages: ${1:-update} — waiting for GitHub to put it live…"
# wait until GitHub has built it and cecilylowe.com is actually serving this version
for i in $(seq 1 60); do
  if curl -s "https://cecilylowe.com/?nocache=$RANDOM$RANDOM" | grep -q "v=$STAMP"; then
    echo "LIVE on https://cecilylowe.com ($(( i * 5 ))s). If your browser still shows the old page, press Cmd+Shift+R."
    exit 0
  fi
  sleep 5
done
echo "Pushed, but not live after 5 minutes — check https://github.com/cecilylowe/cecilylowe-site/actions"
