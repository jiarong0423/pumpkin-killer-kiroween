#!/usr/bin/env node
'use strict';
const assert = require('assert');
const SmartCandidates = require('../js/smart_candidates.js');

function landing(power, startX, startY, direction, angle, wind) {
  // A deterministic stand-in for the page integrator. Its signature matches
  // simulateLandingX so this test proves the builder passes only public values.
  return startX + direction * (power * 18 + (angle - 54) * 4 + wind * 12);
}

function base(overrides) {
  return Object.assign({
    own_hero_id: 'skeleton', own_position: 1560, enemy_position: 420,
    enemy_hp: 90, wind: 1.2, weather: 'clear', fence_hp: 100, round_number: 4,
    start_x: 1502, start_y: 750, direction: -1,
    normal_aim: { angle: 54, power: 63 }, own_skills: { heavy: 1 },
    ultimate_available: false, recent_enemy_hits: 0, simulateLandingX: landing
  }, overrides || {});
}

const input = base();
const first = SmartCandidates.build(input);
const second = SmartCandidates.build(input);
assert.deepStrictEqual(first, second, 'candidate generation is deterministic');
assert(first.length >= 3 && first.length <= 6, 'there are three to six choices');
assert.deepStrictEqual(first.map(item => item.id), first.map((_, index) => index + 1), 'ids are consecutive after sorting');
assert.strictEqual(first[0].kind, 'normal', 'candidate 1 is always the built-in Normal aim (the fallback contract)');
for (let index = 2; index < first.length; index++) {
  assert(first[index - 1].predicted_distance_px <= first[index].predicted_distance_px, 'candidates after the first are sorted by predicted distance');
}
for (const candidate of first) {
  assert.deepStrictEqual(Object.keys(candidate).sort(), (candidate.aim ? ['aim', 'id', 'kind', 'predicted_distance_px'] : ['id', 'kind', 'predicted_distance_px']),
    'candidate contains only the gateway contract fields');
  assert(!JSON.stringify(candidate).match(/slot|pending|item/i), 'candidate never exposes private slot or pending data');
}

const defended = SmartCandidates.build(base({ own_hero_id: 'knight', recent_enemy_hits: 2 }));
assert(defended.some(candidate => candidate.kind === 'defend'), 'the knight can defend after two enemy hits in two rounds');
const notDefended = SmartCandidates.build(base({ own_hero_id: 'knight', recent_enemy_hits: 1 }));
assert(!notDefended.some(candidate => candidate.kind === 'defend'), 'one recent enemy hit does not create a defend choice');
const otherDefended = SmartCandidates.build(base({ own_hero_id: 'wizard', recent_enemy_hits: 3 }));
assert(!otherDefended.some(candidate => candidate.kind === 'defend'), 'only the floating-shield hero receives defend');

const charged = SmartCandidates.build(base({ ultimate_available: true }));
assert(charged.some(candidate => candidate.kind === 'ultimate'), 'charged energy creates an ultimate choice');
const uncharged = SmartCandidates.build(base({ ultimate_available: false }));
assert(!uncharged.some(candidate => candidate.kind === 'ultimate'), 'uncharged energy does not create an ultimate choice');

console.log('test_smart_candidates: determinism, public fields, sorting, defend, and ultimate rules passed');
