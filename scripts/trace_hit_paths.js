#!/usr/bin/env node
'use strict';
// DATA ONLY, NO RENDERING. Traces every projectile of the REAL page physics (index.html in the vm, see page_harness.js) through a grid of
// range (power) x launch angle x formation (spacing, distance) x target classes x wind, in both directions (left team shoots right team, right shoots left), with the confounders removed:
// no fence, no shield, no ultimate, clear weather, one throw at a time, plain weapons only (the bride's wave and ultimates are area effects and are left out on purpose).
// Output (JSON lines): for every physics step in which a living enemy unit is within a coarse window of the shot, one record with the shot centre, the unit, its hp before and after the step.
// scripts/check_hit_trace.py then judges each record with the INDEPENDENT Python hit rule (scripts/hit_mask_py.py): damage where the rule says "not touched" is a false hit; a touch without damage is a miss that should have hit.
// usage: node scripts/trace_hit_paths.js --out logs_local/hit_trace/trace_pilot.jsonl [--angle-step 10] [--power-step 10] [--from N --combos M (combos N+1..M)] [--heroes a,b] [--seed 1] [--no-nearmiss (the page's team near-miss compensation switched off: isolates the direct-hit path)]
const fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const FROM = +arg('from', 0), NONEAR = process.argv.includes('--no-nearmiss');
const OUT = arg('out', 'logs_local/hit_trace/trace_pilot.jsonl'), ASTEP = +arg('angle-step', 10), PSTEP = +arg('power-step', 10), MAXC = +arg('combos', 1e9), SEED = +arg('seed', 1);
const HEROES = (arg('heroes', 'skeleton,bat,knight,hag,hunchback,reaper,wizard')).split(',');
const SETS = [['skeleton', 'wizard', 'knight'], ['bat', 'hag', 'bride'], ['reaper', 'hunchback', 'skeleton']];
// LEGAL formations only (the page keeps units inside their own zone: right 1240..1810, left 110..680; a unit placed outside is moved by the first knockback, which would look like damage without contact)
const X0S = { right: [1240, 1330, 1450, 1600], left: [110, 170, 230, 280] }, SPACING = [125, 150, 200], WINDS = [0, 4, -4];
const ZONE = { right: [1240, 1810], left: [110, 680] };
fs.mkdirSync(path.dirname(OUT), { recursive: true });
const fd = fs.openSync(OUT, 'w');
const wr = o => fs.writeSync(fd, JSON.stringify(o) + '\n');
let combos = 0, shots = 0, records = 0, damagedShots = 0;
const t0 = Date.now();
outer:
for (const dir of ['L2R', 'R2L']) for (const hero of HEROES) for (const x0 of X0S[dir === 'L2R' ? 'right' : 'left']) for (const sp of SPACING) for (let si = 0; si < SETS.length; si++) {
  if (combos >= MAXC) break outer;
  combos++;
  if (combos <= FROM) continue;
  const P = loadPage({ team: 3, seed: SEED + combos, mutate: NONEAR ? [['function cbNearMiss(p, bouncy) {', 'function cbNearMiss(p, bouncy) { return;']] : undefined });
  const shooterTeam = dir === 'L2R' ? 'player' : 'ai', targetSide = dir === 'L2R' ? 'right' : 'left', shooterSide = dir === 'L2R' ? 'left' : 'right';
  let xs = [x0, x0 + sp, x0 + 2 * sp]; const zone = ZONE[targetSide]; const over = xs[2] - zone[1]; if (over > 0) xs = xs.map(x => x - over);   // the whole formation moves back inside the zone, spacing kept
  const projHitRadius = P.get('projHitRadius');
  let k = 0;
  for (let ang = 5; ang <= 85; ang += ASTEP) for (let pw = 10; pw <= 100; pw += PSTEP) {
    k++;
    const wind = WINDS[k % WINDS.length];
    P.reset();
    P.place(shooterSide, dir === 'L2R' ? [300, 450, 600] : [1600, 1450, 1300]); P.place(targetSide, xs);
    P.eval('wind = ' + wind + '; wallHp = 0; turn = ' + JSON.stringify(shooterTeam) + '; matchStarted = true; energy.player = 0; energy.ai = 0; ultArmed.player = false; ultArmed.ai = false; shields.player.active = false; shields.ai.active = false;');
    P.eval('currentHero = ' + JSON.stringify(hero) + '; unitsOf(' + JSON.stringify(shooterSide) + ').forEach(u => { u.profile = ' + JSON.stringify(hero) + '; });');
    P.eval('setActiveUnit(' + JSON.stringify(shooterSide) + ', unitsOf(' + JSON.stringify(shooterSide) + ')[0])');
    const targets = P.units(targetSide); targets.forEach((u, i) => { u.profile = SETS[si][i]; });
    P.eval('wind = ' + wind);
    P.eval('executeThrow(' + JSON.stringify(shooterTeam) + ', ' + pw + ', ' + ang + ')');
    const list = P.get('projectiles'); const p = list[0]; if (!p) continue;
    const hitR = projHitRadius(p), weapon = p.weapon;
    let prev = targets.map(u => u.hp), prevPos = targets.map(u => [u.x, u.y]), steps = 0, shotDamaged = false;
    while (P.get('projectiles').length && steps < 900) {
      const before = prevPos; P.eval('hitStop = 0; updatePhysics(1/60)'); steps++;
      const now = targets.map(u => u.hp);
      targets.forEach((u, i) => {
        if (prev[i] <= 0) return;
        const ux0 = before[i][0], uy0 = before[i][1];   // the unit where it stood when the step began (a knockback inside the step moves it afterwards)
        const dx = p.x - ux0, dy = p.y - uy0;
        const near = Math.abs(dx) <= 70 + hitR + 40 && dy >= -190 - hitR - 40 && dy <= hitR + 40;
        const damaged = now[i] < prev[i];
        if (near || damaged) { wr({ c: combos, dir, hero, weapon, ang, pw, wind, step: steps, hitR: hitR, i, prof: u.profile, side: targetSide, px: p.x, py: p.y, ux: ux0, uy: uy0, hp0: prev[i], hp1: now[i], cool: p.hitCool > 0 ? 1 : 0, pierced: (p.pierced && p.pierced.has && p.pierced.has(u)) ? 1 : 0 }); records++; }
        if (damaged) shotDamaged = true;
      });
      prev = now; prevPos = targets.map(u => [u.x, u.y]);
    }
    shots++; if (shotDamaged) damagedShots++;
  }
}
fs.closeSync(fd);
console.log(JSON.stringify({ combos, shots, damagedShots, records, seconds: Math.round((Date.now() - t0) / 100) / 10, out: OUT }));
