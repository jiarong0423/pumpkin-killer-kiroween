'use strict';
// Owner 2026-11-16: tailwind and headwind must differ clearly AND every target must stay hittable.
// Legacy zone check (dice-move zones left 240..640 / right 1280..1680, hit half-width 70, power 15..100) plus H15 MAX_POWER=115 corner check (110/1810, wind -5..5, see scripts/reach_in_headwind.py).
const assert = require('assert');
const Flight = require('../js/flight.js');
const C = require('../shared/constants.json');
const MAX_DIST = 1460, MIN_DIST = 660, HIT = 45, STORM_BONUS = 1.5;
let failed = 0;
function test(name, fn) { try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.log('FAIL - ' + name + '\n       ' + e.message); } }
// shooters stand at the far edges of their start ranges (red 220, white 1680) so the wall and the canvas edge sit where they really are
function reach(power, angle, dirX, wind) {
  const startX = dirX > 0 ? 220 : 1680;
  const r = Flight.simulate({ startX: startX, startY: 700, dirX: dirX, angleDeg: angle, power: power, wind: wind });
  return (r.landingX - startX) * dirX;
}
function maxReach(dirX, wind) { let b = 0; for (let a = 25; a <= 80; a += 0.5) b = Math.max(b, reach(100, a, dirX, wind)); return b; }
function minReach(power, dirX, wind) { let b = 1e9; for (let a = 25; a <= 80; a += 0.5) b = Math.min(b, reach(power, a, dirX, wind)); return b; }
test('constants: headwind is clearly stronger than tailwind', () => {
  assert.ok(C.WIND_HEAD >= 1.5 * C.WIND_TAIL, 'tail ' + C.WIND_TAIL + ' head ' + C.WIND_HEAD);
});
// ---- real-game pair check (parameters of the live game, 2026-11-16) ----
// hit = ground landing within PAIR_HIT (70) px of the target x; muzzle 58 px in front of the shooter x, 110 px above the feet (ground 860 -> startY 750).
const PAIR_HIT = 70, MUZZLE_DX = 58, MUZZLE_Y = C.GROUND_Y - 110;
const landCache = new Map();
// all ground landings of every (angle 25..80 integer, power 15..100 step 0.5) shot from one shooter x; cached because landing does not depend on the target
function landings(sx, dirX, w) {
  const key = sx + '|' + dirX + '|' + w;
  let list = landCache.get(key);
  if (list) return list;
  list = [];
  for (let a = 25; a <= 80; a++) for (let p = 15; p <= 100; p += 0.5) {
    const r = Flight.simulate({ startX: sx + dirX * MUZZLE_DX, startY: MUZZLE_Y, dirX: dirX, angleDeg: a, power: p, wind: w });
    if (r.hit === 'ground') list.push(r.landingX);
  }
  list.sort((x, y) => x - y);
  landCache.set(key, list);
  return list;
}
function hittable(sx, dirX, tx, w) {
  const list = landings(sx, dirX, w);
  let lo = 0, hi = list.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (list[m] < tx - PAIR_HIT) lo = m + 1; else hi = m; }
  return lo < list.length && list[lo] <= tx + PAIR_HIT;
}
function range(from, to, step) { const o = []; for (let v = from; v <= to; v += step) o.push(v); return o; }
function winds(from, to) { return range(from, to, 1); }
// every shooter in lefts shoots every target in rights (dirX +1) and every shooter in rights shoots every target in lefts (dirX -1)
function scanPairs(lefts, rights, windList) {
  const bad = [], res = { total: 0, bad: bad };
  for (const w of windList) {
    for (const sx of lefts) for (const tx of rights) { res.total++; if (!hittable(sx, 1, tx, w)) bad.push({ w: w, dir: 'L->R', from: sx, to: tx }); }
    for (const sx of rights) for (const tx of lefts) { res.total++; if (!hittable(sx, -1, tx, w)) bad.push({ w: w, dir: 'R->L', from: sx, to: tx }); }
  }
  return res;
}
function byWind(bad) { const m = new Map(); for (const b of bad) { if (!m.has(b.w)) m.set(b.w, []); m.get(b.w).push(b); } return m; }
function pairLabel(b) { return (b.dir === 'L->R' ? 'L' : 'R') + b.from + '->' + (b.dir === 'L->R' ? 'R' : 'L') + b.to; }
function printTable(res, windList) {
  const m = byWind(res.bad);
  console.log('       wind | bad pairs | pairs (shooter x -> target x; L = left side, R = right side)');
  for (const w of windList) {
    const l = m.get(w) || [];
    console.log('       ' + String(w).padStart(4) + ' | ' + String(l.length).padStart(9) + ' | ' + l.map(pairLabel).join(' '));
  }
  console.log('       total bad ' + res.bad.length + ' of ' + res.total + ' pairs');
}
const START_L = range(252, 612, 36), START_R = range(1296, 1656, 36);
const DICE_L = range(240, 640, 40), DICE_R = range(1280, 1680, 40);
test('START ranges: every shooter x can hit every target x, both directions, winds -5..5 (hit half-width 70, angles 25..80, power 15..100)', () => {
  const res = scanPairs(START_L, START_R, winds(-5, 5));
  assert.strictEqual(res.bad.length, 0, res.bad.length + ' of ' + res.total + ' unhittable: ' + res.bad.slice(0, 5).map(pairLabel).join('; '));
});
test('DICE-MOVE zones (left 240..640, right 1280..1680, step 40): every shooter x can hit every target x, both directions, winds -5..5', () => {
  const wl = winds(-5, 5), res = scanPairs(DICE_L, DICE_R, wl);
  console.log('       pairs per wind: ' + (DICE_L.length * DICE_R.length * 2) + ' (' + DICE_L.length + 'x' + DICE_R.length + ' each direction), winds ' + wl.length);
  printTable(res, wl);
  assert.strictEqual(res.bad.length, 0, res.bad.length + ' of ' + res.total + ' pairs unhittable (table above)');
});
test('INFO dice-move reach at winds -6..6 reports, but does not hide, the extreme-wind pairs (6 before the fence collision grew to the drawn gate; 20 since 2026-11-18, none inside winds -5..5)', () => {
  const wl = winds(-6, 6), res = scanPairs(DICE_L, DICE_R, wl);
  printTable(res, wl);
  assert.strictEqual(res.bad.length, 20, 'expected the documented 20 extreme-wind pairs (winds beyond +-5, storm only)');
});
test('INFO proposed zones left 240..640, right 1280..1680 (step 40): pair counts at winds -4..4, -5..5, -6..6 (always passes)', () => {
  const L = range(240, 640, 40), R = range(1280, 1680, 40);
  for (const lim of [4, 5, 6]) {
    const wl = winds(-lim, lim), res = scanPairs(L, R, wl);
    console.log('       winds -' + lim + '..' + lim + ': ' + (res.total - res.bad.length) + ' of ' + res.total + ' pairs hittable, ' + res.bad.length + ' not');
    if (res.bad.length) printTable(res, wl.filter(w => (byWind(res.bad).get(w) || []).length));
  }
});
test('H15 corner retreat limits (110 <-> 1810) remain hittable at MAX_POWER 115 across winds -5..5', () => {
  for (const w of winds(-5, 5)) {
    const okLR = range(25, 80, 1).some(a => { const r = Flight.simulate({ startX: 110 + MUZZLE_DX, startY: MUZZLE_Y, dirX: 1, angleDeg: a, power: 115, wind: w }); return r.hit === 'ground' && Math.abs(r.landingX - 1810) <= PAIR_HIT; }) || range(25, 80, 1).some(a => range(85, 115, 2).some(p => { const r = Flight.simulate({ startX: 110 + MUZZLE_DX, startY: MUZZLE_Y, dirX: 1, angleDeg: a, power: p, wind: w }); return r.hit === 'ground' && Math.abs(r.landingX - 1810) <= PAIR_HIT; }));
    const okRL = range(25, 80, 1).some(a => range(85, 115, 2).some(p => { const r = Flight.simulate({ startX: 1810 - MUZZLE_DX, startY: MUZZLE_Y, dirX: -1, angleDeg: a, power: p, wind: w }); return r.hit === 'ground' && Math.abs(r.landingX - 110) <= PAIR_HIT; }));
    assert.ok(okLR && okRL, 'corner 110<->1810 unreachable at power<=115 wind ' + w);
  }
});
test('the same wind holds a shot back against the wind clearly more than it carries a shot with the wind', () => {
  const calm = reach(45, 54, 1, 0);   // a short shot (the wall and the canvas edge do not cut it) and a wind of 2
  const tail = reach(45, 54, 1, 2) - calm, head = calm - reach(45, 54, 1, -2);
  assert.ok(head > 1.3 * tail, 'tail shift ' + tail + ' head shift ' + head);
});
console.log('test_wind_reach: ' + (failed ? failed + ' FAILED' : 'all passed'));
process.exit(failed ? 1 : 0);
