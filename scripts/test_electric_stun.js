'use strict';
/* Tests for js/electric_stun.js. Node assert only. Run: node scripts/test_electric_stun.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const ElectricStun = require(path.join(__dirname, '..', 'js', 'electric_stun.js'));
const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'electric_stun.js'), 'utf8');
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

test('apply sets one non-stacking private electric-stun marker', () => {
  const unit = { id: 'agent-a' };
  assert.deepStrictEqual(ElectricStun.apply(unit), { applied: true });
  assert.strictEqual(unit.electricStun, 1);
  assert.deepStrictEqual(ElectricStun.apply(unit), { applied: false });
  assert.strictEqual(unit.electricStun, 1);
  assert.deepStrictEqual(ElectricStun.publicState(unit), { electricStun: true });
});

test('the marked next turn lasts seven seconds, does not skip, and consumes the marker', () => {
  const unit = {};
  ElectricStun.apply(unit);
  assert.deepStrictEqual(ElectricStun.startOfTurn(unit), { skip: false, timer: ElectricStun.STUN_SECONDS });
  assert.deepStrictEqual(ElectricStun.publicState(unit), { electricStun: false });
  assert.deepStrictEqual(ElectricStun.startOfTurn(unit), { skip: false, timer: null });
});

test('a KO clears only its own electric-stun marker', () => {
  const knockedOut = {};
  const other = {};
  ElectricStun.apply(knockedOut);
  ElectricStun.apply(other);
  assert.deepStrictEqual(ElectricStun.onKO(knockedOut), { cleared: true });
  assert.deepStrictEqual(ElectricStun.publicState(knockedOut), { electricStun: false });
  assert.deepStrictEqual(ElectricStun.publicState(other), { electricStun: true });
  assert.deepStrictEqual(ElectricStun.clear(knockedOut), { cleared: false });
});

test('public state exposes only the boolean marker', () => {
  const unit = { id: 'hidden-id', hp: 50, electricStun: 1 };
  const state = ElectricStun.publicState(unit);
  assert.deepStrictEqual(state, { electricStun: true });
  assert.deepStrictEqual(Object.keys(state), ['electricStun']);
  state.electricStun = false;
  assert.deepStrictEqual(ElectricStun.publicState(unit), { electricStun: true });
});

test('invalid units are safe no-ops', () => {
  for (const invalid of [null, undefined, 1, 'unit', [], () => {}]) {
    assert.deepStrictEqual(ElectricStun.apply(invalid), { applied: false });
    assert.deepStrictEqual(ElectricStun.clear(invalid), { cleared: false });
    assert.deepStrictEqual(ElectricStun.startOfTurn(invalid), { skip: false, timer: null });
    assert.deepStrictEqual(ElectricStun.publicState(invalid), { electricStun: false });
  }
});

test('the status agrees with a seeded independent shadow model', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const random = mulberry32(seed);
    const unit = {};
    let marked = false;
    const steps = 20 + Math.floor(random() * 100);
    for (let step = 0; step < steps; step++) {
      const operation = Math.floor(random() * 3);
      if (operation === 0) {
        assert.deepStrictEqual(ElectricStun.apply(unit), { applied: !marked });
        marked = true;
      } else if (operation === 1) {
        assert.deepStrictEqual(ElectricStun.startOfTurn(unit), {
          skip: false, timer: marked ? ElectricStun.STUN_SECONDS : null
        });
        marked = false;
      } else {
        assert.deepStrictEqual(ElectricStun.onKO(unit), { cleared: marked });
        marked = false;
      }
      assert.deepStrictEqual(ElectricStun.publicState(unit), { electricStun: marked }, 'seed ' + seed + ' step ' + step);
    }
  }
});

test('the module is deterministic and has no ambient entropy, clock, or DOM dependency', () => {
  assert.strictEqual(/Math\.random|\bDate\b|document|window/.test(source), false);
  const random = Math.random;
  const DateOriginal = global.Date;
  Math.random = () => { throw new Error('ambient entropy used'); };
  global.Date = function () { throw new Error('wall clock used'); };
  try {
    const unit = {};
    assert.deepStrictEqual([ElectricStun.apply(unit), ElectricStun.startOfTurn(unit)], [
      { applied: true }, { skip: false, timer: ElectricStun.STUN_SECONDS }
    ]);
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
  console.log('test_electric_stun: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_electric_stun: all ' + tests.length + ' tests passed');
