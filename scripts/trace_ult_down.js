#!/usr/bin/env node
'use strict';
// DATA ONLY, REAL PAGE PHYSICS. Owner 2026-11-18: "both sides, every angle", "attacks after the wall is destroyed". The fence is destroyed (0 hp, held there), the ULTIMATE is armed for every role, both directions
// (left shoots right, right shoots left), every angle 5..85 step 5 and power 10..100 step 6, three formations including units standing at the very back and the very front of their zone; every physics step of every
// projectile is recorded against every living enemy unit (scripts/match_hit_hook.js, same records as trace_match_hits.js) for scripts/check_match_hits.py. Area effects and the boomerang return hit are flagged and left out by the judge.
// usage: node scripts/trace_ult_down.js --out logs_local/hit_trace/ult_down.jsonl [--plain (ordinary throws instead of the ultimate)] [--wall-one-hit]
const fs = require('fs'), path = require('path'), vm = require('vm');
const { loadPage } = require('./page_harness');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const PMAX = +arg('pmax', 115);
const OUT = arg('out', 'logs_local/hit_trace/ult_down.jsonl'), PLAIN = process.argv.includes('--plain'), ONE = process.argv.includes('--wall-one-hit');   // --wall-one-hit: the fence stands with ONE hit left and nothing holds it down, so the step in which it breaks is recorded as wall_break
fs.mkdirSync(path.dirname(OUT), { recursive: true }); const fd = fs.openSync(OUT, 'w');
const ROLES = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];
const FORM = { right: [[1240, 1370, 1500], [1500, 1650, 1810], [1330, 1330 + 130, 1330 + 260]], left: [[110, 240, 370], [380, 530, 680], [200, 330, 460]] };
const P = loadPage({ team: 3, seed: 21 }); vm.runInContext(require('./match_hit_hook'), P.context);
let shots = 0, recs = 0, cid = 0;
for (const dir of ['L2R', 'R2L']) for (const hero of ROLES) for (let fi = 0; fi < 3; fi++) for (let ang = 5; ang <= 85; ang += 5) for (let pw = 10; pw <= PMAX; pw += 6) {   // PMAX 115 since the owner raised MAX_POWER to 115 on 2026-11-19 (the grid stopped at 100 before: powers 101..115 were never traced)
  const shooter = dir === 'L2R' ? 'left' : 'right', tgt = dir === 'L2R' ? 'right' : 'left', team = dir === 'L2R' ? 'player' : 'ai';
  P.reset(); P.place(shooter, dir === 'L2R' ? [300, 450, 600] : [1600, 1450, 1300]); P.place(tgt, FORM[tgt][fi]);
  P.eval('wind = 0; wallHp = ' + (ONE ? 8 : 0) + '; turn = ' + JSON.stringify(team) + '; matchStarted = true; energy.player = 3; energy.ai = 3; ultUsed.player = 0; ultUsed.ai = 0; ultArmed.player = ' + (!PLAIN && dir === 'L2R') + '; ultArmed.ai = ' + (!PLAIN && dir === 'R2L') + '; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(hero) + '; unitsOf(' + JSON.stringify(shooter) + ').forEach(u => { u.profile = ' + JSON.stringify(hero) + '; }); setActiveUnit(' + JSON.stringify(shooter) + ', unitsOf(' + JSON.stringify(shooter) + ')[0]);');
  P.clearWeather(); P.units(tgt).forEach((u, i) => { u.hp = u.maxHp = 5000; u.profile = ['skeleton', 'bride', 'knight'][(i + fi) % 3]; });
  P.eval('window.__rec = []; window.__tick = 0; window.__mid = ' + (++cid) + '; window.__wallMode = ' + JSON.stringify(ONE ? 'natural' : 'down') + '');
  P.eval('executeThrow(' + JSON.stringify(team) + ', ' + pw + ', ' + ang + ')'); if (!P.get('projectiles').length) continue; shots++;
  let s = 0; while (P.get('projectiles').length && s < 1500) { P.eval('hitStop = 0; updatePhysics(1/60)'); s++; }
  for (const r of Array.from(vm.runInContext('window.__rec', P.context))) { r.dir = dir; r.size = 3; r.hero = hero; r.ang = ang; r.pw = pw; fs.writeSync(fd, JSON.stringify(r) + '\n'); recs++; }
}
fs.closeSync(fd); console.log(JSON.stringify({ shots, records: recs, out: OUT }));
