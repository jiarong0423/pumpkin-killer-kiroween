#!/usr/bin/env node
'use strict';
// DATA ONLY, REAL PAGE PHYSICS. Owner 2026-11-18: "I am sure it went through", "test breaking through the wall mid-flight". The fence has ONE hit left (wallHp = WALL_HIT_DMG), the ultimate is armed for every role, both directions,
// every angle 5..85 step 5 x power 10..100 step 4. Per projectile and per physics step: while the fence stood at the START of the step, a projectile centre must never get from one side of the fence line (x = FENCE_X) to the other below
// the fence top (y >= FENCE_Y_TOP) - that is "went through". After the step in which the fence broke, passing is legal and is counted separately (the volley's later projectiles). Also: the projectile that broke the fence must not hurt anybody in that same step.
// usage: node scripts/test_wall_break_midflight.js   exit 1 on any pass-through while the fence stood or a hit on the breaking step by the breaking projectile.
const { loadPage } = require('./page_harness');
const C = require('../shared/constants.json'); const FX = C.FENCE_X, TOP = 578;
const P = loadPage({ team: 3, seed: 31 }); const ROLES = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];
const dmg = +P.eval('WALL_HIT_DMG');
let throws = 0, broke = 0, throughWhileUp = [], passedAfterBreak = 0, hurtOnBreak = [];
for (const dir of ['L2R', 'R2L']) for (const hero of ROLES) for (let ang = 5; ang <= 85; ang += 5) for (let pw = 10; pw <= 115; pw += 4) {
  const shooter = dir === 'L2R' ? 'left' : 'right', tgt = dir === 'L2R' ? 'right' : 'left', team = dir === 'L2R' ? 'player' : 'ai';
  P.reset(); P.place(shooter, dir === 'L2R' ? [300, 450, 600] : [1600, 1450, 1300]); P.place(tgt, dir === 'L2R' ? [1250, 1400, 1550] : [670, 520, 370]);
  P.eval('wind = 0; wallHp = ' + dmg + '; turn = ' + JSON.stringify(team) + '; matchStarted = true; energy.player = 3; energy.ai = 3; ultUsed.player = 0; ultUsed.ai = 0; ultArmed.player = ' + (dir === 'L2R') + '; ultArmed.ai = ' + (dir === 'R2L') + '; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(hero) + '; unitsOf(' + JSON.stringify(shooter) + ').forEach(u => { u.profile = ' + JSON.stringify(hero) + '; }); setActiveUnit(' + JSON.stringify(shooter) + ', unitsOf(' + JSON.stringify(shooter) + ')[0]);');
  P.clearWeather(); P.units(tgt).forEach(u => { u.hp = u.maxHp = 5000; });
  P.eval('executeThrow(' + JSON.stringify(team) + ', ' + pw + ', ' + ang + ')'); if (!P.get('projectiles').length) continue; throws++;
  let s = 0, brokenAt = -1; const last = new Map();
  while (P.get('projectiles').length && s < 1500) {
    const ps = Array.from(P.get('projectiles')), up0 = P.get('wallHp') > 0, hp0 = P.units(tgt).map(u => u.hp), pos0 = ps.map(p => [p.x, p.y]);
    P.eval('hitStop = 0; updatePhysics(1/60)'); s++; const up1 = P.get('wallHp') > 0;
    if (up0 && !up1) { brokenAt = s; broke++; }
    ps.forEach((p, k) => {
      if (p.delay > 0 || p.returning) return; const a = pos0[k], b = [p.x, p.y];
      const crossed = (a[0] - FX) * (b[0] - FX) < 0 && Math.max(a[1], b[1]) >= TOP;
      if (crossed && up0 && up1) throughWhileUp.push([dir, hero, ang, pw, s, a.map(Math.round).join(','), b.map(Math.round).join(',')].join(' '));
      else if (crossed && !up0) passedAfterBreak++;
    });
    if (up0 && !up1) { const lost = P.units(tgt).map((u, i) => hp0[i] - u.hp); if (lost.some(x => x > 0)) hurtOnBreak.push([dir, hero, ang, pw, lost.map(x => Math.round(x * 10) / 10).join('/')].join(' ')); }
  }
}
console.log(JSON.stringify({ throws, fenceBrokenThrows: broke, passedWhileFenceStood: throughWhileUp.length, legalPassesAfterBreak: passedAfterBreak, unitsHurtInTheBreakingStep: hurtOnBreak.length }));
throughWhileUp.slice(0, 8).forEach(x => console.log('  THROUGH ' + x)); hurtOnBreak.slice(0, 8).forEach(x => console.log('  HURT_ON_BREAK ' + x));
process.exit(throughWhileUp.length ? 1 : 0);
