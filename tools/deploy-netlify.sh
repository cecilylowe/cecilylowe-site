#!/bin/bash
# Publish the site to Netlify (cecilylowe.netlify.app -> cecilylowe.com).
# Copies only the public files into .deploy/ and uploads that. Never publishes _unused/, _private/,
# preview/, tools/ or the README.
#   tools/deploy.sh "what changed"
set -euo pipefail
cd "$(dirname "$0")/.."
SITE_ID=b3f2d5da-8f90-412f-bb7e-c7cc3ebb576d
rm -rf .deploy && mkdir .deploy
cp ./*.html style.css favicon.ico .deploy/
cp -R assets .deploy/assets
rm -f .deploy/assets/cover.jpg            # not used by the current pages
npx --yes netlify-cli deploy --prod --dir .deploy --functions netlify/functions --site "$SITE_ID" --message "${1:-update}"
