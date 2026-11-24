/*
 * Pumpkin Killer - layered scene background (parallax, wind sway, fallback).
 *
 * DOM-free and deterministic. Works in Node (module.exports) and in the
 * browser (global `SceneLayers`). Design: docs/visual_quality_plan.md (part B),
 * wiring: docs/scene_layers_integration.md, spec: .kiro/specs/scene-layers/.
 *
 * What it does
 *  - Reads a manifest (a list of image layers with depth, parallax factor,
 *    wind sway, blend mode) and a map of already loaded images.
 *  - update(dt, wind, cameraX) computes every layer's offset. draw(ctx) paints
 *    the layers back to front.
 *  - When the manifest is empty or invalid, or a required layer image is not
 *    loaded, draw() paints the single baked background (images.bg) instead,
 *    and a flat colour when even that is missing.
 *
 * Conventions
 *  - Canvas coordinates: x to the right, y DOWN. Positive wind blows to +x.
 *  - cameraX is a small horizontal camera offset in px. The play plane (units,
 *    fence) is parallax 1 and never moves on screen; a layer with parallax p
 *    is shifted by cameraX * (1 - p). p < 1 is behind the play plane, p > 1 is
 *    in front of it. cameraX is clamped to +-maxCamera.
 *  - Randomness: none at run time. Per-layer phases come from a seeded
 *    generator (mulberry32) once, in create(). update() and draw() never draw
 *    random numbers and never read a clock, so the same seed and the same
 *    calls give the same pictures.
 *  - draw() uses only: save, restore, drawImage, fillRect, transform,
 *    globalAlpha, globalCompositeOperation, fillStyle, imageSmoothingEnabled,
 *    imageSmoothingQuality.
 *  - images is read at draw time (not copied), so the caller can load images
 *    later or replace images.bg when the scene changes.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.SceneLayers = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var TAU = Math.PI * 2;

  // ---- budget and tuning numbers (a test checks each of these)
  var DEFAULT_WIDTH = 1920;
  var DEFAULT_HEIGHT = 1080;
  var DEFAULT_WIND_MAX = 4;
  var DEFAULT_MAX_CAMERA = 24;     // px; cameraX is clamped to this
  var MAX_CAMERA_LIMIT = 60;       // px; a manifest may not ask for more
  var MAX_LAYERS = 8;              // one scene, all planes
  var MAX_BLEND_FULL = 2;          // layers with a non-default blend that cover the canvas
  var MAX_BOUND = 40;              // px; largest horizontal shift (camera + sway) of one layer
  var MAX_DT = 0.1;                // seconds; a longer frame counts as 0.1 s
  var WIND_EASE_TAU = 0.6;         // seconds; the sway eases toward a new wind
  var MAX_PARALLAX = 1.5;
  var MAX_SWAY = 32;               // px
  var DEFAULT_SWAY_HZ = 0.35;
  var MAX_DRIFT = 400;             // px/s at full wind
  var MAX_CALM_DRIFT = 30;         // px/s with no wind
  var MAX_PULSE = 0.5;

  var BLENDS = ['source-over', 'lighter', 'screen', 'multiply'];
  var PLANES = ['back', 'front'];
  var NAME_RE = /^[a-z0-9_]+$/;
  var FILE_RE = /^assets\/layers\/([a-z0-9_]+)\/(\d\d)_([a-z0-9_]+)\.png$/;

  // ---------------------------------------------------------------------
  // helpers

  function clamp(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
  }

  function isNum(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function posNum(v, def) {
    return isNum(v) && v > 0 ? v : def;
  }

  function isObj(v) {
    return v !== null && typeof v === 'object' && !Array.isArray(v);
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
    return isNum(seed) ? Math.floor(seed) | 0 : 1;
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
    return clamp(w / posNum(windMax, DEFAULT_WIND_MAX), -1, 1);
  }

  // Size of a loaded image, or null when it cannot be drawn yet. Accepts
  // HTMLImageElement (complete, naturalWidth), canvas and ImageBitmap (width).
  function imageSize(im) {
    if (!im || typeof im !== 'object' || im.complete === false) {
      return null;
    }
    var w = im.naturalWidth || im.width || 0;
    var h = im.naturalHeight || im.height || 0;
    return w > 0 && h > 0 ? { w: w, h: h } : null;
  }

  // ---------------------------------------------------------------------
  // manifest

  // How far (px) any pixel of a layer can be displaced horizontally, for
  // |cameraX| <= maxCamera and any wind. Tiled layers wrap instead, so their
  // bound is the canvas width. A pivoted layer is sheared so that its farthest
  // row from the pivot moves by the sway value and no row moves more, so the
  // bound is the same with or without a pivot.
  function offsetBound(layer, width, height, maxCamera) {
    if (layer.tileX) {
      return width;
    }
    return maxCamera * Math.abs(1 - layer.parallax) + (layer.sway || 0);
  }

  // Returns a list of violation strings. An empty list means the manifest is
  // valid. opts: { width, height } of the canvas (defaults 1920 x 1080).
  function validateManifest(manifest, opts) {
    var v = [];
    var o = isObj(opts) ? opts : {};
    var W = posNum(o.width, DEFAULT_WIDTH);
    var H = posNum(o.height, DEFAULT_HEIGHT);
    if (!isObj(manifest)) {
      return ['manifest must be an object'];
    }
    if (manifest.version !== 1) {
      v.push('version must be 1');
    }
    if (typeof manifest.scene !== 'string' || !NAME_RE.test(manifest.scene)) {
      v.push('scene must match [a-z0-9_]+');
    }
    if (manifest.width !== undefined && manifest.width !== W) {
      v.push('width ' + manifest.width + ' does not match the canvas width ' + W);
    }
    if (manifest.height !== undefined && manifest.height !== H) {
      v.push('height ' + manifest.height + ' does not match the canvas height ' + H);
    }
    if (manifest.maxCamera !== undefined &&
        !(isNum(manifest.maxCamera) && manifest.maxCamera >= 0 && manifest.maxCamera <= MAX_CAMERA_LIMIT)) {
      v.push('maxCamera must be 0..' + MAX_CAMERA_LIMIT);
    }
    if (!Array.isArray(manifest.layers)) {
      v.push('layers must be an array');
      return v;
    }
    if (manifest.layers.length > MAX_LAYERS) {
      v.push('at most ' + MAX_LAYERS + ' layers, got ' + manifest.layers.length);
    }
    var names = {};
    var fullBlend = 0;
    var cam = isNum(manifest.maxCamera) ? manifest.maxCamera : DEFAULT_MAX_CAMERA;
    for (var i = 0; i < manifest.layers.length; i++) {
      var L = manifest.layers[i];
      var tag = 'layer ' + i + ': ';
      if (!isObj(L)) {
        v.push(tag + 'must be an object');
        continue;
      }
      if (typeof L.name !== 'string' || !NAME_RE.test(L.name)) {
        v.push(tag + 'name must match [a-z0-9_]+');
      } else if (names[L.name]) {
        v.push(tag + 'duplicate name ' + L.name);
      } else {
        names[L.name] = true;
      }
      var m = typeof L.file === 'string' ? FILE_RE.exec(L.file) : null;
      if (!m) {
        v.push(tag + 'file must look like assets/layers/<scene>/<nn>_<name>.png');
      } else {
        if (m[1] !== manifest.scene) {
          v.push(tag + 'file folder ' + m[1] + ' is not the scene ' + manifest.scene);
        }
        if (m[3] !== L.name) {
          v.push(tag + 'file name part ' + m[3] + ' is not the layer name ' + L.name);
        }
      }
      if (!(isNum(L.depth) && L.depth >= 0 && L.depth <= 100)) {
        v.push(tag + 'depth must be 0..100');
      }
      if (L.plane !== undefined && PLANES.indexOf(L.plane) < 0) {
        v.push(tag + 'plane must be back or front');
      }
      if (!(isNum(L.parallax) && L.parallax >= 0 && L.parallax <= MAX_PARALLAX)) {
        v.push(tag + 'parallax must be 0..' + MAX_PARALLAX);
      }
      if (L.sway !== undefined && !(isNum(L.sway) && L.sway >= 0 && L.sway <= MAX_SWAY)) {
        v.push(tag + 'sway must be 0..' + MAX_SWAY + ' px');
      }
      if (L.swayHz !== undefined && !(isNum(L.swayHz) && L.swayHz >= 0.05 && L.swayHz <= 2)) {
        v.push(tag + 'swayHz must be 0.05..2');
      }
      if (L.pivotY !== undefined && !(isNum(L.pivotY) && L.pivotY >= 0 && L.pivotY <= H)) {
        v.push(tag + 'pivotY must be 0..' + H);
      }
      if (L.tileX !== undefined && typeof L.tileX !== 'boolean') {
        v.push(tag + 'tileX must be true or false');
      }
      if (L.drift !== undefined && !(isNum(L.drift) && Math.abs(L.drift) <= MAX_DRIFT)) {
        v.push(tag + 'drift must be within +-' + MAX_DRIFT + ' px/s');
      }
      if (L.calmDrift !== undefined && !(isNum(L.calmDrift) && Math.abs(L.calmDrift) <= MAX_CALM_DRIFT)) {
        v.push(tag + 'calmDrift must be within +-' + MAX_CALM_DRIFT + ' px/s');
      }
      if ((L.drift || L.calmDrift) && L.tileX !== true) {
        v.push(tag + 'drift needs tileX true (the image must tile horizontally)');
      }
      if (L.blend !== undefined && BLENDS.indexOf(L.blend) < 0) {
        v.push(tag + 'blend must be one of ' + BLENDS.join(', '));
      }
      var alpha = L.alpha === undefined ? 1 : L.alpha;
      if (!(isNum(alpha) && alpha >= 0 && alpha <= 1)) {
        v.push(tag + 'alpha must be 0..1');
      }
      if (L.pulse !== undefined && !(isNum(L.pulse) && L.pulse >= 0 && L.pulse <= MAX_PULSE)) {
        v.push(tag + 'pulse must be 0..' + MAX_PULSE);
      }
      if (L.pulseHz !== undefined && !(isNum(L.pulseHz) && L.pulseHz >= 0.05 && L.pulseHz <= 3)) {
        v.push(tag + 'pulseHz must be 0.05..3');
      }
      if (L.required !== undefined && typeof L.required !== 'boolean') {
        v.push(tag + 'required must be true or false');
      }
      var hasRect = L.rect !== undefined;
      if (hasRect) {
        var r = L.rect;
        if (!(Array.isArray(r) && r.length === 4 && isNum(r[0]) && isNum(r[1]) && isNum(r[2]) && isNum(r[3]) &&
            r[2] > 0 && r[3] > 0)) {
          v.push(tag + 'rect must be [x, y, w, h] with w > 0 and h > 0');
        }
      }
      // Blend modes other than source-over cost fill rate: a layer that covers
      // the whole canvas must be faint, and there may be only a few.
      if (L.blend && L.blend !== 'source-over' && !hasRect) {
        fullBlend++;
        if (alpha > 0.5) {
          v.push(tag + 'a full-canvas ' + L.blend + ' layer needs alpha <= 0.5 (give it a rect instead)');
        }
      }
      // Full-width layers are drawn a little wider than the canvas so a shifted edge never shows.
      // Past MAX_BOUND px that stretch would show, so the layer must be authored wider instead.
      if (isNum(L.parallax) && !L.tileX && cam * Math.abs(1 - L.parallax) + (isNum(L.sway) ? L.sway : 0) > MAX_BOUND) {
        v.push(tag + 'camera shift plus sway is over ' + MAX_BOUND + ' px (lower sway or move parallax toward 1)');
      }
    }
    if (fullBlend > MAX_BLEND_FULL) {
      v.push('at most ' + MAX_BLEND_FULL + ' full-canvas blend layers, got ' + fullBlend);
    }
    return v;
  }

  // Fills defaults and per-layer seeded phases. Input must be valid.
  function normalizeLayers(manifest, rand, W, H, maxCamera) {
    var out = [];
    for (var i = 0; i < manifest.layers.length; i++) {
      var s = manifest.layers[i];
      var L = {
        index: i,
        name: s.name,
        file: s.file,
        depth: s.depth,
        plane: s.plane || 'back',
        parallax: s.parallax,
        sway: s.sway || 0,
        swayHz: (s.swayHz || DEFAULT_SWAY_HZ) * (0.85 + 0.3 * rand()),
        pivotY: s.pivotY === undefined ? null : s.pivotY,
        tileX: s.tileX === true,
        drift: s.drift || 0,
        calmDrift: s.calmDrift || 0,
        blend: s.blend || 'source-over',
        alpha: s.alpha === undefined ? 1 : s.alpha,
        pulse: s.pulse || 0,
        pulseHz: s.pulseHz || 0.4,
        rect: s.rect ? s.rect.slice(0, 4) : null,
        required: s.required !== false,
        phase: rand() * TAU,
        phase2: rand() * TAU,
        driftPos: 0
      };
      // Shear set-up. The pivot row stays put. Content below the pivot (a hanging
      // bell) swings its bottom toward the wind; content above it (a tree) leans
      // its top toward the wind. `far` is the distance from the pivot to the
      // farthest drawn row, so no row moves more than the sway value.
      var rowTop = L.rect ? L.rect[1] : 0;
      var rowBot = L.rect ? L.rect[1] + L.rect[3] : H;
      L.far = 1;
      L.side = -1;
      if (L.pivotY !== null) {
        L.far = Math.max(L.pivotY - rowTop, rowBot - L.pivotY, 1);
        L.side = L.pivotY < (rowTop + rowBot) / 2 ? 1 : -1;   // 1: hanging, -1: standing
      }
      L.bound = offsetBound(L, W, H, maxCamera);
      // Overscan so a shifted layer never shows its edge. Only layers that span the
      // whole canvas width need it; tiled layers wrap, small rect layers float.
      var spansWidth = !L.rect || (L.rect[0] <= 0 && L.rect[0] + L.rect[2] >= W);
      L.margin = (L.tileX || !spansWidth) ? 0 : Math.ceil(L.bound);
      out.push(L);
    }
    // Stable sort by depth: far (small) first. Ties keep manifest order.
    out.sort(function (a, b) { return a.depth - b.depth || a.index - b.index; });
    return out;
  }

  // ---------------------------------------------------------------------
  // scene

  function create(options) {
    var cfg = isObj(options) ? options : {};
    var W = posNum(cfg.width, DEFAULT_WIDTH);
    var H = posNum(cfg.height, DEFAULT_HEIGHT);
    var windMax = posNum(cfg.windMax, DEFAULT_WIND_MAX);
    var images = isObj(cfg.images) ? cfg.images : {};
    var fallbackKey = typeof cfg.fallbackKey === 'string' ? cfg.fallbackKey : 'bg';
    var fallbackColor = typeof cfg.fallbackColor === 'string' ? cfg.fallbackColor : '#0a0514';
    var violations = isObj(cfg.manifest) ? validateManifest(cfg.manifest, { width: W, height: H }) :
      ['manifest missing'];
    var maxCamera = DEFAULT_MAX_CAMERA;
    if (isObj(cfg.manifest) && isNum(cfg.manifest.maxCamera) && violations.length === 0) {
      maxCamera = cfg.manifest.maxCamera;
    }
    var seed = seedToInt(cfg.seed);
    var layers = violations.length === 0 ? normalizeLayers(cfg.manifest, mulberry32(seed), W, H, maxCamera) : [];
    var states = layers.map(function () {
      return { dx: 0, shear: 0, reach: 0, alpha: 1 };
    });
    var time = 0;
    var nTarget = 0;   // wind asked for, in [-1, 1]
    var nCur = 0;      // wind the layers currently show, eased toward nTarget
    var camera = 0;

    function reset() {
      time = 0;
      nTarget = 0;
      nCur = 0;
      camera = 0;
      for (var i = 0; i < layers.length; i++) {
        layers[i].driftPos = 0;
      }
      compute();
    }

    // 'layers': every required layer image is loaded. 'image': the single baked
    // background is drawn. 'fill': a flat colour (nothing loaded yet).
    function getMode() {
      if (layers.length > 0) {
        var ok = true;
        for (var i = 0; i < layers.length; i++) {
          if (layers[i].required && !imageSize(images[layers[i].name])) {
            ok = false;
            break;
          }
        }
        if (ok) {
          return 'layers';
        }
      }
      return imageSize(images[fallbackKey]) ? 'image' : 'fill';
    }

    function compute() {
      var s = Math.abs(nCur);
      var cam = camera;
      for (var i = 0; i < layers.length; i++) {
        var L = layers[i];
        var st = states[i];
        var camOff = cam * (1 - L.parallax);
        var swayX = 0;
        if (L.sway > 0) {
          // |mean| <= 0.5 s and |swing| <= 0.1 + 0.4 s, so |swayX| <= sway.
          swayX = L.sway * (0.5 * nCur + (0.1 + 0.4 * s) * Math.sin(TAU * L.swayHz * time + L.phase));
        }
        var dx;
        var shear = 0;
        if (L.tileX) {
          dx = wrap(L.driftPos + camOff, W);
        } else if (L.pivotY !== null) {
          dx = camOff;
          shear = swayX;
        } else {
          dx = camOff + swayX;
        }
        st.dx = dx;
        st.shear = shear;
        st.reach = L.tileX ? 0 : Math.abs(dx) + Math.abs(shear);
        st.alpha = L.alpha * (1 - L.pulse * (0.5 + 0.5 * Math.sin(TAU * L.pulseHz * time + L.phase2)));
      }
    }

    // dt in seconds (not a positive finite number: ignored; longer than MAX_DT: MAX_DT).
    // wind in game units (non-numbers count as 0). cameraX in px (clamped, non-numbers count as 0).
    function update(dt, wind, cameraX) {
      nTarget = normalizeWind(wind, windMax);
      camera = isNum(cameraX) ? clamp(cameraX, -maxCamera, maxCamera) : 0;
      if (!isNum(dt) || dt <= 0) {
        compute();
        return;
      }
      var step = Math.min(dt, MAX_DT);
      nCur += (nTarget - nCur) * (1 - Math.exp(-step / WIND_EASE_TAU));
      time += step;
      for (var i = 0; i < layers.length; i++) {
        var L = layers[i];
        if (L.tileX && (L.drift || L.calmDrift)) {
          L.driftPos = wrap(L.driftPos + (L.calmDrift + nCur * L.drift) * step, W);
        }
      }
      compute();
    }

    function drawLayer(ctx, L, st, img) {
      ctx.globalCompositeOperation = L.blend;
      ctx.globalAlpha = st.alpha;
      if (L.tileX) {
        // The tile covers the full width; a rect only sets the rows (a low fog band).
        var ty = L.rect ? L.rect[1] : 0;
        var th = L.rect ? L.rect[3] : H;
        var x0 = Math.floor(st.dx);
        // +1 px overlap hides the seam between the two copies.
        ctx.drawImage(img, x0 - W, ty, W + 1, th);
        ctx.drawImage(img, x0, ty, W + 1, th);
        return;
      }
      var r = L.rect ? [L.rect[0] - L.margin, L.rect[1], L.rect[2] + 2 * L.margin, L.rect[3]] :
        [-L.margin, 0, W + 2 * L.margin, H];
      if (L.pivotY !== null && st.shear !== 0) {
        // Shear about the pivot row: x' = x + c*y + e moves the farthest row by
        // `shear` and leaves the pivot row where it is (c*pivotY + e = 0).
        var c = L.side * st.shear / L.far;
        ctx.save();
        ctx.transform(1, 0, c, 1, -c * L.pivotY, 0);
        ctx.drawImage(img, r[0] + st.dx, r[1], r[2], r[3]);
        ctx.restore();
      } else {
        ctx.drawImage(img, r[0] + st.dx, r[1], r[2], r[3]);
      }
    }

    // which: 'back' (before the ground, fence and units), 'front' (after the
    // units), or 'all' / undefined (back, then front).
    function draw(ctx, which) {
      if (!ctx) {
        return;
      }
      var plane = which === 'back' || which === 'front' ? which : 'all';
      var mode = getMode();
      ctx.save();
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      if (mode === 'layers') {
        for (var q = 0; q < PLANES.length; q++) {
          if (plane !== 'all' && plane !== PLANES[q]) {
            continue;
          }
          for (var i = 0; i < layers.length; i++) {
            if (layers[i].plane !== PLANES[q]) {
              continue;
            }
            var img = images[layers[i].name];
            if (imageSize(img)) {   // an optional layer that is not loaded yet is skipped
              drawLayer(ctx, layers[i], states[i], img);
            }
          }
        }
      } else if (plane !== 'front') {
        if (mode === 'image') {
          ctx.globalAlpha = 1;
          ctx.globalCompositeOperation = 'source-over';
          ctx.drawImage(images[fallbackKey], 0, 0, W, H);
        } else {
          ctx.globalAlpha = 1;
          ctx.globalCompositeOperation = 'source-over';
          ctx.fillStyle = fallbackColor;
          ctx.fillRect(0, 0, W, H);
        }
      }
      ctx.restore();
    }

    // Copies of the current numbers, for tests and for the caller's own checks.
    function getState() {
      return {
        mode: getMode(),
        violations: violations.slice(),
        maxCamera: maxCamera,
        layers: layers.map(function (L, i) {
          return {
            name: L.name, plane: L.plane, depth: L.depth, blend: L.blend, tileX: L.tileX,
            dx: states[i].dx, shear: states[i].shear, reach: states[i].reach, alpha: states[i].alpha,
            bound: L.bound, margin: L.margin
          };
        })
      };
    }

    compute();

    return {
      update: update,
      draw: draw,
      reset: reset,
      getMode: getMode,
      getState: getState,
      getViolations: function () { return violations.slice(); },
      width: W,
      height: H,
      layerCount: layers.length
    };
  }

  // A valid manifest with no layers: the scene always uses the single baked image.
  function emptyManifest(scene) {
    return { version: 1, scene: typeof scene === 'string' && NAME_RE.test(scene) ? scene : 'scene', layers: [] };
  }

  return {
    create: create,
    validateManifest: validateManifest,
    offsetBound: offsetBound,
    emptyManifest: emptyManifest,
    imageSize: imageSize,
    MAX_LAYERS: MAX_LAYERS,
    MAX_BLEND_FULL: MAX_BLEND_FULL,
    MAX_BOUND: MAX_BOUND,
    DEFAULT_MAX_CAMERA: DEFAULT_MAX_CAMERA,
    MAX_CAMERA_LIMIT: MAX_CAMERA_LIMIT,
    BLENDS: BLENDS
  };
});
