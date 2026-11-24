'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const Determinism = require(path.join(__dirname, '..', 'js', 'determinism.js'));

const golden = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'determinism_golden.json'), 'utf8'));
const functions = {
  wind: input => Determinism.wind(input.seed, input.round),
  startX: input => Determinism.startX(input.seed, input.side, input.slot),
  moveDie: input => Determinism.moveDie(input.seed, input.round, input.side),
  supplyDrop: input => Determinism.supplyDrop(input.seed, input.round),
  bounceCount: input => Determinism.bounceCount(input.seed, input.round, input.throwId),
  nunStunPick: input => Determinism.nunStunPick(input.seed, input.round, input.throwId, input.n),
  sideDraw: input => Determinism.sideDraw(input.seed),
  coinToss: input => Determinism.coinToss(input.seed)
};

assert.strictEqual(golden.version, 1);
let goldenCount = 0;
for (const name of Object.keys(functions)) {
  const vectors = golden.vectors[name];
  assert.ok(Array.isArray(vectors) && vectors.length >= 40, name + ' needs at least 40 vectors');
  for (const vector of vectors) {
    assert.deepStrictEqual(functions[name](vector.input), vector.output, name + ' ' + JSON.stringify(vector.input));
    goldenCount++;
  }
}

for (let seed = 0; seed < 10000; seed++) {
  const round = (seed % 99) + 1;
  const wind = Determinism.wind(seed, round);
  assert.ok(wind >= -4 && wind <= 4);
  assert.ok(Math.abs(wind * 10 - Math.round(wind * 10)) < 1e-9);

  const slot = seed % 8;
  const left = Determinism.startX(seed, 0, slot);
  const right = Determinism.startX(seed, 1, slot);
  assert.ok(left >= 220 && left <= 620 && left % 36 === 0);
  assert.ok(right >= 1280 && right <= 1680 && right % 36 === 0);
  assert.ok(left < right);

  const die = Determinism.moveDie(seed, round, seed & 1);
  assert.ok(die >= 1 && die <= 6);
  const drop = Determinism.supplyDrop(seed, round);
  assert.ok((drop.side === 0 || drop.side === 1) && (drop.item === 0 || drop.item === 1));
  assert.ok(drop.offset >= -120 && drop.offset <= 120 && Number.isInteger(drop.offset));
  const bounces = Determinism.bounceCount(seed, round, seed);
  assert.ok(bounces >= 1 && bounces <= 6);
  const target = Determinism.nunStunPick(seed, round, seed, (seed % 17) + 1);
  assert.ok(target >= 0 && target < (seed % 17) + 1);
  const chosenSide = Determinism.sideDraw(seed);
  assert.ok(chosenSide === 0 || chosenSide === 1);
  const firstSide = Determinism.coinToss(seed);
  assert.ok(firstSide === 0 || firstSide === 1);
}

console.log('test_determinism.js: ' + goldenCount + ' golden vectors passed');
console.log('test_determinism.js: 10000 seed property cases passed');
