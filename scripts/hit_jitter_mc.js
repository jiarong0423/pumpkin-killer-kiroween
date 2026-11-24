'use strict';
// Release-jitter Monte Carlo for the hold-to-charge meter (backend only, no browser).
// Per scenario (shooter x, angle, wind, target x): find the power p* that lands on the target, then draw N release-time errors
// (Gaussian, sigma ms) -> power error = 100 / T * sigma (the ping-pong meter, T = seconds for one 0..100 sweep) and count landings within the hit half-width.
// Usage: node scripts/hit_jitter_mc.js [draws=30000] [seed=20261116] [out.json]
const fs = require('fs');
const Flight = require('../js/flight.js');
const DRAWS = parseInt(process.argv[2] || '30000', 10), SEED = parseInt(process.argv[3] || '20261116', 10), OUT = process.argv[4] || '';
const HIT = 70, MUZZLE = 58, START_Y = 750;
const SX = [], TX = [];
for (let x = 240; x <= 680; x += 40) SX.push(x);
for (let x = 1240; x <= 1680; x += 40) TX.push(x);
const ANGLES = [40, 54, 70], WINDS = [-4, -3, -2, -1, 0, 1, 2, 3, 4];
const PERIODS = [1.3, 1.8, 2.2, 3.0], SIGMAS = [40, 60];
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const rnd = mulberry32(SEED), Z = new Float64Array(DRAWS);
for (let i = 0; i < DRAWS; i += 2) { const u = Math.max(rnd(), 1e-12), v = rnd(), r = Math.sqrt(-2 * Math.log(u)); Z[i] = r * Math.cos(2 * Math.PI * v); if (i + 1 < DRAWS) Z[i + 1] = r * Math.sin(2 * Math.PI * v); }
const STEP = 0.1, N = 1001;   // landing table over power 0..100
function table(sx, ang, w) {
  const t = new Float64Array(N);
  for (let i = 0; i < N; i++) {
    const r = Flight.simulate({ startX: sx + MUZZLE, startY: START_Y, dirX: 1, angleDeg: ang, power: i * STEP, wind: w });
    t[i] = r.hit === 'ground' ? r.landingX : NaN;   // wall hit or out of canvas counts as a miss
  }
  return t;
}
const rows = {};
for (const T of PERIODS) for (const s of SIGMAS) rows[T + '|' + s] = { n: 0, sumP: 0, below50: 0, below70: 0, byBand: { '45-60': [0, 0], '60-75': [0, 0], '75-90': [0, 0] }, worst: [] };
let scenarios = 0, unreachable = 0;
for (const sx of SX) for (const ang of ANGLES) for (const w of WINDS) {
  const t = table(sx, ang, w);
  for (const tx of TX) {
    let best = -1, bd = 1e9;
    for (let i = 0; i < N; i++) if (!Number.isNaN(t[i])) { const d = Math.abs(t[i] - tx); if (d < bd) { bd = d; best = i; } }
    if (best < 0 || bd > 12) { unreachable++; continue; }
    const pstar = best * STEP;
    if (pstar < 45 || pstar > 90) continue;
    scenarios++;
    const band = pstar < 60 ? '45-60' : (pstar < 75 ? '60-75' : '75-90');
    for (const T of PERIODS) for (const s of SIGMAS) {
      const sigP = 100 / T * s / 1000; let hit = 0;
      for (let k = 0; k < DRAWS; k++) {
        const p = Math.max(0, Math.min(100, pstar + Z[k] * sigP)), f = p / STEP, i0 = Math.floor(f), i1 = Math.min(N - 1, i0 + 1);
        const a = t[i0], b = t[i1]; if (Number.isNaN(a) || Number.isNaN(b)) continue;
        if (Math.abs(a + (b - a) * (f - i0) - tx) <= HIT) hit++;
      }
      const pr = hit / DRAWS, R = rows[T + '|' + s];
      R.n++; R.sumP += pr; if (pr < 0.5) R.below50++; if (pr < 0.7) R.below70++;
      R.byBand[band][0] += pr; R.byBand[band][1]++;
      if (R.worst.length < 5 || pr < R.worst[R.worst.length - 1].p) { R.worst.push({ p: +pr.toFixed(3), sx, ang, w, tx, pstar: +pstar.toFixed(1) }); R.worst.sort((x, y) => x.p - y.p); R.worst = R.worst.slice(0, 5); }
    }
  }
}
const out = { draws: DRAWS, seed: SEED, hitHalfWidth: HIT, scenarios, unreachableOrOutsideBand: unreachable, gate: { 'sigma40': 0.7, 'sigma60': 0.55 }, results: [] };
console.log('draws ' + DRAWS + ' seed ' + SEED + ' scenarios ' + scenarios + ' (shooter 240..680 step 40, target 1240..1680 step 40, angles 40/54/70, winds -4..4, p* 45..90)');
console.log('T(s)  sigma  mean P(hit)  P<50%  P<70%   band 45-60  60-75  75-90   worst');
for (const T of PERIODS) for (const s of SIGMAS) {
  const R = rows[T + '|' + s], mean = R.sumP / R.n, b = k => (R.byBand[k][0] / Math.max(1, R.byBand[k][1])).toFixed(2);
  const gate = s === 40 ? 0.7 : 0.55;
  out.results.push({ T, sigmaMs: s, meanHit: +mean.toFixed(4), shareBelow50: +(R.below50 / R.n).toFixed(4), shareBelow70: +(R.below70 / R.n).toFixed(4), band: { '45-60': +b('45-60'), '60-75': +b('60-75'), '75-90': +b('75-90') }, worst: R.worst, meetsGateOnMean: mean >= gate });
  console.log(String(T).padEnd(5) + ' ' + String(s).padEnd(6) + ' ' + mean.toFixed(3).padEnd(12) + (R.below50 / R.n).toFixed(2).padEnd(7) + (R.below70 / R.n).toFixed(2).padEnd(8) + b('45-60') + '        ' + b('60-75') + '   ' + b('75-90') + '   ' + R.worst[0].p + ' @ sx ' + R.worst[0].sx + ' ang ' + R.worst[0].ang + ' wind ' + R.worst[0].w + ' tx ' + R.worst[0].tx + (mean >= gate ? '  gate-mean OK' : '  gate-mean FAIL'));
}
if (OUT) fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n');
