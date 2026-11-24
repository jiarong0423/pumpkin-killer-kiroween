#!/usr/bin/env node
'use strict';
// Data only. Reads JSON shots on stdin, flies each through the REAL page physics. shot = { dir:'L2R'|'R2L', hero, angle, power, wind, weather:'clear|rain|snow|storm|fog', xs:[3 target x], prof:[3], shooter_x, wall }.
// Every unit stands on the ground line (the harness puts y at GROUND_Y). Output per shot: { hit: index of the unit that lost hp (-1 none, -3 fence), x, y (where the shot ended), dmg: damage dealt to that unit }.
const { loadPage } = require('./page_harness');
const WEATHER = { clear: { id: 'clear', attackMult: 1, moveMult: 1, windBonus: 0 }, rain: { id: 'rain', attackMult: 0.9, moveMult: 1, windBonus: 0 }, snow: { id: 'snow', attackMult: 1, moveMult: 0.5, windBonus: 0 }, storm: { id: 'storm', attackMult: 0.9, moveMult: 1, windBonus: 1.5 }, fog: { id: 'fog', attackMult: 1, moveMult: 1, windBonus: 0 } };
const shots = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const P = loadPage({ team: 3, seed: 3 });
const out = shots.map(s => {
  const sh = s.dir === 'L2R' ? 'left' : 'right', tg = s.dir === 'L2R' ? 'right' : 'left', team = s.dir === 'L2R' ? 'player' : 'ai';
  P.reset(); P.place(sh, [s.shooter_x, s.shooter_x + (s.dir === 'L2R' ? 130 : -130), s.shooter_x + (s.dir === 'L2R' ? 260 : -260)]); P.place(tg, s.xs);
  P.eval('weatherCache = { round: roundNum, scene: pickedScene, seed: matchSeed, w: ' + JSON.stringify(WEATHER[s.weather]) + ' }; wind = ' + s.wind + '; wallHp = ' + (s.wall ? 100 : 0) + '; turn = ' + JSON.stringify(team) + '; matchStarted = true; energy.player = 0; energy.ai = 0; ultArmed.player = false; ultArmed.ai = false; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(s.hero) + '; unitsOf(' + JSON.stringify(sh) + ').forEach(u => { u.profile = ' + JSON.stringify(s.hero) + '; }); setActiveUnit(' + JSON.stringify(sh) + ', unitsOf(' + JSON.stringify(sh) + ')[0]);');
  const t = P.units(tg); t.forEach((u, i) => { u.profile = s.prof[i]; u.hp = u.maxHp = 500; });
  P.eval('executeThrow(' + JSON.stringify(team) + ', ' + s.power + ', ' + s.angle + ')');
  const p = P.get('projectiles')[0]; if (!p) return { hit: -2 };
  let steps = 0; while (P.get('projectiles').length && steps < 900) { P.eval('hitStop = 0; updatePhysics(1/60)'); steps++; }
  const hit = t.findIndex(u => u.hp < 500); const wallHit = s.wall && P.get('wallHp') < 100;
  return { hit: wallHit && hit < 0 ? -3 : hit, x: p.x, y: p.y, dmg: hit >= 0 ? 500 - t[hit].hp : 0 };
});
console.log(JSON.stringify(out));
