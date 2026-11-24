'use strict';
/* Tests for js/sound_wave.js. Node assert only. Run: node scripts/test_sound_wave.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const SoundWave = require(path.join(__dirname, '..', 'js', 'sound_wave.js'));
const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'sound_wave.js'), 'utf8');

const CASES = 300;
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

function expectedDamage(distance, normal) {
  const d = Math.abs(distance);
  if (d <= 35) return normal;          // cells of 35 px (owner 2026-11-18); 40 / 75 before
  if (d <= 70) return normal * 0.75;
  if (d <= 105) return normal * 0.5;
  return 0;
}

test('exports the decided width and stepped band data', () => {
  assert.strictEqual(SoundWave.HIT_HALF_WIDTH, 105);
  assert.deepStrictEqual(SoundWave.BANDS, [
    { maxDistance: 35, multiplier: 1 },
    { maxDistance: 70, multiplier: 0.75 },
    { maxDistance: 105, multiplier: 0.5 }
  ]);
  assert.strictEqual(SoundWave.CELL, 35, 'one cell is 35 px: the three bands are the first, second and third cell');
});

test('damageAt includes every band edge and excludes just beyond 105', () => {
  const normal = 25;
  const cases = [
    [-105, 12.5], [-70, 18.75], [-35, 25], [0, 25],
    [35, 25], [35.0001, 18.75], [70, 18.75], [70.0001, 12.5], [105, 12.5], [105.0001, 0]
  ];
  for (const [distance, expected] of cases) {
    assert.strictEqual(SoundWave.damageAt(distance, normal), expected, 'distance ' + distance);
  }
});

test('300 seeded distances use only the three decided stepped damage bands', () => {
  const random = mulberry32(16501);
  for (let i = 0; i < CASES; i++) {
    const distance = (random() - 0.5) * 260;
    const normal = 1 + Math.floor(random() * 1000) / 10;
    assert.strictEqual(SoundWave.damageAt(distance, normal), expectedDamage(distance, normal), 'case ' + i);
  }
});

test('pickTarget chooses one nearest living unit inside the half-width', () => {
  const units = [
    { id: 'far', x: 30, alive: true },
    { id: 'near', x: 98, alive: true },
    { id: 'dead', x: 101, alive: false },
    { id: 'outside', x: 206, alive: true }
  ];
  assert.strictEqual(SoundWave.pickTarget(units, 100), units[1]);
  assert.strictEqual(SoundWave.pickTarget(units, 300), units[3]);
});

test('dead units are skipped and ties select the smaller id', () => {
  const numericTie = [
    { id: 9, x: 90, alive: true }, { id: 3, x: 110, alive: true },
    { id: 1, x: 100, alive: false }
  ];
  assert.strictEqual(SoundWave.pickTarget(numericTie, 100).id, 3);
  const stringTie = [
    { id: 'zeta', x: 90, alive: true }, { id: 'alpha', x: 110, alive: true }
  ];
  assert.strictEqual(SoundWave.pickTarget(stringTie, 100).id, 'alpha');
});

test('300 seeded target sets choose at most one eligible unit deterministically', () => {
  const random = mulberry32(16502);
  for (let i = 0; i < CASES; i++) {
    const landingX = Math.floor((random() - 0.5) * 2000);
    const units = [];
    for (let id = 0; id < 10; id++) {
      units.push({
        id,
        x: landingX + Math.floor((random() - 0.5) * 300),
        alive: random() >= 0.3
      });
    }
    const selected = SoundWave.pickTarget(units, landingX);
    const eligible = units.filter(unit => unit.alive && Math.abs(unit.x - landingX) <= SoundWave.HIT_HALF_WIDTH);
    if (eligible.length === 0) {
      assert.strictEqual(selected, null, 'case ' + i);
      continue;
    }
    const bestDistance = Math.min(...eligible.map(unit => Math.abs(unit.x - landingX)));
    const expected = eligible.filter(unit => Math.abs(unit.x - landingX) === bestDistance)
      .sort((a, b) => a.id - b.id)[0];
    assert.strictEqual(selected, expected, 'case ' + i);
  }
});

test('malformed values fail closed and the module has no ambient dependencies', () => {
  assert.strictEqual(SoundWave.damageAt(NaN, 25), 0);
  assert.strictEqual(SoundWave.damageAt(20, 0), 0);
  assert.strictEqual(SoundWave.damageAt(20, '25'), 0);
  assert.strictEqual(SoundWave.pickTarget(null, 0), null);
  assert.strictEqual(SoundWave.pickTarget([{ id: 'bad', x: NaN, alive: true }], 0), null);
  assert.strictEqual(/Math\.random|\bDate\b|document|window/.test(source), false);
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
  console.log('test_sound_wave: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_sound_wave: all ' + tests.length + ' tests passed');
