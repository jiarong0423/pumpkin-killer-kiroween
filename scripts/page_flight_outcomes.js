#!/usr/bin/env node
'use strict';
// Data only: reads JSON shots on stdin, flies each through the REAL page physics (page_harness vm), prints the outcome per shot.
// shot = { hero, angle, power, shooter_x, xs:[3 target x], prof:[3 target classes] }  (left team shoots right team, no wind, no fence, no ultimate, plain weapon)
const { loadPage } = require('./page_harness');
const shots = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const P = loadPage({ team: 3, seed: 3 });
const out = shots.map(s => {
  P.reset(); P.place('left', [s.shooter_x, s.shooter_x + 150, s.shooter_x + 300]); P.place('right', s.xs);
  P.eval('wind = 0; wallHp = ' + (s.wall ? 100 : 0) + '; turn = "player"; matchStarted = true; energy.player = 0; energy.ai = 0; ultArmed.player = false; ultArmed.ai = false; shields.player.active = false; shields.ai.active = false; currentHero = ' + JSON.stringify(s.hero) + '; unitsOf("left").forEach(u => { u.profile = ' + JSON.stringify(s.hero) + '; }); setActiveUnit("left", unitsOf("left")[0]);');
  const t = P.units('right'); t.forEach((u, i) => { u.profile = s.prof[i]; u.hp = u.maxHp = 500; });
  if (s.dead_front) t[0].hp = 0;   // the nearest enemy is already dead: the shot must go on to the next one
  P.eval('executeThrow("player", ' + s.power + ', ' + s.angle + ')');
  const p = P.get('projectiles')[0]; if (!p) return { hit: -2 };
  let steps = 0; while (P.get('projectiles').length && steps < 900) { P.eval('hitStop = 0; updatePhysics(1/60)'); steps++; }
  const hit = t.findIndex((u, i) => u.hp < 500 && !(s.dead_front && i === 0));
  const wallHit = s.wall && P.get('wallHp') < 100;
  return { hit: wallHit && hit < 0 ? -3 : hit, x: p.x, y: p.y, weapon: p.weapon };
});
console.log(JSON.stringify(out));
