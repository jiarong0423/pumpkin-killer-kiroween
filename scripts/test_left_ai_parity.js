#!/usr/bin/env node
'use strict';
// The computer on the LEFT seat uses the same skills and ultimates as the right one (owner 2026-11-17, 'full skills and events').
// Before the fix it threw plain shots only, so every computer-versus-computer match of the full AI leaned to the right side (left won 41 to 46 percent, left ultimates 0).
// Runs real matches of the REAL index.html in the Node vm (scripts/page_harness.js + scripts/page_match_driver.js), both seats computer, full AI: the left seat must fire ultimates and skills.
// A mutant without the left preparation must fail the same check.
const assert = require('assert');
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');

function play(mutate) {
  let ultLeft = 0, ultRight = 0, matches = 0;
  for (const [hero, seed] of [['skeleton', 31001], ['wizard', 31002], ['bat', 31003], ['bride', 31004], ['hag', 31005], ['reaper', 31006]]) {
    const P = loadPage({ team: 1, seed, mutate });
    vm.runInContext(D.source, P.context);
    const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify({ hero, size: 1, seed, plainOnly: false, tierLeft: 'normal', tierRight: 'normal' }) + ')', P.context)));
    assert.deepStrictEqual(rec.errors, [], 'match errors: ' + rec.errors);
    ultLeft += rec.ultimates_left; ultRight += rec.ultimates_right; matches++;
  }
  assert.ok(ultRight > 0, 'the right seat fires ultimates (sanity)');
  assert.ok(ultLeft > 0, 'the left seat fires ultimates too: left ' + ultLeft + ', right ' + ultRight + ' in ' + matches + ' matches');
  return { ultLeft, ultRight };
}
const real = play();
console.log('ok   - the left computer fires ultimates like the right one (left ' + real.ultLeft + ', right ' + real.ultRight + ' in 6 matches)');
let caught = null;
try { play([['      prepareLeftAiShot();\n', '']]); } catch (e) { caught = e; }
assert.ok(caught instanceof assert.AssertionError, 'mutant without prepareLeftAiShot must fail: ' + caught);
console.log('ok   - [negative: without prepareLeftAiShot the left seat fires no ultimate]');
console.log('test_left_ai_parity: 2 ok, 0 failed');
