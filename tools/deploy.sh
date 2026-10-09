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
cp ./*.html style.css site.js favicon.ico .deploy/
cp -R assets .deploy/assets
rm -f .deploy/assets/cover.jpg            # not used by the current pages
# clean addresses: links point at /about, /work … and / instead of about.html, index.html.
# (GitHub serves /about from about.html.) The source pages keep .html so local previews still work.
STAMP=$(date +%s)
python3 - .deploy "$STAMP" <<'PY'
import re, sys, pathlib, json
for f in pathlib.Path(sys.argv[1]).glob("*.html"):
    s = f.read_text()
    s = re.sub(r'href="index\.html(#[^"]*)?"', lambda m: f'href="/{m.group(1) or ""}"', s)
    s = re.sub(r'href="([a-z0-9-]+)\.html(#[^"]*)?"', lambda m: f'href="/{m.group(1)}{m.group(2) or ""}"', s)
    # a version stamp on the stylesheet and pictures, so browsers fetch the new ones at once
    # instead of mixing in copies they saved from an earlier publish (not the font: its preload must match
    # the stylesheet's address exactly, or the browser downloads it twice)
    s = re.sub(r'(href|src)="(style\.css|site\.js|assets/(?!fonts/)[^"?]+)"', lambda m: f'{m.group(1)}="{m.group(2)}?v={sys.argv[2]}"', s)
    # freshness check: GitHub lets browsers reuse a saved page for 10 minutes, and Back shows a page
    # from memory. Every page asks for /version.txt (never cached) and, if a newer publish exists,
    # reloads itself once so you always see the current version.
    fresh = ('<script>(function(){var V="%s";'
             # arriving with ?fresh=… : tidy the address bar back to the clean URL
             'try{var u=new URL(location.href);if(u.searchParams.has("fresh")){u.searchParams.delete("fresh");history.replaceState(null,"",u.pathname+(u.search||"")+u.hash)}}catch(e){}'
             'function check(){fetch("/version.txt?"+Date.now(),{cache:"no-store"}).then(function(r){return r.ok?r.text():""})'
             '.then(function(v){v=(v||"").trim();if(!v||v===V)return;var k="cl-fresh-"+v+location.pathname;'
             # guard only against a reload loop (one try per 15 s), not against later visits: Back/Forward
             # can bring up an old saved copy again, and that copy must refresh too
             'try{var t=+sessionStorage.getItem(k)||0;if(Date.now()-t<15000)return;sessionStorage.setItem(k,Date.now())}catch(e){}'
             # overwrite the browser's saved copy of this very address, then reload it, so Back/Forward
             # later find the new page under the same clean URL (no ?fresh address left in history)
             'fetch(location.pathname,{cache:"reload"}).catch(function(){}).then(function(){location.reload()})}).catch(function(){})}'
             # when this page is current, overwrite the browser's saved copies of every other page once
             # per version, so a click never opens an old copy saved before this publish
             'function warm(){var k="cl-warm-"+V;try{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1")}catch(e){}'
             'fetch("/version.txt?"+Date.now(),{cache:"no-store"}).then(function(r){return r.ok?r.text():""}).then(function(v){'
             'if((v||"").trim()!==V)return;PAGES.forEach(function(p){if(p!==location.pathname)fetch(p,{cache:"reload"}).catch(function(){})})}).catch(function(){})}'
             'check();addEventListener("load",function(){setTimeout(warm,300)});addEventListener("pageshow",function(e){if(e.persisted)check()})})();</script>') % sys.argv[2]
    pages = sorted("/" if g.stem == "index" else "/" + g.stem for g in pathlib.Path(sys.argv[1]).glob("*.html"))
    fresh = fresh.replace("PAGES", json.dumps(pages), 1)
    s = s.replace("</head>", fresh + "\n</head>", 1)
    f.write_text(s)
PY
echo "$STAMP" > .deploy/version.txt
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
