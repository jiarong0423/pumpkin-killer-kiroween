#!/usr/bin/env node
'use strict';
// The hp bar over a head never overlaps its neighbours (owner 2026-11-17: 'the boxes above the heads have shifted again'). Real page in the Node vm (scripts/page_harness.js).
// Before: every bar was 150 x uiScale() wide (about 295 world px on a phone) while team slots are 180 px apart, so the three bars of a team merged into one strip.
const assert = require('assert');
const { loadPage } = require('./page_harness');

function check(mutate) {
  const P = loadPage({ team: 3, mutate });
  P.eval('displayScale = function () { return 0.28; }');   // a phone: uiScale() is about 1.96, so the old bar was about 295 world px wide
  const full = P.eval('150 * uiScale()');
  assert.ok(full > 250, 'sanity: the old width is wide on a phone: ' + full);
  P.place('left', [264, 444, 624]);                         // the slot gaps of a 3-unit team: 180 px
  const widths = P.units('left').map((u, i) => P.eval('hpBarWidthFor(unitsOf("left")[' + i + '])'));
  widths.forEach((w, i) => assert.ok(w <= 0.85 * 180 + 1e-9, 'bar ' + i + ' is ' + w + ' wide, more than 85 percent of the 180 px gap'));
  // two teammates only 120 px apart (the closest they may stand): bars of about 102 px, no overlap
  P.place('left', [264, 384, 624]);
  const close = P.eval('hpBarWidthFor(unitsOf("left")[0])');
  assert.ok(close <= 0.85 * 120 + 1e-9 && close >= 60, 'close teammates: ' + close);
  // teammates pushed to 60 px apart (the knight push can do this): the bar still stays inside 85 percent of the gap
  P.place('left', [264, 324, 624]);
  const tight = P.eval('hpBarWidthFor(unitsOf("left")[0])');
  assert.ok(tight <= 0.85 * 60 + 1e-9, 'tight teammates: ' + tight);
  // a dead teammate does not shrink the bar of the survivors
  P.units('left')[1].hp = 0;
  assert.ok(P.eval('hpBarWidthFor(unitsOf("left")[0])') > close, 'a dead neighbour is ignored');
  // one unit per team: exactly the old width
  const Q = loadPage({ team: 1, mutate });
  Q.eval('displayScale = function () { return 0.28; }');
  assert.strictEqual(Q.eval('hpBarWidthFor(unitsOf("left")[0])'), Q.eval('150 * uiScale()'));
}
check();
console.log('ok   - hp bars never overlap a neighbour (85 percent of the gap), a dead neighbour is ignored, one unit keeps the old width');
let caught = null;
try { check([['const hpBarWidth = hpBarWidthFor(u),', 'const hpBarWidth = 150 * uiScale(),'], ['return Math.min(full, Math.max(24, 0.85 * gap));', 'return full;']]); } catch (e) { caught = e; }
assert.ok(caught instanceof assert.AssertionError, 'a mutant with the old width must fail: ' + caught);
console.log('ok   - [negative: the old fixed width fails the check]');
console.log('test_hp_bar_width: 2 ok, 0 failed');
