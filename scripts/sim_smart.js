#!/usr/bin/env node
'use strict';
/*
 * Seeded Smart-seat measurement. It deliberately contains no model call: each
 * policy selects one locally computed candidate against the Normal heuristic.
 */
const ClassStats = require('../js/class_stats.js');
const SmartCandidates = require('../js/smart_candidates.js');
const Sim = require('./sim_balance.js');

const MATCHES = 2000;
const POWER_MIN = 30;
const POWER_MAX = 115;
const ANGLE = 54;
const MAX_ROUNDS = 40;

function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }
function normalAim(me, foe, wind) {
  const gap = Math.max(50, Math.abs(foe.x - me.x) - 58);
  let power = 2.32 * Math.sqrt(gap) + (wind > 0 ? 4 * 84 / 72 : 4 * 56 / 72) * Math.abs(wind);
  return { angle: ANGLE, power: Math.round(clamp(power, POWER_MIN, POWER_MAX)) };
}
function unit(key, side, x) { return { key, side, dir: side === 'left' ? 1 : -1, x, hp: ClassStats.CLASSES[key].hp }; }
function candidateSet(me, foe, wind, normal) {
  const cls = ClassStats.CLASSES[me.key];
  const startX = me.x + me.dir * (cls.launch || { fwd: 58 }).fwd;
  return SmartCandidates.build({
    own_hero_id: me.key, own_position: me.x, enemy_position: foe.x, enemy_hp: foe.hp,
    wind, weather: 'clear', fence_hp: 100, round_number: 1, start_x: startX, start_y: 750,
    direction: me.dir, normal_aim: normal, own_skills: {}, ultimate_available: false, recent_enemy_hits: 0,
    simulateLandingX: (power, ignoredX, ignoredY, ignoredDir, angle, seenWind) =>
      Sim.simulateLandingX(cls, { x: me.x, dir: me.dir }, power, angle, seenWind)
  });
}
function pick(policy, choices, random) {
  if (policy === 'seeded_random') return choices[Math.floor(random() * choices.length)];
  if (policy === 'lowest_predicted_distance') return choices.reduce((best, item) => item.predicted_distance_px < best.predicted_distance_px ? item : best, choices[0]);
  return choices[0];
}
function shot(me, foe, wind, policy, random) {
  const normal = normalAim(me, foe, wind);
  const selected = policy ? pick(policy, candidateSet(me, foe, wind, normal), random) : { kind: 'normal', aim: normal };
  // Defend and move are unavailable in this two-unit measurement; any such
  // candidate therefore resolves to the Normal throw, as the page does when
  // its action cannot be applied.
  const aim = selected.aim || normal;
  const cls = ClassStats.CLASSES[me.key];
  const landing = Sim.simulateLandingX(cls, { x: me.x, dir: me.dir }, aim.power, aim.angle, wind);
  const hit = Math.abs(landing - foe.x) <= cls.hitHalfWidth;
  if (hit) foe.hp -= cls.dmg;
  return hit;
}
function play(policy, seed) {
  const random = Sim.mulberry32(seed);
  const heroes = ClassStats.CLASS_KEYS;
  const left = unit(heroes[Math.floor(random() * heroes.length)], 'left', 240 + Math.floor(random() * 441));
  const right = unit(heroes[Math.floor(random() * heroes.length)], 'right', 1240 + Math.floor(random() * 441));
  let smartHits = 0, smartThrows = 0;
  for (let round = 0; round < MAX_ROUNDS && left.hp > 0 && right.hp > 0; round++) {
    const wind = Sim.rollWind(random);
    shot(left, right, wind, null, random);
    if (right.hp <= 0) return { winner: 'normal', smartHits, smartThrows };
    smartThrows++;
    if (shot(right, left, wind, policy, random)) smartHits++;
    if (left.hp <= 0) return { winner: 'smart', smartHits, smartThrows };
  }
  return { winner: left.hp === right.hp ? 'draw' : left.hp > right.hp ? 'normal' : 'smart', smartHits, smartThrows };
}
function measure(policy) {
  let wins = 0, hits = 0, throws = 0;
  for (let match = 0; match < MATCHES; match++) {
    const result = play(policy, Sim.mixSeed(220, 0, 1, match));
    if (result.winner === 'smart') wins++;
    else if (result.winner === 'draw') wins += 0.5;
    hits += result.smartHits;
    throws += result.smartThrows;
  }
  return { policy, matches: MATCHES, win_rate: wins / MATCHES, hit_rate: throws ? hits / throws : 0 };
}

const report = ['always_1', 'lowest_predicted_distance', 'seeded_random'].map(measure);
const normal = measure(null);
console.log('Smart candidate simulation: 2000 seeded matches per policy against Normal');
for (const row of report) console.log(`${row.policy}: win ${(row.win_rate * 100).toFixed(2)}% hit ${(row.hit_rate * 100).toFixed(2)}%`);
console.log(`normal: win ${(normal.win_rate * 100).toFixed(2)}% hit ${(normal.hit_rate * 100).toFixed(2)}%`);
const delta = Math.abs(report[0].win_rate - normal.win_rate) * 100;
console.log(`always_1 vs Normal delta: ${delta.toFixed(2)} points`);
if (delta > 2) process.exitCode = 1;
