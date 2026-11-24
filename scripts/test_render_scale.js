#!/usr/bin/env node
'use strict';
// Render scale (owner 2026-11-18, phone lag): on a touch screen the canvas backing store follows the device pixels the stage really covers (at most 2 per css pixel, never below half the world), on a mouse screen it keeps the
// full size. Runs the REAL renderScaleFor of index.html in the Node vm with a faked screen. A mutant that ignores the touch rule must fail.
const assert = require('assert');
const vm = require('vm');
const fs = require('fs');
const path = require('path');
const { loadPage } = require('./page_harness');

function scale(P, coarse, cssH, dpr) { return vm.runInContext('renderScaleFor(' + cssH + ', ' + dpr + ', ' + coarse + ')', P.context); }
const P = loadPage({ team: 1, seed: 6161 });
assert.strictEqual(scale(P, false, 800, 1), 1, 'a mouse screen keeps the full size');
assert.strictEqual(scale(P, true, 354, 3), 0.65, 'the real phone (354 css px high stage, dpr 3): 354 x 2 / 1080 = 0.65');
assert.strictEqual(scale(P, true, 354, 1), 0.35 < 0.5 ? 0.5 : 0, 'never below half the world');
assert.strictEqual(scale(P, true, 700, 2), 1, 'a large touch screen is capped at 1');
console.log('ok   - the scale is 1 on a mouse screen, 0.65 on the real phone, at least 0.5, at most 1');
const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
assert.ok(/function paintFrame\(frameDt\) \{\n      ctx\.save\(\);\n      ctx\.setTransform\(RENDER_SCALE, 0, 0, RENDER_SCALE, 0, 0\);[^\n]*\n      ctx\.translate\(PAD, 0\);/.test(src), 'every frame starts with the world-to-pixel transform, before the side pad translate');
assert.ok(/drawImage\(canvas, PAD \* RS, 0, PAD \* RS, CANVAS_H \* RS, 0, 0, PAD, CANVAS_H\)/.test(src) && /drawImage\(canvas, CANVAS_W \* RS, 0, PAD \* RS, CANVAS_H \* RS, -PAD, 0, PAD, CANVAS_H\)/.test(src), 'the side mirror reads backing-store pixels');
assert.ok(!/setTransform\(1, 0, 0, 1, 0, 0\)/.test(src), 'no code resets the transform to identity (it would draw at the wrong size)');
console.log('ok   - the frame starts with the transform, the mirror copy uses backing-store pixels, nothing resets the transform');
let caught = null;
try { const M = loadPage({ team: 1, seed: 6162, mutate: [['if (!coarse) return 1;', 'if (false) return 1;']] }); assert.strictEqual(scale(M, false, 800, 1), 1, 'mouse'); } catch (e) { caught = e; }
assert.ok(caught instanceof assert.AssertionError, 'a mutant that ignores the touch rule must fail: ' + caught);
console.log('ok   - [negative: scaling a mouse screen is caught]');
console.log('test_render_scale: 3 ok, 0 failed');
