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
echo "cecilylowe.com" > .deploy/CNAME     # the custom domain
touch .deploy/.nojekyll                   # serve files exactly as they are
cd .deploy
git init -q -b gh-pages
git add -A
git -c user.name="Cecily Lowe" -c user.email="cecily.lowe@yale.edu" commit -qm "${1:-update}"
git push -qf "$REPO" gh-pages
echo "Published to gh-pages: ${1:-update}"
