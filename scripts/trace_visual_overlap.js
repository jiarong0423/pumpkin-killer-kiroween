#!/usr/bin/env node
'use strict';
// DATA ONLY. For the oriented weapons (spear, flame) record every physics step near a target: shot centre, velocity, and whether the unit lost hp in that step.
// scripts/check_visual_overlap.py then compares what is DRAWN (the weapon picture, rotated along the flight and scaled as the page draws it) with the figure's visible pixels.
// usage: node scripts/trace_visual_overlap.js --out logs_local/hit_trace/visual.jsonl
const fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const OUT = (process.argv.indexOf('--out') > 0 ? process.argv[process.argv.indexOf('--out') + 1] : 'logs_local/hit_trace/visual.jsonl');
fs.mkdirSync(path.dirname(OUT), { recursive: true }); const fd = fs.openSync(OUT, 'w');
const HEROES = ['skeleton', 'reaper'], TARGETS = ['wizard', 'knight', 'skeleton', 'hunchback'];
let shots = 0, recs = 0;
for (const hero of HEROES) for (const tp of TARGETS) for (const x0 of [1300, 1500]) {
  const P = loadPage({ team: 1, seed: 21 });
  for (let ang = 5; ang <= 85; ang += 5) for (let pw = 20; pw <= 100; pw += 4) {
    P.reset(); P.place('left', [300]); P.place('right', [x0]);
    P.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; currentHero = ' + JSON.stringify(hero) + '; energy.player = 0; ultArmed.player = false;');
    P.clearWeather(); const u = P.units('right')[0]; u.hp = u.maxHp = 500; u.profile = tp;
    P.eval('executeThrow("player", ' + pw + ', ' + ang + ')'); const p = P.get('projectiles')[0]; if (!p) continue; shots++;
    let steps = 0, hp = u.hp;
    while (P.get('projectiles').length && steps < 900) {
      P.eval('hitStop = 0; updatePhysics(1/60)'); steps++;
      const dx = p.x - u.x, dy = p.y - u.y;
      const damaged = u.hp < hp; hp = u.hp;
      if ((Math.abs(dx) < 420 && dy > -420 && dy < 80) || damaged) { fs.writeSync(fd, JSON.stringify({ hero, tp, ang, pw, x0, step: steps, weapon: p.weapon, wl: p.wLen, wt: p.wThick, px: p.x, py: p.y, vx: p.vx, vy: p.vy, ux: u.x, uy: u.y, damaged: damaged ? 1 : 0 }) + '\n'); recs++; }
    }
  }
}
fs.closeSync(fd); console.log(JSON.stringify({ shots, records: recs, out: OUT }));
