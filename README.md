# cecilylowe.com — personal site

Static site. No build step, no framework. Open `index.html` in a browser to preview,
or run `python3 -m http.server 8000` from this folder and visit http://localhost:8000.

```
index.html          home: the two bubble-chamber photographs, name and menu on top
research.html       Interests, Publications, CV
blog.html           the blog (empty until there are posts)
about.html          picture on the left, a column of text on the right
style.css           all styling; the current design is the "plain" block at the bottom
script.js           left from the earlier design; the current pages do not load it
assets/             images
_unused/            earlier versions of the pages, kept for reference, not published
tools/              preview builder from the earlier design
CNAME               the custom domain (cecilylowe.com)
```

## Editing content

Everything is plain HTML. Every piece of text you are likely to change carries a
`data-edit="some.key"` attribute; that is what the editable preview and the sync tool use,
so keep the attribute when you rewrite the text inside it.

- **Work**: each entry on `work.html` is an `<article class="entry">`; copy one and change it.
  To use a photo instead of the drawn figure, replace the `<canvas>` with
  `<img src="assets/photo.jpg" alt="…">`.
- **Publications**: each is an `<li class="pub">` with title, authors, venue and links.
- **Blog**: `blog.html`, one page; posts go inside `<main>`.
- **CV**: sections of `<dl class="facts">` with a year on the left. Put the PDF at
  `assets/cecily-lowe-cv.pdf` (that is where the page links).
- **Curious**: the running list is a `<ul class="list">`.
- The cover shows once per browser session on the home page. To turn it off, delete the
  `<div class="cover">` block in `index.html`.

## Editing in the browser (the preview artifact)

The site can be previewed as a Claude artifact, where it becomes one scrolling document with
an `edit` link at the top right (visible to you, the owner). Click it, change any text in
place, then `save` (or ⌘S). The artifact saves a new version of itself.

Those edits live in the artifact, not in these files, until they are copied back:

```bash
# 1. in Claude Code, read the artifact's index.html to disk, then:
python3 tools/sync_from_preview.py path/to/downloaded/index.html --dry-run   # see what changed
python3 tools/sync_from_preview.py path/to/downloaded/index.html             # apply it
# 2. rebuild and republish the preview from the updated source pages:
python3 tools/build_preview.py preview
```

The simplest way to do all of this is to ask Claude Code: "sync my edits from the preview".

## Newsletter provider

The form is wired for **Buttondown** (free up to 100 subscribers, no tracking, plain email).
Create an account at https://buttondown.com, then set `NEWSLETTER.buttondownUsername` in
`script.js`. For Substack or Mailchimp, swap the `action` URL on the form instead; the comments
in `curious.html` show where.

## Deploying to the Squarespace domain

The domain is registered at Squarespace, but the site itself is hosted elsewhere, for free,
on GitHub Pages. Squarespace only has to point the domain at it.

### 1. Put the site on GitHub Pages (one time)

```bash
cd ~/Sites/cecilylowe
git init -b main && git add -A && git commit -m "Site"
gh repo create cecilylowe/cecilylowe.github.io --public --source=. --push
```

Then on GitHub: repo → Settings → Pages → Build and deployment → Source: "Deploy from a
branch", branch `main`, folder `/ (root)`. Within a minute the site is live at
https://cecilylowe.github.io.

### 2. Tell GitHub about the domain

`CNAME` already says `cecilylowe.com`. On GitHub → Settings → Pages → Custom domain, enter
the same domain and tick "Enforce HTTPS" once the DNS check passes.

### 3. Point the Squarespace domain at GitHub

Squarespace → Domains → cecilylowe.com → DNS → DNS settings → Custom records. Delete the
Squarespace default records and add:

| Host | Type  | Data                       |
|------|-------|----------------------------|
| @    | A     | 185.199.108.153            |
| @    | A     | 185.199.109.153            |
| @    | A     | 185.199.110.153            |
| @    | A     | 185.199.111.153            |
| www  | CNAME | cecilylowe.github.io       |

DNS takes anywhere from minutes to a day to propagate. Check with:

```bash
dig +short cecilylowe.com A
dig +short www.cecilylowe.com CNAME
```

### Updating the site later

```bash
cd ~/Sites/cecilylowe && git add -A && git commit -m "Update" && git push
```

GitHub Pages redeploys in under a minute. The `preview/` folder is only for the artifact and
can be left out of the repo (add it to `.gitignore`) or kept; it does no harm.
