'use strict';
/* Tests for js/boomerang.js. Node assert only. Run: node scripts/test_boomerang.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const Boomerang = require(path.join(__dirname, '..', 'js', 'boomerang.js'));
const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'boomerang.js'), 'utf8');

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

function pathAcross(x0, x1) {
  return [{ x: x0, y: 600, t: 0 }, { x: x1, y: 600, t: 1 }];
}

test('the decided boomerang constants include the invented 1400 px/s return speed', () => {
  assert.strictEqual(Boomerang.OUTBOUND_DAMAGE, 21);
  assert.strictEqual(Boomerang.RETURN_DAMAGE, 31.5);
  assert.strictEqual(Boomerang.RETURN_SPEED, 1400);
});

test('outbound contacts pierce in path order, shields do not block, then the first target gets the return hit', () => {
  const hits = Boomerang.resolve(pathAcross(100, 900), [
    { id: 'late', x: 700, y: 600, alive: true, shielded: false },
    { id: 'first', x: 300, y: 600, alive: true, shielded: true },
    { id: 'middle', x: 500, y: 600, alive: true, shielded: false }
  ], 1400);
  assert.deepStrictEqual(hits.map(hit => hit.target), ['first', 'middle', 'late', 'first']);
  assert.deepStrictEqual(hits.map(hit => hit.phase), ['outbound', 'outbound', 'outbound', 'return']);
  assert.deepStrictEqual(hits.map(hit => hit.damage), [21, 21, 21, 31.5]);
  assert.ok(hits.every(hit => hit.blockable === false));
  assert.strictEqual(hits[0].shielded, true);
  assert.ok(hits[0].t < hits[1].t && hits[1].t < hits[2].t && hits[2].t < hits[3].t);
});

test('no outbound unit hit means no return hit', () => {
  assert.deepStrictEqual(Boomerang.resolve(pathAcross(100, 900), [
    { id: 'dead', x: 300, y: 600, alive: false, shielded: false },
    { id: 'miss', x: 400, y: 800, alive: true, shielded: false }
  ], 1400), []);
});

test('the return time follows the outbound polyline in reverse, not a shortcut', () => {
  const hits = Boomerang.resolve([
    { x: 100, y: 100, t: 0 }, { x: 500, y: 100, t: 1 }, { x: 500, y: 500, t: 2 }
  ], [{ id: 'first', x: 300, y: 100, alive: true, shielded: false }], 1400);
  assert.strictEqual(hits.length, 2);
  assert.strictEqual(hits[1].t, 2 + 640 / 1400);
});


test('300 seeded paths retain direction, ordered unique pierce contacts, and a return to the first hit', () => {
  const random = mulberry32(166);
  for (let i = 0; i < 300; i++) {
    const leftToRight = i % 2 === 0;
    const start = leftToRight ? 100 : 1800;
    const end = leftToRight ? 1800 : 100;
    const enemies = [];
    for (let id = 0; id < 5; id++) {
      enemies.push({
        id: id, x: 250 + id * 320 + random() * 12, y: 600 + (random() - 0.5) * 30,
        alive: random() > 0.15, shielded: random() > 0.5
      });
    }
    const hits = Boomerang.resolve(pathAcross(start, end), enemies, 800 + random() * 1600);
    const outbound = hits.filter(hit => hit.phase === 'outbound');
    const expected = enemies.filter(enemy => enemy.alive).sort((a, b) => leftToRight ? a.x - b.x : b.x - a.x).map(enemy => enemy.id);
    assert.deepStrictEqual(outbound.map(hit => hit.target), expected, 'case ' + i);
    assert.strictEqual(new Set(outbound.map(hit => hit.target)).size, outbound.length, 'case ' + i + ' duplicate');
    if (outbound.length === 0) assert.strictEqual(hits.length, 0, 'case ' + i + ' unexpected return');
    else {
      const returned = hits[hits.length - 1];
      assert.strictEqual(returned.phase, 'return', 'case ' + i);
      assert.strictEqual(returned.target, outbound[0].target, 'case ' + i);
      assert.ok(returned.t > outbound[outbound.length - 1].t, 'case ' + i);
    }
  }
});

test('the module is pure and has no ambient entropy, clock, or DOM dependency', () => {
  assert.strictEqual(/Math\.random|\bDate\b|document|window/.test(source), false);
  const random = Math.random;
  const DateOriginal = global.Date;
  Math.random = () => { throw new Error('ambient entropy used'); };
  global.Date = function () { throw new Error('wall clock used'); };
  try {
    assert.deepStrictEqual(Boomerang.resolve(pathAcross(100, 900), [{ id: 'a', x: 300, y: 600, alive: true }]),
      Boomerang.resolve(pathAcross(100, 900), [{ id: 'a', x: 300, y: 600, alive: true }]));
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
  console.log('test_boomerang: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_boomerang: all ' + tests.length + ' tests passed');
