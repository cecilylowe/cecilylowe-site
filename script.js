/* cecilylowe.com
   1. the newsletter form
   2. the clock in the footer
   3. drawings: the diagram (rings, spokes, dust), the array, the charge staircase, a ring-down,
      a hollow-core fibre, the digest — all in the theme's palette
   4. quick view: a drawing in the corner while an index row is hovered
   5. the hero: the photo pinned at the top; the page slides up over it as you scroll
*/

(function () {
  "use strict";

  /* ---------- 1. newsletter ---------- */

  // Buttondown username. Leave empty until the list exists; the form then says so instead of failing.
  var NEWSLETTER = { buttondownUsername: "" };

  var form = document.querySelector("form.news");
  if (form) {
    var note = form.parentNode.querySelector(".note");
    if (NEWSLETTER.buttondownUsername) {
      form.action = "https://buttondown.com/api/emails/embed-subscribe/" + NEWSLETTER.buttondownUsername;
      form.method = "post";
    }
    form.addEventListener("submit", function (e) {
      if (!NEWSLETTER.buttondownUsername) {
        e.preventDefault();
        if (note) note.textContent = "Not taking signups just yet. Check back soon.";
        console.warn("Newsletter: set NEWSLETTER.buttondownUsername in script.js to connect this form.");
        return;
      }
      if (note) note.textContent = "Sending…";
    });
  }

  /* ---------- 2. clock ---------- */

  var clocks = document.querySelectorAll(".clock");
  if (clocks.length) {
    var fmt = new Intl.DateTimeFormat("en-GB", {
      timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false
    });
    var hourFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "America/New_York", hour: "numeric", hour12: false });
    var phrase = function (h) {
      if (h < 5) return "late night";
      if (h < 8) return "early morning";
      if (h < 12) return "morning";
      if (h < 14) return "midday";
      if (h < 17) return "afternoon";
      if (h < 20) return "evening";
      if (h < 23) return "night";
      return "late night";
    };
    var tick = function () {
      var now = new Date();
      var h = parseInt(hourFmt.format(now), 10) % 24;
      var s = fmt.format(now) + " · " + phrase(h);
      for (var i = 0; i < clocks.length; i++) clocks[i].textContent = s;
    };
    tick();
    setInterval(tick, 15000);
  }

  var years = document.querySelectorAll(".year-now");
  for (var y = 0; y < years.length; y++) years[y].textContent = String(new Date().getFullYear());

  /* ---------- shared ---------- */

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var css = getComputedStyle(document.documentElement);
  function token(name, fallback) { return (css.getPropertyValue(name) || "").trim() || fallback; }
  var ink = {
    fg: token("--ink", "#3a3e4a"),
    fg2: token("--ink-2", "rgba(58,62,74,.55)"),
    fg3: token("--ink-3", "rgba(58,62,74,.16)"),
    coral: token("--coral", "#e3927a"),
    coral2: token("--coral-2", "#f2c9bb"),
    blue: token("--blue", "#8ea6d4"),
    blue2: token("--blue-2", "#c9d5ea"),
    straw: token("--straw", "#e9d393"),
    sage: token("--sage", "#aec7b4"),
    lilac: token("--lilac", "#cdc6e4"),
    groundA: token("--ground-a", "#e3e7ee"),
    groundB: token("--ground-b", "#f4e8dc"),
    paper: token("--paper-solid", "#fbf8f3")
  };

  // deterministic pseudo-random, so a drawing looks the same on every visit
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a += 0x6D2B79F5;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(r) {
    var u = 1 - r(), v = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  // size a canvas to its CSS box at device resolution; returns {ctx, w, h} in CSS pixels
  function fit(canvas) {
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    var r = canvas.getBoundingClientRect();
    var w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    }
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: ctx, w: w, h: h };
  }

  /* ---------- 3. drawings ---------- */

  // The six pairings the diagram cycles through: (rings and lobes, dust)
  var PAIRS = [
    ["blue", "coral"], ["coral", "blue"], ["sage", "coral"],
    ["lilac", "straw"], ["blue", "straw"], ["coral", "sage"]
  ];

  var sketch = {

    // Rings, spokes, two translucent lobes and a dust-field, over a split ground.
    // opts: {variant: 0..5, ground: true|false, t: seconds}
    diagram: function (ctx, w, h, t, opts) {
      opts = opts || {};
      var variant = (opts.variant || 0) % PAIRS.length;
      var pair = PAIRS[variant];
      var c1 = ink[pair[0]], c2 = ink[pair[1]];
      var r = rng(101 + variant * 7);
      t = t || 0;

      ctx.clearRect(0, 0, w, h);
      if (opts.ground !== false) {
        // a split ground, the way the paintings divide the canvas
        var vertical = variant % 2 === 0;
        ctx.fillStyle = ink.groundA;
        ctx.fillRect(0, 0, vertical ? w * 0.5 : w, vertical ? h : h * 0.5);
        ctx.fillStyle = ink.groundB;
        if (vertical) ctx.fillRect(w * 0.5, 0, w * 0.5, h); else ctx.fillRect(0, h * 0.5, w, h * 0.5);
      }

      var cx = w * (0.5 + (r() - 0.5) * 0.12), cy = h * (0.5 + (r() - 0.5) * 0.1);
      var R = Math.min(w, h) * (0.42 + r() * 0.08);

      // axes
      ctx.strokeStyle = ink.fg3;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(0, cy + 0.5); ctx.lineTo(w, cy + 0.5); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx + 0.5, 0); ctx.lineTo(cx + 0.5, h); ctx.stroke();

      // spokes, turning very slowly
      var spokes = 24 + Math.floor(r() * 16);
      var rot = t * 0.004;
      ctx.save();
      ctx.globalAlpha = 0.5;
      ctx.strokeStyle = ink.fg3;
      for (var s = 0; s < spokes; s++) {
        var a = rot + s * 2 * Math.PI / spokes;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a) * R * 0.1, cy + Math.sin(a) * R * 0.1);
        ctx.lineTo(cx + Math.cos(a) * R * 1.35, cy + Math.sin(a) * R * 1.35);
        ctx.stroke();
      }
      ctx.restore();

      // lobes: two soft discs, the way two of the paintings hold a pair of blue shapes
      ctx.save();
      ctx.globalAlpha = 0.42;
      ctx.fillStyle = c1;
      var lobeR = R * (0.22 + r() * 0.1);
      var lx = cx - R * 0.2, ly = cy + R * 0.14;
      ctx.beginPath(); ctx.arc(lx, ly, lobeR, 0, 6.2832); ctx.fill();
      ctx.beginPath(); ctx.arc(cx + R * 0.22, cy - R * 0.16, lobeR * 0.9, 0, 6.2832); ctx.fill();
      ctx.restore();

      // rings, or on odd variants sweeping arcs that open like the spiral image
      var rings = 12 + Math.floor(r() * 8);
      var sweep = variant % 2 === 1;
      var a0 = r() * 6.2832;
      for (var i = 0; i < rings; i++) {
        var rr = R * (0.1 + 1.15 * i / rings) * (1 + (r() - 0.5) * 0.03);
        ctx.strokeStyle = (i % 3 === 2) ? c2 : c1;
        ctx.globalAlpha = 0.35 + 0.4 * r();
        ctx.lineWidth = r() < 0.2 ? 1.5 : 0.8;
        ctx.beginPath();
        if (sweep) {
          var span = 2.2 + r() * 2.6;
          ctx.arc(cx, cy, rr, a0 + i * 0.09 + rot, a0 + i * 0.09 + rot + span);
        } else {
          ctx.arc(cx, cy, rr, 0, 6.2832);
        }
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      // dust: a cloud of particles around the centre, colours of the pair plus straw
      var n = Math.round(Math.min(900, (w * h) / 420));
      var drift = reduced ? 0 : 1;
      for (var k = 0; k < n; k++) {
        var rad = Math.abs(gauss(r)) * R * 0.42;
        var ang = r() * 6.2832;
        var wob = drift * Math.sin(t * 0.3 + k) * 1.2;
        var px = cx + Math.cos(ang) * rad + wob, py = cy + Math.sin(ang) * rad - wob;
        var pick = r();
        ctx.fillStyle = pick < 0.45 ? c2 : (pick < 0.85 ? c1 : ink.straw);
        ctx.globalAlpha = 0.45 + r() * 0.5;
        var size = 0.6 + r() * 1.6;
        ctx.beginPath(); ctx.arc(px, py, size, 0, 6.2832); ctx.fill();
      }
      ctx.globalAlpha = 1;
    },

    // 7 x 7 traps seen from above. Every dot jitters: a trapped sphere is never still.
    array: function (ctx, w, h, t) {
      ctx.clearRect(0, 0, w, h);
      var n = 7, s = Math.min(w, h) / (n + 1.6);
      var x0 = (w - s * (n - 1)) / 2, y0 = (h - s * (n - 1)) / 2;
      var r = rng(49);
      for (var i = 0; i < n; i++) {
        for (var j = 0; j < n; j++) {
          var f1 = 0.6 + r() * 0.8, f2 = 0.6 + r() * 0.8, p1 = r() * 6.28, p2 = r() * 6.28;
          var a = s * 0.07;
          var dx = a * Math.sin(t * f1 + p1), dy = a * Math.cos(t * f2 + p2);
          ctx.fillStyle = r() < 0.15 ? ink.coral : ink.blue;
          ctx.beginPath();
          ctx.arc(x0 + i * s + dx, y0 + j * s + dy, s * 0.13, 0, 6.2832);
          ctx.fill();
        }
      }
    },

    // charge on one sphere against UV pulse number: integer plateaus
    steps: function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var levels = [-5, -4, -3, -1, 0, 1, 3, 4];
      var lens = [1.0, 2.1, 1.4, 1.5, 2.4, 5.2, 0.7, 2.3];
      var total = 0, k;
      for (k = 0; k < lens.length; k++) total += lens[k];
      var padL = w * 0.06, padR = w * 0.03, padT = h * 0.08, padB = h * 0.1;
      var pw = w - padL - padR, ph = h - padT - padB;
      var yOf = function (q) { return padT + ph * (1 - (q + 6) / 11); };
      ctx.strokeStyle = ink.blue2;
      ctx.lineWidth = 1;
      for (var q = -6; q <= 5; q++) {
        ctx.beginPath(); ctx.moveTo(padL, yOf(q) + 0.5); ctx.lineTo(w - padR, yOf(q) + 0.5); ctx.stroke();
      }
      ctx.strokeStyle = ink.fg2;
      ctx.beginPath(); ctx.moveTo(padL + 0.5, padT); ctx.lineTo(padL + 0.5, h - padB); ctx.stroke();
      var r = rng(266);
      var x = padL + 2, rad = Math.max(1.2, Math.min(2.2, w / 260));
      ctx.fillStyle = ink.coral;
      for (k = 0; k < levels.length; k++) {
        var segW = pw * lens[k] / total;
        var count = Math.max(6, Math.round(segW / (rad * 2.4)));
        for (var i = 0; i < count; i++) {
          var px = x + segW * (i + 0.5) / count;
          var py = yOf(levels[k] + gauss(r) * 0.13);
          ctx.beginPath(); ctx.arc(px, py, rad, 0, 6.2832); ctx.fill();
        }
        x += segW;
      }
    },

    // a sphere at rest, a kick, a short cold-damped ring-down
    ringdown: function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var padL = w * 0.06, padR = w * 0.03, mid = h * 0.5, amp = h * 0.36;
      var r = rng(7);
      var t0 = 0.3, omega = 2 * Math.PI * 7.5, gamma = 2.2;
      ctx.strokeStyle = ink.fg3;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(padL, mid + 0.5); ctx.lineTo(w - padR, mid + 0.5); ctx.stroke();
      ctx.strokeStyle = ink.fg2;
      ctx.beginPath(); ctx.moveTo(padL + 0.5, h * 0.1); ctx.lineTo(padL + 0.5, h * 0.9); ctx.stroke();
      ctx.strokeStyle = ink.blue;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      var N = Math.round((w - padL - padR) / 1.5);
      for (var i = 0; i <= N; i++) {
        var u = i / N, x = padL + (w - padL - padR) * u;
        var y = gauss(r) * 0.018;
        if (u >= t0) {
          var tau = (u - t0) * 2.6;
          y += Math.exp(-gamma * tau) * Math.sin(omega * tau / 2.6);
        }
        var py = mid - amp * y;
        if (i === 0) ctx.moveTo(x, py); else ctx.lineTo(x, py);
      }
      ctx.stroke();
      var xk = padL + (w - padL - padR) * t0;
      ctx.strokeStyle = ink.coral;
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(xk + 0.5, mid + amp * 0.75); ctx.lineTo(xk + 0.5, mid + amp * 1.05); ctx.stroke();
    },

    // cross-section of a hollow-core fibre: a hexagonal lattice of holes around an empty core,
    // and a few particles sitting in the core
    fibre: function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.46;
      var pitch = R / 7.2, hole = pitch * 0.36, core = pitch * 2.2;
      ctx.lineWidth = 1;
      ctx.strokeStyle = ink.blue;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.2832); ctx.stroke();
      ctx.strokeStyle = ink.straw;
      var rows = Math.ceil(R / (pitch * 0.866)) + 1;
      for (var j = -rows; j <= rows; j++) {
        var y = cy + j * pitch * 0.866;
        var off = (j % 2 ? pitch / 2 : 0);
        for (var i = -rows - 1; i <= rows + 1; i++) {
          var x = cx + i * pitch + off;
          var d = Math.hypot(x - cx, y - cy);
          if (d + hole > R - pitch * 0.5 || d < core + hole * 0.8) continue;
          ctx.beginPath(); ctx.arc(x, y, hole, 0, 6.2832); ctx.stroke();
        }
      }
      ctx.strokeStyle = ink.blue;
      ctx.beginPath(); ctx.arc(cx, cy, core, 0, 6.2832); ctx.stroke();
      ctx.fillStyle = ink.coral;
      for (var k = -1; k <= 1; k++) {
        ctx.beginPath(); ctx.arc(cx + k * core * 0.55, cy, pitch * 0.17, 0, 6.2832); ctx.fill();
      }
    },

    // the morning email: many listings, a few kept
    digest: function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var r = rng(8);
      var rows = 13, pad = h * 0.08, rowH = (h - 2 * pad) / rows;
      var keep = { 1: 1, 4: 1, 8: 1, 11: 1 };
      for (var i = 0; i < rows; i++) {
        var y = pad + rowH * (i + 0.5), kept = !!keep[i];
        var x = w * 0.08;
        ctx.fillStyle = kept ? ink.coral : ink.blue2;
        ctx.beginPath(); ctx.arc(x, y, 2, 0, 6.2832); ctx.fill();
        ctx.fillStyle = kept ? ink.blue : ink.blue2;
        x += w * 0.04;
        ctx.fillRect(x, y - 1, w * 0.09, 2);
        x += w * 0.12;
        ctx.fillRect(x, y - 1, w * (0.28 + r() * 0.42), 2);
      }
    }
  };

  // inline figures
  var figs = [];
  var figCanvases = document.querySelectorAll("canvas[data-sketch]");
  for (var f = 0; f < figCanvases.length; f++) {
    (function (canvas) {
      var name = canvas.getAttribute("data-sketch");
      if (!sketch[name]) return;
      figs.push({
        canvas: canvas, name: name,
        opts: { variant: parseInt(canvas.getAttribute("data-variant") || "0", 10) || 0 }
      });
    })(figCanvases[f]);
  }
  function drawFig(fig, t) {
    var s = fit(fig.canvas);
    sketch[fig.name](s.ctx, s.w, s.h, t || 0, fig.opts);
  }
  function drawAllFigs() { for (var i = 0; i < figs.length; i++) drawFig(figs[i], 0); }
  drawAllFigs();
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(drawAllFigs, 120);
  });

  // the array figures keep jittering, gently, unless the visitor prefers not
  if (!reduced) {
    var moving = figs.filter(function (g) { return g.name === "array"; });
    if (moving.length) {
      var start = performance.now();
      var loop = function (now) {
        var t = (now - start) / 1000;
        for (var i = 0; i < moving.length; i++) drawFig(moving[i], t);
        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }
  }

  /* ---------- 4. quick view ---------- */

  var qv = document.querySelector(".qv");
  if (qv && window.matchMedia("(hover: hover)").matches) {
    var qvCanvas = qv.querySelector("canvas");
    var rowsWithSketch = document.querySelectorAll(".row[data-sketch]");
    var qvT0 = performance.now(), qvName = null, qvRaf = null;
    var qvDraw = function (now) {
      if (!qvName) return;
      var s = fit(qvCanvas);
      sketch[qvName](s.ctx, s.w, s.h, (now - qvT0) / 1000, { variant: 0 });
      if (qvName === "array" && !reduced) qvRaf = requestAnimationFrame(qvDraw);
    };
    for (var q = 0; q < rowsWithSketch.length; q++) {
      (function (row) {
        var name = row.getAttribute("data-sketch");
        if (!sketch[name]) return;
        row.addEventListener("mouseenter", function () {
          qvName = name;
          qv.classList.add("on");
          if (qvRaf) cancelAnimationFrame(qvRaf);
          qvDraw(performance.now());
        });
        row.addEventListener("mouseleave", function () {
          qvName = null;
          qv.classList.remove("on");
          if (qvRaf) cancelAnimationFrame(qvRaf);
        });
      })(rowsWithSketch[q]);
    }
  }

  /* ---------- 5. the hero ---------- */

  // The photo is pinned at the top; the page slides up over it. While that happens the photo
  // zooms in a little, the way a product page does. Nothing to click, just scroll.
  var hero = document.querySelector(".hero");
  if (hero) {
    var heroImg = hero.querySelector(".film");
    var ticking = false;
    var paint = function () {
      ticking = false;
      var h = hero.offsetHeight || window.innerHeight;
      var p = Math.min(1, Math.max(0, window.scrollY / h));
      if (heroImg) {
        heroImg.style.transform = reduced ? "" : "scale(" + (1 + 0.12 * p).toFixed(4) + ")";
      }
      hero.classList.toggle("covered", p >= 0.999);
    };
    var onScroll = function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(paint);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    paint();
  }
})();
