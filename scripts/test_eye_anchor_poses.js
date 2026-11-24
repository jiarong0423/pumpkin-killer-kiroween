#!/usr/bin/env node
'use strict';
// Red-team R1 A3 (2026-11-24): the pumpkin eye anchor must follow the eyes in EVERY wizard and knight picture and never land on the cannon muzzle flash. Every picture the page can draw for these two heroes is decoded here
// (a small PNG decoder, no dependency), run through the page's own detector and chooser, and compared with the unit's idle reference. Without chooseEyes the detector alone puts a halo on the flash in two wizard poses.
const assert = require('assert');
const fs = require('fs'), zlib = require('zlib'), path = require('path');
const ROOT = path.join(__dirname, '..');
const { loadPage } = require('./page_harness');
function decodePng(file) {
  const b = fs.readFileSync(file); let pos = 8, w = 0, h = 0, bd = 0, ct = 0; const idat = [];
  while (pos < b.length) { const len = b.readUInt32BE(pos), type = b.toString('ascii', pos + 4, pos + 8), data = b.slice(pos + 8, pos + 8 + len); if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); bd = data[8]; ct = data[9]; } else if (type === 'IDAT') idat.push(data); pos += 12 + len; }
  if (bd !== 8 || (ct !== 6 && ct !== 2)) throw new Error('unsupported png ' + file + ' bd=' + bd + ' ct=' + ct);
  const bpp = ct === 6 ? 4 : 3, raw = zlib.inflateSync(Buffer.concat(idat)), stride = w * bpp, out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) { const f = raw[y * (stride + 1)]; for (let x = 0; x < stride; x++) { const v = raw[y * (stride + 1) + 1 + x], a = x >= bpp ? out[y * stride + x - bpp] : 0, up = y ? out[(y - 1) * stride + x] : 0, c = (x >= bpp && y) ? out[(y - 1) * stride + x - bpp] : 0; let r; if (f === 0) r = v; else if (f === 1) r = v + a; else if (f === 2) r = v + up; else if (f === 3) r = v + ((a + up) >> 1); else { const p = a + up - c, pa = Math.abs(p - a), pb = Math.abs(p - up), pc = Math.abs(p - c); r = v + (pa <= pb && pa <= pc ? a : pb <= pc ? up : c); } out[y * stride + x] = r & 255; } }
  return { w, h, bpp, px: out };
}
function small(img, width) { const hh = Math.max(1, Math.round(width * img.h / img.w)), d = new Uint8ClampedArray(width * hh * 4); for (let y = 0; y < hh; y++) for (let x = 0; x < width; x++) { const sx = Math.floor((x + 0.5) * img.w / width), sy = Math.floor((y + 0.5) * img.h / hh), i = (sy * img.w + sx) * img.bpp, o = (y * width + x) * 4; d[o] = img.px[i]; d[o + 1] = img.px[i + 1]; d[o + 2] = img.px[i + 2]; d[o + 3] = img.bpp === 4 ? img.px[i + 3] : 255; } return { d, w: width, h: hh }; }

const P = loadPage({ team: 1, seed: 5 });
const src = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const files = {}; for (const m of src.matchAll(/(unit_wizard|unit_knight|unit_knight_unarmed|pose_wiz_[a-z0-9_]+|pose_knight_[a-z0-9_]+):\s*"([^"]+\.png)"/g)) files[m[1]] = m[2];
const detect = key => { const s = small(decodePng(path.join(ROOT, files[key])), 128); P.context.__px = s.d; return JSON.parse(P.eval('JSON.stringify(eyeCentersFromPixels(__px, ' + s.w + ', ' + s.h + '))')); };
const choose = (det, ref, base) => JSON.parse(P.eval('JSON.stringify(chooseEyes(' + JSON.stringify(det) + ', ' + JSON.stringify(ref) + ', ' + base + '))'));
let passed = 0; const check = (name, fn) => { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + e.message); } };
const near = (a, b, tol) => Math.abs(a.left.x - b.left.x) <= tol && Math.abs(a.left.y - b.left.y) <= tol && Math.abs(a.right.x - b.right.x) <= tol && Math.abs(a.right.y - b.right.y) <= tol;
for (const [hero, base, poses] of [['wizard', 'unit_wizard', Object.keys(files).filter(k => /^pose_wiz_/.test(k))], ['knight', 'unit_knight', Object.keys(files).filter(k => /^pose_knight_|unit_knight_unarmed/.test(k))]]) {
  const ref = choose(detect(base), null, true).ref;
  check(hero + ': the idle picture gives a clean reference pair', () => { assert.ok(ref, 'no reference'); assert.ok(ref.right.x - ref.left.x > 0.08, 'eyes too close together: ' + JSON.stringify(ref)); });
  for (const k of poses) check(hero + ' ' + k + ': the chosen eyes stay on the face (within 0.07 of the idle reference)', () => {
    const det = detect(k), r = choose(det, ref, false);
    assert.ok(r.eyes && near(r.eyes, ref, 0.07), k + ': chosen ' + JSON.stringify(r.eyes) + ' is not near the reference ' + JSON.stringify(ref) + ' (raw detection ' + JSON.stringify(det) + ')');
  });
}
check('the raw detector alone is wrong in a wizard pose (why the chooser exists): charge or release leaves the reference by more than 0.07', () => {
  const ref = choose(detect('unit_wizard'), null, true).ref;
  const off = ['pose_wiz_charge', 'pose_wiz_release'].filter(k => !near(detect(k), ref, 0.07));
  assert.ok(off.length >= 1, 'if this fails the detector got better: the chooser may be simplified');
});
check('chooser rules: no reference and not base art gives nothing; an implausible pair is never accepted; a good pair becomes the reference', () => {
  const good = { left: { x: 0.31, y: 0.36 }, right: { x: 0.49, y: 0.34 } }, bad = { left: { x: 0.40, y: 0.36 }, right: { x: 0.42, y: 0.36 } }, tall = { left: { x: 0.31, y: 0.30 }, right: { x: 0.49, y: 0.40 } };
  assert.strictEqual(choose(good, null, false).eyes, null);
  assert.strictEqual(choose(bad, null, true).eyes, null);
  assert.strictEqual(choose(tall, null, true).eyes, null);
  assert.deepStrictEqual(choose(good, null, true), { eyes: good, ref: good });
  assert.deepStrictEqual(choose(bad, good, false).eyes, good, 'an implausible detection falls back to the reference');
  assert.strictEqual(choose(null, good, false).eyes.left.x, 0.31);
});
console.log('test_eye_anchor_poses: ' + passed + ' passed' + (process.exitCode ? ', FAILED' : ''));
