// Loading circle (after architecture.yale.edu): when a link to another page of this site is clicked,
// a spinning circle, black with two opposite white quarters, appears where you clicked and follows the
// pointer until the next page arrives. It carries over: the next page shows it again in the same place and
// keeps it spinning until that page and all its pictures have loaded (2026-10-12). A page that reloads itself
// for a newer publish shows it too (window.clLoading, called from the freshness check deploy.sh adds).
(function () {
  var NS = "http://www.w3.org/2000/svg", el = null, x = innerWidth / 2, y = innerHeight / 2, timer = 0;
  function make() {
    el = document.createElement("div"); el.className = "loadcircle"; el.setAttribute("aria-hidden", "true");
    el.innerHTML = '<svg viewBox="0 0 180 180"><defs><clipPath id="lc-clip"><circle cx="90" cy="90" r="90"/></clipPath></defs>' +
      '<g clip-path="url(#lc-clip)"><rect width="180" height="180" fill="#000"/><rect x="90" y="0" width="90" height="90" fill="#fff"/>' +
      '<rect x="0" y="90" width="90" height="90" fill="#fff"/></g></svg>';
    document.body.appendChild(el);
  }
  function place() { if (el) { el.style.left = x + "px"; el.style.top = y + "px"; } }
  function show() { if (!el) make(); place(); el.classList.add("on"); }
  function hide() { clearTimeout(timer); if (el) el.classList.remove("on"); }
  var KEY = "cl-loading";
  function carry() { try { sessionStorage.setItem(KEY, JSON.stringify({ x: x, y: y, t: Date.now() })); } catch (e) {} }
  window.clLoading = function () { carry(); show(); };
  // arriving from a click on this site: spin until everything on this page has loaded
  (function () {
    var c = null; try { c = JSON.parse(sessionStorage.getItem(KEY)); sessionStorage.removeItem(KEY); } catch (e) {}
    if (!c || Date.now() - c.t > 15000 || document.readyState === "complete") return;
    x = c.x; y = c.y; show();
    addEventListener("load", hide);
    setTimeout(hide, 12000);                                                    // never spin forever
  })();
  addEventListener("pointermove", function (e) { x = e.clientX; y = e.clientY; place(); }, { passive: true });
  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest("a[href]"); if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
    var u = new URL(a.href, location.href);
    if (u.origin !== location.origin) return;                                   // leaving the site
    if (u.pathname === location.pathname && u.search === location.search) return; // same page (#links)
    if (e.clientX || e.clientY) { x = e.clientX; y = e.clientY; }
    carry();
    timer = setTimeout(show, 60);                                               // fast pages never flash it
  });
  addEventListener("pageshow", hide);                                           // Back/Forward from memory
  addEventListener("pagehide", hide);
})();
