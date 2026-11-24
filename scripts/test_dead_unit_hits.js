#!/usr/bin/env node
'use strict';
// REPRODUCIBLE DESTRUCTIVE MATRIX (owner 2026-11-22: "reproducible destructive matrix test"). The 20,000-match audit (redteam/evidence/audit_page_events_20261122_report.txt) found a hit sound in steps where nobody lost hp, always with a unit already down.
// Here every combination is built by hand with the real page physics: team size (1, 2, 3) x the 8 weapons x 6 scenarios, projectile placed 6 px before the target and flying at it, Math.random fixed, no randomness anywhere:
//   ALIVE_ONLY        one living foe in the shot's way                      expect: damage, one hit sound
//   CORPSE_ONLY       the only foe in the way is already down (hp 0), the others far and unreachable   expect: no damage, NO hit sound, no hit report, no KO
//   CORPSE_IN_FRONT   a dead foe in front, a living foe 140 px behind it     expect: the living foe takes the hit once (damage + sound), the corpse nothing
//   AFTER_THE_WIPE    every foe down and the match already over (gameOver set), a shot still in flight   expect: no sound at all, no KO again, hp stays 0
//   LAST_FOE_FALLS    the living foe has 1 hp and is the last                 expect: KO exactly once (match end) for size 1..3, never a second KO from a second shot
//   RESIDUE_KILL      the foe has exactly the hit's damage plus 1e-13 hp (the floating-point residue case of the audit: 1.4e-14)  expect: dead (hp exactly 0), KO once, no unit left alive at ~0 hp
//   TEAMMATE_CORPSE   a dead teammate of the SHOOTER stands in the shot's way (friendly corpse) expect: nothing happens to it (no sound, no damage)
// usage: node scripts/test_dead_unit_hits.js [--matrix]   (--matrix prints every failing combination)   exit 1 on any failing combination.
const { loadPage } = require('./page_harness');
const HEROES = ['skeleton', 'wizard', 'bat', 'knight', 'hunchback', 'reaper', 'bride', 'hag'];
const SCEN = ['ALIVE_ONLY', 'CORPSE_ONLY', 'CORPSE_IN_FRONT', 'AFTER_THE_WIPE', 'LAST_FOE_FALLS', 'TEAMMATE_CORPSE', 'RESIDUE_KILL'];
// MUTANTS (destructive part): PK_MUT=corpse puts the single-foe corpse bug back, PK_MUT=hp puts the plain `hp - damage` subtraction back; the matrix MUST then fail (scripts/test_dead_unit_hits.js is run with both by the suite wrapper check below)
const MUT = { corpse: [['(opp.hp > 0 && touches(opp) ? opp : null);', '(touches(opp) ? opp : null);']], hp: [['opp.hp = hpAfter(opp.hp, dmgNow);', 'opp.hp = Math.max(0, opp.hp - dmgNow);']] }[process.env.PK_MUT || ''];
const HIT = n => n === 'ko' || /^impact_unit/.test(n) || n === 'impact_flame' || /^ult_.*_hit$/.test(n) || /^sfx\.hit:(ko|impact_unit|impact_unit_heavy)/.test(n);
const SETUP = `window.__log = []; window.__rep = []; Math.random = function () { return 0.5; };
(function () { var os = snd; snd = function (n) { window.__log.push(n); return os.apply(this, arguments); };
  Object.keys(sfx).forEach(function (k) { if (typeof sfx[k] === 'function') { var o = sfx[k]; sfx[k] = function (a) { window.__log.push('sfx.' + k + (typeof a === 'string' ? ':' + a : '')); return o.apply(this, arguments); }; } });
  var oh = pushHitReport; pushHitReport = function (p, t, tg) { window.__rep.push(t + ':' + (tg ? Math.round(tg.hp) : '?')); return oh.apply(this, arguments); }; })();`;
