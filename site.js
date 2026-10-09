// Loading circle (after architecture.yale.edu): when a link to another page of this site is clicked,
// a spinning circle, black with two opposite white quarters, appears where you clicked and follows the
// pointer until the next page arrives.
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
  addEventListener("pointermove", function (e) { x = e.clientX; y = e.clientY; place(); }, { passive: true });
  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest("a[href]"); if (!a || a.target === "_blank" || a.hasAttribute("download")) return;
    var u = new URL(a.href, location.href);
    if (u.origin !== location.origin) return;                                   // leaving the site
    if (u.pathname === location.pathname && u.search === location.search) return; // same page (#links)
    if (e.clientX || e.clientY) { x = e.clientX; y = e.clientY; }
    timer = setTimeout(show, 60);                                               // fast pages never flash it
  });
  addEventListener("pageshow", hide);                                           // Back/Forward from memory
  addEventListener("pagehide", hide);
})();
