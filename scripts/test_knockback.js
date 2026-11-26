'use strict';
/* Tests for js/knockback.js. Node assert only. Run: node scripts/test_knockback.js */
const assert = require('assert');
const path = require('path');
const Knockback = require(path.join(__dirname, '..', 'js', 'knockback.js'));

function mulberry32(seed) {
  let state = seed | 0;
  return function () {
    state = (state + 0x6d2b79f5) | 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value = (value + Math.imul(value ^ (value >>> 7), 61 | value)) ^ value;
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

test('ZONES holds the decided player and agent movement bounds', () => {
  assert.deepStrictEqual(Knockback.ZONES, {
    left: { min: 110, max: 640 }, right: { min: 1280, max: 1810 }
  });
});

test('apply moves away from either thrower direction and clamps both zone edges in 300 seeded cases', () => {
  const random = mulberry32(166);
  const names = ['left', 'right'];
  for (let i = 0; i < 300; i++) {
    const name = names[i % names.length];
    const zone = Knockback.ZONES[name];
    const victim = zone.min + random() * (zone.max - zone.min);
    const px = random() * 400;
    const thrower = i % 2 === 0 ? victim - (1 + random() * 500) : victim + (1 + random() * 500);
    const moved = Knockback.apply(victim, thrower, px, name);
    const expected = Math.max(zone.min, Math.min(zone.max, victim + (victim < thrower ? -px : px)));
    assert.strictEqual(moved, expected, 'case ' + i);
    assert.ok(moved >= zone.min && moved <= zone.max, 'case ' + i + ' escaped zone');
    if (victim < thrower && moved > zone.min) assert.ok(moved < victim, 'case ' + i + ' should move left');
    if (victim >= thrower && moved < zone.max) assert.ok(moved > victim, 'case ' + i + ' should move right');
  }
  assert.strictEqual(Knockback.apply(130, 500, 50, 'left'), 110);
  assert.strictEqual(Knockback.apply(1790, 1200, 50, 'right'), 1810);
});

test('only direct non-fatal unit hits are eligible; fatal and non-unit contacts give 0', () => {
  assert.strictEqual(Knockback.eligible({ fatal: false, hitKind: 'unit' }), true);
  for (const hit of [
    { fatal: true, hitKind: 'unit' }, { fatal: false, hitKind: 'fence' },
    { fatal: false, hitKind: 'ground' }, { fatal: false, hitKind: 'shield' },
    { fatal: false, hitKind: 'direct' }, null, undefined
  ]) {
    assert.strictEqual(Number(Knockback.eligible(hit)), 0);
  }
});

test('a push stops 120 px short of a living teammate in its way and never goes backwards', () => {
  assert.strictEqual(Knockback.clearOfMates(300, 250, [150]), 270);   // pushed left toward a mate at 150
  assert.strictEqual(Knockback.clearOfMates(1500, 1550, [1650]), 1530);
  assert.strictEqual(Knockback.clearOfMates(1500, 1550, [1560]), 1500);   // already closer than 120: stay
  assert.strictEqual(Knockback.clearOfMates(300, 250, [450]), 250);   // the mate is behind
  assert.strictEqual(Knockback.clearOfMates(300, 250, []), 250);
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
  console.log('test_knockback: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_knockback: all ' + tests.length + ' tests passed');
