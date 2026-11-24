'use strict';
// Team-battle round hash (2026-11-17): every unit of both teams, ordered by id, same result in JS and Python.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const childProcess = require('child_process');
const RoundHash = require('../js/round_hash.js');
const golden = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'round_hash_golden.json'), 'utf8'));
const clone = value => JSON.parse(JSON.stringify(value));

// The one-versus-one vectors are frozen: the first twenty cases keep their value from before team battle.
assert.strictEqual(golden.cases[0].name, 'state-00');
assert.strictEqual(golden.cases[0].hash, '696f9f69');
assert.strictEqual(golden.cases[1].hash, '2df7b83c');
assert.ok(golden.cases.length >= 33, 'team vectors must be present');

const teamCases = golden.cases.filter(entry => /^team-/.test(entry.name));
for (const size of [1, 2, 3]) assert.ok(teamCases.some(entry => entry.state.teamSize === size), 'a vector for N=' + size);
for (const entry of teamCases) {
  const size = entry.state.teamSize;
  assert.strictEqual(entry.state.units.length, 2 * size, entry.name + ' lists both teams');
  const rows = entry.canonical.split('\n');
  assert.strictEqual(rows.length, 2 * size + 4, entry.name + ' rows');
  const ids = rows.slice(0, 2 * size).map(row => row.split(',')[0]);
  assert.deepStrictEqual(ids, ids.slice().sort(), entry.name + ' rows are ordered by unit id');
  if (size > 1) assert.deepStrictEqual(ids, RoundHash.unitIds(size), entry.name + ' ids');
  // Input order must not matter.
  const reversed = clone(entry.state);
  reversed.units.reverse();
  assert.strictEqual(RoundHash.hash(reversed), entry.hash, entry.name + ' reversed input order');
  // Units given as an object keyed by id hash the same way.
  const keyed = clone(entry.state);
  keyed.units = {};
  entry.state.units.forEach(unit => { const copy = clone(unit); delete copy.id; keyed.units[unit.id] = copy; });
  assert.strictEqual(RoundHash.hash(keyed), entry.hash, entry.name + ' object-keyed units');
  // Every single field of every single unit changes the hash (a forgotten unit or field is loud).
  entry.state.units.forEach((unit, index) => {
    const edits = [
      state => { state.units[index].x += 1; }, state => { state.units[index].y += 1; },
      state => { state.units[index].hp += 0.1; }, state => { state.units[index].alive = !state.units[index].alive; },
      state => { state.units[index].statuses = (state.units[index].statuses || []).concat(['stun']); }
    ];
    edits.forEach((edit, editIndex) => {
      const changed = clone(entry.state);
      edit(changed);
      assert.notStrictEqual(RoundHash.hash(changed), entry.hash, entry.name + ' unit ' + unit.id + ' edit ' + editIndex);
    });
  });
}
assert.ok(teamCases.some(entry => entry.state.units.some(unit => unit.alive === false) && /,false,/.test(entry.canonical)), 'a dead unit stays in the hash');

// Loud failures.
const two = clone(teamCases.find(entry => entry.state.teamSize === 2).state);
const missing = clone(two); missing.units.pop();
assert.throws(() => RoundHash.canonicalText(missing), /every unit of both teams/, 'a missing unit is rejected');
const wrongIds = clone(two); wrongIds.units[0].id = 'left_5';
assert.throws(() => RoundHash.canonicalText(wrongIds), /team units must be/, 'ids outside the roster are rejected');
const duplicate = clone(two); duplicate.units[1].id = duplicate.units[0].id;
assert.throws(() => RoundHash.canonicalText(duplicate), /duplicate unit id/, 'duplicate ids are rejected');
const badSize = clone(two); badSize.teamSize = 4;
assert.throws(() => RoundHash.canonicalText(badSize), /teamSize must be 1\.\.3/, 'N=4 is rejected');
const badId = clone(two); badId.units[0].id = 'left_0,1';
assert.throws(() => RoundHash.canonicalText(badId), /unit id is invalid/);
const noSize = clone(two); delete noSize.teamSize; noSize.units.pop();
assert.doesNotThrow(() => RoundHash.canonicalText(noSize), 'without teamSize the legacy lenient behaviour stays');
// The size key does not enter the text: N=1 hashes are what they were before.
const legacy = clone(teamCases.find(entry => entry.state.teamSize === 1).state);
const withoutSize = clone(legacy); delete withoutSize.teamSize;
assert.strictEqual(RoundHash.hash(withoutSize), RoundHash.hash(legacy));

// MCP ids map to world ids; the same match hashes the same under either naming.
const table = { red_1: 'left_0', red_2: 'left_1', red_3: 'left_2', white_1: 'right_0', white_2: 'right_1', white_3: 'right_2', left_1: 'left_1', right_2: 'right_2', left: 'left', right: 'right' };
Object.keys(table).forEach(key => assert.strictEqual(RoundHash.worldUnitId(key), table[key], key));
['red_0', 'red_4', 'blue_1', '', 'left_10', 'x'].forEach(bad => assert.throws(() => RoundHash.worldUnitId(bad), TypeError, bad));
const mcpNamed = clone(two);
const renamed = { left_0: 'red_1', left_1: 'red_2', right_0: 'white_1', right_1: 'white_2' };
mcpNamed.units.forEach(unit => { unit.id = renamed[unit.id]; });
mcpNamed.units.forEach(unit => { unit.id = RoundHash.worldUnitId(unit.id); });
assert.strictEqual(RoundHash.hash(mcpNamed), RoundHash.hash(two));

// Cross-runtime: 300 pseudo-random states through the Python implementation (stdin mode) give the same text and hash.
let seed = 0x5eed5;
const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0x100000000; };
const wordsPool = ['bleed:', 'poison:', 'burn:', 'weak:', 'slow:'];
const states = [];
for (let n = 0; n < 300; n++) {
  const size = 1 + (n % 3);
  const units = RoundHash.unitIds(size).map(id => {
    const statuses = [];
    wordsPool.forEach(word => { if (random() < 0.3) statuses.push(word + (1 + Math.floor(random() * 4))); });
    if (random() < 0.2) statuses.push('stun');
    const hp = Math.round(random() * 1500) / 10;
    return { id, x: random() * 1920, y: 600 + random() * 300, hp, alive: hp > 0, statuses };
  });
  units.sort(() => random() - 0.5);
  states.push({ teamSize: size, units, wallHp: Math.round(random() * 1000) / 10, round: 1 + Math.floor(random() * 30), phase: 'round_end', seed: 1 + Math.floor(random() * 2147483646) });
}
const python = childProcess.spawnSync('python3', ['-B', path.join(__dirname, 'round_hash_py.py')], { input: states.map(state => JSON.stringify(state)).join('\n') + '\n', encoding: 'utf8', timeout: 60000 });
if (python.error || python.status !== 0) {
  console.log('SKIP cross-runtime fuzz: python3 not runnable here (' + (python.error ? python.error.message : python.stderr.trim()) + ')');
} else {
  const lines = python.stdout.trim().split('\n');
  assert.strictEqual(lines.length, states.length);
  states.forEach((state, index) => {
    const expected = JSON.parse(lines[index]);
    assert.strictEqual(RoundHash.canonicalText(state), expected.canonical, 'fuzz canonical ' + index);
    assert.strictEqual(RoundHash.hash(state), expected.hash, 'fuzz hash ' + index);
  });
  console.log('cross-runtime fuzz: 300 states identical in JS and Python');
}
console.log('PASS: team round hash (' + teamCases.length + ' vectors for N=1..3; order, field, roster and id-mapping checks)');
