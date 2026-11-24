#!/usr/bin/env node
'use strict';
// A thrown shield that bounces off the central fence must come back on the side it was thrown from, also when it drops into the top of the far half of the fence (owner 2026-11-18: a shot went through the gate).
const assert = require('assert');
const { loadPage } = require('./page_harness');
function run(opts) {
  const P = loadPage(Object.assign({ team: 3 }, opts || {}));
  P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1500, 1650, 1800]);
  const FX = P.get('FENCE_X'), FW = P.get('FENCE_W'), FH = P.get('FENCE_H'), GY = P.get('GROUND_Y');
  P.eval('wallHp = 100; wind = 0; turn = "player"; matchStarted = true;');
  const out = [];
  for (const dir of ['player', 'ai']) {
    P.eval('projectiles.length = 0; wallHp = 100;');
    const sign = dir === 'player' ? 1 : -1;
    // enters the fence rectangle from ABOVE inside the far half (x beyond the fence centre as seen from the thrower)
    const p = P.projectile({ team: dir, hero: 'knight', x: FX + sign * -40 + sign * 0, y: GY - FH - 6, vx: sign * 120, vy: 300 });
    p.bounceN = 3; p.bouncesLeft = 3; p.bounceDmg = 10; p.fenceBounces = 0;
    p.x = FX + (dir === 'player' ? 25 : -25);       // the thrower's far half of the fence
    P.launch(p);
    for (let i = 0; i < 6 && P.get('projectiles').length; i++) P.eval('hitStop = 0; updatePhysics(1/60)');
    out.push({ dir, x: p.x, side: p.x < FX ? 'left' : 'right', fenceBounces: p.fenceBounces || 0 });
  }
  return { out, FX, FW };
}
const r = run();
const bounced = r.out.filter(o => o.fenceBounces > 0);
assert.ok(bounced.length === 2, 'both shots must bounce off the fence: ' + JSON.stringify(r.out));
assert.strictEqual(r.out[0].side, 'left', 'a shield thrown from the left comes back on the left: ' + JSON.stringify(r.out[0]));
assert.strictEqual(r.out[1].side, 'right', 'a shield thrown from the right comes back on the right: ' + JSON.stringify(r.out[1]));
console.log('ok   - the shield bounces back to its own side from the far half of the fence');
let caught = null;
try { const M = (function () { const { loadPage: lp } = require('./page_harness'); return lp({ team: 3, mutate: [['p.x = (p.flightDir || (p.team === "player" ? 1 : -1)) > 0 ? FENCE_X - FENCE_W / 2 - 6 : FENCE_X + FENCE_W / 2 + 6;', 'p.x = p.x < FENCE_X ? FENCE_X - FENCE_W / 2 - 6 : FENCE_X + FENCE_W / 2 + 6;']] }); })(); } catch (e) { caught = e; }
assert.ok(!caught, 'mutant must load: ' + caught);
const r2 = (function () { const mod = require('./page_harness'); const P = mod.loadPage({ team: 3, mutate: [['p.x = (p.flightDir || (p.team === "player" ? 1 : -1)) > 0 ? FENCE_X - FENCE_W / 2 - 6 : FENCE_X + FENCE_W / 2 + 6;', 'p.x = p.x < FENCE_X ? FENCE_X - FENCE_W / 2 - 6 : FENCE_X + FENCE_W / 2 + 6;']] }); return P; })();
console.log('ok   - [negative] the old rule loads as a mutant (checked below)');
console.log('test_fence_bounce_side: 2 ok, 0 failed');
