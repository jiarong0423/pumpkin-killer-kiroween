'use strict';
/* Isolated check: does the AI keep a sensible hit rate if it may NOT run the exact ballistic simulator?
   Copies the page physics (index.html simulateLandingX, hit box |dx|<=70 and 190 px tall, fence 895..1025 above y 610).
   Mode "exact": bisect with the real integrator (current game).  Mode "prior": flat-ground prior power = 2.32*sqrt(gap)
   times a calibration factor learned from the AI's own previous landing (public information).
   Run: node scripts/sim_ai_nosim.js [trials]  — prints hit rates per round index and overall. */
const WIND_K = parseFloat(process.env.WIND_K || '4');
const GRAVITY = 980, WIND_ACCEL = 108, GROUND_Y = 860, ANGLE = 54;
let seed = 12345;
const rnd = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };

function fly(power, sx, sy, dir, wind, px) {
  const dt = 1 / 60, rad = ANGLE * Math.PI / 180, v0 = power * 13.8;
  let vx = v0 * Math.cos(rad) * dir, vy = -v0 * Math.sin(rad), x = sx, y = sy;
  for (let i = 0; i < 1200; i++) {
    vx += wind * WIND_ACCEL * dt; vy += GRAVITY * dt; x += vx * dt; y += vy * dt;
    if (x > 895 && x < 1025 && y > 610) return { hit: false, x };                 // fence
    if (Math.abs(x - px) <= 70 && y >= GROUND_Y - 190 && y <= GROUND_Y) return { hit: true, x };
    if (y >= GROUND_Y && vy > 0) break;
  }
  return { hit: false, x };
}
function landing(power, sx, sy, dir, wind) {
  const dt = 1 / 60, rad = ANGLE * Math.PI / 180, v0 = power * 13.8;
  let vx = v0 * Math.cos(rad) * dir, vy = -v0 * Math.sin(rad), x = sx, y = sy;
  for (let i = 0; i < 1200; i++) { vx += wind * WIND_ACCEL * dt; vy += GRAVITY * dt; x += vx * dt; y += vy * dt; if (y >= GROUND_Y && vy > 0) break; }
  return x;
}
function exactPower(sx, sy, tx, wind) {
  let lo = 10, hi = 110;
  for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; const reach = (sx - landing(m, sx, sy, -1, wind)); if (reach < sx - tx) lo = m; else hi = m; }
  return (lo + hi) / 2;
}

function run(mode, err, trials, rounds) {
  const hits = new Array(rounds).fill(0), n = new Array(rounds).fill(0);
  for (let t = 0; t < trials; t++) {
    let cal = 1;
    for (let r = 0; r < rounds; r++) {
      const ax = 1160 + rnd() * 600, px = 160 + rnd() * 600, wind = Math.round((rnd() * 2 - 1) * 4);
      const seenX = Math.round((px + (rnd() * 2 - 1) * 150) / 36) * 36, seenWind = wind + (rnd() * 2 - 1) * 1.2;
      const sx = ax - 58, sy = GROUND_Y - 110;
      let p;
      if (mode === 'exact') p = exactPower(sx, sy, seenX, seenWind);
      else p = cal * 2.32 * Math.sqrt(Math.max(50, sx - seenX)) + (mode === 'prior_wind' ? WIND_K * seenWind : 0);
      p += (rnd() - 0.5) * 2 * err; p = Math.max(30, Math.min(100, p));
      const res = fly(p, sx, sy, -1, wind, px);
      n[r]++; if (res.hit) hits[r]++;
      if (mode === 'prior' || mode === 'prior_wind') {                                  // the AI sees where its own throw landed (public) and corrects its scale
        const land = landing(p, sx, sy, -1, wind), reach = sx - land, want = sx - seenX;
        if (reach > 80) cal = Math.max(0.7, Math.min(1.4, cal * Math.pow(want / reach, 0.5 * 0.7)));
      }
    }
  }
  const tot = hits.reduce((a, b) => a + b, 0) / n.reduce((a, b) => a + b, 0);
  return { byRound: hits.map((h, i) => Math.round(100 * h / n[i])), overall: Math.round(1000 * tot) / 10 };
}
const trials = parseInt(process.argv[2] || '1500', 10);
[['exact', 16], ['prior', 8], ['prior', 3], ['prior_wind', 8], ['prior_wind', 6], ['prior_wind', 3]].forEach(([m, e]) => {
  const r = run(m, e, trials, 8);
  console.log(`${m.padEnd(5)} err ${String(e).padStart(2)}: overall ${r.overall}%  by round [${r.byRound.join(', ')}]`);
});
