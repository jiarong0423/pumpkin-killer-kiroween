'use strict';
const assert = require('assert');
const child = require('child_process');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const Flight = require('../js/flight.js');
const golden = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'flight_golden.json'), 'utf8'));

function near(actual, expected, label) {
  assert.ok(Math.abs(actual - expected) <= 1, label + ': got ' + actual + ', want ' + expected);
}
function mulberry32(seed) {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function cases(count) {
  const random = mulberry32(155); const out = [];
  for (let i = 0; i < count; i++) out.push({
    startX: 220 + random() * 1460, startY: 710 + random() * 120,
    dirX: random() < 0.5 ? 1 : -1, angleDeg: 10 + random() * 70,
    power: 20 + random() * 80, wind: -5 + random() * 10
  });
  return out;
}
function pageSimulator() {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  const marker = 'function simulateLandingX(';
  const start = html.indexOf(marker);
  assert.ok(start >= 0, 'simulateLandingX missing from index.html');
  let brace = html.indexOf('{', start), depth = 0, end = -1;
  for (let i = brace; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) { end = i + 1; break; }
  }
  assert.ok(end > start, 'simulateLandingX has no complete body');
  const sandbox = { Math };
  vm.createContext(sandbox);
  new vm.Script('const WIND_TAIL = 56, WIND_HEAD = 84; const windAccelFor = (w, d) => w * (w * d > 0 ? WIND_TAIL : WIND_HEAD); const GRAVITY = 980; const GROUND_Y = 860;\n' + html.slice(start, end)).runInContext(sandbox);
  return sandbox.simulateLandingX;
}

for (const entry of golden.cases) {
  const actual = Flight.simulate(entry.input);
  assert.strictEqual(actual.hit, entry.result.hit, entry.name + ' hit type');
  near(actual.landingX, entry.result.landingX, entry.name + ' landingX');
  near(actual.landingY, entry.result.landingY, entry.name + ' landingY');
}
assert.ok(golden.cases.some((entry) => entry.result.hit === 'wall'), 'goldens include a fence hit');
assert.ok(golden.cases.some((entry) => entry.result.hit === 'out'), 'goldens include an out case');

const randomCases = cases(500);
const python = child.spawnSync('python3', ['-B', 'scripts/flight_py.py'], {
  cwd: path.join(__dirname, '..'), input: randomCases.map(JSON.stringify).join('\n') + '\n', encoding: 'utf8'
});
assert.strictEqual(python.status, 0, python.stderr);
const pythonResults = python.stdout.trim().split('\n').map(JSON.parse);
assert.strictEqual(pythonResults.length, randomCases.length);
randomCases.forEach((input, index) => {
  const js = Flight.simulate(input), py = pythonResults[index];
  assert.strictEqual(js.hit, py.hit, 'cross-language hit ' + index);
  near(js.landingX, py.landingX, 'cross-language x ' + index);
  near(js.landingY, py.landingY, 'cross-language y ' + index);
});

const simulateLandingX = pageSimulator();
let pageChecks = 0;
for (const input of cases(100)) {
  const flight = Flight.simulate(input);
  if (flight.hit !== 'ground') continue; // The page helper predicts ground only and has no wall/canvas branch.
  const pageX = simulateLandingX(input.power, input.startX, input.startY, input.dirX, input.angleDeg, input.wind);
  near(flight.landingX, pageX, 'page parity ' + pageChecks);
  if (++pageChecks === 30) break;
}
assert.strictEqual(pageChecks, 30, 'need 30 ground-only page comparisons');
const coarse = Flight.coarsePath(Flight.simulate(golden.cases[0].input).points);
assert.ok(coarse.length > 0 && coarse.length <= 5);
coarse.forEach((point) => assert.strictEqual(point.x % 10, 0));
const waveCases = golden.cases.filter((entry) => entry.input.wave === true);
assert.ok(waveCases.length >= 6 && waveCases.every((entry) => entry.result.hit === 'ground' && entry.result.landingY === 860), 'wave goldens land exactly on the ground line (the crossing point, red-team H1 R1-A1)');
console.log('PASS: ' + golden.cases.length + ' flight goldens (' + waveCases.length + ' wave), 500 Python/JS cases, 30 page parity cases');
