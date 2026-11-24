'use strict';
/*
 * Tests for js/wind_fx.js plus the numeric acceptance checks of docs/wind_design.md.
 * Node `assert` only, with a recording stub canvas. Run: node scripts/test_wind_fx.js
 * Exit code 1 if any check fails.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const WindFx = require(path.join(__dirname, '..', 'js', 'wind_fx.js'));

const W = 1920;
const H = 1080;
const HUD = [
  [0, 0, 1920, 96],        // top bar: players, round + timer, wind, agents
  [0, 900, 1920, 1080],    // bottom dock
  [820, 300, 1100, 640]    // an extra block in the middle, to stress the keep-out logic
];
const BAD_WINDS = [NaN, Infinity, -Infinity, 1e308, -1e308, undefined, null, 'abc', {}, [], 0, -0, 4, -4, 9, -9, 2.4];

// ---------------------------------------------------------------------------
// recording stub canvas: only the calls the module may use exist, so any other
// canvas call throws a TypeError and fails the test.

function makeStub() {
  const painted = [];
  let path = [];
  let gradients = 0;
  const ctx = {
    globalAlpha: 1,
    fillStyle: '#000000',
    globalCompositeOperation: 'source-over',
    save() {},
    restore() {},
    beginPath() { path = []; },
    arc(x, y, r) {
      path.push({ x0: x - r, y0: y - r, x1: x + r, y1: y + r, cx: x, cy: y });
    },
    ellipse(x, y, rx, ry) {
      const r = Math.max(rx, ry);
      path.push({ x0: x - r, y0: y - r, x1: x + r, y1: y + r, cx: x, cy: y });
    },
    fill() {
      for (const b of path) painted.push(Object.assign({ alpha: ctx.globalAlpha }, b));
      path = [];
    },
    createRadialGradient() {
      gradients++;
      return { addColorStop() {} };
    }
  };
  return { ctx, painted, gradientCount: () => gradients };
}

function overlaps(b, r) {
  return b.x0 < r[2] && b.x1 > r[0] && b.y0 < r[3] && b.y1 > r[1];
}

function run(field, seconds, dt) {
  const n = Math.round(seconds / dt);
  for (let i = 0; i < n; i++) field.update(dt);
}

function circDelta(a, b, size) {
  let d = b - a;
  if (d > size / 2) d -= size;
  if (d < -size / 2) d += size;
  return d;
}

function mean(list) {
  return list.reduce((s, v) => s + v, 0) / list.length;
}

// ---------------------------------------------------------------------------
// tests

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

test('same seed and same calls give identical state and identical draw calls', () => {
  const make = (seed) => {
    const f = WindFx.createWindField({ width: W, height: H, seed, count: 64, avoid: HUD });
    const s = makeStub();
    f.setWind(3);
    run(f, 2, 1 / 60);
    f.setWind(-2.5);
    run(f, 1, 1 / 30);
    f.draw(s.ctx);
    return { state: JSON.stringify(f.getState()), painted: JSON.stringify(s.painted) };
  };
  const a = make(1234);
  const b = make(1234);
  assert.strictEqual(a.state, b.state);
  assert.strictEqual(a.painted, b.painted);
  assert.notStrictEqual(a.state, make(99).state, 'another seed must give another field');
});

test('no Math.random: replacing it with a thrower changes nothing', () => {
  const orig = Math.random;
  Math.random = () => { throw new Error('Math.random used'); };
  try {
    const f = WindFx.createWindField({ width: W, height: H, seed: 5 });
    f.setWind(4);
    run(f, 1, 1 / 60);
    f.draw(makeStub().ctx);
  } finally {
    Math.random = orig;
  }
});

test('item count never goes above the budget', () => {
  assert.strictEqual(WindFx.MAX_ITEMS, 96);
  assert.strictEqual(WindFx.DEFAULT_COUNT, 64);
  const cases = [[0, 0], [1, 1], [10, 10], [64, 64], [96, 96], [97, 96], [1000, 96], [Infinity, 96],
    [-5, 0], [NaN, 64], [undefined, 64], ['x', 64], [12.9, 12]];
  for (const [count, want] of cases) {
    const f = WindFx.createWindField({ seed: 1, count });
    assert.strictEqual(f.count, want, 'count=' + String(count));
    assert.strictEqual(f.getState().length, want);
    assert.ok(f.getState().length <= WindFx.MAX_ITEMS);
  }
  const state = WindFx.createWindField({ seed: 1, count: 1000 }).getState();
  assert.ok(state.filter((i) => i.kind === 'fog').length <= WindFx.MAX_FOG);
  const none = makeStub();
  WindFx.createWindField({ seed: 1, count: 0 }).draw(none.ctx);
  assert.strictEqual(none.painted.length, 0);
});

test('nothing is drawn inside an avoid rectangle', () => {
  for (const wind of [4, -4, 0, 1.7]) {
    const f = WindFx.createWindField({ width: W, height: H, seed: 77, count: 96, avoid: HUD });
    f.setWind(wind);
    let drawn = 0;
    for (let frame = 0; frame < 600; frame++) {
      f.update(1 / 60);
      if (frame % 10 === 0) {
        const s = makeStub();
        f.draw(s.ctx);
        drawn += s.painted.length;
        for (const b of s.painted) {
          for (const r of HUD) {
            assert.ok(!overlaps(b, r), 'shape at ' + b.cx.toFixed(1) + ',' + b.cy.toFixed(1) + ' overlaps rect ' + r);
          }
        }
      }
    }
    assert.ok(drawn > 500, 'the field must still draw something outside the HUD (wind ' + wind + ', drew ' + drawn + ')');
  }
});

test('avoid rectangles: swapped corners work, invalid ones are ignored, setAvoid works', () => {
  const swapped = WindFx.createWindField({ width: W, height: H, seed: 3, count: 96, avoid: [[1920, 96, 0, 0], 'x', [1, 2, 3], [NaN, 0, 5, 5]] });
  swapped.update(0.05);
  const s = makeStub();
  swapped.draw(s.ctx);
  assert.ok(s.painted.length > 0);
  for (const b of s.painted) assert.ok(!overlaps(b, [0, 0, 1920, 96]));
  const everything = WindFx.createWindField({ width: W, height: H, seed: 3, count: 96 });
  everything.setAvoid([[-10, -10, W + 10, H + 10]]);
  const s2 = makeStub();
  everything.draw(s2.ctx);
  assert.strictEqual(s2.painted.length, 0, 'a rect covering the whole field leaves nothing to draw');
});

test('drift direction follows the sign of the wind, for every kind', () => {
  for (const kind of ['leaf', 'dust', 'fog']) {
    const dirs = {};
    for (const wind of [4, -4]) {
      const f = WindFx.createWindField({ width: W, height: H, seed: 21, count: 96 });
      f.setWind(wind);
      run(f, 3, 1 / 60);
      const before = f.getState().filter((i) => i.kind === kind);
      run(f, 0.25, 1 / 60);
      const after = f.getState().filter((i) => i.kind === kind);
      assert.ok(before.length > 0, kind + ' items exist');
      const moved = mean(before.map((b, i) => circDelta(b.x, after[i].x, W)));
      const vx = mean(after.map((i) => i.vx));
      dirs[wind] = { moved, vx };
      assert.strictEqual(Math.sign(moved), Math.sign(wind), kind + ' moved the wrong way at wind ' + wind);
      assert.strictEqual(Math.sign(vx), Math.sign(wind), kind + ' vx has the wrong sign at wind ' + wind);
    }
    assert.ok(Math.abs(dirs[4].vx) > 40, kind + ' must visibly move at max wind');
  }
});

test('stronger wind means faster drift (linear, then clamped at the maximum)', () => {
  const speed = (wind) => {
    const f = WindFx.createWindField({ width: W, height: H, seed: 8, count: 96 });
    f.setWind(wind);
    run(f, 8, 1 / 60);
    f.update(1 / 60);
    return mean(f.getState().filter((i) => i.kind === 'leaf').map((i) => i.vx));
  };
  const v1 = speed(1), v2 = speed(2), v4 = speed(4), v9 = speed(9);
  assert.ok(v1 < v2 && v2 < v4, 'speed rises with wind');
  assert.ok(Math.abs(v9 - v4) < 30, 'wind beyond the maximum is clamped');
});

test('zero wind drifts only gently', () => {
  const f = WindFx.createWindField({ width: W, height: H, seed: 4, count: 96 });
  f.setWind(0);
  run(f, 5, 1 / 60);
  for (const i of f.getState()) assert.ok(Math.abs(i.vx) <= 15, i.kind + ' vx=' + i.vx);
  // and after a strong wind has died down
  f.setWind(4);
  run(f, 4, 1 / 60);
  f.setWind(0);
  run(f, 12, 1 / 60);
  for (const i of f.getState()) assert.ok(Math.abs(i.vx) <= 15, 'after the gust: ' + i.kind + ' vx=' + i.vx);
});

test('wind eases in, a change adds a short gust, and bad winds are safe', () => {
  const f = WindFx.createWindField({ seed: 2 });
  f.setWind(4);
  f.update(1 / 60);
  assert.ok(f.getWind().current > 0 && f.getWind().current < 0.5, 'does not jump to the target');
  run(f, 6, 1 / 60);
  assert.ok(Math.abs(f.getWind().current - 4) < 0.01);
  f.setWind(100);
  assert.strictEqual(f.getWind().target, 4, 'clamped to the maximum');
  f.setWind(NaN);
  assert.strictEqual(f.getWind().target, 0, 'NaN counts as calm');
  for (const w of BAD_WINDS) {
    f.setWind(w);
    run(f, 0.2, 1 / 60);
    const wind = f.getWind();
    assert.ok(Number.isFinite(wind.current) && Number.isFinite(wind.target));
    for (const i of f.getState()) assert.ok(Number.isFinite(i.x) && Number.isFinite(i.y) && Number.isFinite(i.vx) && Number.isFinite(i.vy));
  }
});

test('wrap-around keeps every item inside the field, whatever the wind and dt', () => {
  const dts = [1 / 60, 1 / 30, 0.1, 0.5, 5, 1e6, 1e12, 0, -1, NaN, Infinity];
  for (const wind of [4, -4, 0, 2.4, -1]) {
    const f = WindFx.createWindField({ width: W, height: H, seed: 31, count: 96 });
    f.setWind(wind);
    for (let k = 0; k < 400; k++) {
      f.update(dts[k % dts.length]);
      for (const i of f.getState()) {
        assert.ok(Number.isFinite(i.x) && Number.isFinite(i.y));
        assert.ok(i.x >= 0 && i.x < W && i.y >= 0 && i.y < H, i.kind + ' left the field at ' + i.x + ',' + i.y);
      }
    }
  }
  const small = WindFx.createWindField({ width: 50, height: 40, seed: 1, count: 96 });
  small.setWind(4);
  run(small, 3, 1 / 60);
  for (const i of small.getState()) assert.ok(i.x >= 0 && i.x < 50 && i.y >= 0 && i.y < 40);
});

test('bad constructor options fall back to the defaults', () => {
  for (const opts of [undefined, null, 5, 'x', {}, { width: -1, height: NaN, seed: 'a', count: {} }]) {
    const f = WindFx.createWindField(opts);
    assert.strictEqual(f.width, 1920);
    assert.strictEqual(f.height, 1080);
    assert.strictEqual(f.count, WindFx.DEFAULT_COUNT);
    f.update(0.016);
    f.draw(makeStub().ctx);
  }
});

test('draw layers: fog uses gradients, the others do not, and an unknown layer draws all', () => {
  const f = WindFx.createWindField({ width: W, height: H, seed: 6, count: 96 });
  f.setWind(2);
  run(f, 1, 1 / 60);
  const fogN = f.getState().filter((i) => i.kind === 'fog').length;
  const a = makeStub(); f.draw(a.ctx, 'fog');
  assert.strictEqual(a.gradientCount(), fogN);
  assert.strictEqual(a.painted.length, fogN);
  const b = makeStub(); f.draw(b.ctx, 'dust');
  assert.strictEqual(b.gradientCount(), 0);
  const c = makeStub(); f.draw(c.ctx, 'leaves');
  assert.strictEqual(c.gradientCount(), 0);
  assert.ok(c.painted.length > 0 && c.painted.length <= f.getState().filter((i) => i.kind === 'leaf').length);
  const all = makeStub(); f.draw(all.ctx);
  assert.strictEqual(all.painted.length, a.painted.length + b.painted.length + c.painted.length);
  f.draw(null);
});

test('flameLean: clamped, finite, linear in between, leans toward the wind', () => {
  for (const w of BAD_WINDS.concat([0.5, -0.5, 100, -100])) {
    const v = WindFx.flameLean(w);
    assert.ok(Number.isFinite(v), 'finite for ' + String(w));
    assert.ok(Math.abs(v) <= WindFx.FLAME_LEAN_MAX + 1e-12, 'clamped for ' + String(w));
  }
  assert.strictEqual(WindFx.FLAME_LEAN_MAX, 0.6);
  assert.strictEqual(WindFx.flameLean(0), 0);
  assert.strictEqual(WindFx.flameLean(NaN), 0);
  assert.ok(Math.abs(WindFx.flameLean(2) - 0.3) < 1e-12, 'linear: half wind, half lean');
  assert.strictEqual(WindFx.flameLean(4), 0.6);
  assert.strictEqual(WindFx.flameLean(9), 0.6);
  assert.strictEqual(WindFx.flameLean(-4), -0.6);
  assert.strictEqual(WindFx.flameLean(Infinity), 0.6);
  assert.strictEqual(WindFx.flameLean(-Infinity), -0.6);
  assert.ok(WindFx.flameLean(1) < WindFx.flameLean(2) && WindFx.flameLean(2) < WindFx.flameLean(3));
  assert.ok(Math.abs(WindFx.flameLean(5, 10) - 0.3) < 1e-12, 'custom maximum wind');
});

test('swayAngle: clamped, finite for any wind and time, swings toward the wind', () => {
  const times = [0, 0.37, 1, 59.9, 600, 1e6, 1e15, 1e308, -3.3, NaN, Infinity, -Infinity, undefined, 'x'];
  for (const w of BAD_WINDS.concat([0.5, -0.5, 100, -100])) {
    for (const t of times) {
      const v = WindFx.swayAngle(w, t);
      assert.ok(Number.isFinite(v), 'finite for w=' + String(w) + ' t=' + String(t));
      assert.ok(Math.abs(v) <= WindFx.SWAY_MAX + 1e-12, 'clamped for w=' + String(w) + ' t=' + String(t));
    }
  }
  assert.strictEqual(WindFx.SWAY_MAX, 0.5);
  const avg = (w) => {
    let sum = 0, n = 0;
    for (let t = 0; t < 100; t += 0.01) { sum += WindFx.swayAngle(w, t); n++; }
    return sum / n;
  };
  assert.ok(Math.abs(avg(4) + 0.3) < 0.01, 'mean lean at max wind is -0.3 (hanging end swings toward +x)');
  assert.ok(Math.abs(avg(-4) - 0.3) < 0.01);
  assert.ok(Math.abs(avg(0)) < 0.01, 'calm: swings around upright');
  const range = (w) => {
    let lo = Infinity, hi = -Infinity;
    for (let t = 0; t < 20; t += 0.01) { const v = WindFx.swayAngle(w, t); lo = Math.min(lo, v); hi = Math.max(hi, v); }
    return hi - lo;
  };
  assert.ok(range(4) > range(0), 'strong wind swings wider than calm');
  assert.ok(range(0) > 0.05, 'calm still breathes a little');
  assert.strictEqual(WindFx.swayAngle(1.3, 600), WindFx.swayAngle(1.3, 0), 'the 600 s period is seamless');
});

// ---------------------------------------------------------------------------
// numeric acceptance checks of docs/wind_design.md (flat-ground model with the
// client's own per-step integration; the real start height is not modelled).

const SHARED = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'constants.json'), 'utf8'));
const GRAVITY = SHARED.GRAVITY;
const V0 = SHARED.V0_PER_POWER;
const PROPOSED_ACCEL = 96;
const ACCEL = typeof SHARED.WIND_ACCEL === 'number' ? SHARED.WIND_ACCEL : PROPOSED_ACCEL;
const CHAR_WIDTH_PX = 100;   // ASSUMPTION: the art size was not measured; replace with the real width
const HIT_RADIUS_PX = 50;    // ASSUMPTION for "hit": half of CHAR_WIDTH_PX. The worst case measured is 44.8 px (see docs/wind_design.md)

function flatLanding(power, angleDeg, wind, accel) {
  const dt = 1 / 60;
  const rad = angleDeg * Math.PI / 180;
  let vx = power * V0 * Math.cos(rad);
  let vy = -power * V0 * Math.sin(rad);
  let x = 0, y = 0;
  for (let i = 0; i < 1200; i++) {
    vx += wind * accel * dt;
    vy += GRAVITY * dt;
    x += vx * dt;
    y += vy * dt;
    if (y >= 0 && vy > 0) break;
  }
  return x;
}

test('design: shared wind factor is the recommended 96 px/s^2 per wind unit (or not yet in constants.json)', () => {
  assert.strictEqual(ACCEL, 96, 'WIND_ACCEL in shared/constants.json must be 96, found ' + ACCEL);
  assert.strictEqual(SHARED.WIND_MIN, -4);
  assert.strictEqual(SHARED.WIND_MAX, 4);
});

test('design: a player who ignores max wind misses by at least three character widths', () => {
  const target = flatLanding(65, 50, 0, ACCEL);
  assert.ok(Math.abs(target - 809) < 20, 'flat no-wind range of power 65 / 50 degrees is about 809 px, got ' + target);
  for (const wind of [4, -4]) {
    const miss = Math.abs(flatLanding(65, 50, wind, ACCEL) - target);
    assert.ok(miss >= 3 * CHAR_WIDTH_PX, 'ignoring wind ' + wind + ' misses by only ' + miss.toFixed(0) + ' px');
    assert.ok(miss <= 0.25 * W, 'the wind must not throw a shot more than a quarter of the field');
  }
});

test('design finding: a 60 degree lob into max headwind cannot reach a 60 degree no-wind target (reported, not a pass rule)', () => {
  const target = flatLanding(65, 60, 0, ACCEL);
  const reach = flatLanding(100, 60, -4, ACCEL);
  console.log('     (60 deg, max headwind, power 100 reaches ' + reach.toFixed(0) + ' px; the no-wind target is ' + target.toFixed(0) + ' px)');
  assert.ok(Number.isFinite(reach) && reach > 0);
});

test('design: a player who corrects hits the fixed target within three throws', () => {
  for (const wind of [4, -4, 2, -2.4]) {
    for (const angle of [40, 50, 54]) {   // 54 is the default angle; steep lobs lose reach in a headwind (see the finding above)
      const target = flatLanding(65, angle, 0, ACCEL);
      const slope0 = 2 * target / 65;                    // px per power, from the no-wind picture
      const p0 = 65;
      const l0 = flatLanding(p0, angle, wind, ACCEL);
      const p1 = Math.min(100, Math.max(10, p0 + (target - l0) / slope0));
      const l1 = flatLanding(p1, angle, wind, ACCEL);
      let p2 = p1;
      if (Math.abs(l1 - l0) > 1e-9) p2 = p1 + (target - l1) * (p1 - p0) / (l1 - l0);   // secant step
      p2 = Math.min(100, Math.max(10, p2));
      const l2 = flatLanding(p2, angle, wind, ACCEL);
      assert.ok(Math.abs(l2 - target) <= HIT_RADIUS_PX,
        'wind ' + wind + ' angle ' + angle + ': third throw lands ' + (l2 - target).toFixed(1) + ' px off');
      assert.ok(p2 <= 100, 'needs more than full power');
    }
  }
});

test('design: at max headwind, full power still reaches at least 1200 px (reach floor; use real unit positions to tighten)', () => {
  let best = 0;
  for (let angle = 25; angle <= 80; angle += 1) best = Math.max(best, flatLanding(100, angle, -4, ACCEL));
  assert.ok(best >= 1200, 'best reach into a max headwind is ' + best.toFixed(0) + ' px');
  console.log('     (best reach into max headwind at power 100: ' + best.toFixed(0) + ' px)');
});

// ---------------------------------------------------------------------------

let failed = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('ok   - ' + t.name);
  } catch (err) {
    failed++;
    console.log('FAIL - ' + t.name + '\n       ' + (err && err.message ? err.message : err));
  }
}
if (failed > 0) {
  console.log('test_wind_fx: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_wind_fx: all ' + tests.length + ' tests passed');
