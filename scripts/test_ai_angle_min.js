#!/usr/bin/env node
'use strict';
// Red-team H1 R1-B1: the computer retune of 2026-11-19 must be pinned by a test. The hard level never plans a throw below 42 degrees (a flat shot ends on the fence: 88 percent of the shots under 30 degrees did),
// easy and normal keep the whole 25..80 range. Source pin + behaviour (the real page, aiPlanShot, a seeded generator).
const assert = require('assert'), fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
assert.match(html, /const AI_ANGLE_MIN_BY_LEVEL = Object\.freeze\(\{ easy: 25, normal: 25, hard: 42 \}\)/, 'AI_ANGLE_MIN_BY_LEVEL literal');
assert.match(html, /const angleMin = AI_ANGLE_MIN_BY_LEVEL\[levelFor\(side\)\] \|\| AI_ANGLE_MIN;/, 'aiPlanShot uses the level table');
function anglesFor(level) {
  const P = loadPage({ team: 1, seed: 5 });
  P.eval('(function () { var s = 12345; Math.random = function () { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; }; })(); seats.level.right = ' + JSON.stringify(level) + ';');
  const out = [];
  for (let i = 0; i < 600; i++) out.push(P.eval('aiPlanShot("right", 1650, 750, -1, 330, 0).angle'));
  return out;
}
const hard = anglesFor('hard'), normal = anglesFor('normal'), easy = anglesFor('easy');
assert.ok(Math.min.apply(null, hard) >= 42 && Math.max.apply(null, hard) <= 80, 'hard angles inside 42..80, min ' + Math.min.apply(null, hard));
assert.ok(Math.min.apply(null, normal) < 35, 'normal still throws flat shots, min ' + Math.min.apply(null, normal));
assert.ok(Math.min.apply(null, easy) < 35, 'easy still throws flat shots, min ' + Math.min.apply(null, easy));
console.log('test_ai_angle_min: hard min ' + Math.min.apply(null, hard) + ', normal min ' + Math.min.apply(null, normal) + ', easy min ' + Math.min.apply(null, easy) + ' ok');
