#!/usr/bin/env python3
"""Build the editable one-page preview of the site for publishing as a Claude artifact.

The real site is seven separate pages. The preview folds them into ONE document with hash
routing (#work, #cv, ...) so that the artifact's `artifact` capability can save the whole thing
as a new version when it is edited in place. Every editable text carries a data-edit="key"
attribute in the source pages; the same keys are what sync_from_preview.py uses to copy edits
back into the real pages.

Usage:  python3 tools/build_preview.py [out_dir]      (default: preview/)
Output: out_dir/index.html plus copies of style.css and script.js.
"""
import re
import shutil
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
PAGES = ["index", "publications", "outreach", "cv"]

# The exact skeleton the Artifact tool wraps a page in. The page republishes itself in this
# shape so that a later publish from the tool recognises the skeleton instead of nesting it.
RESET = (
    ":root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);"
    "padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}"
    "body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#faf9f5;"
    "color:#141413}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}"
)
SKELETON_HEAD = (
    '<!doctype html><html><head><meta charset=utf8>'
    '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
    "<style>" + RESET + "</style></head><body>"
)

PREVIEW_CSS = """
/* preview only: one document, several pages; and the edit mode */
.page[hidden] { display: none; }
#editbar { margin-left: auto; }
#editbar a { color: inherit; }
#editbar .status { margin-left: 0.5rem; }
body.editing [data-edit] { outline: 1px dashed var(--fg-3); outline-offset: 3px; cursor: text; }
body.editing [data-edit]:hover { outline-color: var(--fg-2); }
body.editing [data-edit]:focus { outline: 1.5px solid var(--accent); }
body.editing .row, body.editing .card { pointer-events: auto; }
"""

PREVIEW_JS = r"""
(function () {
  "use strict";
  // The page's own source, captured before any script touches the DOM (script.js is deferred).
  var PAGE = document.getElementById("page");
  var PRISTINE = PAGE.outerHTML;
  var SKELETON_HEAD = __SKELETON_HEAD__;
  var PAGES = __PAGES__;

  /* ---- routing: one document, several pages ---- */
  function show(name) {
    var secs = document.querySelectorAll(".page");
    for (var i = 0; i < secs.length; i++) secs[i].hidden = (secs[i].id !== "page-" + name);
    var links = document.querySelectorAll(".nav a");
    for (var j = 0; j < links.length; j++) {
      if (links[j].getAttribute("href") === "#" + name) links[j].setAttribute("aria-current", "page");
      else links[j].removeAttribute("aria-current");
    }
    var hero = document.querySelector(".hero");
    if (hero) hero.hidden = (name !== "index");
    document.body.classList.toggle("has-hero", name === "index");
    current = name;
    window.dispatchEvent(new Event("resize"));
  }
  var current = null;
  function route() {
    var h = (location.hash || "#index").slice(1);
    if (h === "top") { window.scrollTo(0, 0); return; }
    if (PAGES.indexOf(h) >= 0) { show(h); window.scrollTo(0, 0); return; }
    var el = document.getElementById(h);
    if (el) {
      var sec = el.closest(".page");
      if (sec) show(sec.id.replace("page-", ""));
      el.scrollIntoView();
      return;
    }
    show("index");
  }
  window.addEventListener("hashchange", route);
  route();

  /* ---- edit mode ---- */
  var bar = document.getElementById("editbar");
  if (!bar || !window.claude || typeof window.claude.use !== "function") return;
  var editLink = bar.querySelector('[data-act="edit"]');
  var editing = bar.querySelector(".editing");
  var status = bar.querySelector(".status");
  var isEditing = false, snapshot = {}, art = null;

  function say(t) { status.textContent = t || ""; }
  function regions() { return Array.prototype.slice.call(document.querySelectorAll("[data-edit]")); }

  function clean(html) {
    var t = document.createElement("template");
    t.innerHTML = html;
    var bad = t.content.querySelectorAll("script, style, meta, link, iframe, object, embed");
    for (var i = 0; i < bad.length; i++) bad[i].remove();
    var all = t.content.querySelectorAll("*");
    for (var j = 0; j < all.length; j++) {
      all[j].removeAttribute("style");
      all[j].removeAttribute("contenteditable");
      var attrs = all[j].attributes;
      for (var k = attrs.length - 1; k >= 0; k--) if (/^on/i.test(attrs[k].name)) all[j].removeAttribute(attrs[k].name);
    }
    return t.innerHTML.replace(/ /g, " ");
  }

  function compose(state) {
    var t = document.createElement("template");
    t.innerHTML = PRISTINE;
    for (var key in state) {
      if (!Object.prototype.hasOwnProperty.call(state, key)) continue;
      var el = t.content.querySelector('[data-edit="' + key.replace(/"/g, '\\"') + '"]');
      if (el) el.innerHTML = state[key];
    }
    return SKELETON_HEAD + "\n" + t.innerHTML + "\n</body></html>";
  }

  function start() {
    isEditing = true;
    snapshot = {};
    regions().forEach(function (el) {
      snapshot[el.getAttribute("data-edit")] = el.innerHTML;
      el.setAttribute("contenteditable", el.children.length ? "true" : "plaintext-only");
    });
    document.body.classList.add("editing");
    editLink.hidden = true;
    editing.hidden = false;
    say("click any text");
  }
  function stop() {
    isEditing = false;
    regions().forEach(function (el) { el.removeAttribute("contenteditable"); });
    document.body.classList.remove("editing");
    editLink.hidden = false;
    editing.hidden = true;
  }
  function cancel() {
    regions().forEach(function (el) {
      var k = el.getAttribute("data-edit");
      if (k in snapshot) el.innerHTML = snapshot[k];
    });
    stop();
    say("");
  }
  function save() {
    if (!art) return;
    var state = {}, changed = 0;
    regions().forEach(function (el) {
      var k = el.getAttribute("data-edit");
      var v = clean(el.innerHTML);
      state[k] = v;
      if (v !== snapshot[k]) changed++;
    });
    if (!changed) { stop(); say("nothing changed"); return; }
    say("saving…");
    art.publish(compose(state)).then(function () {
      say("saved · reloading");
    }).catch(function (e) {
      var code = e && e.code;
      if (code === "conflict") { say("someone saved first · reloading"); return; }
      if (code === "not_writer" || code === "not_granted" || code === "not_declared") {
        say("this view is read-only");
        cancel();
        bar.hidden = true;
        return;
      }
      say("could not save (" + (code || "error") + ")");
    });
  }

  // links inside editable text must not navigate while editing
  document.addEventListener("click", function (e) {
    if (isEditing && e.target.closest && e.target.closest("[data-edit]")) e.preventDefault();
  }, true);
  bar.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-act]");
    if (!a) return;
    e.preventDefault();
    var act = a.getAttribute("data-act");
    if (act === "edit") start();
    else if (act === "save") save();
    else if (act === "cancel") cancel();
  });
  window.addEventListener("keydown", function (e) {
    if (!isEditing) return;
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); }
    if (e.key === "Escape") { e.preventDefault(); cancel(); }
  });

  Promise.all([window.claude.use("artifact"), window.claude.use("user")]).then(function (r) {
    art = r[0];
    var user = r[1];
    if (!art) return;
    if (user && typeof user.canEdit === "function" && user.canEdit() === false) return;
    bar.hidden = false;
  });
})();
"""


