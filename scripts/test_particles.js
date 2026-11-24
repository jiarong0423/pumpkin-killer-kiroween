'use strict';
/*
 * Seeded property tests for js/particles.js and js/particles_draw.js.
 * Node `assert` only. Run: node scripts/test_particles.js
 * Exit code 1 if any property fails.
 */
const assert = require('assert');
const path = require('path');
const Particles = require(path.join(__dirname, '..', 'js', 'particles.js'));
const Draw = require(path.join(__dirname, '..', 'js', 'particles_draw.js'));

const CASES = 300; // at least 200 per property
const NAMES = Particles.PRESET_NAMES;
const HEX = /^#[0-9a-f]{6}$/;
const NUMERIC_KEYS = [
  'id', 'x', 'y', 'vx', 'vy', 'life', 'maxLife', 'size', 'sizeEnd', 'alpha',
  'gravity', 'drag', 'spin', 'angle', 'layer', 'lineWidth', 'fade'
];
const SPEC_KEYS = [
  'x', 'y', 'vx', 'vy', 'life', 'maxLife', 'size', 'sizeEnd', 'color', 'colorEnd',
  'alpha', 'gravity', 'drag', 'shape', 'spin', 'layer'
];

// ---------------------------------------------------------------------------
// helpers

function pickFrom(r, list) {
  return list[Math.floor(r() * list.length)];
}

function randOpts(r) {
  const o = {};
  if (r() < 0.8) o.dirX = r() < 0.5 ? -1 : 1;
  else if (r() < 0.5) o.dirX = (r() - 0.5) * 2;
  if (r() < 0.8) o.scale = 0.05 + r() * 5;
  else if (r() < 0.5) o.scale = NaN;
  if (r() < 0.5) o.team = r() < 0.5 ? 'player' : 'agent';
  if (r() < 0.5) o.width = 1 + r() * 1500;
  if (r() < 0.3) o.text = String(Math.floor(r() * 999));
  if (r() < 0.2) o.amount = Math.floor(r() * 120) - 10;
  if (r() < 0.3) o.duration = 0.2 + r() * 10;
  if (r() < 0.2) o.radius = 4 + r() * 300;
  if (r() < 0.2) o.height = 20 + r() * 800;
  return Object.freeze(o);
}

function randCoord(r) {
  return r() < 0.05 ? (r() - 0.5) * 2e6 : (r() - 0.5) * 4000;
}

function emitRandom(sys, r, nameList) {
  return sys.emit(pickFrom(r, nameList || NAMES), randCoord(r), randCoord(r), randOpts(r));
}

function snapshot(particles) {
  return particles.map((p) => Object.assign({}, p));
}

