'use strict';
/* Tests for js/nun_ult.js. Node assert only. Run: node scripts/test_nun_ult.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const NunUlt = require(path.join(__dirname, '..', 'js', 'nun_ult.js'));
const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'nun_ult.js'), 'utf8');
const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

function mulberry32(seed) {
  let state = seed | 0;
  return function () {
    state = (state + 0x6d2b79f5) | 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value = (value + Math.imul(value ^ (value >>> 7), 61 | value)) ^ value;
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function resolve(normal, targets, seed) {
  return NunUlt.resolve({ normal, targets, rng: mulberry32(seed) });
}

test('each contact deals the provisional half-normal damage, rounded to 0.1', () => {
  assert.strictEqual(NunUlt.NUN_ULT_HIT_MULT, 0.575);
  assert.deepStrictEqual(resolve(23, ['a'], 1), {
    hits: [{ target: 'a', damage: 13.2 }], stunned: 'a', total: 13.2
  });
  assert.deepStrictEqual(resolve(19.9, ['a', 'b', 'c'], 2).hits.map(hit => hit.damage), [11.4, 11.4, 11.4]);
  assert.strictEqual(resolve(19.9, ['a', 'b', 'c'], 2).total, 34.2);
  assert.strictEqual(resolve(24, ['a', 'a', 'b', 'b', 'c', 'c'], 3).total, 82.8);
});

test('the cross uses only its first three distinct targets and at most two contacts each', () => {
  const result = resolve(20, ['a', 'a', 'b', 'c', 'a', 'b', 'c', 'd', 'd'], 4);
  assert.deepStrictEqual(result.hits, [
    { target: 'a', damage: 11.5 }, { target: 'a', damage: 11.5 },
    { target: 'b', damage: 11.5 }, { target: 'c', damage: 11.5 },
    { target: 'b', damage: 11.5 }, { target: 'c', damage: 11.5 }
  ]);
  assert.strictEqual(result.total, 69);
  const counts = result.hits.reduce((all, hit) => {
    all[hit.target] = (all[hit.target] || 0) + 1;
    return all;
  }, {});
  assert.deepStrictEqual(Object.keys(counts).sort(), ['a', 'b', 'c']);
  assert.ok(Object.values(counts).every(count => count <= NunUlt.MAX_HITS_PER_TARGET));
});

test('the selected electric stun always belongs to an enemy the cross touched', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const result = resolve(21, ['a', 'a', 'b', 'c'], seed);
    assert.ok(result.hits.some(hit => hit.target === result.stunned), 'seed ' + seed);
  }
});

test('the injected seeded random source makes selection reproducible', () => {
  const targets = ['a', 'a', 'b', 'b', 'c', 'c'];
  assert.deepStrictEqual(resolve(23, targets, 55), resolve(23, targets, 55));
  const stunned = new Set();
  for (let seed = 1; seed <= 200; seed++) stunned.add(resolve(23, targets, seed).stunned);
  assert.deepStrictEqual(Array.from(stunned).sort(), ['a', 'b', 'c']);
});

test('empty and malformed input resolves safely without combat results', () => {
  const empty = { hits: [], stunned: null, total: 0 };
  assert.deepStrictEqual(resolve(23, [], 1), empty);
  for (const bad of [null, undefined, {}, { normal: 0, targets: ['a'], rng: mulberry32(1) },
    { normal: NaN, targets: ['a'], rng: mulberry32(1) }, { normal: 23, targets: 'a', rng: mulberry32(1) },
    { normal: 23, targets: ['a'] }, { normal: 23, targets: [null, {}, ''], rng: mulberry32(1) }]) {
    assert.deepStrictEqual(NunUlt.resolve(bad), empty);
  }
});

test('the module is pure and has no ambient entropy, clock, or DOM dependency', () => {
  assert.strictEqual(/Math\.random|\bDate\b|document|window/.test(source), false);
  const random = Math.random;
  const DateOriginal = global.Date;
  Math.random = () => { throw new Error('ambient entropy used'); };
  global.Date = function () { throw new Error('wall clock used'); };
  try {
    assert.deepStrictEqual(resolve(20, ['a', 'b', 'c'], 9), resolve(20, ['a', 'b', 'c'], 9));
  } finally {
    Math.random = random;
    global.Date = DateOriginal;
  }
});

let failed = 0;
for (const current of tests) {
  try {
    current.fn();
    console.log('ok   - ' + current.name);
  } catch (error) {
    failed++;
    console.log('FAIL - ' + current.name + '\n       ' + (error && error.stack ? error.stack.split('\n').slice(0, 4).join('\n       ') : error));
  }
}
if (failed > 0) {
  console.log('test_nun_ult: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_nun_ult: all ' + tests.length + ' tests passed');