def grab(pattern, text, flags=re.S):
    m = re.search(pattern, text, flags)
    if not m:
        raise SystemExit("could not find " + pattern)
    return m.group(0)


def optional(pattern, text, flags=re.S):
    m = re.search(pattern, text, flags)
    return m.group(0) if m else ""


def rewrite_hrefs(html):
    def fix(m):
        href = m.group(1)
        pm = re.match(r"^([a-z]+)\.html(#[\w-]+)?$", href)
        if not pm:
            return m.group(0)
        page, anchor = pm.group(1), pm.group(2)
        if anchor:
            return 'href="%s"' % anchor
        return 'href="#%s"' % page
    return re.sub(r'href="([^"]+)"', fix, html)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else SITE / "preview"
    out.mkdir(parents=True, exist_ok=True)

    index = (SITE / "index.html").read_text(encoding="utf-8")
    head_bits = "\n".join([
        grab(r"<title>.*?</title>", index),
        optional(r'<meta name="description"[^>]*>', index),
        grab(r'<link rel="preconnect" href="https://fonts.googleapis.com">', index),
        grab(r'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', index),
        grab(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>', index),
        '<link rel="stylesheet" href="style.css">',
        grab(r'<link rel="icon"[^>]*>', index),
    ])
    hero = grab(r'<section class="hero"[^>]*>.*?</section>', index)
    header = grab(r'<header class="top">.*?</header>', index)
    header = header.replace(' aria-current="page"', "")
    header = header.replace(
        "</nav>",
        '</nav>\n  <span id="editbar" class="m dim" hidden>'
        '<a href="#" data-act="edit">edit</a>'
        '<span class="editing" hidden><a href="#" data-act="save">save</a> · <a href="#" data-act="cancel">cancel</a></span>'
        '<span class="status"></span></span>',
    )
    qv = optional(r'<div class="qv"[^>]*>.*?</div>', index)

    sections = []
    for name in PAGES:
        src = (SITE / (name + ".html")).read_text(encoding="utf-8")
        m = re.search(r"<main([^>]*)>(.*?)</main>", src, re.S)
        if not m:
            raise SystemExit("no <main> in " + name)
        attrs, body = m.group(1), m.group(2)
        cls = re.search(r'class="([^"]*)"', attrs)
        classes = "main" + ((" " + cls.group(1)) if cls else "")
        sections.append('<section class="page" id="page-%s" hidden>\n<div class="%s">%s</div>\n</section>'
                        % (name, classes, body))

    js = PREVIEW_JS.replace("__SKELETON_HEAD__", repr(SKELETON_HEAD)).replace("__PAGES__", repr(PAGES))

    doc = "\n".join([
        '<div id="page">',
        head_bits,
        "<style>" + PREVIEW_CSS + "</style>",
        '<div id="top"></div>',
        hero,
        '<div class="sheet">',
        header,
        "\n".join(sections),
        "</div>",
        qv,
        '<script src="script.js" defer></script>',
        '<script id="preview-script">' + js + "</script>",
        "</div>",
    ])
    doc = rewrite_hrefs(doc)

    (out / "index.html").write_text(doc, encoding="utf-8")
    shutil.copy(SITE / "style.css", out / "style.css")
    shutil.copy(SITE / "script.js", out / "script.js")
    assets_out = out / "assets"
    assets_out.mkdir(exist_ok=True)
    for f in (SITE / "assets").glob("*"):
        if f.is_file():
            shutil.copy(f, assets_out / f.name)
    keys = re.findall(r'data-edit="([^"]+)"', doc)
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    print("wrote %s (%d editable regions%s)" % (out / "index.html", len(keys),
                                                 ", DUPLICATE KEYS: %s" % dupes if dupes else ""))


if __name__ == "__main__":
    main()
