#!/usr/bin/env node
'use strict';
// The bride's sound wave is judged where it REALLY lands (owner 2026-11-17: 'the attack judgement failed'). Sweeps angle x power x enemy distance on the REAL page physics
// (scripts/page_harness.js, fixed 1/60 step): every shot that lands within the wave's half width (105 px) of the enemy must do damage, every shot that lands farther must not.
// The same sweep runs on a mutant without the landing-point fix and MUST fail.
const assert = require('assert');
const { loadPage } = require('./page_harness');
function sweep(P) {
  P.clearWeather();
  const GY = P.groundY(); let trials = 0, missed = [], outside = [];
  for (const ex of [1300, 1500, 1700]) for (let ang = 25; ang <= 75; ang += 5) for (let pw = 40; pw <= 95; pw += 1) {
    P.reset(); P.eval('wind = 0; wallHp = 0; currentHero = "bride"; aiClass = "skeleton"; ai.profile = "skeleton"; applyClassStats()');
    const R = P.units('right')[0]; P.place('left', [300]); P.place('right', [ex]);
    const rad = ang * Math.PI / 180, v0 = pw * 13.8;
    P.launch(P.projectile({ hero: 'bride', team: 'player', x: 300, y: GY - 120, vx: v0 * Math.cos(rad), vy: -v0 * Math.sin(rad) }));
    P.eval('landRings.length = 0'); P.run(2000, 1 / 60);
    const ring = Array.from(P.get('landRings')).slice(-1)[0], dealt = R.maxHp - R.hp; trials++;
    if (!ring) { assert.ok(dealt > 0, 'no landing and no damage at ' + ex + ' ' + ang + ' ' + pw); continue; }   // a shot that hit the unit in the air has no landing ring
    const dx = Math.abs(ring.x - ex);
    if (dx <= 105 && dealt <= 0) missed.push([ex, ang, pw, Math.round(dx)]);
    if (dx > 105 && dealt > 0) outside.push([ex, ang, pw, Math.round(dx)]);
  }
  assert.ok(trials > 1000, 'sweep size ' + trials);
  assert.strictEqual(missed.length, 0, 'landed inside the wave range but no damage: ' + JSON.stringify(missed.slice(0, 5)));
  assert.strictEqual(outside.length, 0, 'damage from a landing outside the wave range: ' + JSON.stringify(outside.slice(0, 5)));
  return trials;
}
const trials = sweep(loadPage({ team: 1 }));
console.log('ok   - every wave landing within 105 px of the enemy hurts it, none outside does (' + trials + ' shots)');
const mutant = loadPage({ team: 1, mutate: [['p.x = prevX + (p.x - prevX) * tCross; p.y = GROUND_Y; }', 'p.x = p.x; }']] });
let caught = null; try { sweep(mutant); } catch (e) { caught = e; }
assert.ok(caught instanceof assert.AssertionError, 'mutant without the landing-point fix must fail the sweep: ' + caught);
console.log('ok   - [negative: without the landing-point fix the sweep fails]');
console.log('test_wave_landing: 2 ok, 0 failed');
