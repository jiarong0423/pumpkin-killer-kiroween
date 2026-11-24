'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const Weather = require(path.join(__dirname, '..', 'js', 'weather.js'));

const root = path.join(__dirname, '..');
const vectors = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'weather_golden.json'), 'utf8'));
assert.ok(vectors.cases.length >= 200);
assert.deepStrictEqual(new Set(vectors.cases.map((item) => item.scene)),
  new Set(['graveyard', 'church', 'school', 'bell_tower']));
for (let round = 1; round <= 40; round++) {
  assert.ok(vectors.cases.some((item) => item.round === round), 'round ' + round);
}
for (const vector of vectors.cases) {
  assert.deepStrictEqual(Weather.forRound(vector.seed, vector.round, vector.scene), vector.weather, vector);
}
console.log('test_weather_golden.js: ' + vectors.cases.length + ' cases passed');
