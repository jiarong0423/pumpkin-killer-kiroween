#!/usr/bin/env node
'use strict';
// Simulated hand control and dropped frames for the aim angle (owner 2026-11-18: 'simulate the human hand and the frame drops, the movement is not smooth, the sensitivity is wrong, left thumb only').
// Data only, no rendering. A MODEL, not human data: every number below is an assumption written in the open and can be changed on the command line.
//
// Schemes for a touch screen:
//   absolute   today's rule (index.html aimFromPointer): angle = direction from the throwing hand to the finger, clamped 25..80; the finger has to be IN the field around the unit
//   relative   proposed left-thumb rule: angle = angle at touch-down + (drag up in px) / PX_PER_DEG, clamped, finger anywhere; at a clamp the anchor stays put (dead travel when the finger comes back)
//   sling      the SHIPPED slingshot (2026-11-18): the angle is the direction of the pull from the touch-down point, so it jitters like 'absolute' with the pull length as the radius (the first review found it missing from this table)
//   slip       relative, but at a clamp the anchor follows the finger, so reversing responds at once (nothing to 'get stuck' on)
// Human model: wants an angle drawn from 30..75; first move lands with a placement error (SD 3 px) and tremor (1 px per event); then closed-loop corrections every 150 ms with gain 0.6 and 8 percent motor noise;
// settled when the shown angle is within 1 degree for 3 events in a row, timeout 3 s. Pointer events come at 60 / 30 / 15 Hz and some are lost (frame drops): a lost event leaves the old angle on screen.
// Absolute scheme: the finger sits at radius r from the hand, r from 25 to 140 css px (a thumb on the left of a 756 px phone reaches about that far into the field).
// Review of 2026-11-18 (another session): (1) the first version let the simulated person know the px-per-degree scale of the relative scheme exactly, which flatters it: the first move now misjudges the scale
// (log-normal, SD 0.3 by default, --scale-sd) and the closed loop has to learn it; (2) the table now also shows the largest jump of the shown angle in one event and the average age of the shown angle
// (input to screen lag), because the complaint is 'not smooth', not only 'slow to settle'; (3) the pass thresholds are written HERE, before the numbers, and the table prints PASS or FAIL against them:
//   median settle <= 500 ms, p95 settle <= 1500 ms, releases over 2 degrees <= 5 percent, p95 tremor jitter <= 1 degree per event, mean age of the shown angle <= 60 ms.
//   (jitter = how far the shown angle shakes per event from a 1 px tremor of the thumb: absolute 1/r radians at distance r from the hand, relative 1/PX_PER_DEG; the first version's 'largest jump' counted the landing of the thumb and then the corrections, which says nothing about smoothness)
// What this model still cannot say: real touch event rates and drops (to be measured on the phone), real learning, and how a left thumb FEELS (to be tried by the owner, see the switchable versions plan).
// Usage: node scripts/aim_input_sim.js [--trials 20000] [--pxdeg 3] [--scale-sd 0.3] [--out docs/INPUT_SIM_20261118.md]
const fs = require('fs');
const path = require('path');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const TRIALS = Number(arg('--trials', 20000)), PX_PER_DEG = Number(arg('--pxdeg', 3)), SCALE_SD = Number(arg('--scale-sd', 0.3)), OUT = arg('--out', '');
const LIMITS = { median: 500, p95: 1500, over2: 5, jump95: 1, age: 60 };
const LO = 25, HI = 80, clamp = v => Math.max(LO, Math.min(HI, v));
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function gauss(r) { return Math.sqrt(-2 * Math.log(1 - r())) * Math.cos(2 * Math.PI * r()); }

