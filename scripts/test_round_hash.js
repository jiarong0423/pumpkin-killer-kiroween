'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const RoundHash = require('../js/round_hash.js');
const golden = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'round_hash_golden.json'), 'utf8'));

for (const entry of golden.cases) {
  assert.strictEqual(RoundHash.canonicalText(entry.state), entry.canonical, entry.name + ' canonical text');
  assert.strictEqual(RoundHash.hash(entry.state), entry.hash, entry.name + ' hash');
}
const base = golden.cases[0].state;
const smallDifference = JSON.parse(JSON.stringify(base));
smallDifference.units[0].x += 0.0004;
const onePixelDifference = JSON.parse(JSON.stringify(base));
onePixelDifference.units[0].x += 1;
assert.strictEqual(RoundHash.hash(smallDifference), RoundHash.hash(base), '0.0004 px must not change the hash');
assert.notStrictEqual(RoundHash.hash(onePixelDifference), RoundHash.hash(base), '1 px must change the hash');
console.log('PASS: ' + golden.cases.length + ' round-hash goldens; sub-pixel stable and one-pixel sensitive');
