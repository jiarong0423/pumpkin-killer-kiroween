#!/usr/bin/env node
'use strict';
// Direct hits per throw of the page computer, one-unit matches, both sides the same level, plain throws (owner 2026-11-17: easy 0.15, normal 0.30, hard 0.45;
// before the weakening 0.43 / 0.54 / 0.87). A small sample (4 matches per hero) with bands wide enough for it; the full calibration is scripts/calibrate_page_ai.js
// (160 matches per level: 0.152 / 0.307 / 0.444 before the hit masks and before the fence collision grew to 238 x 282; after commit 23a02165 the same knobs gave 0.262 normal / 0.384 hard). 2026-11-19 (owner: 'raise the computer 5-7'; read as percentage points, an assumption): normal multiplier 0.52, hard multiplier 0.17 with the minimum launch angle 42; now 0.319 / 0.446 (scripts/sweep_ai_multiplier.js, 96 matches). Slow (about 40 s).
const assert = require('assert');
const { measure } = require('./calibrate_page_ai_lib');
// red-team H1 R1-B1: the bands sit around the 2026-11-19 measurement (4 matches per hero: easy 0.141, normal 0.332, hard 0.462 with MAX_POWER 115 and hard 0.27; 12 per hero: hard 0.451, normal 0.319; before MAX_POWER 115, hard 0.17 was 0.441/0.446 and jumped to 0.516 after MAX_POWER 115) so that the old values FAIL: normal multiplier 0.75 measured 0.284 on this very sample and hard with minimum angle 25 measured 0.347 (red-team H1 R2-B).
const bands = { easy: [0.10, 0.21], normal: [0.30, 0.38], hard: [0.40, 0.50] };
let rates = {};
for (const level of ['easy', 'normal', 'hard']) {
  const r = measure(level, 4, 1, 71000);
  rates[level] = r.rate;
  assert.ok(r.errors === 0, level + ': no match error');
  assert.ok(r.rate >= bands[level][0] && r.rate <= bands[level][1], level + ' hits per throw ' + r.rate.toFixed(3) + ' outside ' + bands[level]);
}
assert.ok(rates.easy < rates.normal && rates.normal < rates.hard, 'ordered easy < normal < hard');
console.log('test_page_ai_hit_rates: ' + Object.entries(rates).map(([k, v]) => k + ' ' + v.toFixed(3)).join(', ') + ' inside the bands');