const POLAR = scheme => scheme === 'absolute' || scheme === 'sling';   // the angle is the direction of the finger around a centre: the hand (absolute) or the touch-down point (slingshot)
function trial(scheme, rate, drop, r) {
  const want = 30 + r() * 45, dt = 1000 / rate;
  const rad = d => d * Math.PI / 180;
  let fingerAngle, rr, fy;                         // absolute: polar position of the finger around the hand; relative: vertical finger position
  let anchorY = 0, anchorAngle = 54, y = 0;
  rr = scheme === 'sling' ? 40 + r() * 70 : 25 + r() * 115;   // sling: the pull length, 40 to 110 css px (power needs at least about 25 px)
  let shown = 54, ok = 0, t = 0, corrections = 0, deadTravel = 0;
  const start = 54;
  if (POLAR(scheme)) { fingerAngle = rad(start); }
  else { y = 0; anchorY = 0; anchorAngle = start; }
  const angleOf = () => POLAR(scheme) ? clamp(fingerAngle * 180 / Math.PI) : null;
  // first move: aim straight at the wanted angle with a placement error
  const place = want + gauss(r) * 3 / (POLAR(scheme) ? Math.max(rr, 5) : PX_PER_DEG) * (POLAR(scheme) ? 180 / Math.PI : 1);
  if (POLAR(scheme)) fingerAngle = rad(place); else y = -(place - start) * PX_PER_DEG * Math.exp(gauss(r) * SCALE_SD);   // the person does not know the scale: the first move is off by a log-normal factor
  let nextCorrection = 150, maxJump = 0, ageSum = 0, steps = 0, lastArrival = 0, prevShown = shown;
  for (t = 0; t < 3000; t += dt) {
    // tremor on every event
    if (POLAR(scheme)) fingerAngle += gauss(r) * 1 / Math.max(rr, 5); else y += gauss(r) * 1;
    if (r() >= drop) {                              // the event arrives: the shown angle follows the finger
      lastArrival = t;
      if (POLAR(scheme)) shown = clamp(fingerAngle * 180 / Math.PI);
      else {
        const raw = anchorAngle + (anchorY - y) / PX_PER_DEG, c = clamp(raw);
        if (raw !== c) { if (scheme === 'slip') { anchorAngle = c; anchorY = y; } else deadTravel += Math.abs(raw - c); }
        shown = c;
      }
    }
    prevShown = shown; ageSum += t - lastArrival; steps++;   // (the 'largest jump' metric was dropped: it counted the landing of the thumb and the corrections; jitter is the closed form below)
    if (Math.abs(shown - want) <= 1) { if (++ok >= 3) break; } else ok = 0;
    if (t >= nextCorrection) {                      // closed loop: the user looks at the shown angle and corrects
      nextCorrection += 150; corrections++;
      const err = want - shown, step = 0.6 * err * (1 + 0.08 * gauss(r));
      if (POLAR(scheme)) fingerAngle += rad(step); else y -= step * PX_PER_DEG;
    }
  }
  const jitter = POLAR(scheme) ? (180 / Math.PI) / Math.max(rr, 5) : 1 / PX_PER_DEG;   // degrees of shake per event for a 1 px tremor
  return { t, err: Math.abs(shown - want), timeout: t >= 3000, corrections, deadTravel, maxJump: jitter, age: ageSum / Math.max(steps, 1) };
}
const conds = [['60 Hz, no loss', 60, 0], ['30 Hz, 10% lost', 30, 0.1], ['15 Hz, 25% lost', 15, 0.25]];
const lines = ['| scheme | events | median settle (ms) | p95 settle (ms) | median error (deg) | releases over 2 deg | timeouts | mean corrections | p95 tremor jitter (deg per event) | mean age of shown angle (ms) | verdict |', '|---|---|---|---|---|---|---|---|---|---|---|'];
for (const scheme of ['absolute', 'sling', 'relative', 'slip']) for (const [name, rate, drop] of conds) {
  const r = rng(20261118 + rate), res = [];
  for (let i = 0; i < TRIALS; i++) res.push(trial(scheme, rate, drop, r));
  const q = (arr, p) => arr.slice().sort((a, b) => a - b)[Math.floor(arr.length * p)];
  const ts = res.map(x => x.t), es = res.map(x => x.err);
  const over2 = 100 * res.filter(x => x.err > 2).length / TRIALS, jump95 = q(res.map(x => x.maxJump), 0.95), age = res.reduce((s, x) => s + x.age, 0) / TRIALS, m = q(ts, 0.5), p = q(ts, 0.95);
  const pass = m <= LIMITS.median && p <= LIMITS.p95 && over2 <= LIMITS.over2 && jump95 <= LIMITS.jump95 && age <= LIMITS.age;
  lines.push('| ' + [scheme, name, m.toFixed(0), p.toFixed(0), q(es, 0.5).toFixed(2), over2.toFixed(1) + '%', (100 * res.filter(x => x.timeout).length / TRIALS).toFixed(1) + '%', (res.reduce((s, x) => s + x.corrections, 0) / TRIALS).toFixed(1), jump95.toFixed(1), age.toFixed(0), pass ? 'PASS' : 'FAIL'].join(' | ') + ' |');
}
const doc = ['# Aim input simulation (model, 2026-11-18)', '', 'Generated by `scripts/aim_input_sim.js` (' + TRIALS + ' trials per row, ' + PX_PER_DEG + ' css px per degree, first-move scale error SD ' + SCALE_SD + '). A MODEL with the assumptions listed in the script header, not measured human data; it is a first filter, not an acceptance test.', '', 'Thresholds written before the numbers: median settle <= ' + LIMITS.median + ' ms, p95 settle <= ' + LIMITS.p95 + ' ms, releases over 2 degrees <= ' + LIMITS.over2 + ' percent, p95 tremor jitter <= ' + LIMITS.jump95 + ' degree per event, mean age of the shown angle <= ' + LIMITS.age + ' ms.', '', ...lines, '', 'Reading (2026-11-18, after the first red-team review): the SHIPPED slingshot (row sling) takes its angle from the direction of the pull, so a 1 px tremor swings the angle by about 57.3 / pull-length degrees: 1.3 degrees at p95 in this model, above the 1 degree threshold, and worse for short pulls (2.5 degrees per px at a pull of 23 px). The owner reported in chat, after trying it, that the slingshot is fine (\u300c\u525b\u525b\u6e2c\u5f48\u5f13\u53ef\u4ee5\u300d, 2026-11-18; no test record or data exists, and the pull range of this row, 40 to 110 px, is narrower than the shipped firing range of about 25 to 120 px, where the p95 jitter is closer to 1.9 degrees); if it feels jumpy for short pulls the candidates are a smoothed angle that follows the pull length, or a longer minimum pull; nothing was changed because the owner accepts it as it is. The jitter column is a closed form (1 / radius, or 1 / px-per-degree), not a simulated value; the age column counts only lost events.', '', 'Not covered: real touch event rates and drops (measure on the phone), real learning, and the feel of a left thumb (the owner tries switchable versions).', ''].join('\n');
console.log(doc);
if (OUT) fs.writeFileSync(path.resolve(OUT), doc + '\n');
