#!/usr/bin/env node
'use strict';
// DATA ONLY: every projectile of every throw (also all members of a volley: triple javelin, shuriken rain, three flames, double shot, boomerang return) against the central fence, real page physics, fence ON.
// Violation: a projectile whose step touched the fence rectangle and which is on the FAR side of the fence after the step (it flew through; a bounce back to the own side is fine).
// usage: node scripts/trace_fence_all.js [--ult]   (--ult arms the ultimate of the role)
const { loadPage } = require('./page_harness');
const P = loadPage({ team: 3, seed: 13 });
const FX = P.get('FENCE_X'), FW = P.get('FENCE_W'), FH = P.get('FENCE_H'), GY = P.get('GROUND_Y');
const x0 = FX - FW / 2, x1 = FX + FW / 2, top = GY - FH;
const ULT = process.argv.includes('--ult');
const inRect = (x, y) => x >= x0 && x <= x1 && y >= top;
const seg = (ax, ay, bx, by) => { const n = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / 2)); for (let k = 0; k <= n; k++) { const f = k / n; if (inRect(ax + (bx - ax) * f, ay + (by - ay) * f)) return true; } return false; };
const ROLES = ['skeleton', 'bat', 'knight', 'hag', 'hunchback', 'reaper', 'wizard', 'bride'];
let shots = 0, projectilesSeen = 0; const bad = []; const byRole = {};
for (const dir of ['L2R', 'R2L']) for (const hero of ROLES) for (let ang = 15; ang <= 80; ang += 5) for (let pw = 15; pw <= 115; pw += 3) {
  P.reset(); const shooter = dir === 'L2R' ? 'left' : 'right', team = dir === 'L2R' ? 'player' : 'ai';
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.eval('wind = 0; wallHp = 100; turn = ' + JSON.stringify(team) + '; matchStarted = true; energy.player = ' + (ULT ? 3 : 0) + '; energy.ai = ' + (ULT ? 3 : 0) + '; ultUsed.player = 0; ultUsed.ai = 0; ultArmed.player = ' + (ULT && dir === 'L2R') + '; ultArmed.ai = ' + (ULT && dir === 'R2L') + '; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(hero) + '; unitsOf(' + JSON.stringify(shooter) + ').forEach(u => { u.profile = ' + JSON.stringify(hero) + '; }); setActiveUnit(' + JSON.stringify(shooter) + ', unitsOf(' + JSON.stringify(shooter) + ')[0]);');
  P.clearWeather(); P.units(dir === 'L2R' ? 'right' : 'left').forEach(u => { u.hp = u.maxHp = 500; });
  P.eval('executeThrow(' + JSON.stringify(team) + ', ' + pw + ', ' + ang + ')'); shots++;
  const prev = new Map(); let steps = 0;
  const flightDir = dir === 'L2R' ? 1 : -1;
  while (P.get('projectiles').length && steps < 1400) {
    const list = Array.from(P.get('projectiles'));
    for (const p of list) if (!prev.has(p)) { prev.set(p, [p.x, p.y]); projectilesSeen++; }
    P.eval('hitStop = 0; updatePhysics(1/60)'); steps++;
    const after = new Set(Array.from(P.get('projectiles')));
    for (const p of list) {
      if (!after.has(p)) continue;                              // resolved in this step
      const [ax, ay] = prev.get(p); const bx = p.x, by = p.y;
      if (!(p.delay > 0) && seg(ax, ay, bx, by) && (flightDir > 0 ? bx > x1 : bx < x0)) { const k = hero + (p.ultThrow ? '(ult)' : ''); byRole[k] = (byRole[k] || 0) + 1; if (bad.length < 40) bad.push([dir, hero, ang, pw, 'weapon ' + p.weapon, 'ult ' + !!p.ultThrow, 'prev', Math.round(ax), Math.round(ay), 'now', Math.round(bx), Math.round(by)].join(' ')); }
      prev.set(p, [bx, by]);
    }
  }
}
console.log(JSON.stringify({ throws: shots, projectiles: projectilesSeen, flewThroughTheFence: Object.values(byRole).reduce((a, b) => a + b, 0), byRole }));
bad.slice(0, 10).forEach(b => console.log('  ' + b));
process.exit(bad.length ? 1 : 0);
