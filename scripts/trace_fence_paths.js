#!/usr/bin/env node
'use strict';
// DATA ONLY: does any shot fly THROUGH the central fence? Real page physics, the fence ON (wallHp 100), no shield / ultimate / weather, a grid of power x angle x weapon x wind, both directions.
// A shot "goes through" when the straight segment of a physics step touches the fence rectangle (x within FENCE_X +- FENCE_W/2, y below GROUND_Y - FENCE_H) and the shot is on the FAR side of the fence after that step (a bounce back to its own side is allowed).
const { loadPage } = require('./page_harness');
const P = loadPage({ team: 3, seed: 9 });
const FX = P.get('FENCE_X'), FW = P.get('FENCE_W'), FH = P.get('FENCE_H'), GY = P.get('GROUND_Y');
const x0 = FX - FW / 2, x1 = FX + FW / 2, top = GY - FH;
const segHitsRect = (ax, ay, bx, by) => { for (let k = 0; k <= 24; k++) { const f = k / 24, x = ax + (bx - ax) * f, y = ay + (by - ay) * f; if (x >= x0 && x <= x1 && y >= top) return true; } return false; };
const HEROES = ['skeleton', 'bat', 'knight', 'hag', 'hunchback', 'reaper', 'wizard', 'bride'];
const ULT = process.argv.includes('--ult');   // also arm the ultimate (energy 3, armed) for every role
let shots = 0, crossed = 0, stopped = 0; const bad = [];
for (const dir of ['L2R', 'R2L']) for (const hero of HEROES) for (let ang = 5; ang <= 85; ang += 5) for (let pw = 10; pw <= 115; pw += 5) for (const wind of [0, 4, -4]) {
  P.reset(); const shooter = dir === 'L2R' ? 'left' : 'right', tgt = dir === 'L2R' ? 'right' : 'left';
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.eval('wind = ' + wind + '; wallHp = 100; turn = ' + JSON.stringify(dir === 'L2R' ? 'player' : 'ai') + '; matchStarted = true; energy.player = ' + (ULT ? 3 : 0) + '; energy.ai = ' + (ULT ? 3 : 0) + '; ultUsed.player = 0; ultUsed.ai = 0; ultArmed.player = ' + (ULT && dir === 'L2R') + '; ultArmed.ai = ' + (ULT && dir === 'R2L') + '; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(hero) + '; unitsOf(' + JSON.stringify(shooter) + ').forEach(u => { u.profile = ' + JSON.stringify(hero) + '; }); setActiveUnit(' + JSON.stringify(shooter) + ', unitsOf(' + JSON.stringify(shooter) + ')[0]);');
  P.units(tgt).forEach(u => { u.hp = u.maxHp = 500; });
  P.eval('executeThrow(' + JSON.stringify(dir === 'L2R' ? 'player' : 'ai') + ', ' + pw + ', ' + ang + ')');
  const p = P.get('projectiles')[0]; if (!p) continue; shots++;
  let prevx = p.x, prevy = p.y, steps = 0, crossedHere = false, wall0 = P.get('wallHp');
  while (P.get('projectiles').length && steps < 900) {
    P.eval('hitStop = 0; updatePhysics(1/60)'); steps++;
    const nx = p.x, ny = p.y;
    if (!P.get('projectiles').length) break;                 // it landed or hit something this step: handled below by the end state
    if (segHitsRect(prevx, prevy, nx, ny)) { const beyond = dir === 'L2R' ? nx > x1 : nx < x0; if (beyond) { crossedHere = true; break; } }   // a step that touched the fence rectangle and ended on the FAR side of it (a bounce back to the own side is fine)
    prevx = nx; prevy = ny;
  }
  if (crossedHere) { crossed++; bad.push([dir, hero, ang, pw, wind, Math.round(prevx), Math.round(prevy), Math.round(p.x), Math.round(p.y)].join(' ')); }
}
console.log(JSON.stringify({ shots, shotsThatKeptFlyingAfterTouchingTheFence: crossed }));
bad.slice(0, 12).forEach(b => console.log('  ' + b));
process.exit(crossed ? 1 : 0);
