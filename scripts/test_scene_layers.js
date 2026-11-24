'use strict';
/*
 * Tests for js/scene_layers.js. Node `assert` only, with a recording stub canvas.
 * Run: node scripts/test_scene_layers.js        Exit code 1 if any check fails.
 * The last line is the summary.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const SL = require(path.join(__dirname, '..', 'js', 'scene_layers.js'));

const ROOT = path.join(__dirname, '..');
const W = 1920;
const H = 1080;
const EPS = 1e-9;

// ---------------------------------------------------------------------------
// fixtures

function layer(name, nn, extra) {
  return Object.assign({
    name: name,
    file: 'assets/layers/graveyard/' + nn + '_' + name + '.png',
    depth: Number(nn),
    parallax: 0
  }, extra || {});
}

function goodManifest() {
  return {
    version: 1,
    scene: 'graveyard',
    width: W,
    height: H,
    maxCamera: 24,
    layers: [
      layer('sky', '00', { parallax: 0 }),
      layer('castle', '10', { parallax: 0.1 }),
      layer('trees', '20', { parallax: 0.35, sway: 14, swayHz: 0.3, pivotY: 860 }),
      layer('tombs', '30', { parallax: 0.7 }),
      layer('moon_glow', '35', { parallax: 0.05, blend: 'lighter', alpha: 0.4, pulse: 0.2, pulseHz: 0.2 }),
      layer('ground', '40', { parallax: 1 }),
      layer('fog', '50', { parallax: 0.9, tileX: true, drift: 120, calmDrift: 6, alpha: 0.5 }),
      layer('foreground', '90', { parallax: 1.3, sway: 6, plane: 'front', alpha: 0.5 })
    ]
  };
}

function fakeImage(w, h) {
  return { width: w || W, height: h || H, complete: true };
}

function allImages(manifest) {
  const images = { bg: fakeImage(1536, 864) };
  manifest.layers.forEach((l) => { images[l.name] = fakeImage(); });
  return images;
}

// Stub canvas: only the calls the module may use exist, so any other canvas
// call throws a TypeError and fails the test. Records state at drawImage time.
function makeStub() {
  const calls = [];
  const stack = [];
  let depth = 0;
  const ctx = {
    globalAlpha: 1,
    globalCompositeOperation: 'source-over',
    fillStyle: '#000000',
    imageSmoothingEnabled: false,
    imageSmoothingQuality: 'low',
    save() { depth++; stack.push({ a: ctx.globalAlpha, b: ctx.globalCompositeOperation, f: ctx.fillStyle }); },
    restore() {
      depth--;
      const s = stack.pop();
      if (s) { ctx.globalAlpha = s.a; ctx.globalCompositeOperation = s.b; ctx.fillStyle = s.f; }
    },
    transform(a, b, c, d, e, f) { calls.push({ op: 'transform', args: [a, b, c, d, e, f] }); },
    drawImage(img, x, y, w, h) {
      calls.push({ op: 'drawImage', img: img, x: x, y: y, w: w, h: h, alpha: ctx.globalAlpha,
        blend: ctx.globalCompositeOperation, smooth: ctx.imageSmoothingEnabled, depth: depth });
    },
    fillRect(x, y, w, h) { calls.push({ op: 'fillRect', x: x, y: y, w: w, h: h, style: ctx.fillStyle }); }
  };
  return { ctx: ctx, calls: calls, depth: () => depth };
}

function drawn(calls) { return calls.filter((c) => c.op === 'drawImage'); }

function rng(seed) {   // test-side generator, so the module is the only thing under test
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function make(manifest, extra) {
  const m = manifest || goodManifest();
  const images = allImages(m);
  const scene = SL.create(Object.assign({ manifest: m, images: images, seed: 7 }, extra || {}));
  return { scene: scene, images: images, manifest: m };
}

function run(scene, seconds, dt, wind, cam) {
  const n = Math.round(seconds / dt);
  for (let i = 0; i < n; i++) scene.update(dt, wind, cam);
}

const tests = [];
function test(name, fn) { tests.push({ name: name, fn: fn }); }

// ---------------------------------------------------------------------------
// source hygiene

test('source has no Math.random, clock or DOM access', () => {
  const src = fs.readFileSync(path.join(ROOT, 'js', 'scene_layers.js'), 'utf8');
  assert.ok(!/Math\.random\s*\(/.test(src), 'Math.random call');
  assert.ok(!/Date\.now|new Date|performance\.now|setTimeout|requestAnimationFrame/.test(src), 'clock call');
  assert.ok(!/\bwindow\.|\bdocument\.|\bnew Image\b|createElement/.test(src), 'DOM access');
});

test('running with Math.random and Date.now rigged to throw still works', () => {
  const r = Math.random;
  const d = Date.now;
  Math.random = () => { throw new Error('Math.random used'); };
  Date.now = () => { throw new Error('Date.now used'); };
  try {
    const { scene } = make();
    run(scene, 3, 1 / 60, 2, 5);
    const stub = makeStub();
    scene.draw(stub.ctx);
    assert.ok(drawn(stub.calls).length > 0);
  } finally {
    Math.random = r;
    Date.now = d;
  }
});

// ---------------------------------------------------------------------------
// validator

test('a good manifest has no violations', () => {
  assert.deepStrictEqual(SL.validateManifest(goodManifest()), []);
});

test('the empty manifest is valid, null and non-objects are not', () => {
  assert.deepStrictEqual(SL.validateManifest(SL.emptyManifest('graveyard')), []);
  [null, undefined, 5, 'x', [], true].forEach((m) => {
    assert.ok(SL.validateManifest(m).length > 0, String(m));
  });
  assert.ok(SL.validateManifest({}).length > 0);
});

const BAD = [
  ['wrong version', (m) => { m.version = 2; }],
  ['bad scene name', (m) => { m.scene = 'Grave Yard'; }],
  ['width mismatch', (m) => { m.width = 1536; }],
  ['height mismatch', (m) => { m.height = 864; }],
  ['maxCamera too big', (m) => { m.maxCamera = 500; }],
  ['maxCamera negative', (m) => { m.maxCamera = -1; }],
  ['layers not an array', (m) => { m.layers = {}; }],
  ['too many layers', (m) => { for (let i = 0; i < 4; i++) m.layers.push(layer('extra' + i, '6' + i)); }],
  ['duplicate name', (m) => { m.layers[1].name = 'sky'; m.layers[1].file = 'assets/layers/graveyard/10_sky.png'; }],
  ['bad layer name', (m) => { m.layers[0].name = 'Sky!'; }],
  ['file not under assets/layers', (m) => { m.layers[0].file = 'assets/env/sky.png'; }],
  ['file folder is another scene', (m) => { m.layers[0].file = 'assets/layers/belltower/00_sky.png'; }],
  ['file name differs from layer name', (m) => { m.layers[0].file = 'assets/layers/graveyard/00_heaven.png'; }],
  ['file is not png', (m) => { m.layers[0].file = 'assets/layers/graveyard/00_sky.jpg'; }],
  ['depth missing', (m) => { delete m.layers[0].depth; }],
  ['depth NaN', (m) => { m.layers[0].depth = NaN; }],
  ['unknown plane', (m) => { m.layers[0].plane = 'middle'; }],
  ['parallax negative', (m) => { m.layers[0].parallax = -0.1; }],
  ['parallax too big', (m) => { m.layers[0].parallax = 3; }],
  ['parallax missing', (m) => { delete m.layers[0].parallax; }],
  ['sway too big', (m) => { m.layers[2].sway = 100; }],
  ['sway too negative', (m) => { m.layers[2].sway = -1; }],
  ['camera shift plus sway over 40 px', (m) => { m.layers[0].sway = 32; }],
  ['swayHz too fast', (m) => { m.layers[2].swayHz = 20; }],
  ['pivotY above the canvas', (m) => { m.layers[2].pivotY = -5; }],
  ['pivotY below the canvas', (m) => { m.layers[2].pivotY = 5000; }],
  ['tileX not boolean', (m) => { m.layers[6].tileX = 'yes'; }],
  ['drift without tileX', (m) => { delete m.layers[6].tileX; }],
  ['drift too fast', (m) => { m.layers[6].drift = 9999; }],
  ['unknown blend', (m) => { m.layers[4].blend = 'color-dodge'; }],
  ['alpha above 1', (m) => { m.layers[0].alpha = 1.2; }],
  ['alpha negative', (m) => { m.layers[0].alpha = -0.1; }],
  ['pulse too big', (m) => { m.layers[4].pulse = 0.9; }],
  ['rect wrong length', (m) => { m.layers[0].rect = [0, 0, 10]; }],
  ['rect zero width', (m) => { m.layers[0].rect = [0, 0, 0, 10]; }],
  ['full-canvas additive layer too bright', (m) => { m.layers[4].alpha = 0.9; }],
  ['required not boolean', (m) => { m.layers[0].required = 'no'; }],
  ['layer is not an object', (m) => { m.layers[0] = 5; }]
];
BAD.forEach((pair) => {
  test('validator rejects: ' + pair[0], () => {
    const m = goodManifest();
    pair[1](m);
    const v = SL.validateManifest(m);
    assert.ok(v.length > 0, 'no violation reported');
    v.forEach((s) => assert.strictEqual(typeof s, 'string'));
  });
});

test('validator: too many full-canvas blend layers', () => {
  const m = goodManifest();
  m.layers.push(layer('glow_a', '60', { blend: 'screen', alpha: 0.3 }));
  m.layers.push(layer('glow_b', '61', { blend: 'screen', alpha: 0.3 }));
  assert.ok(SL.validateManifest(m).some((s) => /full-canvas blend layers/.test(s)));
});

test('validator: a bright additive layer is fine when it has a rect', () => {
  const m = goodManifest();
  m.layers[4].alpha = 1;
  m.layers[4].rect = [1400, 40, 400, 400];
  assert.deepStrictEqual(SL.validateManifest(m), []);
});

test('the manifest example in docs/visual_quality_plan.md is valid', () => {
  const doc = fs.readFileSync(path.join(ROOT, 'docs', 'visual_quality_plan.md'), 'utf8');
  const m = /```json manifest-example\n([\s\S]*?)\n```/.exec(doc);
  assert.ok(m, 'no ```json manifest-example block in the plan');
  assert.deepStrictEqual(SL.validateManifest(JSON.parse(m[1])), []);
});

// ---------------------------------------------------------------------------
// determinism

function trace(seed, steps) {
  const { scene } = make(null, { seed: seed });
  const r = rng(99);
  const out = [];
  for (let i = 0; i < steps; i++) {
    scene.update(1 / 60, (r() * 2 - 1) * 4, (r() * 2 - 1) * 30);
    if (i % 17 === 0) out.push(JSON.stringify(scene.getState().layers));
  }
  return out.join('|');
}

test('same seed and same calls give identical numbers', () => {
  assert.strictEqual(trace(5, 600), trace(5, 600));
});

test('another seed gives another sway phase', () => {
  assert.notStrictEqual(trace(5, 600), trace(6, 600));
});

test('reset() replays the first run exactly', () => {
  const { scene } = make();
  const r1 = rng(3);
  const first = [];
  for (let i = 0; i < 300; i++) { scene.update(1 / 60, (r1() - 0.5) * 8, (r1() - 0.5) * 40); first.push(JSON.stringify(scene.getState().layers)); }
  scene.reset();
  const r2 = rng(3);
  for (let i = 0; i < 300; i++) {
    scene.update(1 / 60, (r2() - 0.5) * 8, (r2() - 0.5) * 40);
    assert.strictEqual(JSON.stringify(scene.getState().layers), first[i], 'step ' + i);
  }
});

test('update has no hidden clock: two long idle gaps equal two short ones of the same total', () => {
  const a = make().scene;
  const b = make().scene;
  for (let i = 0; i < 10; i++) a.update(0.1, 1, 0);
  for (let i = 0; i < 100; i++) b.update(0.01, 1, 0);
  const sa = a.getState().layers.find((l) => l.name === 'trees').shear;
  const sb = b.getState().layers.find((l) => l.name === 'trees').shear;
  // Eased wind differs slightly with the step size; the sway stays in the same range.
  assert.ok(Math.abs(sa - sb) < 3, 'sway ' + sa + ' vs ' + sb);
});

// ---------------------------------------------------------------------------
// offsets

test('offsets stay within the published bound for random wind and camera, bad values included', () => {
  const { scene } = make();
  const r = rng(11);
  const bad = [NaN, Infinity, -Infinity, 1e308, -1e308, undefined, null, 'abc', {}, [], 9, -9];
  for (let i = 0; i < 4000; i++) {
    const wind = i % 7 === 0 ? bad[i % bad.length] : (r() * 2 - 1) * 5;
    const cam = i % 11 === 0 ? bad[(i + 3) % bad.length] : (r() * 2 - 1) * 80;
    const dt = i % 13 === 0 ? bad[(i + 5) % bad.length] : r() * 0.2;
    scene.update(dt, wind, cam);
    scene.getState().layers.forEach((l) => {
      assert.ok(Number.isFinite(l.dx) && Number.isFinite(l.shear) && Number.isFinite(l.alpha), l.name + ' not finite');
      if (l.tileX) {
        assert.ok(l.dx >= 0 && l.dx < W, l.name + ' tile dx ' + l.dx);
      } else {
        assert.ok(l.reach <= l.bound + EPS, l.name + ' reach ' + l.reach + ' > bound ' + l.bound);
        assert.ok(l.margin >= l.reach - EPS || l.margin === 0, l.name + ' overscan ' + l.margin + ' < reach ' + l.reach);
      }
      assert.ok(l.alpha >= 0 && l.alpha <= 1, l.name + ' alpha ' + l.alpha);
    });
  }
});

test('offsetBound matches the formula', () => {
  assert.strictEqual(SL.offsetBound({ parallax: 0.5, sway: 0 }, W, H, 24), 12);
  assert.strictEqual(SL.offsetBound({ parallax: 1, sway: 10 }, W, H, 24), 10);
  assert.ok(Math.abs(SL.offsetBound({ parallax: 1.3, sway: 0 }, W, H, 20) - 6) < 1e-9);
  assert.strictEqual(SL.offsetBound({ parallax: 0, tileX: true }, W, H, 24), W);
  // a pivot does not change the bound: no row moves more than the sway value
  assert.strictEqual(SL.offsetBound({ parallax: 1, sway: 10, pivotY: 270 }, W, H, 24), 10);
});

test('the play plane (parallax 1) never moves with the camera; parallax 0 moves with the full camera', () => {
  const { scene } = make();
  scene.update(1 / 60, 0, 20);
  const s = scene.getState().layers;
  assert.ok(Math.abs(s.find((l) => l.name === 'ground').dx) < EPS);
  assert.ok(Math.abs(s.find((l) => l.name === 'sky').dx - 20) < EPS);
  assert.ok(Math.abs(s.find((l) => l.name === 'castle').dx - 18) < EPS);   // 20 * (1 - 0.1)
});

test('a layer in front of the play plane (parallax > 1) moves the other way', () => {
  const { scene } = make();
  scene.update(1 / 60, 0, 20);
  const fg = scene.getState().layers.find((l) => l.name === 'foreground');
  assert.ok(Math.abs(fg.dx + 6) <= 6 * 0.1 + EPS + 1e-6, 'dx ' + fg.dx);   // 20 * (1 - 1.3) = -6, plus the calm sway (<= 6 * 0.1)
});

test('the camera is clamped to maxCamera', () => {
  const a = make().scene;
  const b = make().scene;
  a.update(1 / 60, 0, 24);
  b.update(1 / 60, 0, 1e9);
  assert.deepStrictEqual(a.getState().layers, b.getState().layers);
});

test('no camera, no wind: only a tiny sway, and sky stays put', () => {
  const { scene } = make();
  run(scene, 10, 1 / 60, 0, 0);
  const s = scene.getState().layers;
  assert.strictEqual(s.find((l) => l.name === 'sky').dx, 0);
  const trees = s.find((l) => l.name === 'trees');
  assert.ok(Math.abs(trees.shear) <= 14 * 0.1 + EPS, 'calm shear ' + trees.shear);
});

test('wind pushes the sway toward +x for positive wind and -x for negative wind', () => {
  function meanShear(wind) {
    const { scene } = make();
    run(scene, 3, 1 / 60, wind, 0);   // let the wind ease in
    let sum = 0;
    const n = 600;
    for (let i = 0; i < n; i++) { scene.update(1 / 60, wind, 0); sum += scene.getState().layers.find((l) => l.name === 'trees').shear; }
    return sum / n;
  }
  const pos = meanShear(4);
  const neg = meanShear(-4);
  assert.ok(pos > 3, 'positive wind mean shear ' + pos);
  assert.ok(neg < -3, 'negative wind mean shear ' + neg);
  assert.ok(Math.abs(pos + neg) < 1.5, 'symmetry ' + pos + ' / ' + neg);
});

test('stronger wind gives a larger swing', () => {
  function swing(wind) {
    const { scene } = make();
    run(scene, 4, 1 / 60, wind, 0);
    let lo = Infinity;
    let hi = -Infinity;
    for (let i = 0; i < 900; i++) {
      scene.update(1 / 60, wind, 0);
      const s = scene.getState().layers.find((l) => l.name === 'trees').shear;
      lo = Math.min(lo, s); hi = Math.max(hi, s);
    }
    return hi - lo;
  }
  assert.ok(swing(4) > swing(0.5) * 2, swing(4) + ' vs ' + swing(0.5));
});

test('a non-positive or non-finite dt does not advance time; a huge dt counts as 0.1 s', () => {
  const a = make().scene;
  const b = make().scene;
  [0, -1, NaN, Infinity, undefined, 'x'].forEach((dt) => a.update(dt, 3, 0));
  assert.deepStrictEqual(a.getState().layers, b.getState().layers);
  const c = make().scene;
  const d = make().scene;
  c.update(100, 2, 0);
  d.update(0.1, 2, 0);
  assert.deepStrictEqual(c.getState().layers, d.getState().layers);
});

test('fog drifts downwind, wraps inside the canvas, and drifts slowly in calm air', () => {
  const calm = make().scene;
  run(calm, 5, 1 / 60, 0, 0);
  const calmX = calm.getState().layers.find((l) => l.name === 'fog').dx;
  assert.ok(calmX > 20 && calmX < 40, 'calm drift ' + calmX);   // about 6 px/s for 5 s
  const windy = make().scene;
  run(windy, 20, 1 / 60, 4, 0);
  const x1 = windy.getState().layers.find((l) => l.name === 'fog').dx;
  assert.ok(x1 >= 0 && x1 < W);
  const left = make().scene;
  run(left, 3, 1 / 60, -4, 0);
  const x2 = left.getState().layers.find((l) => l.name === 'fog').dx;
  assert.ok(x2 > W / 2, 'negative wind should wrap below 0 into the upper half, got ' + x2);
});

test('pulse keeps alpha between alpha*(1-pulse) and alpha', () => {
  const { scene } = make();
  let lo = Infinity;
  let hi = -Infinity;
  for (let i = 0; i < 1200; i++) {
    scene.update(1 / 60, 0, 0);
    const a = scene.getState().layers.find((l) => l.name === 'moon_glow').alpha;
    lo = Math.min(lo, a); hi = Math.max(hi, a);
  }
  assert.ok(lo >= 0.4 * 0.8 - EPS && hi <= 0.4 + EPS, lo + '..' + hi);
  assert.ok(hi - lo > 0.04, 'the glow should visibly pulse');
});

// ---------------------------------------------------------------------------
// drawing and fallback

test('with every image loaded the mode is layers and layers are drawn in depth order', () => {
  const { scene, images, manifest } = make();
  scene.update(1 / 60, 0, 0);
  assert.strictEqual(scene.getMode(), 'layers');
  const stub = makeStub();
  scene.draw(stub.ctx);
  const d = drawn(stub.calls);
  // tileX fog draws two copies
  assert.strictEqual(d.length, manifest.layers.length + 1);
  const order = d.map((c) => c.img);
  const expected = manifest.layers.slice().sort((a, b) => a.depth - b.depth).map((l) => images[l.name]);
  const dedup = order.filter((im, i) => i === 0 || im !== order[i - 1]);
  assert.deepStrictEqual(dedup, expected);
});

test('draw keeps save/restore balanced and leaves the context state as it found it', () => {
  const { scene } = make();
  scene.update(1 / 60, 3, 10);
  const stub = makeStub();
  stub.ctx.globalAlpha = 0.77;
  stub.ctx.globalCompositeOperation = 'multiply';
  scene.draw(stub.ctx);
  assert.strictEqual(stub.depth(), 0);
  assert.strictEqual(stub.ctx.globalAlpha, 0.77);
  assert.strictEqual(stub.ctx.globalCompositeOperation, 'multiply');
});

test('draw turns on high quality image smoothing', () => {
  const { scene } = make();
  const stub = makeStub();
  scene.draw(stub.ctx);
  drawn(stub.calls).forEach((c) => assert.strictEqual(c.smooth, true));
});

test('full-canvas layers are drawn with overscan so a shifted edge never shows', () => {
  const { scene } = make();
  scene.update(1 / 60, 4, 24);
  const stub = makeStub();
  scene.draw(stub.ctx);
  const st = scene.getState().layers;
  const d = drawn(stub.calls);
  const sky = d[0];
  const skyState = st.find((l) => l.name === 'sky');
  assert.ok(sky.x + 0 <= 0 && sky.x + sky.w >= W, 'sky covers 0..W: x=' + sky.x + ' w=' + sky.w);
  assert.ok(skyState.margin >= 24);
  assert.strictEqual(sky.y, 0);
  assert.strictEqual(sky.h, H);
});

test('a full-width rect layer is widened by its margin; a tiled layer with a rect uses only the rect rows', () => {
  const m = goodManifest();
  m.layers.find((l) => l.name === 'castle').rect = [0, 260, W, 600];
  m.layers.find((l) => l.name === 'fog').rect = [0, 700, W, 300];
  const { scene } = make(m);
  scene.update(1 / 60, 0, 24);
  const stub = makeStub();
  scene.draw(stub.ctx);
  const d = drawn(stub.calls);
  const st = scene.getState().layers;
  const cs = st.find((l) => l.name === 'castle');
  const expectedX = -cs.margin + cs.dx;
  const hit = d.find((c) => c.y === 260);
  assert.ok(hit, 'castle drawn at its rect row');
  assert.ok(Math.abs(hit.x - expectedX) < EPS && Math.abs(hit.w - (W + 2 * cs.margin)) < EPS && hit.h === 600);
  assert.ok(hit.x <= 0 && hit.x + hit.w >= W, 'no gap at either edge');
  const fogDraws = d.filter((c) => c.y === 700);
  assert.strictEqual(fogDraws.length, 2);
  fogDraws.forEach((c) => assert.strictEqual(c.h, 300));
});

test('a small rect layer (moon glow) is not widened and may sit anywhere', () => {
  const m = goodManifest();
  const g = m.layers.find((l) => l.name === 'moon_glow');
  g.rect = [1220, 0, 700, 700];
  g.alpha = 0.8;   // allowed: it has a rect
  assert.deepStrictEqual(SL.validateManifest(m), []);
  const { scene } = make(m);
  scene.update(1 / 60, 0, 24);
  const stub = makeStub();
  scene.draw(stub.ctx);
  const glow = drawn(stub.calls).find((c) => c.blend === 'lighter');
  assert.strictEqual(glow.w, 700);
  assert.strictEqual(glow.y, 0);
});

test('blend mode and alpha are set when drawing and restored after', () => {
  const { scene } = make();
  scene.update(1 / 60, 0, 0);
  const stub = makeStub();
  scene.draw(stub.ctx);
  const glow = drawn(stub.calls).find((c) => c.blend === 'lighter');
  assert.ok(glow, 'the additive layer was drawn with lighter');
  assert.ok(glow.alpha <= 0.4 + EPS && glow.alpha > 0);
  drawn(stub.calls).filter((c) => c !== glow).forEach((c) => assert.strictEqual(c.blend, 'source-over'));
});

test('a layer with pivotY is sheared about the pivot row', () => {
  const { scene } = make();
  run(scene, 2, 1 / 60, 4, 0);
  const stub = makeStub();
  scene.draw(stub.ctx);
  const t = stub.calls.filter((c) => c.op === 'transform');
  assert.strictEqual(t.length, 1, 'only the trees layer has a pivot');
  const a = t[0].args;
  const shear = scene.getState().layers.find((l) => l.name === 'trees').shear;
  assert.ok(Math.abs(a[4] - shear) < EPS);
  assert.ok(Math.abs(a[2] + shear / 860) < EPS);
  // the pivot row does not move: x' = x + c*y + e at y = pivotY
  assert.ok(Math.abs(a[2] * 860 + a[4]) < 1e-6);
});

test('a hanging layer (pivot near the top of its rect) swings its bottom toward the wind; no row moves more than the sway', () => {
  const m = goodManifest();
  m.layers.push(layer('bell', '45', { parallax: 1, sway: 10, pivotY: 150, rect: [700, 120, 300, 300] }));
  m.layers.splice(7, 1);   // keep to 8 layers: drop the foreground
  const { scene } = make(m);
  run(scene, 3, 1 / 60, 4, 0);
  const stub = makeStub();
  scene.draw(stub.ctx);
  const t = stub.calls.filter((c) => c.op === 'transform');
  assert.strictEqual(t.length, 2, 'trees and bell are both sheared');
  const bell = scene.getState().layers.find((l) => l.name === 'bell');
  const a = t[1].args;   // trees (depth 20) is drawn before the bell (depth 45)
  const far = Math.max(150 - 120, 420 - 150);   // 270
  assert.ok(Math.abs(a[2] - bell.shear / far) < EPS, 'hanging: c = +shear/far');
  assert.ok(Math.abs(a[2] * 150 + a[4]) < 1e-6, 'the pivot row stays put');
  for (let y = 120; y <= 420; y += 10) {
    const disp = a[2] * y + a[4];
    assert.ok(Math.abs(disp) <= Math.abs(bell.shear) + 1e-9, 'row ' + y + ' moves ' + disp);
  }
  // with positive wind the bottom of the bell moves toward +x
  const bottom = a[2] * 420 + a[4];
  assert.ok(bell.shear >= 0 && bottom >= -EPS, 'bottom row moves ' + bottom + ' for shear ' + bell.shear);
});

test('draw("back") and draw("front") split the planes', () => {
  const { scene } = make();
  scene.update(1 / 60, 0, 0);
  const b = makeStub();
  const f = makeStub();
  const all = makeStub();
  scene.draw(b.ctx, 'back');
  scene.draw(f.ctx, 'front');
  scene.draw(all.ctx);
  assert.strictEqual(drawn(f.calls).length, 1);
  assert.strictEqual(drawn(b.calls).length + drawn(f.calls).length, drawn(all.calls).length);
  // the front layer is the last thing drawn by draw('all')
  assert.strictEqual(drawn(all.calls).pop().img, drawn(f.calls)[0].img);
});

test('fallback: an empty manifest draws the single baked background, stretched to the canvas', () => {
  const bg = fakeImage(1536, 864);
  const scene = SL.create({ manifest: SL.emptyManifest('graveyard'), images: { bg: bg } });
  assert.strictEqual(scene.getMode(), 'image');
  const stub = makeStub();
  scene.draw(stub.ctx);
  const d = drawn(stub.calls);
  assert.strictEqual(d.length, 1);
  assert.deepStrictEqual([d[0].img, d[0].x, d[0].y, d[0].w, d[0].h], [bg, 0, 0, W, H]);
  assert.strictEqual(d[0].alpha, 1);
  assert.strictEqual(d[0].blend, 'source-over');
});

test('fallback: null, {} and a broken manifest all fall back without throwing', () => {
  const bg = fakeImage(1536, 864);
  const broken = goodManifest();
  broken.layers[0].parallax = 99;
  [null, undefined, {}, { layers: [] }, broken, 'text', 42].forEach((m) => {
    const scene = SL.create({ manifest: m, images: { bg: bg } });
    scene.update(1 / 60, 1, 5);
    assert.strictEqual(scene.getMode(), 'image', JSON.stringify(m));
    const stub = makeStub();
    scene.draw(stub.ctx);
    assert.strictEqual(drawn(stub.calls).length, 1);
  });
  const scene = SL.create({ manifest: broken, images: { bg: bg } });
  assert.ok(scene.getViolations().length > 0, 'the broken manifest reports why it was rejected');
  assert.strictEqual(scene.layerCount, 0);
});

test('fallback: nothing loaded draws the flat colour', () => {
  const scene = SL.create({ manifest: null, images: {} });
  assert.strictEqual(scene.getMode(), 'fill');
  const stub = makeStub();
  scene.draw(stub.ctx);
  const fr = stub.calls.filter((c) => c.op === 'fillRect');
  assert.strictEqual(fr.length, 1);
  assert.deepStrictEqual([fr[0].x, fr[0].y, fr[0].w, fr[0].h, fr[0].style], [0, 0, W, H, '#0a0514']);
  assert.strictEqual(drawn(stub.calls).length, 0);
  const s2 = SL.create({ manifest: null, images: {}, fallbackColor: '#123456' });
  const st2 = makeStub();
  s2.draw(st2.ctx);
  assert.strictEqual(st2.calls[0].style, '#123456');
});

test('fallback: an image that is not complete counts as not loaded', () => {
  const scene = SL.create({ manifest: null, images: { bg: { width: 100, height: 100, complete: false } } });
  assert.strictEqual(scene.getMode(), 'fill');
  const s2 = SL.create({ manifest: null, images: { bg: { naturalWidth: 0, naturalHeight: 0, complete: true } } });
  assert.strictEqual(s2.getMode(), 'fill');
});

test('fallback: a missing REQUIRED layer image sends the whole scene back to the baked image', () => {
  const { scene, images } = make();
  delete images.castle;
  assert.strictEqual(scene.getMode(), 'image');
  const stub = makeStub();
  scene.draw(stub.ctx);
  assert.strictEqual(drawn(stub.calls).length, 1);
  assert.strictEqual(drawn(stub.calls)[0].img, images.bg);
});

test('an OPTIONAL layer that is missing is skipped, the others still draw', () => {
  const m = goodManifest();
  m.layers.find((l) => l.name === 'moon_glow').required = false;
  const { scene, images } = make(m);
  delete images.moon_glow;
  assert.strictEqual(scene.getMode(), 'layers');
  const stub = makeStub();
  scene.draw(stub.ctx);
  assert.strictEqual(drawn(stub.calls).length, m.layers.length);   // 8 layers - 1 skipped + 1 extra fog copy
  assert.ok(!drawn(stub.calls).some((c) => c.blend === 'lighter'));
});

test('fallback: draw("front") draws nothing when the scene is in fallback mode', () => {
  const scene = SL.create({ manifest: null, images: { bg: fakeImage() } });
  const stub = makeStub();
  scene.draw(stub.ctx, 'front');
  assert.strictEqual(stub.calls.length, 0);
});

test('images are read live: a layer loaded later switches the mode, images.bg can be replaced', () => {
  const m = goodManifest();
  const images = { bg: fakeImage(1536, 864) };
  const scene = SL.create({ manifest: m, images: images, seed: 1 });
  assert.strictEqual(scene.getMode(), 'image');
  m.layers.forEach((l) => { images[l.name] = fakeImage(); });
  assert.strictEqual(scene.getMode(), 'layers');
  const other = SL.create({ manifest: null, images: images });
  const bg2 = fakeImage(1920, 1080);
  images.bg = bg2;
  const stub = makeStub();
  other.draw(stub.ctx);
  assert.strictEqual(drawn(stub.calls)[0].img, bg2);
});

test('a layer image given as a canvas-like object (width/height, no complete) is accepted', () => {
  assert.deepStrictEqual(SL.imageSize({ width: 10, height: 20 }), { w: 10, h: 20 });
  assert.strictEqual(SL.imageSize(null), null);
  assert.strictEqual(SL.imageSize({ width: 0, height: 5 }), null);
  assert.strictEqual(SL.imageSize({ naturalWidth: 7, naturalHeight: 9, complete: true }).w, 7);
});

test('draw(null) and a custom canvas size do not throw', () => {
  const { scene } = make();
  scene.draw(null);
  scene.draw(undefined);
  const small = SL.create({ manifest: SL.emptyManifest('x'), images: { bg: fakeImage(64, 36) }, width: 960, height: 540 });
  const stub = makeStub();
  small.draw(stub.ctx);
  const d = drawn(stub.calls)[0];
  assert.deepStrictEqual([d.w, d.h], [960, 540]);
});

test('layer budget: at most MAX_LAYERS layers and the published limits', () => {
  assert.strictEqual(SL.MAX_LAYERS, 8);
  assert.strictEqual(SL.MAX_BLEND_FULL, 2);
  assert.strictEqual(SL.DEFAULT_MAX_CAMERA, 24);
  assert.deepStrictEqual(SL.BLENDS, ['source-over', 'lighter', 'screen', 'multiply']);
  assert.ok(make().scene.layerCount <= SL.MAX_LAYERS);
});

// ---------------------------------------------------------------------------

let failed = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('ok   - ' + t.name);
  } catch (err) {
    failed++;
    console.log('FAIL - ' + t.name + '\n       ' + (err && err.message ? err.message : err));
  }
}
console.log(failed === 0 ? 'ALL ' + tests.length + ' TESTS PASSED' : failed + ' of ' + tests.length + ' TESTS FAILED');
process.exit(failed === 0 ? 0 : 1);
