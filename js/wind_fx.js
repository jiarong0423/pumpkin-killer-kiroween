/*
 * Pumpkin Killer - wind scene reaction (leaves, ghost-dust, fog) and lean helpers.
 *
 * DOM-free and deterministic. Works in Node (module.exports) and in the
 * browser (global `WindFx`). Design: docs/wind_design.md.
 *
 * Conventions
 *  - Canvas coordinates: x to the right, y DOWN. Positive wind blows to +x.
 *  - Wind values are in game wind units (shared/constants.json, -4..+4).
 *    Anything non-numeric or NaN counts as 0; +-Infinity is clamped.
 *  - The random generator is used only inside createWindField, once, to place
 *    the items. update() and draw() never draw random numbers, so the same
 *    seed and the same calls give the same pictures.
 *  - draw() only uses: save, restore, beginPath, arc, ellipse, fill,
 *    createRadialGradient (+ addColorStop), globalAlpha, fillStyle,
 *    globalCompositeOperation. No transforms, so every shape position is an
 *    absolute canvas coordinate and the HUD keep-out test is exact.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.WindFx = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var TAU = Math.PI * 2;

  // ---- budget and tuning numbers (a test can check each of these)
  var DEFAULT_WIDTH = 1920;
  var DEFAULT_HEIGHT = 1080;
  var DEFAULT_WIND_MAX = 4;
  var MAX_ITEMS = 96;          // hard budget: fog puffs + dust + leaves
  var DEFAULT_COUNT = 64;
  var MAX_FOG = 8;             // fog puffs inside the budget
  var MAX_DT = 0.1;            // seconds; a longer frame is treated as 0.1 s
  var WIND_EASE_TAU = 0.6;     // seconds; the field eases toward a new wind
  var GUST_TAU = 1.0;          // seconds; a wind change adds a gust that fades
  var AVOID_MIN_GAP = 1;       // px; nothing is drawn closer than this to a keep-out rect
  var AVOID_FADE = 24;         // px; items fade out over this distance before a keep-out rect
  var FLAME_LEAN_MAX = 0.6;    // rad (about 34 degrees)
  var SWAY_MEAN_MAX = 0.3;     // rad
  var SWAY_MAX = 0.5;          // rad, hard clamp

  // Horizontal speed at full wind (px/s) and calm drift (px/s) per kind.
  var WIND_SPEED = { fog: 90, dust: 260, leaf: 420 };
  var CALM_DRIFT = { fog: 4, dust: 10, leaf: 14 };

  var LEAF_COLORS = ['#8a4b1f', '#a35a22', '#5c3a1a', '#7a3d18'];
  var DUST_COLORS = ['#bfe9ff', '#d9b8ff', '#ffe9a3', '#9ff3ff'];

  // ---------------------------------------------------------------------
  // helpers

  function clamp(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
  }

  function isFiniteNumber(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function posNum(v, def) {
    return isFiniteNumber(v) && v > 0 ? v : def;
  }

  function mulberry32(seed) {
    var a = seed | 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function seedToInt(seed) {
    return isFiniteNumber(seed) ? Math.floor(seed) | 0 : 1;
  }

  function wrap(v, size) {
    var r = v - Math.floor(v / size) * size;
    return r >= size || r < 0 ? 0 : r;
  }

  // Wind in game units -> [-1, 1]. Non-numbers and NaN give 0.
  function normalizeWind(w, windMax) {
    if (typeof w !== 'number' || w !== w) {
      return 0;
    }
    var m = posNum(windMax, DEFAULT_WIND_MAX);
    return clamp(w / m, -1, 1);
  }

  // Angle for ctx.rotate() on something that points UP from its base (a flame).
  // Positive wind gives a positive angle, so the tip leans toward +x.
  // Linear in wind, clamped to +-FLAME_LEAN_MAX.
  function flameLean(w, windMax) {
    return clamp(FLAME_LEAN_MAX * normalizeWind(w, windMax), -FLAME_LEAN_MAX, FLAME_LEAN_MAX);
  }

  // Angle for ctx.rotate() on something that hangs DOWN from a pivot (lantern,
  // branch). Positive wind gives a negative angle, so the free end swings
  // toward +x. Mean lean is linear in wind; the swing grows with strength.
  // The frequencies are fixed, so a change of wind never makes the phase jump.
  function swayAngle(w, t, windMax) {
    var n = normalizeWind(w, windMax);
    var s = Math.abs(n);
    // 600 s is a whole number of periods for both swing frequencies.
    var tt = isFiniteNumber(t) ? t % 600 : 0;
    var mean = -SWAY_MEAN_MAX * n;
    var swing = (0.04 + 0.1 * s) * Math.sin(TAU * 0.6 * tt) + 0.02 * s * Math.sin(TAU * 1.7 * tt + 1.3);
    return clamp(mean + swing, -SWAY_MAX, SWAY_MAX);
  }

  // Keep-out rectangles: [x0, y0, x1, y1] with finite numbers. Corners may be
  // given in any order. Invalid entries are dropped.
  function normalizeAvoid(list) {
    var out = [];
    if (!Array.isArray(list)) {
      return out;
    }
    for (var i = 0; i < list.length; i++) {
      var r = list[i];
      if (!Array.isArray(r) || r.length < 4) {
        continue;
      }
      if (!isFiniteNumber(r[0]) || !isFiniteNumber(r[1]) || !isFiniteNumber(r[2]) || !isFiniteNumber(r[3])) {
        continue;
      }
      out.push([Math.min(r[0], r[2]), Math.min(r[1], r[3]), Math.max(r[0], r[2]), Math.max(r[1], r[3])]);
    }
    return out;
  }

  // 0 when the square [x - ext, x + ext] x [y - ext, y + ext] is closer than
  // AVOID_MIN_GAP to any keep-out rectangle, rising to 1 at AVOID_MIN_GAP +
  // AVOID_FADE or more.
  function avoidFade(avoid, x, y, ext) {
    var f = 1;
    for (var i = 0; i < avoid.length; i++) {
      var r = avoid[i];
      var dx = Math.max(r[0] - (x + ext), (x - ext) - r[2], 0);
      var dy = Math.max(r[1] - (y + ext), (y - ext) - r[3], 0);
      var gap = Math.sqrt(dx * dx + dy * dy);
      var k = clamp((gap - AVOID_MIN_GAP) / AVOID_FADE, 0, 1);
      if (k < f) {
        f = k;
      }
    }
    return f;
  }

  // ---------------------------------------------------------------------
  // items

  function buildItems(rand, count, width, height) {
    var fog = Math.min(MAX_FOG, Math.round(count * 0.09));
    var rest = count - fog;
    var leaves = Math.round(rest * 0.45);
    var dust = rest - leaves;
    var items = [];
    var i;
    function base(kind) {
      return {
        kind: kind, x: rand() * width, y: rand() * height, vx: 0, vy: 0,
        k: 1, g: 0, phase: rand() * TAU, freq: 0.3 + rand() * 0.5,
        r: 1, ext: 1, alpha: 1, color: 0, angle: 0, spin: 0, rise: 0, fall: 0
      };
    }
    for (i = 0; i < fog; i++) {            // low banks near the ground
      var f = base('fog');
      f.y = height * (0.72 + 0.24 * rand());
      f.r = 90 + 80 * rand();
      f.k = 0.6 + 0.4 * rand();
      f.g = (rand() * 2 - 1) * CALM_DRIFT.fog;
      f.alpha = 0.7 + 0.3 * rand();
      f.ext = f.r;
      items.push(f);
    }
    for (i = 0; i < dust; i++) {           // ghost-dust motes that float up
      var d = base('dust');
      d.r = 1.5 + 2 * rand();
      d.k = 0.6 + 0.6 * rand();
      d.g = (rand() * 2 - 1) * CALM_DRIFT.dust;
      d.rise = 8 + 16 * rand();
      d.alpha = 0.55 + 0.4 * rand();
      d.color = Math.floor(rand() * DUST_COLORS.length);
      d.ext = d.r * 3;                     // halo radius; the stretched core can be wider (see extentOf)
      items.push(d);
    }
    for (i = 0; i < leaves; i++) {         // dry leaves that fall and tumble
      var l = base('leaf');
      l.r = 6 + 4 * rand();
      l.k = 0.7 + 0.6 * rand();
      l.g = (rand() * 2 - 1) * CALM_DRIFT.leaf;
      l.fall = 40 + 50 * rand();
      l.alpha = 0.5 + 0.3 * rand();
      l.color = Math.floor(rand() * LEAF_COLORS.length);
      l.spin = (rand() * 2 - 1) * 2;
      l.angle = rand() * TAU;
      l.ext = l.r;
      items.push(l);
    }
    return items;
  }

  // Half width of the biggest shape drawn for the item (px), at wind strength s.
  function extentOf(it, s) {
    if (it.kind === 'dust') {
      return Math.max(it.r * 3, it.r * (1 + 2.5 * s));
    }
    return it.ext;
  }

  // ---------------------------------------------------------------------
  // field

  function createWindField(options) {
    var cfg = options && typeof options === 'object' ? options : {};
    var width = posNum(cfg.width, DEFAULT_WIDTH);
    var height = posNum(cfg.height, DEFAULT_HEIGHT);
    var windMax = posNum(cfg.windMax, DEFAULT_WIND_MAX);
    var count = typeof cfg.count === 'number' && cfg.count === cfg.count ?
      clamp(Math.floor(cfg.count), 0, MAX_ITEMS) : DEFAULT_COUNT;   // Infinity -> budget, NaN -> default
    var avoid = normalizeAvoid(cfg.avoid);
    var items = buildItems(mulberry32(seedToInt(cfg.seed)), count, width, height);
    var nTarget = 0;   // wind asked for, in [-1, 1]
    var nCur = 0;      // wind the field currently shows, eased toward nTarget
    var gust = 0;      // 0..1, fades with GUST_TAU
    var time = 0;      // seconds of simulated time

    // Wind in game units. A change adds a short gust, bigger for bigger changes.
    function setWind(w) {
      var n = normalizeWind(w, windMax);
      gust = Math.max(gust, Math.min(1, Math.abs(n - nTarget) * 1.5));
      nTarget = n;
    }

    function setAvoid(list) {
      avoid = normalizeAvoid(list);
    }

    // dt in seconds. Not a positive finite number: ignored. Longer than MAX_DT: MAX_DT.
    function update(dt) {
      if (!isFiniteNumber(dt) || dt <= 0) {
        return;
      }
      var step = Math.min(dt, MAX_DT);
      nCur += (nTarget - nCur) * (1 - Math.exp(-step / WIND_EASE_TAU));
      gust *= Math.exp(-step / GUST_TAU);
      time += step;
      var s = Math.abs(nCur);
      var gustWave = 1 + 0.25 * s * Math.sin(TAU * time / 3.1 + 0.7) + 0.5 * gust;
      for (var i = 0; i < items.length; i++) {
        var it = items[i];
        var wob = Math.cos(TAU * it.freq * time + it.phase);
        it.vx = it.g + nCur * WIND_SPEED[it.kind] * it.k * gustWave;
        if (it.kind === 'leaf') {
          it.vy = it.fall + 18 * wob;
          it.angle = (it.angle + it.spin * (1 + 3 * s) * step) % TAU;
        } else if (it.kind === 'dust') {
          it.vy = -it.rise + 10 * wob;
        } else {
          it.vy = 3 * wob;
        }
        it.x = wrap(it.x + it.vx * step, width);
        it.y = wrap(it.y + it.vy * step, height);
      }
    }

    // layer: 'fog', 'dust', 'leaf' (or 'leaves'); anything else draws all, back to front.
    function draw(ctx, layer) {
      if (!ctx) {
        return;
      }
      var s = Math.abs(nCur);
      var kinds = layer === 'fog' ? ['fog'] : layer === 'dust' ? ['dust'] :
        (layer === 'leaf' || layer === 'leaves') ? ['leaf'] : ['fog', 'dust', 'leaf'];
      ctx.save();
      for (var q = 0; q < kinds.length; q++) {
        for (var i = 0; i < items.length; i++) {
          if (items[i].kind === kinds[q]) {
            drawItem(ctx, items[i], s);
          }
        }
      }
      ctx.restore();
    }

    function drawItem(ctx, it, s) {
      var fade = avoidFade(avoid, it.x, it.y, extentOf(it, s));
      if (fade <= 0) {
        return;
      }
      if (it.kind === 'fog') {
        // calm: thin and bluish. strong: a little denser and paler.
        var fa = (0.05 + 0.04 * s) * it.alpha * fade;
        var g = ctx.createRadialGradient(it.x, it.y, 0, it.x, it.y, it.r);
        g.addColorStop(0, 'rgba(207,216,255,1)');
        g.addColorStop(1, 'rgba(207,216,255,0)');
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = fa;
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(it.x, it.y, it.r, 0, TAU);
        ctx.fill();
      } else if (it.kind === 'dust') {
        // calm: round motes. strong: motes stretched into short streaks.
        var da = it.alpha * (0.7 + 0.3 * s) * fade;
        ctx.globalCompositeOperation = 'lighter';
        ctx.fillStyle = DUST_COLORS[it.color];
        ctx.globalAlpha = da * 0.18;
        ctx.beginPath();
        ctx.arc(it.x, it.y, it.r * 3, 0, TAU);
        ctx.fill();
        ctx.globalAlpha = da;
        ctx.beginPath();
        ctx.ellipse(it.x, it.y, it.r * (1 + 2.5 * s), it.r, 0, 0, TAU);
        ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
      } else {
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = it.alpha * fade;
        ctx.fillStyle = LEAF_COLORS[it.color];
        ctx.beginPath();
        ctx.ellipse(it.x, it.y, it.r, it.r * 0.5, it.angle, 0, TAU);
        ctx.fill();
      }
    }

    // Copies of the items, for tests and for the caller's own checks.
    function getState() {
      var s = Math.abs(nCur);
      return items.map(function (it) {
        return { kind: it.kind, x: it.x, y: it.y, vx: it.vx, vy: it.vy, r: it.r, ext: extentOf(it, s) };
      });
    }

    // Current (eased) and target wind, in game units.
    function getWind() {
      return { current: nCur * windMax, target: nTarget * windMax };
    }

    return {
      setWind: setWind,
      setAvoid: setAvoid,
      update: update,
      draw: draw,
      getState: getState,
      getWind: getWind,
      width: width,
      height: height,
      count: items.length
    };
  }

  return {
    createWindField: createWindField,
    flameLean: flameLean,
    swayAngle: swayAngle,
    normalizeWind: normalizeWind,
    MAX_ITEMS: MAX_ITEMS,
    DEFAULT_COUNT: DEFAULT_COUNT,
    MAX_FOG: MAX_FOG,
    FLAME_LEAN_MAX: FLAME_LEAN_MAX,
    SWAY_MAX: SWAY_MAX,
    CALM_DRIFT: CALM_DRIFT,
    WIND_SPEED: WIND_SPEED
  };
});
