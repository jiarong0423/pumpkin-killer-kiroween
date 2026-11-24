#!/usr/bin/env node
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const D = require(path.join(root, 'js', 'determinism.js'));
const page = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const golden = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'determinism_golden.json'), 'utf8'));

const coinVectors = golden.vectors.coinToss;
assert.ok(Array.isArray(coinVectors) && coinVectors.length >= 40, 'coin toss needs at least 40 golden vectors');
for (const vector of coinVectors) assert.strictEqual(D.coinToss(vector.input.seed), vector.output);
assert.ok(coinVectors.some(vector => vector.output === 0), 'vectors include a left-first result');
assert.ok(coinVectors.some(vector => vector.output === 1), 'vectors include a right-first result');

function firstTurn(side, seat) {
  if (seat === 'agent') return 'wait';
  if (seat === 'ai' && side === 'right') return 'ai';
  if (side === 'right') return 'curtain';
  return 'player';
}
assert.strictEqual(firstTurn('left', 'human'), 'player');
assert.strictEqual(firstTurn('right', 'human'), 'curtain');
assert.strictEqual(firstTurn('right', 'ai'), 'ai');
assert.strictEqual(firstTurn('left', 'agent'), 'wait');
assert.match(page, /showCoinToss\(Determinism\.coinToss\(matchSeed\)\)/);
assert.match(page, /function beginOpeningTurn\(side\)/);
assert.match(page, /setTimeout\(finish, 2200\)/);
assert.match(page, /face === 0 \? "1800deg" : "1980deg"/);
assert.match(page, /coin\.leftFirst/);
assert.match(page, /coin\.rightFirst/);

assert.match(page, /const AI_LEVEL_MULTIPLIERS = Object\.freeze\(\{ easy: 2\.25, normal: 0\.52, hard: 0\.27 \}\)/);
assert.match(page, /const levelKnobs = side => \{ const multiplier = AI_LEVEL_MULTIPLIERS\[levelFor\(side\)\] \|\| 1[,;]/);
assert.match(page, /aiLevel !== "easy" && ai\.hp < ai\.maxHp \* 0\.45/);
assert.match(page, /const skillChanceFor = side => levelFor\(side\) === "hard" \? 0\.35 : 0\.2/);
assert.match(page, /let seats = \{ left: "human", right: "ai" \};\s*seats\.level = \{ left: "normal", right: "normal" \}/);
assert.match(page, /const matchSettings = \(\) => \(\{ seats:/);

assert.match(page, /const choices = relayAddress \? \["human", "ai", "agent"\] : \["human", "ai"\]/);
assert.match(page, /T\(kind === "human"[\s\S]*kind === "agent" \? "seat\.agent"/);
assert.match(page, /function showAgentWaiting\(side\)/);
assert.match(page, /id="agent-room-qr"/);
assert.match(page, /if \(seats\.right === "agent"\) \{ showAgentWaiting\("right"\); return; \}/);

console.log('opening coin toss, seat levels, and agent option: ok');
