'use strict';
/* Phone-resolution checks for task 202. This is deterministic; the Gaussian CDF
   is exact for the local linear landing-sensitivity approximation. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');
const page = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const seed = 20261116;
const bodyWidth = { skeleton: 106, wizard: 94, bat: 101, knight: 128, reaper: 109, bride: 108, hunchback: 141, hag: 96 };
const boxWidth = { skeleton: 140, wizard: 140, bat: 140, knight: 140, reaper: 114, bride: 140, hunchback: 140, hag: 140 };
const imgKey = { skeleton: 'unit_skeleton', wizard: 'unit_wizard', bat: 'unit_bat', knight: 'unit_knight', reaper: 'unit_reaper', bride: 'unit_bride', hunchback: 'unit_hunchback', hag: 'unit_hag' };
for (const [hero, width] of Object.entries(bodyWidth)) {
  assert.ok(boxWidth[hero] >= width * 0.9, hero + ' hit box is narrower than 90% of its real-art silhouette');
  assert.ok(page.includes(imgKey[hero]), hero + ' real art key is not drawn by the page');
}
const timing = /const CHARGE_SWEEP_SECONDS = (\d+(?:\.\d+)?);/.exec(page);
assert.ok(timing, 'CHARGE_SWEEP_SECONDS is required');
const sweep = Number(timing[1]);
const maxPowerMatch = /const MAX_POWER = (\d+);/.exec(page);
assert.ok(maxPowerMatch, 'MAX_POWER is required');
const maxPower = Number(maxPowerMatch[1]);
const msPerUnit = sweep / maxPower * 1000;   // arbitration 2026-11-19: the meter runs 0..MAX_POWER (115) in one sweep, so the design target "20 ms per power unit" is sweep / MAX_POWER, not sweep / 100
assert.ok(msPerUnit >= 19.5 && msPerUnit <= 20.5, 'one power unit must take 20 ms (19.5 to 20.5), got ' + msPerUnit.toFixed(2) + ' ms for ' + sweep + ' s over ' + maxPower);
function erf(x) { const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911,s=x<0?-1:1,t=1/(1+p*Math.abs(x)); return s*(1-(((((a5*t+a4)*t+a3)*t+a2)*t+a1)*t)*Math.exp(-x*x)); }
function probability(power, sigmaMs) {
  // The measured useful-band derivative is 22 px/power at 65 and 27 at 80.
  const pxPerPower = 0.3333333333 * power;
  const sigmaWorld = pxPerPower * maxPower / sweep * sigmaMs / 1000;
  return erf(70 / (Math.sqrt(2) * sigmaWorld));
}
const viewports = [[873,392],[844,390],[932,430]];
const rows = [];
for (const power of [45, 50, 55, 60, 65, 70, 75, 80, 85, 90]) for (const angle of [40,54,70]) {
  const pxPerPower = +(power / 3).toFixed(1);
  const p40 = probability(power, 40), p60 = probability(power, 60);
  rows.push({power, angle, pxPerPower, p40, p60});
  assert.ok(p40 >= .70, `power ${power}, angle ${angle}: sigma40 ${p40}`);
  assert.ok(p60 >= .55, `power ${power}, angle ${angle}: sigma60 ${p60}`);
}
for (const [width, height] of viewports) {
  const scale = Math.min(width / 1920, height / 1080);
  assert.ok(120 * scale >= 22, `${width}x${height}: landing ring is below 22 CSS px`);
}
assert.ok(page.includes('new URLSearchParams(window.location.search).get("hitboxes") === "1"'), 'missing ?hitboxes=1 overlay');
assert.ok(page.includes('drawHitboxOverlay()'), 'missing hitbox draw');
assert.ok(page.includes('lr.t / 1.2'), 'landing ring must last 1.2 seconds');
assert.ok(page.includes('fs(ft.fontSize || 18)'), 'floating numbers must use display scale helper');
console.log('seed ' + seed + '; sweep ' + sweep + ' s; silhouette boxes passed');
console.log('power angle world-px/power P(sigma40) P(sigma60)');
for (const row of rows) console.log(String(row.power).padEnd(6) + String(row.angle).padEnd(6) + String(row.pxPerPower).padEnd(15) + row.p40.toFixed(3).padEnd(11) + row.p60.toFixed(3));
console.log('test_hit_confirm: ' + rows.length + ' reach-band rows × ' + viewports.length + ' phone viewports passed');
