'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const AiLevelsPage = require('../js/ai_levels_page.js');
const sweep = require('./sweep_page_ai_levels.js');

const normal = AiLevelsPage.knobsFor(2);
assert.deepStrictEqual(AiLevelsPage.levelName(1), 'easy');
assert.deepStrictEqual(AiLevelsPage.levelName(2), 'normal');
assert.deepStrictEqual(AiLevelsPage.levelName(3), 'hard');
assert.deepStrictEqual(Object.keys(normal).sort(), ['aimError', 'ok', 'viewPosNoise', 'viewWindNoise']);
assert.strictEqual(normal.ok, true);

const invalid = AiLevelsPage.knobsFor(99);
assert.strictEqual(invalid.ok, false);
assert.deepStrictEqual(
  { viewPosNoise: invalid.viewPosNoise, viewWindNoise: invalid.viewWindNoise, aimError: invalid.aimError },
  { viewPosNoise: normal.viewPosNoise, viewWindNoise: normal.viewWindNoise, aimError: normal.aimError }
);

const easy = AiLevelsPage.knobsFor(1);
const hard = AiLevelsPage.knobsFor(3);
for (const knobs of [easy, normal, hard]) {
  assert.deepStrictEqual(Object.keys(knobs).sort(), ['aimError', 'ok', 'viewPosNoise', 'viewWindNoise']);
}
assert.notDeepStrictEqual(easy, normal);
assert.notDeepStrictEqual(normal, hard);

const first = sweep.runSweep(1000);
const second = sweep.runSweep(1000);
assert.deepStrictEqual(first, second, 'fixed seeds must give the same table');
assert(first[0].hitRate < first[1].hitRate && first[1].hitRate < first[2].hitRate,
  'small run must order easy < normal < hard');

const moduleSource = fs.readFileSync(path.join(__dirname, '../js/ai_levels_page.js'), 'utf8');
assert(!moduleSource.includes('Math.random'), 'level module must not use Math.random');
assert(!moduleSource.includes('Date'), 'level module must not use Date');
console.log('PASS: page AI level table is deterministic, safe, and ordered');