function parseHex(c) {
  assert.ok(HEX.test(c), 'bad colour ' + c);
  return [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
}

function checkParticle(p, label) {
  // The message is only built when a check fails (keeps the 300-case runs fast).
  const check = (cond, what) => {
    if (!cond) assert.fail(label + ': bad ' + what + ' in ' + JSON.stringify(p));
  };
  for (const k of SPEC_KEYS) check(k in p, 'missing ' + k);
  for (const k of NUMERIC_KEYS) check(Number.isFinite(p[k]), 'non-finite ' + k);
  check(p.life > 0, 'life');
  check(p.maxLife >= p.life, 'maxLife');
  check(p.size >= 0 && p.sizeEnd >= 0, 'size');
  check(p.alpha >= 0 && p.alpha <= 1, 'alpha');
  check(p.fade >= 0 && p.fade <= 1, 'fade');
  check(p.drag >= 0, 'drag');
  check([0, 1, 2].includes(p.layer), 'layer');
  check(Particles.SHAPES.includes(p.shape), 'shape');
  check(HEX.test(p.color) && HEX.test(p.colorEnd), 'colour');
  check(typeof p.text === 'string', 'text');
}

// A random but reproducible script of emits and updates.
function runScript(systemSeed, scriptSeed, maxParticles) {
  const sys = Particles.createSystem({ seed: systemSeed, maxParticles });
  const r = Particles.mulberry32(scriptSeed);
  sys.emit('impact_burst', 10, 20, { scale: 1 });
  const steps = 5 + Math.floor(r() * 15);
  for (let i = 0; i < steps; i++) {
    if (r() < 0.6) emitRandom(sys, r);
    else sys.update(1 / 120 + r() * 0.05);
  }
  sys.emit('impact_burst', -30, 40, { scale: 2 });
  return snapshot(sys.particles);
}

// Minimal recording 2D context.
function makeStubCtx() {
  const calls = [];
  const sets = [];
  const state = { depth: 0, minDepth: 0 };
  const gradient = { addColorStop: (o, c) => calls.push(['addColorStop', o, c]) };
  const store = {};
  const ctx = new Proxy(store, {
    get(target, prop) {
      if (prop in target) return target[prop];
      return (...args) => {
        calls.push([prop, ...args]);
        if (prop === 'save') state.depth++;
        if (prop === 'restore') {
          state.depth--;
          state.minDepth = Math.min(state.minDepth, state.depth);
        }
        if (prop === 'createRadialGradient') return gradient;
        return undefined;
      };
    },
    set(target, prop, value) {
      target[prop] = value;
      sets.push([prop, value]);
      return true;
    }
  });
  return { ctx, calls, sets, state };
}

// ---------------------------------------------------------------------------
// properties

const tests = [];
function property(name, fn) {
  tests.push({ name, fn });
}

property('same seed + same calls -> identical particles; other seed differs', () => {
  const r = Particles.mulberry32(101);
  for (let i = 0; i < CASES; i++) {
    const seed = Math.floor(r() * 4294967296) - 2147483648;
    const scriptSeed = Math.floor(r() * 1e9);
    const max = r() < 0.3 ? 20 + Math.floor(r() * 200) : undefined;
    const a = runScript(seed, scriptSeed, max);
    const b = runScript(seed, scriptSeed, max);
    assert.ok(a.length > 0, 'case ' + i + ' produced no particles');
    assert.deepStrictEqual(a, b, 'case ' + i + ' not deterministic');
    const c = runScript(seed + 1, scriptSeed, max);
    assert.notStrictEqual(JSON.stringify(a), JSON.stringify(c), 'case ' + i + ' ignores the seed');
  }
});

property('pool never exceeds maxParticles and drops the oldest first', () => {
  const r = Particles.mulberry32(202);
  const big = ['poison_cloud', 'impact_burst', 'dart_rain', 'smoke_puff'];
  let sawDefaultFull = false;
  for (let i = 0; i < CASES; i++) {
    const useDefault = i % 5 === 0;
    const max = useDefault ? undefined : 1 + Math.floor(r() * 150);
    const expectedMax = useDefault ? 1500 : max;
    const sys = Particles.createSystem({ seed: i, maxParticles: max });
    assert.strictEqual(sys.maxParticles, expectedMax);
    const steps = useDefault ? 40 : 25;
    for (let s = 0; s < steps; s++) {
      const before = sys.particles.map((p) => p.id);
      const name = useDefault ? pickFrom(r, big) : pickFrom(r, NAMES);
      const opts = useDefault ? { scale: 3 + r(), width: 700 } : randOpts(r);
      const ret = sys.emit(name, randCoord(r), randCoord(r), opts);
      const after = sys.particles.map((p) => p.id);
      assert.ok(after.length <= expectedMax, 'case ' + i + ' overflow ' + after.length);
      assert.ok(ret >= 1 && ret <= after.length, 'case ' + i + ' bad return ' + ret);
      for (let k = 1; k < after.length; k++) assert.ok(after[k] > after[k - 1], 'ids not ascending');
      const keptOld = after.length - ret;
      assert.deepStrictEqual(after.slice(0, keptOld), before.slice(before.length - keptOld),
        'case ' + i + ' did not drop the oldest');
      const newest = before.length ? before[before.length - 1] : 0;
      assert.ok(after.slice(keptOld).every((id) => id > newest), 'new ids must be newest');
      if (useDefault && after.length === expectedMax) sawDefaultFull = true;
      if (r() < 0.3) {
        sys.update(1 / 60);
        assert.ok(sys.particles.length <= expectedMax);
      }
    }
  }
  assert.ok(sawDefaultFull, 'default pool of 1500 was never filled, test is too weak');
});

for (const name of NAMES) {
  property('preset ' + name + ' emits >= 1 particle, all values finite', () => {
    const r = Particles.mulberry32(303 + name.length);
    for (let i = 0; i < CASES; i++) {
      const sys = Particles.createSystem({ seed: i });
      const opts = randOpts(r);
      const n = sys.emit(name, randCoord(r), randCoord(r), opts);
      assert.ok(n >= 1, name + ' emitted nothing');
      assert.strictEqual(sys.particles.length, n);
      for (const p of sys.particles) {
        checkParticle(p, name);
        assert.strictEqual(p.preset, name);
        assert.strictEqual(p.maxLife, p.life);
      }
      for (let s = 0; s < 5; s++) {
        sys.update(1 / 60);
        for (const p of sys.particles) checkParticle(p, name + ' after update');
      }
    }
  });
}

property('emit handles missing opts, bad coordinates and unknown presets', () => {
  const sys = Particles.createSystem({ seed: 5 });
  for (const name of NAMES) {
    assert.ok(sys.emit(name, 0, 0) >= 1);
    assert.ok(sys.emit(name, 0, 0, null) >= 1);
    assert.ok(sys.emit(name, 0, 0, 'junk') >= 1);
  }
  const len = sys.particles.length;
  for (const bad of [NaN, Infinity, -Infinity, 1e12, undefined, '5']) {
    assert.strictEqual(sys.emit('impact_burst', bad, 0), 0);
    assert.strictEqual(sys.emit('impact_burst', 0, bad), 0);
  }
  assert.strictEqual(sys.particles.length, len);
  assert.throws(() => sys.emit('nope', 0, 0), /Unknown particle preset/);
  assert.throws(() => sys.emit('__proto__', 0, 0), /Unknown particle preset/);
  assert.throws(() => sys.emit('toString', 0, 0), /Unknown particle preset/);
});

property('life strictly decreases, dead particles are removed, system drains', () => {
  const r = Particles.mulberry32(404);
  for (let i = 0; i < CASES; i++) {
    const sys = Particles.createSystem({ seed: i });
    const emits = 1 + Math.floor(r() * 4);
    for (let e = 0; e < emits; e++) emitRandom(sys, r);
    for (let s = 0; s < 30; s++) {
      const dt = 1 / 600 + r() * 0.25;
      const before = new Map(sys.particles.map((p) => [p.id, p.life]));
      sys.update(dt);
      const afterIds = new Set(sys.particles.map((p) => p.id));
      for (const p of sys.particles) {
        assert.ok(before.has(p.id), 'unknown particle appeared in update');
        assert.ok(p.life < before.get(p.id), 'life did not decrease');
        assert.strictEqual(p.life, before.get(p.id) - dt);
        assert.ok(p.life > 0, 'dead particle kept');
      }
      for (const [id, life] of before) {
        assert.strictEqual(afterIds.has(id), life - dt > 0, 'removal mismatch for id ' + id);
      }
      if (r() < 0.1) emitRandom(sys, r);
    }
    for (let s = 0; s < 200 && sys.particles.length > 0; s++) sys.update(0.5);
    assert.strictEqual(sys.particles.length, 0, 'case ' + i + ' did not drain');
  }
});

property('update ignores non-positive or non-finite dt; clear empties in place', () => {
  const sys = Particles.createSystem({ seed: 9 });
  sys.emit('impact_burst', 0, 0);
  const ref = sys.particles;
  const snap = snapshot(ref);
  for (const bad of [0, -1, NaN, Infinity, -Infinity, undefined, '1']) {
    sys.update(bad);
    assert.deepStrictEqual(snapshot(sys.particles), snap);
  }
  sys.clear();
  assert.strictEqual(sys.particles, ref, 'particles array must keep its identity');
  assert.strictEqual(ref.length, 0);
});

property('poison_cloud colours stay green (g channel dominant)', () => {
  const r = Particles.mulberry32(505);
  for (let i = 0; i < CASES; i++) {
    const sys = Particles.createSystem({ seed: i });
    const opts = Object.assign({}, randOpts(r), { dirX: r() < 0.5 ? -1 : 1 });
    sys.emit('poison_cloud', randCoord(r), randCoord(r), opts);
    assert.ok(sys.particles.length >= 2);
    for (let s = 0; s < 3; s++) {
      for (const p of sys.particles) {
        for (const c of [p.color, p.colorEnd]) {
          const [rr, g, b] = parseHex(c);
          assert.ok(g > rr && g > b, 'not green: ' + c);
        }
        for (const t of [0, 0.25, 0.5, 0.75, 1]) {
          const [rr, g, b] = Draw.lerpRgb(p.color, p.colorEnd, t);
          assert.ok(g > rr && g > b, 'blend not green at t=' + t);
        }
      }
      sys.update(1 / 60);
    }
  }
});

property('poison_cloud lingers for rounds * secondsPerRound (configurable)', () => {
  const r = Particles.mulberry32(515);
  for (let i = 0; i < CASES; i++) {
    const rounds = 1 + Math.floor(r() * 5);
    const perRound = 0.5 + r() * 3;
    const explicit = r() < 0.3 ? 0.5 + r() * 10 : undefined;
    const dur = explicit !== undefined ? explicit : rounds * perRound;
    const sys = Particles.createSystem({ seed: i });
    sys.emit('poison_cloud', 0, 0, { rounds, secondsPerRound: perRound, duration: explicit });
    const eps = 1e-9;
    for (const p of sys.particles) {
      assert.ok(p.life <= dur + eps, 'lives longer than the duration');
      assert.ok(p.life >= 0.7 * dur - eps, 'dies too early');
    }
    const longest = Math.max(...sys.particles.map((p) => p.life));
    assert.ok(longest >= 0.85 * dur, 'cloud never reaches near its duration');
  }
  // default: 3 rounds
  const sys = Particles.createSystem({ seed: 1 });
  sys.emit('poison_cloud', 0, 0);
  assert.ok(Math.max(...sys.particles.map((p) => p.life)) <= 6 + 1e-9);
  assert.ok(Math.max(...sys.particles.map((p) => p.life)) >= 0.85 * 6);
});

property('dart_rain x positions lie inside [x - width/2, x + width/2]', () => {
  const r = Particles.mulberry32(606);
  for (let i = 0; i < CASES; i++) {
    const sys = Particles.createSystem({ seed: i });
    const width = r() < 0.1 ? 1 + r() * 3 : 1 + r() * 2000;
    const x = (r() - 0.5) * 2000;
    const y = (r() - 0.5) * 2000;
    const n = sys.emit('dart_rain', x, y, { width, scale: 0.2 + r() * 3, dirX: r() < 0.5 ? -1 : 1 });
    assert.ok(n >= 12, 'dart_rain should be many streaks');
    for (const p of sys.particles) {
      assert.ok(p.x >= x - width / 2 && p.x <= x + width / 2, 'x ' + p.x + ' outside width ' + width + ' at ' + x);
      assert.strictEqual(p.shape, 'streak');
      assert.ok(p.vy > 0 && p.y < y, 'streaks must start above the zone and fall');
    }
  }
});

property('update(dt) in many small steps matches 1/60 steps within tolerance', () => {
  const r = Particles.mulberry32(707);
  const TOL = 1e-6;
  for (let i = 0; i < CASES; i++) {
    const frames = 1 + Math.floor(r() * 40);
    const k = 2 + Math.floor(r() * 19);
    const plan = [];
    for (let f = 0; f < frames; f++) {
      plan.push(r() < 0.3 ? [pickFrom(r, NAMES), randCoord(r), randCoord(r), randOpts(r)] : null);
    }
    plan[0] = ['impact_burst', 0, 0, { scale: 1 }];
    const run = (substeps) => {
      const sys = Particles.createSystem({ seed: 1000 + i });
      for (let f = 0; f < frames; f++) {
        if (plan[f]) sys.emit(plan[f][0], plan[f][1], plan[f][2], plan[f][3]);
        for (let s = 0; s < substeps; s++) sys.update(1 / 60 / substeps);
      }
      return new Map(sys.particles.map((p) => [p.id, Object.assign({}, p)]));
    };
    const a = run(1);
    const b = run(k);
    let shared = 0;
    for (const [id, pa] of a) {
      const pb = b.get(id);
      if (!pb) {
        assert.ok(pa.life < TOL, 'case ' + i + ': id ' + id + ' alive in 1/60 run only, life ' + pa.life);
        continue;
      }
      shared++;
      for (const key of NUMERIC_KEYS) {
        assert.ok(Math.abs(pa[key] - pb[key]) <= TOL * (1 + Math.abs(pa[key])),
          'case ' + i + ' k=' + k + ' ' + key + ': ' + pa[key] + ' vs ' + pb[key]);
      }
    }
    for (const [id, pb] of b) {
      if (!a.has(id)) assert.ok(pb.life < TOL, 'case ' + i + ': id ' + id + ' alive in split run only');
    }
    if (a.size > 0) assert.ok(shared > 0, 'case ' + i + ' shared no particles');
  }
});

property('presets do not mutate their opts (frozen opts accepted)', () => {
  const r = Particles.mulberry32(808);
  for (let i = 0; i < CASES; i++) {
    const opts = randOpts(r);
    const copy = JSON.stringify(opts);
    const sys = Particles.createSystem({ seed: i });
    sys.emit(pickFrom(r, NAMES), 0, 0, opts);
    assert.strictEqual(JSON.stringify(opts), copy);
  }
});

property('drawParticles: balanced save/restore, finite args, two blend modes, no mutation', () => {
  const r = Particles.mulberry32(909);
  for (let i = 0; i < 60; i++) {
    const sys = Particles.createSystem({ seed: i });
    for (const name of NAMES) sys.emit(name, 300 + r() * 100, 300 + r() * 100, randOpts(r));
    for (let s = 0; s < 6; s++) {
      const before = snapshot(sys.particles);
      const { ctx, calls, sets, state } = makeStubCtx();
      Draw.drawParticles(ctx, sys.particles);
      assert.deepStrictEqual(snapshot(sys.particles), before, 'draw mutated particles');
      assert.strictEqual(state.depth, 0, 'save/restore unbalanced');
      assert.ok(state.minDepth >= 0, 'restore without save');
      for (const c of calls) {
        for (const a of c.slice(1)) {
          if (typeof a === 'number') assert.ok(Number.isFinite(a), c[0] + ' got non-finite arg');
        }
      }
      for (const [prop, value] of sets) {
        if (typeof value === 'number') assert.ok(Number.isFinite(value), prop + ' set non-finite');
        if (prop === 'globalAlpha') assert.ok(value >= 0 && value <= 1, 'globalAlpha out of range');
        if (prop === 'globalCompositeOperation') {
          assert.ok(value === 'source-over' || value === 'lighter', 'unexpected blend ' + value);
        }
      }
      sys.update(0.07);
    }
  }
  // empty input draws nothing
  const empty = makeStubCtx();
  Draw.drawParticles(empty.ctx, []);
  assert.strictEqual(empty.calls.length, 0);
  // rings are stroked arcs, text is filled text, glow uses additive blending
  const sys = Particles.createSystem({ seed: 1 });
  sys.emit('shield_materialize_ripple', 100, 100);
  sys.emit('damage_number', 100, 100, { text: '42' });
  const stub = makeStubCtx();
  Draw.drawParticles(stub.ctx, sys.particles);
  const names = stub.calls.map((c) => c[0]);
  assert.ok(names.includes('arc') && names.includes('stroke'), 'ring should be a stroked arc');
  assert.ok(names.includes('fillText'), 'damage number should use fillText');
  assert.ok(stub.sets.some(([p, v]) => p === 'globalCompositeOperation' && v === 'lighter'));
});

property('new ultimate presets are deterministic, bounded, and start inside the canvas', () => {
  const ultimatePresets = [
    'ult_pip_socket', 'shock_ring', 'ghost_spear_fall', 'chain_hop_trail',
    'bell_toll_rings', 'soundwave_rings', 'bat_swarm', 'spark_electric', 'cross_spin_trail',
    'axe_spin_trail', 'boomerang_return'
  ];
  for (const name of ultimatePresets) {
    assert.ok(NAMES.includes(name), 'missing ultimate preset ' + name);
    for (let seed = 0; seed < CASES; seed++) {
      const options = { scale: 1, dirX: seed % 2 ? -1 : 1 };
      const a = Particles.createSystem({ seed });
      const b = Particles.createSystem({ seed });
      const count = a.emit(name, 960, 700, options);
      b.emit(name, 960, 700, options);
      assert.ok(count >= 1 && count <= 12, name + ' particle count is unbounded');
      assert.strictEqual(a.particles.length, count);
      assert.deepStrictEqual(snapshot(a.particles), snapshot(b.particles), name + ' is not deterministic');
      for (const particle of a.particles) {
        checkParticle(particle, name);
        assert.ok(particle.x >= 0 && particle.x <= 1920, name + ' x begins outside the canvas');
        assert.ok(particle.y >= 0 && particle.y <= 1080, name + ' y begins outside the canvas');
      }
    }
  }
});

property('element trail presets are deterministic, bounded, and start inside the canvas', () => {
  const elementTrails = [
    'trail_frost', 'trail_toxic', 'trail_shadow', 'trail_iron_sparks',
    'trail_soulfire', 'trail_holy_lightning'
  ];
  for (const name of elementTrails) {
    assert.ok(NAMES.includes(name), 'missing element trail ' + name);
    for (let seed = 0; seed < CASES; seed++) {
      const options = { scale: 0.1 + (seed % 40) / 10, dirX: seed % 2 ? -1 : 1 };
      const a = Particles.createSystem({ seed });
      const b = Particles.createSystem({ seed });
      const count = a.emit(name, seed % 2 ? 0 : 1920, seed % 3 ? 0 : 1080, options);
      b.emit(name, seed % 2 ? 0 : 1920, seed % 3 ? 0 : 1080, options);
      assert.strictEqual(count, 2, name + ' should stay compact');
      assert.deepStrictEqual(snapshot(a.particles), snapshot(b.particles), name + ' is not deterministic');
      for (const particle of a.particles) {
        checkParticle(particle, name);
        assert.ok(particle.x >= 0 && particle.x <= 1920, name + ' x begins outside the canvas');
        assert.ok(particle.y >= 0 && particle.y <= 1080, name + ' y begins outside the canvas');
      }
    }
  }
});

property('tinted sprite presets honor custom hex colors, dirX flip, and squash', () => {
  const sys = Particles.createSystem({ seed: 42 });
  sys.emit('sprite_slash_arc', 500, 400, { dirX: -1, color: '#ffd27a', colorEnd: '#ef4444' });
  sys.emit('sprite_arcane_seal', 600, 700, { squash: 0.4, color: '#e0ffff', colorEnd: '#00cec9' });
  sys.emit('sprite_star_ring', 700, 700, { squash: 0.38, color: 'bad', colorEnd: '#2ecc71' });
  assert.strictEqual(sys.particles.length, 6);
  assert.strictEqual(sys.particles[0].scaleX, -1);
  assert.strictEqual(sys.particles[0].colorEnd, '#ef4444');
  assert.strictEqual(sys.particles[2].scaleY, 0.4);
  assert.strictEqual(sys.particles[4].color, '#fef08a');   // invalid hex falls back cleanly
  assert.strictEqual(sys.particles[4].colorEnd, '#2ecc71');
  assert.strictEqual(sys.particles[4].scaleY, 0.38);

  const img = { complete: true, naturalWidth: 512, naturalHeight: 512, width: 512, height: 512 };
  Draw.setSprites({ fx_slash_arc: img, fx_arcane_circle: img, fx_star_ring: img });
  const stub = makeStubCtx();
  Draw.drawParticles(stub.ctx, sys.particles);
  Draw.setSprites({});
  assert.strictEqual(stub.state.depth, 0);
  assert.ok(stub.calls.some((c) => c[0] === 'scale' && c[1] === -1 && c[2] === 1));
  assert.ok(stub.calls.some((c) => c[0] === 'scale' && c[1] === 1 && c[2] === 0.4));
  assert.strictEqual(stub.calls.filter((c) => c[0] === 'drawImage').length, 6);
});

// ---------------------------------------------------------------------------
// runner

let failed = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('ok   ' + t.name);
  } catch (err) {
    failed++;
    console.log('FAIL ' + t.name);
    console.log('     ' + (err && err.stack ? err.stack.split('\n').slice(0, 4).join('\n     ') : err));
  }
}
console.log('\n' + (tests.length - failed) + '/' + tests.length + ' properties passed');
process.exit(failed ? 1 : 0);