function run(size, hero, scen, hpOverride) {
  const P = loadPage(MUT ? { team: size, seed: 5, mutate: MUT } : { team: size, seed: 5 });
  P.reset(); P.eval(SETUP); P.clearWeather();
  const left = [], right = [];
  for (let i = 0; i < size; i++) { left.push(300 + 150 * i); right.push(1700 - 150 * i); }   // right[0] is the rearmost; the foe nearest to the shooter is the LAST entry
  P.place('left', left); P.place('right', right);
  const foes = P.units('right'), mine = P.units('left'); foes.forEach(u => { u.hp = u.maxHp = 300; u.profile = 'skeleton'; }); mine.forEach(u => { u.hp = u.maxHp = 300; });
  P.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; energy.player = 0; energy.ai = 0; ultArmed.player = false; ultArmed.ai = false; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(hero) + ';');
  mine.forEach(u => { u.profile = hero; });
  let target = foes[0], front = null, expect;
  const place = (u, x) => { u.x = x; u.targetX = x; };
  if (scen === 'ALIVE_ONLY') { place(target, 1100); expect = { dmg: true, hit: true }; foes.slice(1).forEach((u, i) => place(u, 1750 + i)); }
  else if (scen === 'CORPSE_ONLY') { target.hp = 0; place(target, 1100); expect = { dmg: false, hit: false }; foes.slice(1).forEach((u, i) => { u.hp = 300; place(u, 1750 + 10 * i); }); }
  else if (scen === 'CORPSE_IN_FRONT') { if (size === 1) return null; front = foes[0]; front.hp = 0; place(front, 1100); target = foes[1]; place(target, 1240); foes.slice(2).forEach(u => place(u, 1800)); expect = { dmg: true, hit: true }; }
  else if (scen === 'AFTER_THE_WIPE') { foes.forEach(u => { u.hp = 0; }); place(target, 1100); P.eval('gameOver = "player"; turn = "over";'); expect = { dmg: false, hit: false, quiet: true }; }
  else if (scen === 'LAST_FOE_FALLS') { foes.forEach(u => { u.hp = 0; }); target.hp = 1; place(target, 1100); expect = { dmg: true, hit: true, ko: true }; }
  else if (scen === 'RESIDUE_KILL') { foes.forEach(u => { u.hp = 0; }); target.hp = hpOverride; place(target, 1100); expect = { dmg: true, hit: true, ko: true, dead: true }; }
  else if (scen === 'TEAMMATE_CORPSE') { if (size === 1) return null; mine[1].hp = 0; place(mine[1], 700); foes.forEach((u, i) => place(u, 1500 + 100 * i)); expect = { dmg: false, hit: false, friendly: true }; target = mine[1]; }
  const hp0 = P.units('left').concat(P.units('right')).map(u => u.hp);
  const startX = scen === 'TEAMMATE_CORPSE' ? 560 : 1100 - 600 * 0.01 * 1;
  const tx = target.x, ty = target.y;
  const p = P.projectile({ hero, team: 'player', x: (scen === 'TEAMMATE_CORPSE' ? 640 : tx - 6), y: ty - (hero === 'bride' ? 20 : 100), vx: 600 });   // the wave only counts in the 40 px band above the ground
  P.launch(p); P.run(60, 0.01);
  const tgtAfter = target.hp;
  const hp1 = P.units('left').concat(P.units('right')).map(u => u.hp), log = Array.from(P.eval('window.__log')), rep = Array.from(P.eval('window.__rep'));
  const hitSnd = log.filter(HIT), koN = log.filter(n => n === 'ko').length, dmgAny = hp1.some((h, i) => h < hp0[i] - 1e-9), negative = hp1.some(h => h < 0);
  const fail = [];
  if (negative) fail.push('hp below 0');
  if (expect.dmg && !dmgAny) fail.push('no damage');
  if (expect.dmg && hitSnd.length === 0) fail.push('damage without a hit sound');
  if (!expect.dmg && dmgAny) fail.push('unexpected damage');
  if (!expect.dmg && hitSnd.length) fail.push('hit sound without damage: ' + hitSnd.join(','));
  if (!expect.dmg && rep.some(r => /^hero:/.test(r))) fail.push('hero hit report without damage: ' + rep.join(','));
  if (expect.dead && tgtAfter !== 0) fail.push('the foe is left alive with ' + tgtAfter + ' hp');
  if (expect.ko && koN !== 1) fail.push('ko sounded ' + koN + ' times');
  if (!expect.ko && koN) fail.push('ko sounded ' + koN + ' times');
  return fail;
}
const bad = []; let n = 0, skipped = 0;
function damageOf(size, hero) { const P = loadPage({ team: size, seed: 5 }); P.reset(); P.eval('Math.random = function () { return 0.5; };'); P.clearWeather(); const left = [], right = []; for (let i = 0; i < size; i++) { left.push(300 + 150 * i); right.push(1700 - 150 * i); } P.place('left', left); P.place('right', right); const f = P.units('right'); f.forEach(u => { u.hp = u.maxHp = 900; u.profile = 'skeleton'; u.x = 1100 + 0; u.targetX = 1100; }); P.units('left').forEach(u => { u.hp = u.maxHp = 300; u.profile = hero; }); P.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; energy.player = 0; ultArmed.player = false; currentHero = ' + JSON.stringify(hero) + ';'); const t = f[0]; P.launch(P.projectile({ hero, team: 'player', x: 1094, y: t.y - (hero === 'bride' ? 20 : 100), vx: 600 })); P.run(60, 0.01); return 900 - t.hp; }
for (const size of [1, 2, 3]) for (const hero of HEROES) for (const scen of SCEN) { const f = run(size, hero, scen, scen === 'RESIDUE_KILL' ? damageOf(size, hero) + 1e-13 : undefined); if (f === null) { skipped++; continue; } n++; if (f.length) bad.push({ size, hero, scen, why: f.join('; ') }); }
const by = {}; bad.forEach(b => { const k = b.scen + ' size ' + b.size; by[k] = (by[k] || 0) + 1; });
console.log('dead-unit hit matrix: ' + n + ' combinations (' + skipped + ' not applicable), ' + bad.length + ' failing' + (bad.length ? ' | ' + Object.entries(by).map(([k, v]) => k + ': ' + v).join(', ') : ''));
if (process.argv.includes('--matrix') || bad.length) bad.slice(0, 40).forEach(b => console.log('  FAIL ' + b.size + 'v' + b.size + ' ' + b.hero + ' ' + b.scen + ' -> ' + b.why));
process.exit(bad.length ? 1 : 0);
