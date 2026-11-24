#!/usr/bin/env node
'use strict';
// The giant axe pushes a surviving unit back 50 px. The push must stay (every size since 2026-11-17; first found in team matches): the page glides every unit toward targetX
// (u.x += (targetX - u.x) * 4 * dt), so a push that only moved x slid back within a second, and two devices that hashed the round at
// different moments disagreed by a pixel or two (found by scripts/run_hybrid_room.py, 2026-11-17). 
const assert = require('assert');
const { loadPage } = require('./page_harness');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n       ') : e)); } }

function axeHit(team) {
  const P = loadPage({ team });
  P.reset();
  const victim = P.place('right', [1500], 1000)[0];
  P.place('left', [600], 1000);
  const gy = P.groundY();
  const shot = P.projectile({ hero: 'hunchback', team: 'player', x: 1300, y: gy - 110, vx: 600, vy: 0, extra: { weapon: 'proj_axe' } });
  P.launch(shot);
  P.run(300, 0.01);
  return { P, victim, hpLost: 1000 - victim.hp };
}

check('N = 3: the push of the axe changes targetX with x (the unit stays where it was pushed)', () => {
  const { victim, hpLost } = axeHit(3);
  assert.ok(hpLost > 0, 'the axe hit (hp lost ' + hpLost + ')');
  assert.strictEqual(victim.targetX, victim.x, 'targetX equals x right after the push');
  assert.ok(victim.x > 1500, 'pushed away from the thrower (x ' + victim.x + ')');
});

check('N = 3: a hundred more physics steps do not slide the unit back', () => {
  const { P, victim } = axeHit(3);
  const x0 = victim.x;
  for (let i = 0; i < 100; i++) P.eval('updatePhysics(0.01)');
  assert.ok(Math.abs(victim.x - x0) < 0.01, 'x stays ' + x0 + ' (now ' + victim.x + ')');
});

check('N = 1: the push stays too (owner 2026-11-17: the one-unit axe push no longer slides back)', () => {
  const { P, victim, hpLost } = axeHit(1);
  assert.ok(hpLost > 0);
  assert.strictEqual(victim.targetX, victim.x, 'targetX equals x right after the push');
  const x0 = victim.x;
  for (let i = 0; i < 100; i++) P.eval('updatePhysics(0.01)');
  assert.ok(Math.abs(victim.x - x0) < 0.01, 'x stays ' + x0 + ' (now ' + victim.x + ')');
});
console.log('test_team_knockback: ' + passed + ' checks passed');
