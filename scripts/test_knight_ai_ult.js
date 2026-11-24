#!/usr/bin/env node
'use strict';
// The computer knight fires its ultimate (the Shield Wall) on both seats (owner 2026-11-17: the page computer never did, 0 of 10,008 full-event matches, so its knight was the weakest hero).
// Real matches of the REAL index.html in the Node vm, both seats computer with the full AI, knight against skeleton and skeleton against knight:
//   - the knight side spends its ultimate (ultimates_left / ultimates_right > 0 for its side),
//   - the wall really blocks a shot now and then (hit type "ultblock"),
//   - a mutant that never places the wall fails the same checks.
const assert = require('assert');
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');

function play(mutate) {
  let knightLeftUlts = 0, knightRightUlts = 0, blocks = 0;
  for (let k = 0; k < 8; k++) {
    for (const knightSide of ['left', 'right']) {
      const seed = 32000 + k * 2 + (knightSide === 'left' ? 0 : 1);
      const hero = knightSide === 'left' ? 'knight' : 'skeleton', heroRight = knightSide === 'left' ? 'skeleton' : 'knight';
      const P = loadPage({ team: 1, seed, mutate });
      vm.runInContext(D.source, P.context);
      vm.runInContext('window.__blocks = 0; (function () { var o = pushHitReport; pushHitReport = function (p, t) { if (t === "ultblock") window.__blocks++; return o.apply(this, arguments); }; })();', P.context);
      const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify({ hero, heroRight, size: 1, seed, plainOnly: false, tierLeft: 'normal', tierRight: 'normal' }) + ')', P.context)));
      assert.deepStrictEqual(rec.errors, [], 'match errors: ' + rec.errors);
      if (knightSide === 'left') knightLeftUlts += rec.ultimates_left; else knightRightUlts += rec.ultimates_right;
      blocks += vm.runInContext('window.__blocks', P.context);
    }
  }
  assert.ok(knightLeftUlts > 0, 'the left computer knight fires its ultimate: ' + knightLeftUlts);
  assert.ok(knightRightUlts > 0, 'the right computer knight fires its ultimate: ' + knightRightUlts);
  assert.ok(blocks > 0, 'a computer Shield Wall blocks a shot: ' + blocks);
  return { knightLeftUlts, knightRightUlts, blocks };
}
const real = play();
console.log('ok   - the computer knight fires its ultimate on both seats and the wall blocks (left ' + real.knightLeftUlts + ', right ' + real.knightRightUlts + ' ultimates, ' + real.blocks + ' blocked shots in 16 matches)');
let caught = null;
try { play([['      energy[own] = 0; ultUsed[own]++; snd("ult_knight");\n      if (side === "left")', '      return false;\n      if (side === "left")']]); } catch (e) { caught = e; }
assert.ok(caught instanceof assert.AssertionError, 'mutant that never places the wall must fail: ' + caught);
console.log('ok   - [negative: a computer knight that never places the wall fails the check]');
console.log('test_knight_ai_ult: 2 ok, 0 failed');
