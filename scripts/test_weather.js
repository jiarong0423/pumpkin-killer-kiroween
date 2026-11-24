'use strict';
const assert = require('assert');
const path = require('path');
const Weather = require(path.join(__dirname, '..', 'js', 'weather.js'));

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

const GOLDEN = {
  0: ['clear', 'clear', 'clear', 'clear', 'storm', 'storm', 'clear', 'clear', 'rain', 'rain', 'fog', 'fog'],
  1: ['fog', 'fog', 'clear', 'clear', 'snow', 'snow', 'clear', 'clear', 'rain', 'rain', 'fog', 'fog'],
  2: ['fog', 'fog', 'clear', 'clear', 'snow', 'snow', 'clear', 'clear', 'rain', 'rain', 'storm', 'storm'],
  7: ['storm', 'storm', 'clear', 'clear', 'rain', 'rain', 'fog', 'fog', 'clear', 'clear', 'snow', 'snow'],
  99: ['clear', 'clear', 'rain', 'rain', 'storm', 'storm', 'clear', 'clear', 'rain', 'rain', 'fog', 'fog']
};

test('five seed golden values stay stable for twelve rounds', () => {
  for (const seed of Object.keys(GOLDEN)) {
    const got = [];
    for (let round = 1; round <= 12; round++) got.push(Weather.forRound(Number(seed), round, 'unknown').id);
    assert.deepStrictEqual(got, GOLDEN[seed], 'seed ' + seed);
  }
});

test('one weather result covers exactly a two-round block', () => {
  for (let round = 1; round < 30; round++) {
    const a = Weather.forRound(41, round, 'graveyard');
    const b = Weather.forRound(41, round + 1, 'graveyard');
    if (round % 2 === 1) {
      assert.strictEqual(a.id, b.id);
      assert.strictEqual(a.startsRound, round);
      assert.strictEqual(a.endsRound, round + 1);
    }
  }
});

test('each scene follows its declared weights over 2000 seeded draws', () => {
  for (const scene of Object.keys(Weather.WEIGHTS)) {
    const counts = { clear: 0, rain: 0, snow: 0, storm: 0, fog: 0 };
    for (let seed = 0; seed < 2000; seed++) counts[Weather.forRound(seed, 1, scene).id]++;
    for (const id of Object.keys(counts)) {
      const actual = counts[id] / 2000;
      const expected = Weather.WEIGHTS[scene][id] / 100;
      assert.ok(Math.abs(actual - expected) <= 0.001, scene + ' ' + id + ': ' + actual);
    }
    assert.ok(counts.rain > 0 && counts.snow > 0, scene + ' permits rain and snow');
  }
});

test('known ids and provisional multipliers have safe ranges', () => {
  for (let seed = -500; seed < 500; seed++) {
    for (let round = 1; round <= 12; round++) {
      const weather = Weather.forRound(seed, round, 'bell tower');
      assert.ok(Object.prototype.hasOwnProperty.call(Weather.WEATHER, weather.id));
      assert.ok(weather.attackMult >= 0.9 && weather.attackMult <= 1);
      assert.ok(weather.moveMult >= 0.5 && weather.moveMult <= 1);
      assert.ok(weather.windBonus >= 0 && weather.windBonus <= 1.5);
    }
  }
});

test('application, public state and hash text preserve the public weather rules', () => {
  const rain = Weather.forRound(50, 1, 'church');
  const snow = Weather.forRound(50, 1, 'bell_tower');
  assert.strictEqual(Weather.applyAttack(rain, 24), 21.6);
  assert.strictEqual(Weather.applyAttack(rain, 0.2), 1);
  assert.strictEqual(Weather.applyAttack(rain, 0), 0);
  assert.strictEqual(Weather.applyMove(snow, 36), 18);
  assert.deepStrictEqual(Weather.publicState(rain), {
    id: rain.id, endsRound: rain.endsRound, attackMult: rain.attackMult, moveMult: rain.moveMult
  });
  assert.strictEqual(Weather.hashText(rain), rain.id + ',' + rain.endsRound + ',' + rain.attackMult.toFixed(1) + ',' + rain.moveMult.toFixed(1) + ',' + rain.windBonus.toFixed(1));
});

test('bad input falls back safely and remains deterministic', () => {
  const bad = [undefined, null, NaN, Infinity, -Infinity, 'seed', {}, []];
  for (const seed of bad) {
    for (const round of bad) {
      const a = Weather.forRound(seed, round, null);
      const b = Weather.forRound(seed, round, null);
      assert.deepStrictEqual(a, b);
      assert.ok(Object.prototype.hasOwnProperty.call(Weather.WEATHER, a.id));
      assert.ok(Number.isFinite(a.startsRound) && Number.isFinite(a.endsRound));
    }
  }
  assert.strictEqual(Weather.applyAttack(null, 'bad'), 0);
  assert.strictEqual(Weather.applyMove(null, 'bad'), 0);
  assert.ok(typeof Weather.hashText(null) === 'string');
});

let failed = 0;
for (const t of tests) {
  try { t.fn(); console.log('ok   - ' + t.name); }
  catch (error) { failed++; console.log('FAIL - ' + t.name + '\n       ' + error.message); }
}
if (failed) {
  console.log('test_weather: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_weather: all ' + tests.length + ' tests passed');
