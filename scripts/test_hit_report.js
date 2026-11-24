'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const HitReport = require('../js/hit_report.js');
const vectors = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'hit_report_vectors.json'), 'utf8'));
assert.ok(vectors.length >= 30, 'shared vectors must cover at least 30 outcomes');
const heroes = new Set(vectors.map(v => v.hero));
assert.deepStrictEqual(heroes, new Set(['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag']));
for (const vector of vectors) {
  const report = HitReport.classify(vector.landingX, vector.targetX, vector.hitType, vector.weapon);
  const actual = report.kind === 'wave' ? 'wave' + report.params.band : report.kind === 'hit' ? 'hit' : report.key === 'hitReport.fence' ? 'fence' : report.key === 'hitReport.shield' ? 'shield' : report.key === 'hitReport.short' ? 'short' : 'long';
  assert.strictEqual(actual, vector.expected, vector.id);
}
assert.strictEqual(HitReport.classify(1328, 1400, 'ground', 'cannonball').steps, 2);
assert.strictEqual(HitReport.waveBand(35), '100');   // cells of 35 px (owner 2026-11-18)
assert.strictEqual(HitReport.waveBand(35.1), '75');
assert.strictEqual(HitReport.waveBand(70), '75');
assert.strictEqual(HitReport.waveBand(70.1), '50');
assert.strictEqual(HitReport.waveBand(105), '50');
assert.strictEqual(HitReport.waveBand(105.1), 'out');
console.log('test_hit_report: ' + vectors.length + ' shared vectors passed');
