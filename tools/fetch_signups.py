#!/usr/bin/env python3
"""Copy newsletter sign-ups from Netlify Forms into subscribers/ (private: never published or committed).

Writes:
  subscribers/subscribers.csv   email, signed up (UTC), one row per address, oldest first
  subscribers/emails.txt        just the addresses, one per line, ready to paste into an email's BCC

Usage:  python3 tools/fetch_signups.py
"""
import csv, json, os, urllib.request
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SITE_ID = "b3f2d5da-8f90-412f-bb7e-c7cc3ebb576d"
cfg = json.load(open(os.path.expanduser("~/Library/Preferences/netlify/config.json")))
TOKEN = cfg["users"][cfg["userId"]]["auth"]["token"]

def get(path):
    req = urllib.request.Request("https://api.netlify.com/api/v1" + path, headers={"Authorization": "Bearer " + TOKEN})
    return json.load(urllib.request.urlopen(req))

forms = [f for f in get(f"/sites/{SITE_ID}/forms") if f.get("name") == "newsletter"]
if not forms:
    raise SystemExit("No 'newsletter' form on Netlify yet (it appears after the first deploy with form detection on).")
subs, page = [], 1
while True:
    batch = get(f"/forms/{forms[0]['id']}/submissions?per_page=100&page={page}")
    subs += batch
    if len(batch) < 100: break
    page += 1

seen = {}
for s in sorted(subs, key=lambda s: s["created_at"]):
    email = (s.get("data", {}).get("email") or s.get("email") or "").strip().lower()
    if email and email not in seen:
        seen[email] = s["created_at"]

out = SITE / "subscribers"; out.mkdir(exist_ok=True)
with open(out / "subscribers.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["email", "signed_up_utc"]); w.writerows(seen.items())
(out / "emails.txt").write_text("".join(e + "\n" for e in seen))
print(f"{len(seen)} subscriber(s) -> {out}/subscribers.csv and emails.txt")
