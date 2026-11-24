#!/usr/bin/env node
'use strict';
// The aim arrow (owner 2026-11-17 / 2026-11-18): red neon chevrons from the hero's real launch point along the current angle, flashing crosswise, angle only.
// Runs the REAL drawAimArrow of index.html in the Node vm against a recording fake context (no browser). The first version had a parameter named `ctx` that shadowed the canvas
// context and stopped the whole frame loop (black canvas on the phone): a no-argument call must draw on the page's own ctx, and a negative proves the pin.
const assert = require('assert');
const vm = require('vm');
const fs = require('fs');
const path = require('path');
const { loadPage } = require('./page_harness');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack || e).split('\n').slice(0, 4).join('\n       ')); } }

function recorder() {
  const calls = []; let alpha = 1;
  const g = { calls, get globalAlpha() { return alpha; }, set globalAlpha(v) { alpha = v; } };
  ['save', 'restore', 'translate', 'scale', 'rotate', 'beginPath', 'rect', 'clip'].forEach(n => { g[n] = (...a) => { calls.push({ n, a }); }; });
  g.drawImage = (...a) => { calls.push({ n: 'drawImage', a, alpha }); };
  return g;
}
function setup(hero, side) {
  const P = loadPage({ team: 1, seed: 9100 });
  vm.runInContext('images.aim_pointer = { complete: true, naturalWidth: 480 }; currentHero = ' + JSON.stringify(hero) + ';' + (side === 'right' ? ' seats.left = "agent"; seats.right = "human"; turn = "ai";' : ''), P.context);
  return P;
}
const draw = (P, g) => { P.context.__g = g; vm.runInContext('drawAimArrow(__g)', P.context); };
const num = a => a.map(Number);

check('the arrow starts at the real launch point of each hero and is rotated by the current angle (skeleton 58/110, wizard 70/118, knight 51/73)', () => {
  for (const [hero, fwd, up] of [['skeleton', 58, 110], ['wizard', 70, 118], ['knight', 51, 73]]) {
    const P = setup(hero); const g = recorder(); draw(P, g);
    const ux = vm.runInContext('unitOf("left").x', P.context), uy = vm.runInContext('unitOf("left").y', P.context), ang = vm.runInContext('activeAngle()', P.context);
    const tr = g.calls.find(c => c.n === 'translate'), rot = g.calls.find(c => c.n === 'rotate');
    assert.deepStrictEqual(num(tr.a), [ux + fwd, uy - up], hero + ' launch point');
    assert.ok(Math.abs(rot.a[0] + ang * Math.PI / 180) < 1e-12, hero + ' rotation = minus the angle (up is negative y)');
  }
});

check('six chevron slices are drawn, each clipped to its own 76 px slice, odd and even slices flash in opposite phase, all semi-transparent', () => {
  const P = setup('skeleton'); const g = recorder(); draw(P, g);
  const images = g.calls.filter(c => c.n === 'drawImage'), clips = g.calls.filter(c => c.n === 'rect');
  assert.strictEqual(images.length, 6, 'one drawImage per chevron'); assert.strictEqual(clips.length, 6);
  images.forEach(c => assert.ok(c.alpha > 0.4 && c.alpha <= 1.0, 'bright but not solid: ' + c.alpha));
  const sc = vm.runInContext('AIM_ARROW_LEN', P.context) / 440;
  clips.forEach((c, k) => assert.ok(Math.abs(c.a[0] - (76 * k - 8) * sc) < 1e-9 && Math.abs(c.a[2] - 76 * sc) < 1e-9, 'slice ' + k));
  // opposite phase: after removing the tip fade (1 - 0.1 k) the odd and even alphas of a pair sum to 1.55 (0.55 + 0.45 phase and 0.55 + 0.45 (1 - phase)) (the sine and its negative)
  const base = k => images[k].alpha / (1 - 0.06 * k);
  for (let k = 0; k < 6; k += 2) assert.ok(Math.abs(base(k) + base(k + 1) - 1.55) < 1e-9, 'pair ' + k + ' flashes crosswise: ' + base(k) + ' + ' + base(k + 1));
  for (let k = 1; k < 6; k++) assert.ok(images[k].alpha / (1 - 0.06 * k) <= 1.0 + 1e-9);   // owner 2026-11-18: brighter; never fully solid
});

check('the arrow is short (owner: too big, then: too easy to guess the trajectory): 150 world px, about a twelfth of the 1920 stage', () => {
  const P = setup('skeleton');
  const len = vm.runInContext('AIM_ARROW_LEN', P.context);
  assert.strictEqual(len, 150); assert.ok(len < 1920 / 10);
});

check('mirrored on the right side (a human on the right throws to the left): the arrow flips', () => {
  const P = setup('skeleton', 'right'); const g = recorder(); draw(P, g);
  const sc = g.calls.find(c => c.n === 'scale');
  assert.ok(sc && sc.a[0] === -1 && sc.a[1] === 1, 'x mirrored: ' + JSON.stringify(sc));
});

check('nothing is drawn (and nothing throws) while the picture is not loaded', () => {
  const P = setup('skeleton'); vm.runInContext('images.aim_pointer = { complete: false, naturalWidth: 0 }', P.context);
  const g = recorder(); draw(P, g); assert.strictEqual(g.calls.length, 0);
});

check('a no-argument call works on the PAGE\'s own canvas context (the parameter is `g = ctx`, never `ctx`)', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(/function drawAimArrow\(g = ctx\)/.test(src), 'signature');
  assert.ok(!/function drawAimArrow\(ctx\b/.test(src), 'no parameter named ctx');
  const P = setup('skeleton');
  vm.runInContext('drawAimArrow()', P.context);   // must not throw: the default is the page context
});

check('[negative] a parameter named ctx that shadows the context kills a no-argument call (the black-canvas bug) and the test above would fail on it', () => {
  const M = loadPage({ team: 1, seed: 9101, mutate: [['function drawAimArrow(g = ctx) {', 'function drawAimArrow(ctx) { const g = ctx;']] });
  vm.runInContext('images.aim_pointer = { complete: true, naturalWidth: 480 };', M.context);
  assert.throws(() => vm.runInContext('drawAimArrow()', M.context), e => e && e.name === 'TypeError', 'the shadowing mutant must throw on a no-argument call (the error comes from the vm realm: compared by name)');
});

console.log('test_aim_arrow: ' + passed + ' ok' + (process.exitCode ? ', FAILED' : ', 0 failed'));
