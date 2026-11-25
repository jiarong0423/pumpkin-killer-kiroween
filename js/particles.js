/*
 * Pumpkin Killer - particle effects core.
 *
 * DOM-free and deterministic. Works in Node (module.exports) and in the
 * browser (global `Particles`). Drawing lives in js/particles_draw.js.
 *
 * Conventions
 *  - Canvas coordinates: x to the right, y DOWN. Gravity > 0 pulls down,
 *    gravity < 0 floats up.
 *  - Time is in seconds, distances in pixels.
 *  - `size` is a radius for circle / glow / ring, a length for streak,
 *    a half side for square and a font size in px for text.
 *  - Integration is closed form (exact for constant gravity plus linear
 *    drag), so update() gives the same result however dt is split.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.Particles = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var DEFAULT_MAX_PARTICLES = 1500;
  var TAU = Math.PI * 2;
  var MAX_ABS_COORD = 1e9;

  // layer = draw pass. BODY and TEXT use normal blending, GLOW is additive.
  var LAYERS = { BODY: 0, GLOW: 1, TEXT: 2 };
  var SHAPES = ['circle', 'glow', 'square', 'streak', 'ring', 'text', 'sprite'];

  var TEAM_PALETTE = {
    player: { hot: '#fff0b8', mid: '#ffa94d', dark: '#8f2d12' },
    agent: { hot: '#efe6ff', mid: '#a78bfa', dark: '#2f1a6b' }
  };

  // Poison palettes: every entry has green strictly above red and blue.
  var GREEN_BODY = ['#3fbf3f', '#4ade4a', '#2fa84f', '#58d65a'];
  var GREEN_END = ['#1f6b2a', '#2a8a3a', '#18552a'];
  var GREEN_BUBBLE = ['#9dff7a', '#7dff5a', '#b6ffa0'];

  var WISP_START = ['#7df9ff', '#b388ff', '#a5f3ff', '#c7a6ff'];
  var WISP_END = ['#2a4d8f', '#3a1c71'];

  // ---------------------------------------------------------------------
  // helpers

  function clamp(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
  }

  function isFiniteNumber(v) {
    return typeof v === 'number' && isFinite(v);
  }

  // Finite number clamped to [lo, hi], otherwise the default.
  function numOpt(v, def, lo, hi) {
    return isFiniteNumber(v) ? clamp(v, lo, hi) : def;
  }

  // Particle count for a base count and a scale: grows with sqrt(scale).
  function cnt(base, scale) {
    return Math.max(1, Math.round(base * Math.sqrt(scale)));
  }

  function isCoord(v) {
    return isFiniteNumber(v) && Math.abs(v) <= MAX_ABS_COORD;
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

  function normalizeOpts(opts) {
    var src = opts && typeof opts === 'object' ? opts : {};
    var o = Object.assign({}, src);
    o.dirX = isFiniteNumber(src.dirX) && src.dirX < 0 ? -1 : 1;
    o.scale = numOpt(src.scale, 1, 0.1, 4);
    o.team = src.team === 'agent' ? 'agent' : 'player';
    o.color = isHexColor(src.color) ? src.color : null;
    o.colorEnd = isHexColor(src.colorEnd) ? src.colorEnd : null;
    o.squash = numOpt(src.squash, 1, 0.25, 1);
    return o;
  }

  function isHexColor(v) {
    return typeof v === 'string' && /^#[0-9a-fA-F]{6}$/.test(v);
  }

  // ---------------------------------------------------------------------
  // presets: function (B, x, y, o). B is the builder created per system,
  // o the normalised options (dirX is -1 or 1, scale in [0.1, 4]).

  var PRESETS = {};

  // Burst at a barrel or hand. dirX = firing direction.
  PRESETS.muzzle_flash = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    var pal = TEAM_PALETTE[o.team];
    B.add({
      x: x, y: y, size: 44 * s, sizeEnd: 6 * s, life: 0.09,
      color: pal.hot, colorEnd: pal.mid, alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    B.add({
      x: x + d * 14 * s, y: y, size: 26 * s, sizeEnd: 2 * s, life: 0.07,
      color: '#ffffff', colorEnd: pal.hot, alpha: 1, shape: 'circle', layer: LAYERS.GLOW
    });
    var n = cnt(10, s);
    var base = d > 0 ? 0 : Math.PI;
    for (var i = 0; i < n; i++) {
      var ang = base + B.range(-0.38, 0.38);
      var sp = B.range(320, 780) * s;
      B.add({
        x: x + d * 8 * s, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp,
        size: B.range(14, 30) * s, sizeEnd: 2 * s, life: B.range(0.1, 0.22),
        color: pal.hot, colorEnd: pal.dark, alpha: 0.95,
        gravity: 260, drag: 3.5, shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  // Grey smoke that rises and spreads. dirX = drift direction.
  PRESETS.smoke_puff = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    var n = cnt(9, s);
    for (var i = 0; i < n; i++) {
      B.add({
        x: x + B.range(-6, 6) * s, y: y + B.range(-4, 4) * s,
        vx: d * B.range(10, 70) * s + B.range(-25, 25), vy: -B.range(25, 95) * s,
        size: B.range(9, 16) * s, sizeEnd: B.range(30, 46) * s, life: B.range(0.8, 1.5),
        color: '#a3a3b0', colorEnd: '#2d2d3a', alpha: B.range(0.4, 0.6),
        gravity: -25, drag: 1.6, shape: 'glow', layer: LAYERS.BODY
      });
    }
  };

  // ---- Sprite presets (Colab-made art, keyed from magenta). The picture is drawn by particles_draw.js; when the picture is not
  // loaded the particle is skipped, so each of these is an optional extra on top of the plain presets above.
  PRESETS.sprite_impact_flash = function (B, x, y, o) {
    var s = o.scale;
    B.add({ x: x, y: y, size: 54 * s, sizeEnd: 86 * s, life: 0.22, alpha: 1, sprite: 'fx_impact_flash', shape: 'sprite', angle: B.range(-0.4, 0.4), spin: B.range(-2, 2), layer: LAYERS.GLOW, fade: 0.5 });
  };
  PRESETS.sprite_ghostfire = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(2, s);
    for (var i = 0; i < n; i++) {
      B.add({ x: x + B.range(-8, 8) * s, y: y, vx: B.range(-12, 12), vy: -B.range(30, 70) * s, size: B.range(14, 22) * s, sizeEnd: B.range(5, 9) * s, life: B.range(0.5, 0.9), alpha: 0.9, sprite: 'fx_ghostfire', shape: 'sprite', gravity: -20, drag: 1, layer: LAYERS.GLOW });
    }
  };
  PRESETS.sprite_rune_circle = function (B, x, y, o) {
    var s = o.scale;
    B.add({ x: x, y: y, size: 20 * s, sizeEnd: 70 * s, life: 0.9, alpha: 0.6, sprite: 'fx_rune_circle', shape: 'sprite', spin: 1.4, layer: LAYERS.GLOW, fade: 0.4 });
  };
  PRESETS.sprite_stardust = function (B, x, y, o) {
    var s = o.scale;
    B.add({ x: x, y: y, size: 12 * s, sizeEnd: 44 * s, life: 0.6, alpha: 1, sprite: 'fx_stardust', shape: 'sprite', spin: B.range(-1.5, 1.5), layer: LAYERS.GLOW, fade: 0.5 });
  };
  PRESETS.sprite_mist = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(3, s);
    for (var i = 0; i < n; i++) {
      B.add({ x: x + B.range(-14, 14) * s, y: y + B.range(-6, 6) * s, vx: B.range(-18, 18), vy: -B.range(15, 45) * s, size: B.range(26, 40) * s, sizeEnd: B.range(60, 90) * s, life: B.range(1.2, 1.9), alpha: 0.55, sprite: 'fx_spirit_mist', shape: 'sprite', spin: B.range(-0.4, 0.4), gravity: -8, drag: 1.2, layer: LAYERS.BODY });
    }
  };
  PRESETS.sprite_poison = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(3, s);
    for (var i = 0; i < n; i++) {
      B.add({ x: x + B.range(-12, 12) * s, y: y, vx: B.range(-10, 10), vy: -B.range(40, 90) * s, size: B.range(9, 15) * s, sizeEnd: B.range(5, 9) * s, life: B.range(0.7, 1.1), alpha: 0.9, sprite: 'fx_poison_bubbles', shape: 'sprite', gravity: -30, drag: 1.2, layer: LAYERS.GLOW });
    }
  };
  // Animated white-mask FX sprites with live color tinting & directional flip/squash.
  PRESETS.sprite_slash_arc = function (B, x, y, o) {
    var s = o.scale, d = o.dirX;
    var c1 = o.color || '#ffffff';
    var c2 = o.colorEnd || (o.color || '#38bdf8');
    B.add({
      x: x, y: y, size: 34 * s, sizeEnd: 108 * s, life: 0.28, alpha: 1,
      color: c1, colorEnd: c2, sprite: 'fx_slash_arc', shape: 'sprite',
      angle: -0.95, spin: 10.5, scaleX: d, scaleY: 1, layer: LAYERS.GLOW, fade: 0.45
    });
    B.add({
      x: x, y: y, size: 24 * s, sizeEnd: 82 * s, life: 0.2, alpha: 0.95,
      color: '#ffffff', colorEnd: c1, sprite: 'fx_slash_arc', shape: 'sprite',
      angle: -1.15, spin: 12.0, scaleX: d, scaleY: 1, layer: LAYERS.GLOW, fade: 0.55
    });
  };
  PRESETS.sprite_arcane_seal = function (B, x, y, o) {
    var s = o.scale, sy = o.squash;
    var c1 = o.color || '#f5d0fe';
    var c2 = o.colorEnd || (o.color || '#a855f7');
    B.add({
      x: x, y: y, size: 36 * s, sizeEnd: 118 * s, life: 0.72, alpha: 0.88,
      color: c1, colorEnd: c2, sprite: 'fx_arcane_circle', shape: 'sprite',
      angle: 0, spin: 1.8, scaleX: 1, scaleY: sy, layer: LAYERS.GLOW, fade: 0.45
    });
    B.add({
      x: x, y: y, size: 24 * s, sizeEnd: 84 * s, life: 0.56, alpha: 0.82,
      color: '#ffffff', colorEnd: c1, sprite: 'fx_arcane_circle', shape: 'sprite',
      angle: 0.7, spin: -3.1, scaleX: 1, scaleY: sy, layer: LAYERS.GLOW, fade: 0.5
    });
  };
  PRESETS.sprite_star_ring = function (B, x, y, o) {
    var s = o.scale, d = o.dirX, sy = o.squash;
    var c1 = o.color || '#fef08a';
    var c2 = o.colorEnd || (o.color || '#f59e0b');
    B.add({
      x: x, y: y, size: 22 * s, sizeEnd: 122 * s, life: 0.52, alpha: 0.92,
      color: c1, colorEnd: c2, sprite: 'fx_star_ring', shape: 'sprite',
      angle: B.range(0, TAU), spin: 2.6 * d, scaleX: 1, scaleY: sy, layer: LAYERS.GLOW, fade: 0.5
    });
    B.add({
      x: x, y: y, size: 14 * s, sizeEnd: 86 * s, life: 0.36, alpha: 0.85,
      color: '#ffffff', colorEnd: c1, sprite: 'fx_star_ring', shape: 'sprite',
      angle: B.range(0, TAU), spin: -3.4 * d, scaleX: 1, scaleY: sy, layer: LAYERS.GLOW, fade: 0.6
    });
  };
  PRESETS.sprite_fire_tongue = function (B, x, y, o) {
    var s = o.scale;
    var c1 = o.color || '#ffb703';
    var c2 = o.colorEnd || (o.color || '#dc2626');
    B.add({
      x: x + B.range(-10, 10) * s, y: y + B.range(-4, 4) * s,
      vx: B.range(-14, 14), vy: -B.range(28, 65) * s,
      size: B.range(24, 34) * s, sizeEnd: B.range(10, 16) * s, life: B.range(0.55, 0.95), alpha: 0.95,
      color: c1, colorEnd: c2, sprite: 'fx_fire_tongue', shape: 'sprite',
      angle: B.range(-0.18, 0.18), spin: B.range(-0.6, 0.6), scaleX: B.sign(), scaleY: 1,
      gravity: -35, drag: 1.1, layer: LAYERS.GLOW, fade: 0.45
    });
    B.add({
      x: x + B.range(-6, 6) * s, y: y + 4 * s,
      vx: B.range(-8, 8), vy: -B.range(18, 45) * s,
      size: B.range(14, 20) * s, sizeEnd: B.range(4, 8) * s, life: B.range(0.32, 0.55), alpha: 0.9,
      color: '#fffbeb', colorEnd: c1, sprite: 'fx_fire_tongue', shape: 'sprite',
      angle: B.range(-0.12, 0.12), spin: B.range(-0.8, 0.8), scaleX: B.sign(), scaleY: 1,
      gravity: -25, drag: 1.2, layer: LAYERS.GLOW, fade: 0.5
    });
  };

  // The three orbiting ghost fires leave the body with the ultimate and race ahead along the throw (owner 2026-11-09). dirX = throw direction.
  PRESETS.ult_fires = function (B, x, y, o) {
    var s = o.scale, d = o.dirX || 1;
    for (var i = 0; i < 3; i++) {
      B.add({
        x: x + d * i * 16 * s, y: y + (i - 1) * 22 * s, vx: d * B.range(620, 900) * s, vy: -B.range(80, 220) * s,
        size: 46 * s, sizeEnd: 12 * s, life: B.range(0.7, 1.0), alpha: 1, sprite: 'fx_ghostfire', shape: 'sprite',
        gravity: 500, spin: B.range(-2, 2), layer: LAYERS.GLOW, fade: 0.5
      });
    }
  };
  // Green healing rain (owner 2026-11-09): glowing green drops fall onto the unit from above the head, with a few pale sparks rising. x,y = just above the head.
  PRESETS.heal_rain = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(26, s);
    for (var i = 0; i < n; i++) {
      B.add({
        x: x + B.range(-58, 58) * s, y: y - B.range(0, 140) * s,
        vx: B.range(-8, 8), vy: B.range(260, 420) * s,
        size: B.range(4, 8) * s, sizeEnd: B.range(2, 4) * s, life: B.range(0.55, 0.95),
        color: '#7dffa0', colorEnd: '#1fa84f', alpha: 0.95,
        gravity: 260, drag: 0.1, shape: 'circle', layer: LAYERS.GLOW
      });
    }
    for (var j = 0; j < cnt(6, s); j++) {
      B.add({
        x: x + B.range(-40, 40) * s, y: y + B.range(180, 260) * s,
        vx: B.range(-14, 14), vy: -B.range(30, 90) * s,
        size: B.range(3, 5) * s, sizeEnd: 1, life: B.range(0.7, 1.1),
        color: '#eaffd8', colorEnd: '#7dffa0', alpha: 0.9, shape: 'circle', layer: LAYERS.GLOW
      });
    }
  };

  // Cartoon red drops that spray to the side when a unit is hit (owner 2026-11-09). dirX = direction the hit travelled; drops fly forward and up, then fall.
  PRESETS.blood_spray = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    var n = cnt(9, s);
    for (var i = 0; i < n; i++) {
      B.add({
        x: x + B.range(-6, 6) * s, y: y + B.range(-8, 8) * s,
        vx: d * B.range(60, 240) * s + B.range(-30, 30), vy: -B.range(60, 260) * s,
        size: B.range(3, 7) * s, sizeEnd: B.range(1, 3) * s, life: B.range(0.45, 0.9),
        color: '#e0243b', colorEnd: '#7a0f1f', alpha: 1,
        gravity: 820, drag: 0.4, shape: 'circle', layer: LAYERS.BODY
      });
    }
  };


  // ---- weapon-effect presets written by Kiro task 42 (spec .kiro/specs/weapon-effects)
  var WAVE_NOTES = ['\u266a', '\u266b'];
  var ICE_SHARDS = ['#ffffff', '#dff4ff', '#9fd8ff'];
  // Shield skips off the ground or the fence: a gold ring and two glints running along the ground.
  // The design asks for a flat ellipse; the drawer has no squash field yet, so the ring is a circle for now.
  PRESETS.bounce_ring = function (B, x, y, o) {
    var s = o.scale;
    B.add({
      x: x, y: y, size: 6 * s, sizeEnd: 54 * s, life: 0.35,
      color: '#ffe9a3', colorEnd: '#b45309', alpha: 0.9, lineWidth: 3, shape: 'ring', layer: LAYERS.GLOW
    });
    for (var side = -1; side <= 1; side += 2) {
      B.add({
        x: x, y: y, vx: side * B.range(180, 260) * s, vy: 0,
        size: B.range(16, 26) * s, sizeEnd: 2 * s, life: B.range(0.15, 0.25),
        color: '#fff3d6', colorEnd: '#b45309', alpha: 0.9, drag: 4, shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  // Ice shards when the javelin's frost curse lands: a white flash and square shards that fall.
  PRESETS.frost_shatter = function (B, x, y, o) {
    var s = o.scale;
    B.add({
      x: x, y: y, size: 40 * s, sizeEnd: 6 * s, life: 0.12,
      color: '#ffffff', colorEnd: '#9fd8ff', alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    var n = cnt(8, s);
    for (var i = 0; i < n; i++) {
      var ang = B.range(0, TAU);
      var sp = B.range(120, 320) * s;
      B.add({
        x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 80 * s,
        size: B.range(4, 8) * s, sizeEnd: 1 * s, life: B.range(0.4, 0.7),
        color: B.pick(ICE_SHARDS), colorEnd: '#3b6fe0', alpha: 1, gravity: 600, drag: 0.8,
        spin: B.range(-10, 10), shape: 'square', layer: LAYERS.GLOW
      });
    }
  };

  // Sound wave hits a unit: three widening rings and a few notes. Scale it by the damage share (22 at the centre down to 8 at the edge).
  // Rings share one start time, so they start at different radii instead of 80 ms apart (the system has no start delay).
  PRESETS.impact_wave = function (B, x, y, o) {
    var s = o.scale;
    var startR = [10, 6, 2];
    var endR = [110, 100, 90];
    var life = [0.5, 0.6, 0.7];
    var alpha = [0.9, 0.7, 0.5];
    var i;
    for (i = 0; i < 3; i++) {
      B.add({
        x: x, y: y, size: startR[i] * s, sizeEnd: endR[i] * s, life: life[i],
        color: '#f4ecff', colorEnd: '#9b7bff', alpha: alpha[i], lineWidth: 3.5 - 0.5 * i,
        shape: 'ring', layer: LAYERS.GLOW
      });
    }
    B.add({
      x: x, y: y, size: 50 * s, sizeEnd: 8 * s, life: 0.14,
      color: '#ffffff', colorEnd: '#e8d8ff', alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    var n = cnt(4, s);
    for (i = 0; i < n; i++) {
      var ang = B.range(0, TAU);
      var sp = B.range(60, 140) * s;
      B.add({
        x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 40,
        size: 16 * s, sizeEnd: 10 * s, life: B.range(0.7, 1.0), color: '#e8d8ff', colorEnd: '#9b7bff',
        alpha: 0.9, fade: 0.4, drag: 1.5, text: B.pick(WAVE_NOTES), shape: 'text', layer: LAYERS.TEXT
      });
    }
  };

  // One scythe slash landing on a unit. Option `index` (0, 1, 2) picks the slash; odd ones leave the other way round.
  // Sparks are soul-green. The crescent picture (reaper_slash_1..3) is drawn by the game, not here.
  PRESETS.scythe_slash_fx = function (B, x, y, o) {
    var s = o.scale;
    var idx = isFiniteNumber(o.index) ? Math.abs(Math.floor(o.index)) % 3 : 0;
    var d = o.dirX * (idx % 2 === 0 ? 1 : -1);
    B.add({
      x: x, y: y, size: 34 * s, sizeEnd: 6 * s, life: 0.09,
      color: '#ffffff', colorEnd: '#d6ffe6', alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    var n = cnt(8, s);
    var base = d > 0 ? Math.PI : 0;
    var i;
    for (i = 0; i < n; i++) {
      var ang = base + B.range(-1.1, 1.1);
      var sp = B.range(220, 560) * s;
      B.add({
        x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 80 * s,
        size: B.range(10, 22) * s, sizeEnd: 2 * s, life: B.range(0.15, 0.35),
        color: '#d6ffe6', colorEnd: '#3ddc97', alpha: 1, gravity: 700, drag: 2, shape: 'streak', layer: LAYERS.GLOW
      });
    }
    for (i = 0; i < 2; i++) {
      B.add({
        x: x + B.range(-10, 10) * s, y: y + B.range(-6, 6) * s, vx: B.range(-12, 12), vy: -B.range(30, 70) * s,
        size: B.range(6, 11) * s, sizeEnd: 1 * s, life: B.range(0.4, 0.8),
        color: '#3ddc97', colorEnd: '#0f5a3c', alpha: 0.8, gravity: -40, drag: 0.9, shape: 'glow', layer: LAYERS.GLOW
      });
    }
  };

  // Hunchback's bell in flight (call every step): bronze dust, and now and then a thin ring (about every 0.25 s at 60 calls per second).
  PRESETS.weapon_trail_bell = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 12 * s + B.range(-6, 6) * s, y: y + B.range(-6, 6) * s, vx: -d * B.range(10, 50), vy: B.range(-20, 20),
      size: B.range(10, 16) * s, sizeEnd: 2 * s, life: B.range(0.3, 0.5),
      color: '#e6b450', colorEnd: '#6b4a1a', alpha: 0.8, gravity: 80, drag: 1.5, shape: 'glow', layer: LAYERS.GLOW
    });
    if (B.rand() < 1 / 15) {
      B.add({
        x: x, y: y, size: 14 * s, sizeEnd: 40 * s, life: 0.3,
        color: '#ffe9a3', colorEnd: '#b45309', alpha: 0.8, lineWidth: 2, shape: 'ring', layer: LAYERS.GLOW
      });
    }
  };

  // Reaper's skull in flight (call every step): soul-green glow that drifts up, and a ghost-fire sprite about every 3rd call.
  // The sprite is skipped by the drawer while the picture is not loaded.
  PRESETS.weapon_trail_skull = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 10 * s, y: y + B.range(-6, 6) * s, vx: -d * B.range(5, 30), vy: -20,
      size: B.range(10, 16) * s, sizeEnd: 2 * s, life: B.range(0.3, 0.5),
      color: '#d6ffe6', colorEnd: '#3ddc97', alpha: 0.85, drag: 1.2, shape: 'glow', layer: LAYERS.GLOW
    });
    if (B.rand() < 1 / 3) {
      B.add({
        x: x - d * B.range(4, 20) * s, y: y + B.range(-6, 6) * s, vx: -d * B.range(5, 25), vy: -B.range(20, 50),
        size: B.range(12, 18) * s, sizeEnd: 5 * s, life: B.range(0.4, 0.7), alpha: 0.8,
        sprite: 'fx_ghostfire', shape: 'sprite', gravity: -20, drag: 1, layer: LAYERS.GLOW
      });
    }
  };

  // Bride's sound wave in flight. Call about every 6th physics step: one ring, one soft glow, sometimes a note glyph.
  // The ring centre jitters +-3 px so the wave reads as vibrating.
  PRESETS.weapon_trail_wave = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x + B.range(-3, 3), y: y + B.range(-3, 3), size: 10 * s, sizeEnd: 56 * s, life: 0.45,
      color: '#e8d8ff', colorEnd: '#9b7bff', alpha: 0.8, lineWidth: 3, shape: 'ring', layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, size: 30 * s, sizeEnd: 8 * s, life: 0.3,
      color: '#e8d8ff', colorEnd: '#9b7bff', alpha: 0.35, shape: 'glow', layer: LAYERS.GLOW
    });
    if (B.rand() < 0.4) {
      B.add({
        x: x - d * B.range(0, 16), y: y + B.range(-10, 10) * s, vx: -d * B.range(10, 40), vy: -B.range(20, 50),
        size: 18 * s, sizeEnd: 12 * s, life: 0.9, color: '#e8d8ff', colorEnd: '#9b7bff', alpha: 0.9, fade: 0.4,
        text: B.pick(WAVE_NOTES), shape: 'text', layer: LAYERS.TEXT
      });
    }
  };

  // Projectile hits the ground or a unit: flash, ring, embers, debris, dust.
  // dirX = direction the projectile was travelling (debris leans that way).
  PRESETS.impact_burst = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    var pal = TEAM_PALETTE[o.team];
    var i;
    B.add({
      x: x, y: y, size: 70 * s, sizeEnd: 10 * s, life: 0.14,
      color: pal.hot, colorEnd: pal.mid, alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, size: 8 * s, sizeEnd: 80 * s, life: 0.35,
      color: pal.hot, colorEnd: pal.mid, alpha: 0.8, lineWidth: 4 * s,
      shape: 'ring', layer: LAYERS.GLOW
    });
    var embers = cnt(20, s);
    for (i = 0; i < embers; i++) {
      var ang = B.range(0, TAU);
      var sp = B.range(120, 480) * s;
      B.add({
        x: x, y: y, vx: Math.cos(ang) * sp + d * 50 * s, vy: Math.sin(ang) * sp - 60 * s,
        size: B.range(3, 7) * s, sizeEnd: 0.5 * s, life: B.range(0.35, 0.85),
        color: pal.hot, colorEnd: pal.dark, alpha: 1,
        gravity: 700, drag: 1.2, shape: 'circle', layer: LAYERS.GLOW
      });
    }
    var debris = cnt(7, s);
    for (i = 0; i < debris; i++) {
      var da = B.range(0, TAU);
      var ds = B.range(90, 300) * s;
      B.add({
        x: x, y: y, vx: Math.cos(da) * ds + d * 40 * s, vy: -B.range(80, 260) * s,
        size: B.range(3, 6) * s, sizeEnd: 2 * s, life: B.range(0.5, 1.0),
        color: '#6b4a2f', colorEnd: '#2a1c12', alpha: 1,
        gravity: 900, drag: 0.6, spin: B.range(-12, 12), shape: 'square', layer: LAYERS.BODY
      });
    }
    var dust = cnt(5, s);
    for (i = 0; i < dust; i++) {
      B.add({
        x: x + B.range(-8, 8) * s, y: y,
        vx: B.range(-60, 60) * s, vy: -B.range(10, 60) * s,
        size: B.range(12, 18) * s, sizeEnd: B.range(34, 44) * s, life: B.range(0.6, 1.1),
        color: '#9b8670', colorEnd: '#4a3f35', alpha: 0.4,
        gravity: -10, drag: 2, shape: 'glow', layer: LAYERS.BODY
      });
    }
  };

  // Sparks thrown back off a unit. dirX = direction the projectile was
  // travelling, sparks leave the opposite way.
  PRESETS.hit_sparks = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    var pal = TEAM_PALETTE[o.team];
    B.add({
      x: x, y: y, size: 24 * s, sizeEnd: 4 * s, life: 0.08,
      color: '#ffffff', colorEnd: pal.hot, alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    var n = cnt(16, s);
    var base = d > 0 ? Math.PI : 0;
    for (var i = 0; i < n; i++) {
      var ang = base + B.range(-1.2, 1.2);
      var sp = B.range(200, 620) * s;
      B.add({
        x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 100 * s,
        size: B.range(10, 24) * s, sizeEnd: 2 * s, life: B.range(0.15, 0.4),
        color: pal.hot, colorEnd: pal.mid, alpha: 1,
        gravity: 900, drag: 2, shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  // Green lingering mist (poison shell). Options:
  //   duration         seconds the cloud lasts (clamped 0.1..60). Default is
  //                    rounds * secondsPerRound.
  //   rounds           default 3, secondsPerRound default 2.
  //   radius           horizontal radius in px, default 90 * scale.
  // Particle lifetimes are 70%..100% of the duration so the cloud thins out
  // instead of vanishing in one frame.
  PRESETS.poison_cloud = function (B, x, y, o) {
    var s = o.scale;
    var rounds = numOpt(o.rounds, 3, 1, 20);
    var perRound = numOpt(o.secondsPerRound, 2, 0.1, 20);
    var dur = numOpt(o.duration, clamp(rounds * perRound, 0.1, 60), 0.1, 60);
    var radius = numOpt(o.radius, 90 * s, 4, 1000);
    var i;
    var n = cnt(34, s);
    for (i = 0; i < n; i++) {
      var r = radius * Math.sqrt(B.rand());
      var th = B.range(0, TAU);
      var size = B.range(26, 46) * s;
      B.add({
        x: x + Math.cos(th) * r, y: y + Math.sin(th) * r * 0.55,
        vx: B.range(-10, 10), vy: -B.range(4, 16),
        size: size, sizeEnd: size * B.range(1.1, 1.5), life: dur * B.range(0.7, 1),
        color: B.pick(GREEN_BODY), colorEnd: B.pick(GREEN_END), alpha: B.range(0.22, 0.38),
        gravity: -2, drag: 0.8, shape: 'glow', layer: LAYERS.BODY
      });
    }
    var m = cnt(12, s);
    for (i = 0; i < m; i++) {
      var br = radius * Math.sqrt(B.rand());
      var bt = B.range(0, TAU);
      B.add({
        x: x + Math.cos(bt) * br, y: y + Math.sin(bt) * br * 0.55,
        vx: B.range(-8, 8), vy: -B.range(10, 30),
        size: B.range(2, 4.5) * s, sizeEnd: 0.5 * s, life: dur * B.range(0.7, 1),
        color: B.pick(GREEN_BUBBLE), colorEnd: B.pick(GREEN_BODY), alpha: 0.8,
        gravity: -6, drag: 0.5, shape: 'circle', layer: LAYERS.GLOW
      });
    }
  };

  // Drops falling off a poisoned unit. Call every ~0.1 s while poisoned.
  PRESETS.poison_drip = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(4, s);
    for (var i = 0; i < n; i++) {
      B.add({
        x: x + B.range(-10, 10) * s, y: y + B.range(-4, 6) * s,
        vx: B.range(-14, 14), vy: B.range(0, 50) * s,
        size: B.range(2.5, 4.5) * s, sizeEnd: B.range(1, 2) * s, life: B.range(0.5, 0.9),
        color: '#5dff4a', colorEnd: '#1f8f2e', alpha: 0.95,
        gravity: 620, drag: 0.2, shape: 'circle', layer: LAYERS.BODY
      });
    }
    B.add({
      x: x + B.range(-8, 8) * s, y: y,
      vx: 0, vy: -B.range(15, 35), size: 6 * s, sizeEnd: 1 * s, life: B.range(0.8, 1.2),
      color: '#9dff7a', colorEnd: '#3fbf3f', alpha: 0.5,
      gravity: -20, drag: 0.5, shape: 'glow', layer: LAYERS.GLOW
    });
  };

  // Many streaks falling over an area. (x, y) is the centre of the landing
  // zone, opts.width its width (px, clamped 1..5000, default 240 * scale).
  // Streaks start above (opts.height, default 380 * scale) at x positions
  // inside [x - width / 2, x + width / 2], fall vertically and reach y when
  // their life ends. No sideways drift, so the area stays exactly that wide.
  PRESETS.dart_rain = function (B, x, y, o) {
    var s = o.scale;
    var width = numOpt(o.width, 240 * s, 1, 5000);
    var height = numOpt(o.height, 380 * s, 20, 3000);
    var lo = x - width / 2;
    var hi = x + width / 2;
    var n = clamp(Math.round(width / 8), 12, 120);
    for (var i = 0; i < n; i++) {
      var px = clamp(lo + B.rand() * width, lo, hi);
      var startY = y - B.range(0.6, 1.4) * height;
      var speed = B.range(950, 1350);
      var len = B.range(22, 40) * s;
      B.add({
        x: px, y: startY, vx: 0, vy: speed,
        size: len, sizeEnd: len, life: Math.max(0.05, (y - startY) / speed),
        color: '#e6f2ff', colorEnd: '#8fa6bd', alpha: 0.9, fade: 0.08,
        gravity: 0, drag: 0, shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  // Sparks bouncing off the sky shield. dirX = direction the projectile was
  // travelling, sparks leave the opposite way and up.
  PRESETS.shield_ricochet_sparks = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x, y: y, size: 30 * s, sizeEnd: 6 * s, life: 0.1,
      color: '#ffffff', colorEnd: '#4deeea', alpha: 1, shape: 'glow', layer: LAYERS.GLOW
    });
    var n = cnt(14, s);
    var base = d > 0 ? Math.PI : 0;
    for (var i = 0; i < n; i++) {
      var ang = base + B.range(-0.9, 0.9);
      var sp = B.range(260, 700) * s;
      B.add({
        x: x, y: y, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 140 * s,
        size: B.range(12, 26) * s, sizeEnd: 2 * s, life: B.range(0.2, 0.45),
        color: '#f2ffff', colorEnd: '#4deeea', alpha: 1,
        gravity: 520, drag: 2.4, shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  // The sky shield appearing. (x, y) is the bar centre, opts.width the bar
  // width (px, clamped 1..5000, default 160 * scale). Three expanding rings,
  // a flash along the bar and rising motes.
  PRESETS.shield_materialize_ripple = function (B, x, y, o) {
    var s = o.scale;
    var width = numOpt(o.width, 160 * s, 1, 5000);
    var ringEnd = [0.35, 0.55, 0.8];
    var ringLife = [0.45, 0.6, 0.8];
    var ringAlpha = [0.9, 0.7, 0.5];
    var ringLine = [3, 2.5, 2];
    var i;
    for (i = 0; i < 3; i++) {
      B.add({
        x: x, y: y, size: 6 * s, sizeEnd: ringEnd[i] * width, life: ringLife[i],
        color: '#d8ffff', colorEnd: '#4deeea', alpha: ringAlpha[i], lineWidth: ringLine[i] * s,
        shape: 'ring', layer: LAYERS.GLOW
      });
    }
    // Horizontal flash: a streak whose head is the right end of the bar.
    B.add({
      x: x + width / 2, y: y, size: width, sizeEnd: width * 1.1, life: 0.3,
      color: '#ffffff', colorEnd: '#4deeea', alpha: 0.9, lineWidth: 4 * s,
      angle: 0, shape: 'streak', layer: LAYERS.GLOW
    });
    var m = cnt(12, s);
    for (i = 0; i < m; i++) {
      B.add({
        x: x + B.range(-0.5, 0.5) * width, y: y + B.range(-4, 4) * s,
        vx: B.range(-12, 12), vy: -B.range(15, 70) * s,
        size: B.range(2, 4) * s, sizeEnd: 0.5 * s, life: B.range(0.5, 1.0),
        color: '#ffffff', colorEnd: '#4deeea', alpha: 1,
        gravity: -30, drag: 1, shape: 'circle', layer: LAYERS.GLOW
      });
    }
  };

  // Ground landing: two rings plus dust kicked sideways.
  PRESETS.landing_ring_dust = function (B, x, y, o) {
    var s = o.scale;
    var i;
    B.add({
      x: x, y: y, size: 6 * s, sizeEnd: 72 * s, life: 0.5,
      color: '#ffe3b0', colorEnd: '#c98b4a', alpha: 0.85, lineWidth: 3 * s,
      shape: 'ring', layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, size: 3 * s, sizeEnd: 44 * s, life: 0.35,
      color: '#fff3d6', colorEnd: '#c98b4a', alpha: 0.6, lineWidth: 2 * s,
      shape: 'ring', layer: LAYERS.GLOW
    });
    var n = cnt(12, s);
    for (i = 0; i < n; i++) {
      B.add({
        x: x + B.range(-8, 8) * s, y: y,
        vx: B.sign() * B.range(40, 220) * s, vy: -B.range(10, 70) * s,
        size: B.range(5, 11) * s, sizeEnd: B.range(14, 26) * s, life: B.range(0.5, 1.0),
        color: '#b59a7a', colorEnd: '#5f5042', alpha: 0.5,
        gravity: 40, drag: 3, shape: 'glow', layer: LAYERS.BODY
      });
    }
  };

  // Cyan and violet ghost fire rising from a knocked-out unit.
  PRESETS.ko_wisps = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(12, s);
    for (var i = 0; i < n; i++) {
      B.add({
        x: x + B.range(-14, 14) * s, y: y + B.range(-6, 6) * s,
        vx: B.range(-28, 28) * s, vy: -B.range(50, 150) * s,
        size: B.range(6, 13) * s, sizeEnd: 1 * s, life: B.range(0.9, 1.8),
        color: B.pick(WISP_START), colorEnd: B.pick(WISP_END), alpha: 0.85,
        gravity: -90, drag: 0.9, shape: 'glow', layer: LAYERS.GLOW
      });
    }
    B.add({
      x: x, y: y - 6 * s, vx: 0, vy: -40 * s, size: 22 * s, sizeEnd: 8 * s, life: 1.4,
      color: '#e0fbff', colorEnd: '#7a5cff', alpha: 0.6,
      gravity: -30, drag: 0.8, shape: 'glow', layer: LAYERS.GLOW
    });
  };

  // Floating text. Options: text (string) or amount (number), color (#rrggbb).
  // Default colour comes from the team palette.
  PRESETS.damage_number = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    var text;
    if (o.text !== undefined && o.text !== null) {
      text = String(o.text).slice(0, 16);
    } else if (isFiniteNumber(o.amount)) {
      text = String(Math.round(o.amount));
    } else {
      text = '!';
    }
    var color = isHexColor(o.color) ? o.color.toLowerCase() : TEAM_PALETTE[o.team].hot;
    B.add({
      x: x, y: y, vx: d * B.range(10, 35) + B.range(-8, 8), vy: -B.range(130, 170) * s,
      size: 30 * s, sizeEnd: 22 * s, life: 1.1,
      color: color, colorEnd: color, alpha: 1, fade: 0.35,
      gravity: 0, drag: 2.6, text: text, shape: 'text', layer: LAYERS.TEXT
    });
  };

  // ---- weapon and face effects (owner request 2026-11-09: effects on the weapons, small face motions)
  // The trail presets are meant to be called every frame while a weapon flies (1-3 particles per call).
  // dirX = direction of travel; the particles are left behind the weapon.

  // Spear: thin pale streak and a few cold glints.
  PRESETS.weapon_trail_spear = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 18 * s, y: y, vx: -d * B.range(30, 90) * s, vy: B.range(-20, 20),
      size: B.range(26, 44) * s, sizeEnd: 3 * s, life: B.range(0.12, 0.2),
      color: '#f4fbff', colorEnd: '#6aa6ff', alpha: 0.85, drag: 3, shape: 'streak', layer: LAYERS.GLOW
    });
    if (B.rand() < 0.25) {
      B.add({
        x: x - d * B.range(6, 40) * s, y: y + B.range(-8, 8) * s, vx: -d * B.range(10, 50), vy: B.range(-40, 10),
        size: B.range(5, 9) * s, sizeEnd: 1 * s, life: B.range(0.2, 0.4),
        color: '#ffffff', colorEnd: '#7dd3fc', alpha: 1, gravity: 120, shape: 'glow', layer: LAYERS.GLOW
      });
    }
  };

  // Dart: tiny silver glints and an orange tail-fin spark.
  PRESETS.weapon_trail_dart = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 14 * s, y: y, vx: -d * B.range(20, 60), vy: B.range(-15, 15),
      size: B.range(8, 14) * s, sizeEnd: 1 * s, life: B.range(0.15, 0.28),
      color: '#ffb066', colorEnd: '#7a2d12', alpha: 0.9, drag: 2, shape: 'glow', layer: LAYERS.GLOW
    });
    if (B.rand() < 0.2) {
      B.add({
        x: x + B.range(-10, 10) * s, y: y + B.range(-6, 6) * s, vx: B.range(-20, 20), vy: B.range(-30, 10),
        size: B.range(4, 8) * s, sizeEnd: 0.5 * s, life: B.range(0.18, 0.34),
        color: '#ffffff', colorEnd: '#c0c8d8', alpha: 1, shape: 'square', spin: B.range(-9, 9), layer: LAYERS.GLOW
      });
    }
  };

  // Cannonball: fire embers and dark smoke behind the shot.
  PRESETS.weapon_trail_cannon = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 20 * s, y: y + B.range(-6, 6) * s, vx: -d * B.range(20, 80) * s, vy: B.range(-30, 10),
      size: B.range(12, 20) * s, sizeEnd: 36 * s, life: B.range(0.5, 0.9),
      color: '#6b6b78', colorEnd: '#1f1f2a', alpha: 0.5, gravity: -20, drag: 1.4, shape: 'glow', layer: LAYERS.BODY
    });
    B.add({
      x: x - d * 10 * s, y: y + B.range(-8, 8) * s, vx: -d * B.range(40, 140) * s, vy: B.range(-60, 30),
      size: B.range(8, 15) * s, sizeEnd: 1 * s, life: B.range(0.2, 0.4),
      color: '#ffd06a', colorEnd: '#c2410c', alpha: 1, gravity: 260, drag: 2, shape: 'glow', layer: LAYERS.GLOW
    });
  };

  // Thrown shield: cyan ring sparkles and spinning shards.
  PRESETS.weapon_trail_shield = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 10 * s, y: y, vx: -d * B.range(10, 50), vy: B.range(-20, 20),
      size: B.range(20, 34) * s, sizeEnd: 4 * s, life: B.range(0.16, 0.26),
      color: '#a5f3ff', colorEnd: '#2563eb', alpha: 0.6, shape: 'ring', lineWidth: 2.5, layer: LAYERS.GLOW
    });
    if (B.rand() < 0.25) {   // few shards: the trail must stay clean (owner feedback)
      B.add({
        x: x + B.range(-14, 14) * s, y: y + B.range(-14, 14) * s, vx: -d * B.range(10, 60), vy: B.range(-50, 20),
        size: B.range(4, 7) * s, sizeEnd: 1 * s, life: B.range(0.25, 0.45),
        color: '#e0fbff', colorEnd: '#38bdf8', alpha: 0.9, gravity: 160, shape: 'square', spin: B.range(-12, 12), layer: LAYERS.GLOW
      });
    }
  };

  // Aura around a held weapon while charging a throw. Call a few times per second; scale grows with power.
  PRESETS.weapon_charge_aura = function (B, x, y, o) {
    var s = o.scale;
    var pal = TEAM_PALETTE[o.team];
    var n = cnt(2, s);
    for (var i = 0; i < n; i++) {
      var ang = B.range(0, TAU);
      var r = B.range(10, 30) * s;
      B.add({
        x: x + Math.cos(ang) * r, y: y + Math.sin(ang) * r, vx: -Math.cos(ang) * 40 * s, vy: -Math.sin(ang) * 40 * s - 20,
        size: B.range(6, 12) * s, sizeEnd: 1 * s, life: B.range(0.25, 0.45),
        color: pal.hot, colorEnd: pal.mid, alpha: 0.9, shape: 'glow', layer: LAYERS.GLOW
      });
    }
  };

  // Small face motion: flicker of the jack-o'-lantern glow (call every ~0.15 s per pumpkin character).
  // Owner 2026-11-23: pumpkin roles get the Kenney CC0 halo (kn_halo, tinted) on both eyes, kept small; the old soft flicker stays, smaller.
  PRESETS.face_glow_pumpkin = function (B, x, y, o) {
    var s = o.scale;
    B.add({
      x: x + B.range(-3, 3) * s, y: y + B.range(-2, 2) * s, vx: B.range(-6, 6), vy: -B.range(8, 24),
      size: B.range(8, 13) * s, sizeEnd: 3 * s, life: B.range(0.25, 0.5),
      color: '#ffb347', colorEnd: '#c2410c', alpha: B.range(0.3, 0.55), shape: 'glow', layer: LAYERS.GLOW
    });
    // One halo per eye. The page passes the measured eye spots (o.eyes, world pixels); without them the halos sit 9 px either side of the point.
    var eyes = (o.eyes && o.eyes.length === 2) ? o.eyes : [{ x: x - 9 * s, y: y }, { x: x + 9 * s, y: y }];
    eyes.forEach(function (eye) {
      B.add({
        x: eye.x, y: eye.y + B.range(-1, 1) * s, vx: 0, vy: -B.range(2, 8),
        size: B.range(6, 9) * s, sizeEnd: 4 * s, life: B.range(0.3, 0.5),
        color: '#ffd27a', colorEnd: '#ff8a2b', alpha: B.range(0.5, 0.85), sprite: 'kn_halo', shape: 'sprite', layer: LAYERS.GLOW, fade: 0.5
      });
    });
  };

  // Small face motion: cold blue flame rising from the skeleton's eye sockets.
  PRESETS.face_glow_skeleton = function (B, x, y, o) {
    var s = o.scale;
    var eyes = (o.eyes && o.eyes.length === 2) ? o.eyes : [{ x: x - 7 * s, y: y }, { x: x + 7 * s, y: y }];
    eyes.forEach(function (eye) {
      B.add({
        x: eye.x + B.range(-1.5, 1.5) * s, y: eye.y + B.range(-1, 1) * s, vx: B.range(-4, 4), vy: -B.range(16, 38),
        size: B.range(6, 10) * s, sizeEnd: 1.5 * s, life: B.range(0.28, 0.52),
        color: '#7df9ff', colorEnd: '#1d4ed8', alpha: B.range(0.55, 0.9), shape: 'glow', layer: LAYERS.GLOW
      });
    });
  };

  // ---- enchantment look (owner: Halloween magic, like a wizard-school spell): gold and violet stardust, rune halo
  var ENCHANT_COLORS = ['#ffe9a3', '#d9b8ff', '#9ff3ff', '#ffd27a'];

  // Per-frame stardust left by an enchanted weapon: twinkling stars drifting down.
  PRESETS.weapon_enchant_stardust = function (B, x, y, o) {
    var s = o.scale;
    var n = cnt(2, s);
    for (var i = 0; i < n; i++) {
      var c = B.pick(ENCHANT_COLORS);
      B.add({
        x: x + B.range(-14, 14) * s, y: y + B.range(-14, 14) * s,
        vx: B.range(-30, 30), vy: B.range(-20, 50),
        size: B.range(5, 11) * s, sizeEnd: 0.5 * s, life: B.range(0.35, 0.8),
        color: c, colorEnd: '#6d28d9', alpha: 1, gravity: 90, shape: 'square', spin: B.range(-10, 10),
        layer: LAYERS.GLOW
      });
    }
  };

  // Rune halo: a ring that opens around the weapon plus sparks orbiting outwards. Use on charge and on spell release.
  PRESETS.weapon_rune_halo = function (B, x, y, o) {
    var s = o.scale;
    B.add({
      x: x, y: y, size: 18 * s, sizeEnd: 70 * s, life: 0.45,
      color: '#d9b8ff', colorEnd: '#4c1d95', alpha: 0.9, shape: 'ring', lineWidth: 3, layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, size: 10 * s, sizeEnd: 46 * s, life: 0.35,
      color: '#ffe9a3', colorEnd: '#b45309', alpha: 0.8, shape: 'ring', lineWidth: 2, layer: LAYERS.GLOW
    });
    var n = cnt(8, s);
    for (var i = 0; i < n; i++) {
      var ang = (i / n) * TAU + B.range(-0.2, 0.2);
      B.add({
        x: x + Math.cos(ang) * 30 * s, y: y + Math.sin(ang) * 30 * s,
        vx: Math.cos(ang) * B.range(40, 110) * s, vy: Math.sin(ang) * B.range(40, 110) * s - 20,
        size: B.range(6, 12) * s, sizeEnd: 1 * s, life: B.range(0.4, 0.8),
        color: B.pick(ENCHANT_COLORS), colorEnd: '#312e81', alpha: 1, drag: 1.5,
        shape: 'glow', layer: LAYERS.GLOW
      });
    }
  };

  // Code-drawn ultimate effects. These avoid optional sprite files so the
  // timelines remain readable while the Colab art is still pending.
  PRESETS.ult_pip_socket = function (B, x, y, o) {
    var s = o.scale;
    B.add({
      x: x, y: y, size: 8 * s, sizeEnd: 24 * s, life: 0.35,
      color: '#fff3c4', colorEnd: '#d97706', alpha: 0.95, lineWidth: 2 * s,
      shape: 'ring', layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, size: 15 * s, sizeEnd: 30 * s, life: 0.5,
      color: '#ffb347', colorEnd: '#5b210f', alpha: 0.55, lineWidth: 1.5 * s,
      shape: 'ring', layer: LAYERS.GLOW
    });
  };

  // The particle drawer's ring primitive is circular. Three thin expanding
  // rings give the intended ground-shock silhouette without a bitmap.
  PRESETS.shock_ring = function (B, x, y, o) {
    var s = o.scale;
    var radii = [14, 24, 36];
    for (var i = 0; i < radii.length; i++) {
      B.add({
        x: x, y: y, size: radii[i] * s, sizeEnd: (radii[i] + 84) * s, life: 0.35,
        color: '#fff1bf', colorEnd: '#c2410c', alpha: 0.8 - i * 0.14, lineWidth: 2.5 * s,
        shape: 'ring', layer: LAYERS.GLOW
      });
    }
  };

  PRESETS.ghost_spear_fall = function (B, x, y, o) {
    var s = o.scale;
    for (var i = 0; i < 3; i++) {
      B.add({
        x: x + (i - 1) * 22 * s, y: y - 150 - i * 42, vx: B.range(-12, 12), vy: B.range(520, 650) * s,
        size: B.range(52, 68) * s, sizeEnd: 24 * s, life: B.range(0.32, 0.42),
        color: '#ecfeff', colorEnd: '#60a5fa', alpha: 0.55, gravity: 480, drag: 0.35,
        shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  PRESETS.chain_hop_trail = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x - d * 14 * s, y: y, vx: -d * B.range(80, 145) * s, vy: B.range(-24, 24),
      size: 56 * s, sizeEnd: 16 * s, life: 0.28,
      color: '#fff0a8', colorEnd: '#b45309', alpha: 0.9, lineWidth: 4 * s, drag: 3,
      shape: 'streak', layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, size: 12 * s, sizeEnd: 36 * s, life: 0.32,
      color: '#ffe9a3', colorEnd: '#92400e', alpha: 0.55,
      shape: 'glow', layer: LAYERS.GLOW
    });
  };

  PRESETS.bell_toll_rings = function (B, x, y, o) {
    var s = o.scale;
    for (var i = 0; i < 3; i++) {
      B.add({
        x: x, y: y, size: (10 + i * 15) * s, sizeEnd: (86 + i * 16) * s, life: 0.5 + i * 0.08,
        color: '#ffe0a3', colorEnd: '#8a4b16', alpha: 0.85 - i * 0.15, lineWidth: (3 - i * 0.5) * s,
        shape: 'ring', layer: LAYERS.GLOW
      });
    }
  };

  PRESETS.soundwave_rings = function (B, x, y, o) {
    var s = o.scale;
    for (var i = 0; i < 3; i++) {
      B.add({
        x: x, y: y, size: (8 + i * 14) * s, sizeEnd: (74 + i * 20) * s, life: 0.45 + i * 0.08,
        color: '#fef3c7', colorEnd: '#a16207', alpha: 0.8 - i * 0.14, lineWidth: 2.5 * s,
        shape: 'ring', layer: LAYERS.GLOW
      });
    }
  };

  // Bride ultimate impact: a compact flock fans out from each enemy. The
  // sprite is optional and is skipped by the drawer until its image is ready.
  PRESETS.bat_swarm = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    for (var i = 0; i < 6; i++) {
      var angle = -0.9 + i * 0.36;
      var speed = B.range(90, 180) * s;
      B.add({
        x: x + B.range(-14, 14) * s, y: y + B.range(-12, 12) * s,
        vx: d * Math.cos(angle) * speed, vy: Math.sin(angle) * speed - B.range(20, 65) * s,
        size: B.range(18, 28) * s, sizeEnd: B.range(10, 16) * s, life: B.range(0.35, 0.6),
        alpha: 0.9, sprite: 'fx_bat_swarm', shape: 'sprite', gravity: 90, drag: 1.4,
        layer: LAYERS.GLOW
      });
    }
  };

  PRESETS.axe_spin_trail = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x, y: y, vx: -d * B.range(40, 80) * s, vy: B.range(-20, 20),
      size: 46 * s, sizeEnd: 20 * s, life: 0.26,
      color: '#f8fafc', colorEnd: '#475569', alpha: 0.9, angle: 0, spin: 4 * Math.PI,
      lineWidth: 6 * s, drag: 2.4, shape: 'streak', layer: LAYERS.GLOW
    });
    B.add({
      x: x, y: y, vx: -d * B.range(25, 55) * s, vy: B.range(-18, 18),
      size: 32 * s, sizeEnd: 14 * s, life: 0.26,
      color: '#cbd5e1', colorEnd: '#334155', alpha: 0.8, angle: Math.PI / 2, spin: 4 * Math.PI,
      lineWidth: 4 * s, drag: 2.4, shape: 'streak', layer: LAYERS.GLOW
    });
  };

  PRESETS.boomerang_return = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    B.add({
      x: x, y: y, vx: d * B.range(140, 220) * s, vy: B.range(-30, 30),
      size: 18 * s, sizeEnd: 4 * s, life: 0.32,
      color: '#fff7ed', colorEnd: '#c2410c', alpha: 0.95, drag: 3, shape: 'streak', layer: LAYERS.GLOW
    });
    for (var i = 0; i < 3; i++) {
      B.add({
        x: x - d * B.range(6, 28) * s, y: y + B.range(-14, 14) * s,
        vx: -d * B.range(20, 70) * s, vy: B.range(-45, 25) * s,
        size: B.range(3, 7) * s, sizeEnd: 1, life: B.range(0.22, 0.42),
        color: '#fef3c7', colorEnd: '#b45309', alpha: 0.9, gravity: 120, drag: 1.8,
        shape: 'glow', layer: LAYERS.GLOW
      });
    }
  };

  PRESETS.spark_electric = function (B, x, y, o) {
    var s = o.scale;
    B.add({
      x: x, y: y, size: 24 * s, sizeEnd: 5 * s, life: 0.12,
      color: '#ffffff', colorEnd: '#facc15', alpha: 1,
      shape: 'glow', layer: LAYERS.GLOW
    });
    for (var i = 0; i < 6; i++) {
      var angle = i * TAU / 6 + B.range(-0.28, 0.28);
      var speed = B.range(120, 250) * s;
      B.add({
        x: x, y: y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
        size: B.range(16, 30) * s, sizeEnd: 3 * s, life: B.range(0.12, 0.24),
        color: '#fffde7', colorEnd: '#f59e0b', alpha: 1, gravity: 120, drag: 4,
        shape: 'streak', layer: LAYERS.GLOW
      });
    }
  };

  PRESETS.cross_spin_trail = function (B, x, y, o) {
    var s = o.scale;
    var d = o.dirX;
    // The thrown cross is a picture now (assets/fx/sprites/fx_cross_silver.png). The two rotating streaks that used to read as
    // a code-drawn cross are gone: left on the path they were a second, cross-shaped afterimage. A per-step glow was tried and smeared into a haze, so only the smoke puffs remain.
    for (var i = 0; i < 4; i++) {
      B.add({
        x: x - d * B.range(8, 28) * s, y: y + B.range(-12, 12) * s,
        vx: -d * B.range(25, 70) * s, vy: -B.range(10, 55) * s,
        size: B.range(10, 18) * s, sizeEnd: B.range(24, 36) * s, life: B.range(0.35, 0.6),
        color: '#3f271e', colorEnd: '#09090b', alpha: 0.25, gravity: -15, drag: 1.5,
        shape: 'glow', layer: LAYERS.BODY
      });
    }
  };

  // Dedicated normal-attack trails. Each keeps its initial particles inside
  // the 1920 x 1080 playfield, even when the caller supplies an edge point.
  function trailOrigin(x, y) {
    return { x: clamp(x, 120, 1800), y: clamp(y, 120, 960) };
  }

  PRESETS.trail_frost = function (B, x, y, o) {
    var p = trailOrigin(x, y), s = o.scale, d = o.dirX;
    B.add({ x: p.x - d * 18 * s, y: p.y, vx: -d * B.range(35, 85) * s, vy: B.range(-18, 18), size: B.range(28, 42) * s, sizeEnd: 3 * s, life: B.range(0.12, 0.2), color: '#ecfeff', colorEnd: '#60a5fa', alpha: 0.9, drag: 3, shape: 'streak', layer: LAYERS.GLOW });
    B.add({ x: p.x - d * B.range(8, 28) * s, y: p.y + B.range(-10, 10) * s, vx: -d * B.range(12, 44) * s, vy: B.range(-45, -10) * s, size: B.range(3, 7) * s, sizeEnd: 1, life: B.range(0.2, 0.38), color: '#ffffff', colorEnd: '#9fd8ff', alpha: 0.95, gravity: 220, spin: B.range(-8, 8), shape: 'square', layer: LAYERS.GLOW });
  };

  PRESETS.trail_toxic = function (B, x, y, o) {
    var p = trailOrigin(x, y), s = o.scale, d = o.dirX;
    B.add({ x: p.x - d * 16 * s, y: p.y + B.range(-8, 8) * s, vx: -d * B.range(15, 55) * s, vy: -B.range(10, 45) * s, size: B.range(10, 16) * s, sizeEnd: B.range(20, 32) * s, life: B.range(0.35, 0.6), color: '#58d65a', colorEnd: '#18552a', alpha: 0.48, gravity: -8, drag: 1.4, shape: 'glow', layer: LAYERS.BODY });
    B.add({ x: p.x - d * B.range(4, 20) * s, y: p.y + B.range(-8, 8) * s, vx: -d * B.range(10, 35), vy: -B.range(25, 70), size: B.range(2, 5) * s, sizeEnd: 1, life: B.range(0.18, 0.35), color: '#ffb347', colorEnd: '#c2410c', alpha: 0.9, gravity: 80, shape: 'circle', layer: LAYERS.GLOW });
  };

  PRESETS.trail_shadow = function (B, x, y, o) {
    var p = trailOrigin(x, y), s = o.scale, d = o.dirX;
    B.add({ x: p.x - d * 14 * s, y: p.y + B.range(-8, 8) * s, vx: -d * B.range(20, 65) * s, vy: -B.range(12, 45), size: B.range(13, 20) * s, sizeEnd: B.range(28, 40) * s, life: B.range(0.35, 0.65), color: '#3f271e', colorEnd: '#09090b', alpha: 0.48, gravity: -12, drag: 1.6, shape: 'glow', layer: LAYERS.BODY });
    B.add({ x: p.x - d * B.range(6, 26) * s, y: p.y + B.range(-9, 9) * s, vx: -d * B.range(12, 50), vy: B.range(-35, 10), size: B.range(2, 5) * s, sizeEnd: 1, life: B.range(0.2, 0.4), color: '#f6d365', colorEnd: '#8a5a18', alpha: 0.95, gravity: 80, shape: 'circle', layer: LAYERS.GLOW });
  };

  PRESETS.trail_iron_sparks = function (B, x, y, o) {
    var p = trailOrigin(x, y), s = o.scale, d = o.dirX;
    B.add({ x: p.x - d * 15 * s, y: p.y, vx: -d * B.range(35, 92) * s, vy: B.range(-24, 24), size: B.range(18, 34) * s, sizeEnd: 3 * s, life: B.range(0.12, 0.22), color: '#f8fafc', colorEnd: '#64748b', alpha: 0.9, drag: 3.2, shape: 'streak', layer: LAYERS.GLOW });
    B.add({ x: p.x - d * B.range(8, 24) * s, y: p.y + B.range(-8, 8) * s, vx: -d * B.range(14, 55), vy: -B.range(25, 80), size: B.range(3, 6) * s, sizeEnd: 1, life: B.range(0.16, 0.3), color: '#e2e8f0', colorEnd: '#475569', alpha: 0.95, gravity: 500, spin: B.range(-8, 8), shape: 'square', layer: LAYERS.GLOW });
  };

  PRESETS.trail_soulfire = function (B, x, y, o) {
    var p = trailOrigin(x, y), s = o.scale, d = o.dirX;
    B.add({ x: p.x - d * 18 * s, y: p.y + B.range(-7, 7) * s, vx: -d * B.range(12, 55) * s, vy: -B.range(30, 82) * s, size: B.range(14, 22) * s, sizeEnd: B.range(4, 8) * s, life: B.range(0.28, 0.5), color: '#e9d5ff', colorEnd: '#7e22ce', alpha: 0.9, gravity: -25, drag: 1.4, shape: 'glow', layer: LAYERS.GLOW });
    B.add({ x: p.x - d * B.range(5, 24) * s, y: p.y + B.range(-10, 10) * s, vx: -d * B.range(10, 42), vy: -B.range(25, 65), size: B.range(3, 6) * s, sizeEnd: 1, life: B.range(0.18, 0.32), color: '#f5d0fe', colorEnd: '#581c87', alpha: 0.9, gravity: -20, shape: 'circle', layer: LAYERS.GLOW });
  };

  PRESETS.trail_holy_lightning = function (B, x, y, o) {
    var p = trailOrigin(x, y), s = o.scale, d = o.dirX;
    B.add({ x: p.x - d * 16 * s, y: p.y, vx: -d * B.range(34, 88) * s, vy: B.range(-25, 25), size: B.range(24, 38) * s, sizeEnd: 3 * s, life: B.range(0.1, 0.18), color: '#fffde7', colorEnd: '#f59e0b', alpha: 1, drag: 3.5, shape: 'streak', layer: LAYERS.GLOW });
    B.add({ x: p.x - d * B.range(5, 24) * s, y: p.y + B.range(-12, 12) * s, vx: -d * B.range(10, 45), vy: B.range(-38, 18), size: B.range(3, 6) * s, sizeEnd: 1, life: B.range(0.16, 0.3), color: '#facc15', colorEnd: '#c2410c', alpha: 0.95, gravity: 160, shape: 'circle', layer: LAYERS.GLOW });
  };

  var PRESET_NAMES = Object.keys(PRESETS);

  // ---------------------------------------------------------------------
  // integration

  // Exact step for constant gravity g and linear drag k (dv/dt = g - k v).
  function integrate(p, dt) {
    var k = p.drag;
    var g = p.gravity;
    if (k > 1e-4) {
      var e = Math.exp(-k * dt);
      var f = -Math.expm1(-k * dt) / k;
      var vt = g / k;
      p.x += p.vx * f;
      p.y += vt * dt + (p.vy - vt) * f;
      p.vx *= e;
      p.vy = vt + (p.vy - vt) * e;
    } else {
      p.x += p.vx * dt;
      p.y += p.vy * dt + 0.5 * g * dt * dt;
      p.vy += g * dt;
    }
    p.angle += p.spin * dt;
  }

  // ---------------------------------------------------------------------
  // system

  function createSystem(options) {
    var cfg = options || {};
    var maxParticles = isFiniteNumber(cfg.maxParticles) && cfg.maxParticles >= 1
      ? Math.floor(cfg.maxParticles)
      : DEFAULT_MAX_PARTICLES;
    var rand = mulberry32(seedToInt(cfg.seed));
    var particles = []; // oldest first, mutated in place, never replaced
    var nextId = 1;
    var currentPreset = '';
    var added = 0;

    var builder = {
      rand: rand,
      range: function (a, b) { return a + rand() * (b - a); },
      sign: function () { return rand() < 0.5 ? -1 : 1; },
      pick: function (list) { return list[Math.floor(rand() * list.length)]; },
      add: function (s) {
        var life = s.life;
        var size = s.size === undefined ? 1 : s.size;
        var color = s.color === undefined ? '#ffffff' : s.color;
        particles.push({
          id: nextId++,
          preset: currentPreset,
          x: s.x,
          y: s.y,
          vx: s.vx === undefined ? 0 : s.vx,
          vy: s.vy === undefined ? 0 : s.vy,
          life: life,
          maxLife: life,
          size: size,
          sizeEnd: s.sizeEnd === undefined ? size : s.sizeEnd,
          color: color,
          colorEnd: s.colorEnd === undefined ? color : s.colorEnd,
          alpha: s.alpha === undefined ? 1 : s.alpha,
          gravity: s.gravity === undefined ? 0 : s.gravity,
          drag: s.drag === undefined ? 0 : s.drag,
          shape: s.shape === undefined ? 'circle' : s.shape,
          spin: s.spin === undefined ? 0 : s.spin,
          angle: s.angle === undefined ? 0 : s.angle,
          layer: s.layer === undefined ? LAYERS.BODY : s.layer,
          lineWidth: s.lineWidth === undefined ? 0 : s.lineWidth,
          fade: s.fade === undefined ? 0.35 : s.fade,
          text: s.text === undefined ? '' : s.text,
          sprite: s.sprite === undefined ? '' : s.sprite,
          scaleX: isFiniteNumber(s.scaleX) && s.scaleX !== 0 ? s.scaleX : 1,
          scaleY: isFiniteNumber(s.scaleY) && s.scaleY !== 0 ? s.scaleY : 1
        });
        added++;
      }
    };

    // Returns the number of particles from this call that are alive in the
    // pool afterwards. Throws on an unknown preset (programmer error).
    // Non-finite or absurd coordinates are ignored and return 0, so a bad
    // value can never put NaN into the pool.
    function emit(name, x, y, opts) {
      var preset = Object.prototype.hasOwnProperty.call(PRESETS, name) ? PRESETS[name] : null;
      if (!preset) {
        throw new Error('Unknown particle preset: ' + String(name));
      }
      if (!isCoord(x) || !isCoord(y)) {
        return 0;
      }
      currentPreset = name;
      added = 0;
      preset(builder, x, y, normalizeOpts(opts));
      var excess = particles.length - maxParticles;
      if (excess > 0) {
        particles.splice(0, excess); // drop the oldest
      }
      return Math.min(added, maxParticles);
    }

    // Advance by dt seconds. dt that is not a positive finite number is
    // ignored. Does not use the RNG, so the way dt is split cannot change
    // which particles exist.
    function update(dt) {
      if (!isFiniteNumber(dt) || dt <= 0) {
        return;
      }
      var w = 0;
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.life -= dt;
        if (p.life <= 0) {
          continue;
        }
        integrate(p, dt);
        particles[w++] = p;
      }
      particles.length = w;
    }

    // Empties the pool. The RNG state and id counter keep going.
    function clear() {
      particles.length = 0;
    }

    return {
      emit: emit,
      update: update,
      particles: particles,
      clear: clear,
      maxParticles: maxParticles
    };
  }

  return {
    createSystem: createSystem,
    mulberry32: mulberry32,
    PRESET_NAMES: PRESET_NAMES,
    LAYERS: LAYERS,
    SHAPES: SHAPES,
    DEFAULT_MAX_PARTICLES: DEFAULT_MAX_PARTICLES
  };
});
