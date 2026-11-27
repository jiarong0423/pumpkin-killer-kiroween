#!/usr/bin/env node
'use strict';
// A throw that leaves the field must not raise "out of sync" over a few px outside it (2026-11-27, room monkey seed 3: 1921.75 vs 1927 and -1.75 vs -7).
const assert = require('assert');
const { loadPage } = require('./page_harness');
const agrees = loadPage({}).eval('relayLandingAgrees');
assert.strictEqual(agrees(1921.75, 1927), true);
assert.strictEqual(agrees(-1.75, -7), true);
assert.strictEqual(agrees(900, 903.9), true);
assert.strictEqual(agrees(900, 906), false);
assert.strictEqual(agrees(1915, 1927), false, 'one inside, one outside: still a difference');
assert.strictEqual(agrees(-20, 1940), false, 'opposite sides');
console.log('test_landing_agrees: OK');
