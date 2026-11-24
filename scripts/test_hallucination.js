'use strict';
/* Tests for js/hallucination.js. Node assert only. Run: node scripts/test_hallucination.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const Hallucination = require(path.join(__dirname, '..', 'js', 'hallucination.js'));
const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'hallucination.js'), 'utf8');
const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function modelState(marked) { return { hallucination: marked }; }

test('apply never stacks a hallucination marker', () => {
  const unit = { id: 'agent-a' };
  assert.deepStrictEqual(Hallucination.apply(unit), { applied: true });
  assert.strictEqual(unit.hallucination, 1);
  assert.deepStrictEqual(Hallucination.apply(unit), { applied: false });
  assert.strictEqual(unit.hallucination, 1);
  assert.deepStrictEqual(Hallucination.publicState(unit), { hallucination: true });
});

test('a marked unit skips exactly one turn and the marker is consumed', () => {
  const unit = {};
  Hallucination.apply(unit);
  assert.deepStrictEqual(Hallucination.startOfTurn(unit), { skip: true });
  assert.deepStrictEqual(Hallucination.publicState(unit), { hallucination: false });
  assert.deepStrictEqual(Hallucination.startOfTurn(unit), { skip: false });
});

test('a KO clears hallucination without affecting another unit', () => {
  const knockedOut = {};
  const other = {};
  Hallucination.apply(knockedOut);
  Hallucination.apply(other);
  assert.deepStrictEqual(Hallucination.onKO(knockedOut), { cleared: true });
  assert.deepStrictEqual(Hallucination.publicState(knockedOut), { hallucination: false });
  assert.deepStrictEqual(Hallucination.publicState(other), { hallucination: true });
  assert.deepStrictEqual(Hallucination.clear(knockedOut), { cleared: false });
});

test('the public state contains only the hallucination boolean', () => {
  const unit = { id: 'hidden-id', hp: 50, hallucination: 1 };
  const state = Hallucination.publicState(unit);
  assert.deepStrictEqual(state, { hallucination: true });
  assert.deepStrictEqual(Object.keys(state), ['hallucination']);
  state.hallucination = false;
  assert.deepStrictEqual(Hallucination.publicState(unit), { hallucination: true });
});

test('the module is deterministic and has no ambient entropy, clock, or DOM dependency', () => {
  assert.strictEqual(/Math\.random|\bDate\b|document|window/.test(source), false);
  const run = () => {
    const unit = {};
    return JSON.stringify([
      Hallucination.apply(unit), Hallucination.apply(unit), Hallucination.startOfTurn(unit),
      Hallucination.startOfTurn(unit), Hallucination.clear(unit), Hallucination.publicState(unit)
    ]);
  };
  const random = Math.random;
  const DateOriginal = global.Date;
  Math.random = () => { throw new Error('ambient entropy used'); };
  global.Date = function () { throw new Error('wall clock used'); };
  try {
    assert.strictEqual(run(), run());
  } finally {
    Math.random = random;
    global.Date = DateOriginal;
  }
});

test('property: 200 seeded scripts agree with the independent shadow model', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const random = mulberry32(seed);
    const unit = {};
    let marked = false;
    const steps = 20 + Math.floor(random() * 100);
    for (let step = 0; step < steps; step++) {
      const operation = Math.floor(random() * 4);
      let got;
      if (operation === 0) {
        got = Hallucination.apply(unit);
        const applied = !marked;
        marked = true;
        assert.deepStrictEqual(got, { applied }, 'seed ' + seed + ' step ' + step + ': apply');
      } else if (operation === 1) {
        got = Hallucination.startOfTurn(unit);
        const skip = marked;
        marked = false;
        assert.deepStrictEqual(got, { skip }, 'seed ' + seed + ' step ' + step + ': startOfTurn');
      } else {
        got = operation === 2 ? Hallucination.clear(unit) : Hallucination.onKO(unit);
        const cleared = marked;
        marked = false;
        assert.deepStrictEqual(got, { cleared }, 'seed ' + seed + ' step ' + step + ': clear');
      }
      assert.deepStrictEqual(Hallucination.publicState(unit), modelState(marked), 'seed ' + seed + ' step ' + step + ': public state');
    }
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
  console.log('test_hallucination: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_hallucination: all ' + tests.length + ' tests passed');
