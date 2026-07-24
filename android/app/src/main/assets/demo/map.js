// reimap offline demo renderer — a self-contained animated world map.
// Pure canvas, no external libraries. Draws a filled land outline, great-circle
// arcs radiating from the home origin, pulsing endpoint markers, and packets
// travelling along each arc. Original implementation for reimap.
(function () {
  "use strict";

  var canvas = document.getElementById("map");
  var ctx = canvas.getContext("2d");
  var css = getComputedStyle(document.documentElement);
  var COL = {
    land: css.getPropertyValue("--land").trim() || "#1c2748",
    country: css.getPropertyValue("--panel2").trim() || "#1a2547",
    accent: css.getPropertyValue("--accent").trim() || "#4f8cff",
    accent2: css.getPropertyValue("--accent2").trim() || "#00d3a7",
    text: css.getPropertyValue("--text").trim() || "#e6ecff",
    bg: css.getPropertyValue("--bg").trim() || "#0b1021"
  };

  var W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);
  var land = [];

  function resize() {
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener("resize", resize);
  resize();

  // Equirectangular projection covering the full canvas.
  function project(lon, lat) {
    return [(lon + 180) / 360 * W, (90 - lat) / 180 * H];
  }

  // Southern hemisphere markers get a diamond, mirroring the desktop geo_enricher
  // plugin's ui.marker_styled hook — so the two experiences look identical.
  function isSouthern(lat) { return lat < 0; }

  function drawLand() {
    ctx.fillStyle = COL.land;
    ctx.strokeStyle = COL.country;
    ctx.lineWidth = 0.4;
    for (var p = 0; p < land.length; p++) {
      var poly = land[p];
      for (var r = 0; r < poly.length; r++) {
        var ring = poly[r];
        ctx.beginPath();
        for (var i = 0; i < ring.length; i++) {
          var xy = project(ring[i][0], ring[i][1]);
          if (i === 0) ctx.moveTo(xy[0], xy[1]); else ctx.lineTo(xy[0], xy[1]);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
    }
  }

  // A gentle arc between two projected points (quadratic bezier lifted toward the
  // top of the canvas), plus the parametric point at t for the travelling packet.
  function arcPath(x1, y1, x2, y2) {
    var mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    var dist = Math.hypot(x2 - x1, y2 - y1);
    var lift = Math.min(dist * 0.28, H * 0.34);
    return { cx: mx, cy: my - lift, x1: x1, y1: y1, x2: x2, y2: y2 };
  }
  function bez(a, t) {
    var u = 1 - t;
    return [
      u * u * a.x1 + 2 * u * t * a.cx + t * t * a.x2,
      u * u * a.y1 + 2 * u * t * a.cy + t * t * a.y2
    ];
  }

  var endpoints = [];
  function build() {
    var home = window.REIMAP_HOME;
    var h = project(home.lon, home.lat);
    endpoints = (window.REIMAP_DEMO || []).map(function (d, i) {
      var xy = project(d[6], d[5]);
      return {
        x: xy[0], y: xy[1], city: d[3], country: d[4], lat: d[5],
        arc: arcPath(h[0], h[1], xy[0], xy[1]),
        phase: (i * 0.55) % (Math.PI * 2),
        speed: 0.15 + (i % 5) * 0.03
      };
    });
    document.getElementById("stats").innerHTML =
      "Total <b>" + endpoints.length + "</b>  Mapped <b>" + endpoints.length +
      "</b>  Countries <b>" + new Set(endpoints.map(function (e) { return e.country; })).size + "</b>";
  }

  function hex2rgba(hex, a) {
    var n = parseInt(hex.replace("#", ""), 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")";
  }

  var t0 = performance.now();
  function frame(now) {
    var t = (now - t0) / 1000;
    ctx.clearRect(0, 0, W, H);
    drawLand();

    var home = window.REIMAP_HOME;
    var h = project(home.lon, home.lat);

    // Arcs.
    ctx.lineWidth = 1;
    for (var i = 0; i < endpoints.length; i++) {
      var e = endpoints[i], a = e.arc;
      ctx.strokeStyle = hex2rgba(COL.accent, 0.28);
      ctx.beginPath();
      ctx.moveTo(a.x1, a.y1);
      ctx.quadraticCurveTo(a.cx, a.cy, a.x2, a.y2);
      ctx.stroke();
      // Travelling packet.
      var tt = (t * e.speed + i * 0.13) % 1;
      var pp = bez(a, tt);
      ctx.fillStyle = hex2rgba(COL.accent2, 0.9);
      ctx.beginPath();
      ctx.arc(pp[0], pp[1], 2.2, 0, Math.PI * 2);
      ctx.fill();
    }

    // Endpoint markers (pulsing).
    for (var j = 0; j < endpoints.length; j++) {
      var m = endpoints[j];
      var pulse = 1 + 0.3 * Math.sin(t * 2.2 + m.phase);
      var base = 5 * pulse;
      ctx.fillStyle = COL.accent2;
      if (isSouthern(m.lat)) {
        // diamond
        ctx.save(); ctx.translate(m.x, m.y); ctx.rotate(Math.PI / 4);
        ctx.fillRect(-base * 0.8, -base * 0.8, base * 1.6, base * 1.6);
        ctx.restore();
      } else {
        ctx.beginPath(); ctx.arc(m.x, m.y, base, 0, Math.PI * 2); ctx.fill();
      }
      // soft glow ring
      ctx.strokeStyle = hex2rgba(COL.accent2, 0.25 * (2 - pulse));
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(m.x, m.y, base + 6 * pulse, 0, Math.PI * 2); ctx.stroke();
    }

    // Home star.
    var starPulse = 1 + 0.15 * Math.sin(t * 3);
    ctx.fillStyle = COL.accent2;
    ctx.strokeStyle = COL.text;
    ctx.lineWidth = 1;
    drawStar(h[0], h[1], 5, 9 * starPulse, 4.5 * starPulse);

    requestAnimationFrame(frame);
  }

  function drawStar(cx, cy, spikes, outer, inner) {
    var rot = -Math.PI / 2, step = Math.PI / spikes;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(rot) * outer, cy + Math.sin(rot) * outer);
    for (var i = 0; i < spikes; i++) {
      rot += step;
      ctx.lineTo(cx + Math.cos(rot) * inner, cy + Math.sin(rot) * inner);
      rot += step;
      ctx.lineTo(cx + Math.cos(rot) * outer, cy + Math.sin(rot) * outer);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  // Load land data then start.
  fetch("land.json")
    .then(function (r) { return r.json(); })
    .then(function (data) { land = data; build(); requestAnimationFrame(frame); })
    .catch(function () { build(); requestAnimationFrame(frame); });
})();
