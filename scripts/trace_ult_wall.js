#!/usr/bin/env node
'use strict';
// DATA ONLY: an ultimate that is stopped by the central fence must not hurt anybody on the far side of it (owner 2026-11-18: "ultimates must not go through the wall").
// Real page physics, fence ON, the ultimate armed for every role, both directions, a grid of power x angle; targets stand behind the fence. A violation = the fence took the hit (wallHp dropped) AND an enemy unit lost hp.
const { loadPage } = require('./page_harness');
const P = loadPage({ team: 3, seed: 11 });
const ROLES = ['skeleton', 'wizard', 'bat', 'reaper', 'bride', 'hunchback', 'hag'];
let shots = 0, wallHits = 0; const bad = [];
for (const dir of ['L2R', 'R2L']) for (const hero of ROLES) for (let ang = 20; ang <= 70; ang += 5) for (let pw = 20; pw <= 70; pw += 2) {
  P.reset(); const shooter = dir === 'L2R' ? 'left' : 'right', tgt = dir === 'L2R' ? 'right' : 'left';
  P.place('left', [300, 450, 600]); P.place('right', [1250, 1400, 1550]);
  P.eval('wind = 0; wallHp = 100; turn = ' + JSON.stringify(dir === 'L2R' ? 'player' : 'ai') + '; matchStarted = true; energy.player = 3; energy.ai = 3; ultUsed.player = 0; ultUsed.ai = 0; ultArmed.player = ' + (dir === 'L2R') + '; ultArmed.ai = ' + (dir === 'R2L') + '; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(hero) + '; unitsOf(' + JSON.stringify(shooter) + ').forEach(u => { u.profile = ' + JSON.stringify(hero) + '; }); setActiveUnit(' + JSON.stringify(shooter) + ', unitsOf(' + JSON.stringify(shooter) + ')[0]);');
  P.clearWeather(); P.units(tgt).forEach(u => { u.hp = u.maxHp = 500; });
  P.eval('executeThrow(' + JSON.stringify(dir === 'L2R' ? 'player' : 'ai') + ', ' + pw + ', ' + ang + ')');
  const p = P.get('projectiles')[0]; if (!p) continue; shots++;
  let s = 0; while (P.get('projectiles').length && s < 1200) { P.eval('hitStop = 0; updatePhysics(1/60)'); s++; }
  if (P.get('wallHp') < 100) { wallHits++; const lost = P.units(tgt).map(u => 500 - u.hp); if (lost.some(x => x > 0)) bad.push([dir, hero, ang, pw, lost.map(x => Math.round(x * 10) / 10).join('/')].join(' ')); }
}
console.log(JSON.stringify({ ultimateShots: shots, stoppedByTheFence: wallHits, hurtSomebodyBehindIt: bad.length }));
const by = {}; bad.forEach(b => { const h = b.split(" ")[1]; by[h] = (by[h] || 0) + 1; }); console.log(JSON.stringify(by)); bad.filter(b => !/skeleton|reaper/.test(b)).slice(0, 10).forEach(b => console.log("  " + b));
process.exit(bad.length ? 1 : 0);
