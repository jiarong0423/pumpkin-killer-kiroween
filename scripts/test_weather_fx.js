'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const WeatherFx = require(path.join(__dirname, '..', 'js', 'weather_fx.js'));

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

function stub() {
  const calls = [];
  const ctx = {
    globalAlpha: 1, fillStyle: '', strokeStyle: '', lineWidth: 1,
    save() { calls.push(['save']); }, restore() { calls.push(['restore']); },
    beginPath() { calls.push(['begin']); },
    moveTo(x, y) { calls.push(['move', x, y]); }, lineTo(x, y) { calls.push(['line', x, y]); },
    stroke() { calls.push(['stroke', this.globalAlpha]); },
    arc(x, y, r) { calls.push(['arc', x, y, r]); },
    ellipse(x, y, rx, ry) { calls.push(['ellipse', x, y, rx, ry]); },
    fill() { calls.push(['fill', this.globalAlpha]); },
    fillRect(x, y, w, h) { calls.push(['rect', x, y, w, h, this.globalAlpha]); }
  };
  return { ctx, calls };
}

function step(field, seconds, wind) {
  for (let i = 0; i < Math.ceil(seconds * 60); i++) field.update(1 / 60, wind);
}

test('the same seed and updates yield identical state and drawing', () => {
  function make(seed) {
    const field = WeatherFx.create({ w: 640, h: 360, id: 'storm', seed, quality: 'high' });
    step(field, 2, -3);
    const canvas = stub(); field.draw(canvas.ctx);
    return { items: field.items(), calls: canvas.calls };
  }
  assert.deepStrictEqual(make(19), make(19));
  assert.notDeepStrictEqual(make(19).items, make(20).items);
});

test('rain streaks slant in the wind direction', () => {
  for (const wind of [-4, 4]) {
    const field = WeatherFx.create({ w: 640, h: 360, id: 'rain', seed: 3, quality: 'high' });
    field.update(1 / 60, wind);
    for (const item of field.items()) assert.strictEqual(Math.sign(item.lean), Math.sign(wind));
  }
});

test('quality budgets cap every effect and low quality is smaller', () => {
  for (const id of ['clear', 'rain', 'snow', 'storm', 'fog']) {
    const high = WeatherFx.create({ id, seed: 1, quality: 'high' });
    const low = WeatherFx.create({ id, seed: 1, quality: 'low' });
    assert.ok(high.count <= 220, id + ' high cap');
    assert.ok(low.count <= 60, id + ' low cap');
    assert.ok(low.count <= high.count, id + ' low count');
  }
  assert.strictEqual(WeatherFx.create({ id: 'storm', quality: 'high' }).count, 220);
  assert.strictEqual(WeatherFx.create({ id: 'storm', quality: 'low' }).count, 55);
});

test('all item coordinates stay inside the canvas under valid and bad updates', () => {
  const field = WeatherFx.create({ w: 50, h: 40, id: 'snow', seed: 9, quality: 'high' });
  for (const dt of [1 / 60, 1 / 20, 1, 1e6, 0, -1, NaN, Infinity]) {
    field.update(dt, -4);
    for (const item of field.items()) {
      assert.ok(Number.isFinite(item.x) && Number.isFinite(item.y));
      assert.ok(item.x >= 0 && item.x < 50 && item.y >= 0 && item.y < 40, item.x + ',' + item.y);
    }
  }
});

test('storm lightning is deterministic, capped at alpha 0.35, and absent on low', () => {
  const high = WeatherFx.create({ id: 'storm', seed: 11, quality: 'high' });
  let flashes = [];
  for (let i = 0; i < 8 * 60 && flashes.length === 0; i++) {
    high.update(1 / 60, 0);
    const painted = stub(); high.draw(painted.ctx);
    flashes = painted.calls.filter((call) => call[0] === 'rect');
  }
  assert.strictEqual(flashes.length, 1);
  assert.ok(flashes[0][5] <= 0.35);
  const low = WeatherFx.create({ id: 'storm', seed: 11, quality: 'low' });
  step(low, 7, 0);
  const dim = stub(); low.draw(dim.ctx);
  assert.strictEqual(dim.calls.filter((call) => call[0] === 'rect').length, 0);
});

test('update and draw do not use Math.random', () => {
  const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'weather_fx.js'), 'utf8');
  assert.ok(!source.includes('Math.random'));
  const original = Math.random;
  Math.random = () => { throw new Error('random call'); };
  try {
    const field = WeatherFx.create({ id: 'fog', seed: 2 });
    field.update(1 / 60, 2);
    field.draw(stub().ctx);
  } finally {
    Math.random = original;
  }
});

test('invalid create options safely use defaults', () => {
  const field = WeatherFx.create({ w: -1, h: NaN, id: 'bad', seed: 'x', quality: 'bad' });
  assert.strictEqual(field.width, 1920);
  assert.strictEqual(field.height, 1080);
  assert.strictEqual(field.id, 'clear');
  assert.strictEqual(field.quality, 'high');
  field.update(1 / 60, 'bad');
  field.draw(stub().ctx);
});

let failed = 0;
for (const t of tests) {
  try { t.fn(); console.log('ok   - ' + t.name); }
  catch (error) { failed++; console.log('FAIL - ' + t.name + '\n       ' + error.message); }
}
if (failed) {
  console.log('test_weather_fx: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_weather_fx: all ' + tests.length + ' tests passed');
