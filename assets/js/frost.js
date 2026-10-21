/* FROST portal interactions. No dependencies. */
(function () {
  "use strict";
  if (/[?&]noanim/.test(location.search)) document.documentElement.classList.add("noanim");
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* header: mobile menu + transparent-on-dark-hero */
  var header = $(".site-header");
  if (header) {
    var btn = $(".menu-btn", header);
    if (btn) btn.addEventListener("click", function () {
      var open = header.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (document.body.hasAttribute("data-dark-hero")) {
      var tone = function () { header.classList.toggle("on-dark", window.scrollY < 40); };
      tone(); window.addEventListener("scroll", tone, { passive: true });
    }
  }

  /* reveal on scroll */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("seen"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    $$(".fade-in").forEach(function (el) { io.observe(el); });
  } else { $$(".fade-in").forEach(function (el) { el.classList.add("seen"); }); }

  /* tabs (three ways in) */
  $$("[data-tabs]").forEach(function (root) {
    var tabs = $$("[role=tab]", root);
    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        tabs.forEach(function (x) { x.setAttribute("aria-selected", x === t ? "true" : "false"); });
        $$(".panel", root).forEach(function (p) { p.classList.toggle("active", p.id === t.getAttribute("aria-controls")); });
      });
    });
  });

  /* copy citation */
  $$("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var txt = b.getAttribute("data-copy");
      var done = function () { var o = b.textContent; b.textContent = "Copied"; setTimeout(function () { b.textContent = o; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, done); else done();
    });
  });

  /* gallery + lightbox */
  var lb = $(".lightbox");
  var lbItems = [], lbIdx = 0;
  function lbShow(i) {
    if (!lbItems.length) return;
    lbIdx = (i + lbItems.length) % lbItems.length;
    $("img", lb).src = lbItems[lbIdx].src; $("img", lb).alt = lbItems[lbIdx].cap;
    $("figcaption", lb).textContent = lbItems[lbIdx].cap;
  }
  function lbOpen(items, i) { lbItems = items; lb.classList.add("open"); lbShow(i); $(".x", lb).focus(); }
  function lbClose() { lb.classList.remove("open"); }
  if (lb) {
    $(".x", lb).addEventListener("click", lbClose);
    $(".prev", lb).addEventListener("click", function () { lbShow(lbIdx - 1); });
    $(".next", lb).addEventListener("click", function () { lbShow(lbIdx + 1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) lbClose(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") lbClose();
      if (e.key === "ArrowLeft") lbShow(lbIdx - 1);
      if (e.key === "ArrowRight") lbShow(lbIdx + 1);
    });
  }
  $$(".gallery").forEach(function (g) {
    var main = $(".main", g), img = $(".main img", g), cap = $(".cap", g);
    var thumbs = $$(".thumbs button", g);
    var items = thumbs.length ? thumbs.map(function (t) { return { src: t.getAttribute("data-full"), cap: t.getAttribute("data-cap") }; })
                              : [{ src: img.getAttribute("src"), cap: img.getAttribute("alt") }];
    var cur = 0;
    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function () {
        cur = i; img.src = items[i].src; img.alt = items[i].cap; cap.textContent = items[i].cap;
        thumbs.forEach(function (x) { x.setAttribute("aria-current", x === t ? "true" : "false"); });
      });
    });
    if (main && lb) main.addEventListener("click", function () { lbOpen(items, cur); });
  });
  $$("[data-zoom]").forEach(function (el) {
    if (!lb) return;
    el.style.cursor = "zoom-in";
    el.addEventListener("click", function () { lbOpen([{ src: el.getAttribute("data-zoom"), cap: el.getAttribute("data-cap") || "" }], 0); });
  });

  /* faceted filtering (datasets, publications, software) */
  $$("[data-filter-root]").forEach(function (root) {
    var items = $$("[data-item]", root);
    var search = $("[data-search]", root);
    var countEl = $("[data-count]", root);
    var empty = $(".empty", root);
    var sortSel = $("[data-sort]", root);
    var list = $("[data-list]", root);
    var state = {};
    function matches(it) {
      for (var k in state) {
        if (!state[k].length) continue;
        var vals = (it.getAttribute("data-" + k) || "").split("|");
        if (!state[k].some(function (v) { return vals.indexOf(v) >= 0; })) return false;
      }
      if (search && search.value.trim()) {
        var q = search.value.trim().toLowerCase().split(/\s+/);
        var hay = (it.getAttribute("data-text") || it.textContent).toLowerCase();
        if (!q.every(function (w) { return hay.indexOf(w) >= 0; })) return false;
      }
      return true;
    }
    function apply() {
      var n = 0;
      items.forEach(function (it) { var ok = matches(it); it.hidden = !ok; if (ok) n++; });
      $$("[data-group]", root).forEach(function (g) {
        var any = $$("[data-item]", g).some(function (it) { return !it.hidden; });
        g.hidden = !any;
        var c = $("[data-group-count]", g);
        if (c) c.textContent = $$("[data-item]", g).filter(function (it) { return !it.hidden; }).length + " papers";
      });
      if (countEl) countEl.textContent = n;
      if (empty) empty.style.display = n ? "none" : "block";
    }
    $$(".opt[data-key], .coll-card[data-key]", root).forEach(function (o) {
      o.addEventListener("click", function () {
        var k = o.getAttribute("data-key"), v = o.getAttribute("data-val");
        state[k] = state[k] || [];
        var i = state[k].indexOf(v);
        if (i >= 0) state[k].splice(i, 1); else state[k].push(v);
        $$('[data-key="' + k + '"][data-val="' + v + '"]', root).forEach(function (x) { x.setAttribute("aria-pressed", i >= 0 ? "false" : "true"); });
        apply();
      });
    });
    if (search) search.addEventListener("input", apply);
    var clear = $("[data-clear]", root);
    if (clear) clear.addEventListener("click", function () {
      state = {}; if (search) search.value = "";
      $$("[aria-pressed]", root).forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
      apply();
    });
    if (sortSel && list) sortSel.addEventListener("change", function () {
      var key = sortSel.value;
      var arr = items.slice();
      var rel = { "v0.5": 0, "v1.0": 1, "v2.0": 2 };
      arr.sort(function (a, b) {
        if (key === "az") return a.getAttribute("data-title").localeCompare(b.getAttribute("data-title"));
        if (key === "release") return (rel[a.getAttribute("data-release")] - rel[b.getAttribute("data-release")]) || (+a.getAttribute("data-order") - +b.getAttribute("data-order"));
        if (key === "newest") return (+b.getAttribute("data-year") - +a.getAttribute("data-year")) || (+a.getAttribute("data-order") - +b.getAttribute("data-order"));
        return +a.getAttribute("data-order") - +b.getAttribute("data-order");
      });
      arr.forEach(function (x) { list.appendChild(x); });
    });
    var params = new URLSearchParams(location.search);
    params.forEach(function (v, k) {
      var o = $('[data-key="' + k + '"][data-val="' + v + '"]', root);
      if (o) o.click();
    });
    if (params.get("q") && search) { search.value = params.get("q"); }
    apply();
  });

  /* coverage chart */
  var cv = $("#coverage-chart");
  if (cv && window.FROST_COVERAGE) {
    var D = window.FROST_COVERAGE;
    var W = 640, H = 420, m = { l: 58, r: 20, t: 18, b: 52 };
    var x = function (t) { return m.l + (t + 20) / 20 * (W - m.l - m.r); };
    var ly = function (v) { return Math.log10(v); };
    var y0 = ly(0.2), y1 = ly(6);
    var y = function (v) { return m.t + (1 - (ly(v) - y0) / (y1 - y0)) * (H - m.t - m.b); };
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Scatter plot of icing-tunnel campaign conditions: air temperature from −20 to 0 °C against liquid water content from 0.2 to 6 g/m³, by test-article family");
    function el(tag, attrs, parent) { var e = document.createElementNS(ns, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); (parent || svg).appendChild(e); return e; }
    var g = el("g", { "class": "grid" });
    [-20, -15, -10, -5, 0].forEach(function (t) { el("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b }, g); });
    [0.3, 0.5, 1, 2, 4].forEach(function (v) { el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }, g); });
    var ax = el("g", { "class": "axis" });
    [-20, -15, -10, -5, 0].forEach(function (t) { var tx = el("text", { x: x(t), y: H - m.b + 20, "text-anchor": "middle" }, ax); tx.textContent = t === 0 ? "0" : "−" + Math.abs(t); });
    [0.3, 0.5, 1, 2, 4].forEach(function (v) { var tx = el("text", { x: m.l - 10, y: y(v) + 4, "text-anchor": "end" }, ax); tx.textContent = v; });
    var xt = el("text", { x: (m.l + W - m.r) / 2, y: H - 10, "text-anchor": "middle", "class": "axis-title" }); xt.textContent = "Air temperature T∞ (°C)";
    var yt = el("text", { x: 16, y: (m.t + H - m.b) / 2, "text-anchor": "middle", "class": "axis-title", transform: "rotate(-90 16 " + (m.t + H - m.b) / 2 + ")" }); yt.textContent = "Liquid water content (g/m³, log)";
    var rf = el("g", { "class": "ref" });
    [[-5, "glaze reference"], [-15, "rime reference"]].forEach(function (r) {
      el("line", { x1: x(r[0]), x2: x(r[0]), y1: y(5.6), y2: H - m.b }, rf);
      var tx = el("text", { x: x(r[0]) + 5, y: y(5.6) + 10 }, rf); tx.textContent = r[1];
    });
    var plan = el("g", {});
    D.plan.forEach(function (p) { el("circle", { cx: x(p[0]), cy: y(p[1]), r: 2.4, "class": "plan" }, plan); });
    var tip = document.createElement("div"); tip.className = "tip"; cv.appendChild(tip);
    function shape(kind, cx, cy, s, color, parent) {
      var attrs = { fill: color, stroke: "#fff", "stroke-width": 2, "class": "pt", tabindex: 0 };
      var e;
      if (kind === "circle") { attrs.cx = cx; attrs.cy = cy; attrs.r = s; e = el("circle", attrs, parent); }
      else if (kind === "square") { attrs.x = cx - s * .9; attrs.y = cy - s * .9; attrs.width = s * 1.8; attrs.height = s * 1.8; attrs.rx = 2; e = el("rect", attrs, parent); }
      else if (kind === "triangle") { attrs.points = [cx, cy - s * 1.15, cx + s * 1.05, cy + s * .8, cx - s * 1.05, cy + s * .8].join(","); e = el("polygon", attrs, parent); }
      else { attrs.points = [cx, cy - s * 1.2, cx + s * 1.1, cy, cx, cy + s * 1.2, cx - s * 1.1, cy].join(","); e = el("polygon", attrs, parent); }
      return e;
    }
    D.series.forEach(function (s, si) {
      var gg = el("g", {});
      s.points.forEach(function (p) {
        var dx = (si - 1.5) * 0.28;
        var cy = p[1] ? y(p[1]) : H - m.b - 8;
        var e = shape(s.shape, x(p[0] + dx), cy, 5.2, s.color, gg);
        var lbl = s.name + (p[2] ? " · " + p[2] : "");
        var cond = "T∞ = " + (p[0] < 0 ? "−" : "") + Math.abs(p[0]) + " °C · " + (p[1] ? "LWC = " + p[1] + " g/m³" : "LWC not controlled (natural cloud)");
        e.setAttribute("aria-label", lbl + ", " + cond);
        var show = function () {
          var r = cv.getBoundingClientRect(), b = e.getBoundingClientRect();
          tip.innerHTML = "<b>" + lbl + "</b><br><span class='tc'>" + cond + "</span>";
          tip.style.left = (b.left + b.width / 2 - r.left) + "px"; tip.style.top = (b.top - r.top) + "px"; tip.style.opacity = 1;
        };
        e.addEventListener("mouseenter", show); e.addEventListener("focus", show);
        e.addEventListener("mouseleave", function () { tip.style.opacity = 0; }); e.addEventListener("blur", function () { tip.style.opacity = 0; });
      });
    });
    cv.insertBefore(svg, tip);
    var tb = $("[data-table-toggle]");
    if (tb) tb.addEventListener("click", function () {
      var t = $("#coverage-table"); var open = t.hidden; t.hidden = !open;
      tb.textContent = open ? "Hide data table" : "Show data table";
    });
  }

  /* access request -> email */
  var form = $("#access-form");
  if (form) form.addEventListener("submit", function (e) {
    e.preventDefault();
    var f = new FormData(form);
    var body = ["Name: " + f.get("name"), "Email: " + f.get("email"), "Affiliation: " + f.get("aff"),
      "Interested in: " + f.get("tier"), "Collections: " + (f.get("coll") || "-"), "", "Intended use:", f.get("use") || ""].join("\n");
    location.href = "mailto:" + form.getAttribute("data-to") + "?subject=" + encodeURIComponent("FROST access request: " + f.get("name")) + "&body=" + encodeURIComponent(body);
  });
})();
