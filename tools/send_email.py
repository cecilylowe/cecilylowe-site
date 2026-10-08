#!/usr/bin/env python3
"""Send any HTML file as an email from newsletter@cecilylowe.com, through Resend.

Any images the HTML points to with a local path (e.g. src="welcome-jupiter.jpg") are attached
inside the email and shown inline, so the email does not depend on the website. Images with a full
https:// address are left as they are. Replies go to cecily.lowe@yale.edu.

Usage:
  python3 tools/send_email.py emails/welcome.html "Welcome to Cecily's Newsletter" --to someone@example.com
  python3 tools/send_email.py emails/issue-01.html "Issue 1" --to a@x.com --to b@y.com

The Resend API key is read from ~/.config/cecilylowe/resend_key (one line, kept private, never committed).
"""
import argparse, base64, html as htmllib, json, mimetypes, re, sys, urllib.request
from pathlib import Path

FROM = "Cecily Lowe <newsletter@cecilylowe.com>"
REPLY_TO = "cecily.lowe@yale.edu"
KEY_FILE = Path.home() / ".config/cecilylowe/resend_key"


def build(html_path: Path):
    html = html_path.read_text()
    attachments, seen = [], {}

    def inline(m):
        src = m.group(2)
        if re.match(r"^(https?:|cid:|data:)", src):
            return m.group(0)
        f = (html_path.parent / src).resolve()
        if not f.exists():
            sys.exit(f"Image not found: {src}")
        if src not in seen:
            cid = re.sub(r"[^A-Za-z0-9]", "-", f.stem) + f"-{len(seen) + 1}"
            seen[src] = cid
            attachments.append({
                "filename": f.name,
                "content": base64.b64encode(f.read_bytes()).decode(),
                "content_id": cid,
                "content_type": mimetypes.guess_type(f.name)[0] or "application/octet-stream",
            })
        return f'{m.group(1)}cid:{seen[src]}{m.group(3)}'

    html = re.sub(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', inline, html)
    # plain-text fallback: the visible words, or the images' alt text if there are none
    body = re.sub(r"(?is)<(script|style|title)\b.*?</\1>|<!--.*?-->", "", html)
    words = " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", body)).split())
    if not words:
        words = " ".join(htmllib.unescape(a) for a in re.findall(r'\balt="([^"]*)"', html))
    return html, words + "\n\ncecilylowe.com\n", attachments


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path)
    ap.add_argument("subject")
    ap.add_argument("--to", action="append", required=True, help="recipient (repeat for several; each gets their own copy)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be sent, send nothing")
    a = ap.parse_args()

    html, text, attachments = build(a.html)
    print(f"From {FROM}  |  reply-to {REPLY_TO}  |  subject: {a.subject}")
    print(f"{len(attachments)} inline image(s): {[x['filename'] for x in attachments]}  |  {len(a.to)} recipient(s)")
    if a.dry_run:
        return
    key = KEY_FILE.read_text().strip()
    for to in a.to:                                   # one email per person: nobody sees anyone else's address
        payload = {"from": FROM, "to": [to], "reply_to": REPLY_TO, "subject": a.subject,
                   "html": html, "text": text, "attachments": attachments}
        req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(payload).encode(),
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            r = json.load(urllib.request.urlopen(req))
            print(f"  sent to {to}  (id {r.get('id')})")
        except urllib.error.HTTPError as e:
            print(f"  FAILED for {to}: {e.code} {e.read().decode()[:300]}")


if __name__ == "__main__":
    main()
