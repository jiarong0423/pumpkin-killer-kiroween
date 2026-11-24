'use strict';
/*
 * Tests for js/ultimate.js (the ultimate ledger). Spec: .kiro/specs/ultimate-ledger/requirements.md.
 * Node `assert` only, no DOM, no network. Seeded random scripts are compared with a small shadow model
 * written separately in this file. Run: node scripts/test_ultimate.js
 * Exit code 1 if any check fails.
 */
const assert = require('assert');
const path = require('path');
const Ultimate = require(path.join(__dirname, '..', 'js', 'ultimate.js'));

const R = Ultimate.REASONS;
const CASES = 300;

function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function ctxFor(side, round, extra) {
  return Object.assign({ turn: side, side, round, defendTurn: false, dead: false }, extra || {});
}

// Lights all pips of one side with fresh throw ids starting at `from`.
function light(ledger, side, from) {
  for (let i = 0; i < 3; i++) ledger.registerHit(side, from + i);
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

// ---------------------------------------------------------------------------
// requirements 1 to 5: pips

test('published constants and defaults', () => {
  assert.strictEqual(Ultimate.ULT_PIPS, 3);
  assert.strictEqual(Ultimate.ULT_MAX_PER_MATCH, 2);
  assert.strictEqual(Ultimate.ULT_PER_ROUND, 1);
  assert.strictEqual(Ultimate.ULT_COOLDOWN_ROUNDS, 0);
  assert.strictEqual(Ultimate.ULT_MULT, 1.5);
  const l = Ultimate.createLedger({ maxPips: 3, maxUses: 2 });
  assert.strictEqual(l.maxPips, 3);
  assert.strictEqual(l.maxUses, 2);
  const d = Ultimate.createLedger();
  assert.strictEqual(d.maxPips, 3);
  assert.strictEqual(d.maxUses, 2);
  assert.strictEqual(d.cooldownRounds, 0);
  for (const bad of [null, 5, 'x', { maxPips: 0 }, { maxPips: NaN, maxUses: -1 }]) {
    const b = Ultimate.createLedger(bad);
    assert.ok(b.maxPips >= 1 && b.maxUses >= 1);
  }
});

test('a hit adds one pip, three pips make it ready, the fourth hit adds nothing', () => {
  const l = Ultimate.createLedger({ maxPips: 3, maxUses: 2 });
  assert.deepStrictEqual(l.getState('player'), {
    ult_pips: 0, ult_ready: false, ult_armed: false, ultimates_remaining: 2, ultimates_used: 0, ult_used_this_round: false
  });
  assert.deepStrictEqual(l.registerHit('player', 1), { counted: true, pips: 1, reason: null });
  assert.strictEqual(l.registerHit('player', 2).pips, 2);
  assert.strictEqual(l.getState('player').ult_ready, false);
  assert.strictEqual(l.registerHit('player', 3).pips, 3);
  assert.strictEqual(l.getState('player').ult_ready, true);
  const full = l.registerHit('player', 4);
  assert.deepStrictEqual(full, { counted: false, pips: 3, reason: R.PIPS_FULL });
  assert.strictEqual(l.getState('player').ult_pips, 3);
});

test('the same throwId never counts twice (also when it arrives after the pips are full)', () => {
  const l = Ultimate.createLedger();
  assert.strictEqual(l.registerHit('player', 7).counted, true);
  assert.deepStrictEqual(l.registerHit('player', 7), { counted: false, pips: 1, reason: R.DUPLICATE_THROW });
  assert.strictEqual(l.registerHit('player', 7).pips, 1);
  l.registerHit('player', 8);
  l.registerHit('player', 9);
  l.registerHit('player', 10);   // pips already full: id 10 is remembered
  assert.strictEqual(l.getState('player').ult_pips, 3);
  l.arm('player', ctxFor('player', 4));
  l.consume('player', 4);        // pips back to 0
  assert.strictEqual(l.registerHit('player', 10).counted, false, 'a late hit of an old throw gives nothing');
  assert.strictEqual(l.registerHit('player', 11).counted, true);
  // string ids work, and 5 and "5" are different ids
  assert.strictEqual(l.registerHit('ai', 5).counted, true);
  assert.strictEqual(l.registerHit('ai', '5').counted, true);
  assert.strictEqual(l.registerHit('ai', 'a').counted, true);
  assert.strictEqual(l.registerHit('ai', 'a').reason, R.DUPLICATE_THROW);
});

test('each side counts its own pips', () => {
  const l = Ultimate.createLedger();
  l.registerHit('player', 1);
  l.registerHit('player', 2);
  l.registerHit('ai', 3);
  assert.strictEqual(l.getState('player').ult_pips, 2);
  assert.strictEqual(l.getState('ai').ult_pips, 1);
  l.registerKO('player');
  assert.strictEqual(l.getState('player').ult_pips, 0);
  assert.strictEqual(l.getState('ai').ult_pips, 1, 'the other side is untouched');
});

test('bad throw ids and unknown sides are refused without changing anything', () => {
  const l = Ultimate.createLedger();
  for (const id of [undefined, null, NaN, Infinity, '', {}, [], true]) {
    const r = l.registerHit('player', id);
    assert.strictEqual(r.counted, false);
    assert.strictEqual(r.reason, R.BAD_THROW_ID);
  }
  for (const side of ['red', '', undefined, null, 5, {}, '__proto__', 'constructor', 'toString']) {
    assert.strictEqual(l.registerHit(side, 1).reason, R.UNKNOWN_SIDE);
    assert.strictEqual(l.canArm(side, ctxFor('player', 1)).reason, R.UNKNOWN_SIDE);
    assert.strictEqual(l.arm(side, ctxFor('player', 1)).reason, R.UNKNOWN_SIDE);
    assert.strictEqual(l.cancel(side).reason, R.UNKNOWN_SIDE);
    assert.strictEqual(l.consume(side, 1).reason, R.UNKNOWN_SIDE);
    assert.strictEqual(l.registerKO(side).reason, R.UNKNOWN_SIDE);
    assert.strictEqual(l.getState(side), null);
  }
  assert.strictEqual(l.getState('player').ult_pips, 0);
});

test('custom sides are possible (red / white as in the MCP server)', () => {
  const l = Ultimate.createLedger({ sides: ['red', 'white'] });
  l.registerHit('red', 1);
  assert.strictEqual(l.getState('red').ult_pips, 1);
  assert.strictEqual(l.getState('player'), null);
});

// ---------------------------------------------------------------------------
// requirements 6 to 12: arming

test('arming needs three pips: otherwise ultimate_not_ready', () => {
  const l = Ultimate.createLedger();
  for (let n = 0; n < 3; n++) {
    const r = l.canArm('player', ctxFor('player', 1));
    assert.deepStrictEqual(r, { ok: false, reason: R.NOT_READY });
    assert.deepStrictEqual(l.arm('player', ctxFor('player', 1)), { ok: false, reason: R.NOT_READY });
    assert.strictEqual(l.getState('player').ult_armed, false);
    l.registerHit('player', 100 + n);
  }
  assert.deepStrictEqual(l.canArm('player', ctxFor('player', 1)), { ok: true, reason: null });
  assert.strictEqual(l.getState('player').ult_armed, false, 'canArm alone never arms');
  assert.deepStrictEqual(l.arm('player', ctxFor('player', 1)), { ok: true, reason: null });
  assert.strictEqual(l.getState('player').ult_armed, true);
});

test('arming only on the side own turn (wrong_phase)', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  assert.strictEqual(l.canArm('player', ctxFor('player', 2, { turn: 'ai' })).reason, R.WRONG_PHASE);
  assert.strictEqual(l.canArm('player', ctxFor('player', 2, { turn: 'busy' })).reason, R.WRONG_PHASE);
  assert.strictEqual(l.canArm('player', ctxFor('player', 2, { turn: undefined })).reason, R.WRONG_PHASE);
  assert.strictEqual(l.canArm('player', ctxFor('player', 2, { side: 'ai' })).reason, R.WRONG_PHASE);
  assert.strictEqual(l.canArm('player', ctxFor('player', 2)).ok, true);
  assert.strictEqual(l.arm('player', ctxFor('player', 2, { turn: 'ai' })).ok, false);
  assert.strictEqual(l.getState('player').ult_armed, false);
  // ctx.side may be left out
  assert.strictEqual(l.canArm('player', { turn: 'player', round: 2 }).ok, true);
});

test('never on a defend turn, never when dead', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  assert.strictEqual(l.canArm('player', ctxFor('player', 3, { defendTurn: true })).reason, R.WITH_DEFEND);
  assert.strictEqual(l.canArm('player', ctxFor('player', 3, { dead: true })).reason, R.DEAD);
  assert.strictEqual(l.arm('player', ctxFor('player', 3, { dead: true })).ok, false);
  assert.strictEqual(l.getState('player').ult_pips, 3, 'pips are kept when arming is refused');
  assert.strictEqual(l.canArm('player', ctxFor('player', 3)).ok, true);
});

test('bad contexts are refused', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  for (const c of [undefined, null, 5, 'x']) assert.strictEqual(l.canArm('player', c).reason, R.BAD_CONTEXT);
  for (const round of [undefined, NaN, Infinity, 'a', null]) {
    assert.strictEqual(l.canArm('player', ctxFor('player', round)).reason, R.BAD_ROUND);
  }
  assert.strictEqual(l.consume('player', NaN).reason, R.BAD_ROUND);
});

test('armed state can be cancelled for free; it cannot be armed twice', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  l.arm('player', ctxFor('player', 2));
  assert.deepStrictEqual(l.arm('player', ctxFor('player', 2)), { ok: false, reason: R.ALREADY_ARMED });
  assert.deepStrictEqual(l.cancel('player'), { ok: true, wasArmed: true, reason: null });
  const s = l.getState('player');
  assert.strictEqual(s.ult_armed, false);
  assert.strictEqual(s.ult_pips, 3);
  assert.strictEqual(s.ultimates_used, 0);
  assert.deepStrictEqual(l.cancel('player'), { ok: true, wasArmed: false, reason: null });
  assert.strictEqual(l.arm('player', ctxFor('player', 2)).ok, true, 'it can be armed again after a cancel');
});

test('lockout: no round-1 lockout, no back-to-back lockout, one use per side per round', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  assert.strictEqual(l.arm('player', ctxFor('player', 1)).ok, true, 'round 1 is allowed');
  assert.strictEqual(l.consume('player', 1).ok, true);
  light(l, 'player', 10);   // three more hits in the same round
  assert.deepStrictEqual(l.canArm('player', ctxFor('player', 1)), { ok: false, reason: R.USED_THIS_ROUND });
  assert.strictEqual(l.getState('player', 1).ult_used_this_round, true);
  assert.strictEqual(l.getState('player', 2).ult_used_this_round, false);
  assert.strictEqual(l.canArm('player', ctxFor('player', 2)).ok, true, 'the next round is allowed, no back-to-back lockout');
  // the other side is not limited by this side's use
  light(l, 'ai', 20);
  assert.strictEqual(l.canArm('ai', ctxFor('ai', 1)).ok, true, 'both sides may fire in the same round');
});

test('cooldownRounds is the one lever: 0 by default, N blocks the next N rounds', () => {
  const l = Ultimate.createLedger({ cooldownRounds: 2 });
  assert.strictEqual(l.cooldownRounds, 2);
  light(l, 'player', 1);
  l.arm('player', ctxFor('player', 3));
  l.consume('player', 3);
  light(l, 'player', 10);
  assert.strictEqual(l.canArm('player', ctxFor('player', 3)).reason, R.USED_THIS_ROUND);
  assert.strictEqual(l.canArm('player', ctxFor('player', 4)).reason, R.COOLDOWN);
  assert.strictEqual(l.canArm('player', ctxFor('player', 5)).reason, R.COOLDOWN);
  assert.strictEqual(l.canArm('player', ctxFor('player', 6)).ok, true);
});

// ---------------------------------------------------------------------------
// requirements 13 to 17: spending

test('consume spends the armed ultimate: pips to 0, used count up, hit or miss alike', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  assert.deepStrictEqual(l.consume('player', 2), { ok: false, reason: R.NOT_ARMED }, 'cannot spend what is not armed');
  assert.strictEqual(l.getState('player').ult_pips, 3);
  l.arm('player', ctxFor('player', 2));
  assert.deepStrictEqual(l.consume('player', 2, 50), { ok: true, reason: null, uses: 1, remaining: 1 });
  assert.deepStrictEqual(l.getState('player', 2), {
    ult_pips: 0, ult_ready: false, ult_armed: false, ultimates_remaining: 1, ultimates_used: 1, ult_used_this_round: true
  });
  assert.deepStrictEqual(l.consume('player', 2), { ok: false, reason: R.NOT_ARMED }, 'a second spend needs a new arming');
});

test('the ultimate throw itself gives no pip (its throwId is blocked)', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  l.arm('player', ctxFor('player', 2));
  l.consume('player', 2, 99);
  assert.strictEqual(l.registerHit('player', 99).counted, false);
  assert.strictEqual(l.registerHit('player', 99).reason, R.DUPLICATE_THROW);
  assert.strictEqual(l.getState('player').ult_pips, 0);
  assert.strictEqual(l.registerHit('player', 100).counted, true, 'the next normal throw counts again');
});

test('at most two uses per side per match; then pips stop counting and arming is refused', () => {
  const l = Ultimate.createLedger({ maxPips: 3, maxUses: 2 });
  light(l, 'player', 1);
  l.arm('player', ctxFor('player', 2));
  l.consume('player', 2);
  light(l, 'player', 10);
  l.arm('player', ctxFor('player', 5));
  l.consume('player', 5);
  const s = l.getState('player');
  assert.strictEqual(s.ultimates_remaining, 0);
  assert.strictEqual(s.ultimates_used, 2);
  const late = l.registerHit('player', 20);
  assert.deepStrictEqual(late, { counted: false, pips: 0, reason: R.NO_LEFT });
  assert.strictEqual(l.getState('player').ult_pips, 0);
  assert.strictEqual(l.canArm('player', ctxFor('player', 9)).reason, R.NO_LEFT);
  assert.strictEqual(l.getState('player').ult_ready, false);
  // the other side still has both
  assert.strictEqual(l.getState('ai').ultimates_remaining, 2);
});

test('a KO loses the pips and the arming but does not spend a use', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  l.arm('player', ctxFor('player', 2));
  assert.deepStrictEqual(l.registerKO('player'), { ok: true, reason: null });
  assert.deepStrictEqual(l.getState('player', 2), {
    ult_pips: 0, ult_ready: false, ult_armed: false, ultimates_remaining: 2, ultimates_used: 0, ult_used_this_round: false
  });
  assert.strictEqual(l.consume('player', 2).reason, R.NOT_ARMED);
  assert.strictEqual(l.canArm('player', ctxFor('player', 3)).reason, R.NOT_READY);
});

test('getState: exact field names, a copy each time, round defaults to the last round seen', () => {
  const l = Ultimate.createLedger();
  const names = ['ult_armed', 'ult_pips', 'ult_ready', 'ult_used_this_round', 'ultimates_remaining', 'ultimates_used'];
  assert.deepStrictEqual(Object.keys(l.getState('player')).sort(), names);
  const s = l.getState('player');
  s.ult_pips = 99;
  s.ultimates_used = 99;
  assert.strictEqual(l.getState('player').ult_pips, 0, 'mutating the returned object changes nothing');
  light(l, 'player', 1);
  l.arm('player', ctxFor('player', 6));
  l.consume('player', 6);
  assert.strictEqual(l.getState('player').ult_used_this_round, true, 'last round seen was 6');
  assert.strictEqual(l.getState('player', 7).ult_used_this_round, false);
  for (const v of Object.values(l.getState('player'))) assert.ok(typeof v === 'boolean' || Number.isInteger(v));
});

test('reset clears every side, every pip and every remembered throw id', () => {
  const l = Ultimate.createLedger();
  light(l, 'player', 1);
  light(l, 'ai', 5);
  l.arm('player', ctxFor('player', 2));
  l.consume('player', 2);
  l.reset();
  for (const side of ['player', 'ai']) {
    assert.deepStrictEqual(l.getState(side), {
      ult_pips: 0, ult_ready: false, ult_armed: false, ultimates_remaining: 2, ultimates_used: 0, ult_used_this_round: false
    });
  }
  assert.strictEqual(l.registerHit('player', 1).counted, true, 'old throw ids are forgotten');
});

test('splitDamage: 1.5 x normal shared over the strikes, rounded to 0.1', () => {
  assert.strictEqual(Ultimate.splitDamage(24, 3), 12);
  assert.strictEqual(Ultimate.splitDamage(18, 3), 9);
  assert.strictEqual(Ultimate.splitDamage(26, 5), 7.8);
  assert.strictEqual(Ultimate.splitDamage(20, 5), 6);
  assert.strictEqual(Ultimate.splitDamage(28, 1), 42);
  for (const [n, k] of [[NaN, 3], [-5, 3], [24, 0], [24, NaN], [24, -2], [Infinity, 2], [undefined, undefined]]) {
    const v = Ultimate.splitDamage(n, k);
    assert.ok(Number.isFinite(v) && v >= 0, 'splitDamage(' + n + ', ' + k + ') = ' + v);
  }
});

// ---------------------------------------------------------------------------
// purity and robustness

test('no Math.random and no Date: replacing them with throwers changes nothing', () => {
  const rnd = Math.random;
  const DateOrig = global.Date;
  Math.random = () => { throw new Error('Math.random used'); };
  global.Date = function () { throw new Error('Date used'); };
  global.Date.now = () => { throw new Error('Date.now used'); };
  try {
    const l = Ultimate.createLedger();
    light(l, 'player', 1);
    l.arm('player', ctxFor('player', 2));
    l.consume('player', 2, 9);
    l.registerKO('ai');
    l.getState('player');
    l.reset();
  } finally {
    Math.random = rnd;
    global.Date = DateOrig;
  }
});

test('garbage arguments never throw and never change the state', () => {
  const junk = [undefined, null, NaN, Infinity, -Infinity, 0, -1, 1.5, '', 'x', {}, [], true, false, () => 1, Symbol.iterator, 1e308];
  const l = Ultimate.createLedger({ maxPips: 3, maxUses: 2 });
  light(l, 'player', 1);
  const before = JSON.stringify([l.getState('player'), l.getState('ai')]);
  for (const a of junk) {
    for (const b of junk) {
      let sideSym = typeof a === 'symbol' ? 'x' : a;   // a symbol cannot be turned into a string key
      assert.doesNotThrow(() => {
        l.registerHit(sideSym, b);
        l.canArm(sideSym, b);
        l.arm(sideSym, b);
        l.cancel(sideSym);
        l.consume(sideSym, b);
        l.registerKO(sideSym);
        l.getState(sideSym, b);
      });
    }
  }
  assert.strictEqual(JSON.stringify([l.getState('player'), l.getState('ai')]), before);
  assert.doesNotThrow(() => Ultimate.createLedger({ sides: 5 }));
  assert.doesNotThrow(() => Ultimate.createLedger({ sides: [1, null, ''] }));
});

// ---------------------------------------------------------------------------
// seeded random scripts against a shadow model (written separately from the module)

function makeModel(cfg) {
  const st = {};
  for (const s of ['player', 'ai']) st[s] = { pips: 0, uses: 0, armed: false, last: null, ids: new Set() };
  return {
    hit(side, id) {
      const s = st[side];
      if (s.ids.has(id)) return false;
      s.ids.add(id);
      if (s.uses >= cfg.maxUses || s.pips >= cfg.maxPips) return false;
      s.pips++;
      return true;
    },
    can(side, c) {
      const s = st[side];
      if (c.turn !== side) return R.WRONG_PHASE;
      if (c.dead) return R.DEAD;
      if (c.defendTurn) return R.WITH_DEFEND;
      if (s.armed) return R.ALREADY_ARMED;
      if (s.uses >= cfg.maxUses) return R.NO_LEFT;
      if (s.last === c.round) return R.USED_THIS_ROUND;
      if (cfg.cooldown > 0 && s.last !== null && c.round - s.last <= cfg.cooldown) return R.COOLDOWN;
      if (s.pips < cfg.maxPips) return R.NOT_READY;
      return null;
    },
    arm(side, c) { const r = this.can(side, c); if (!r) st[side].armed = true; return r; },
    cancel(side) { st[side].armed = false; },
    consume(side, round, id) {
      const s = st[side];
      if (!s.armed) return R.NOT_ARMED;
      s.armed = false; s.pips = 0; s.uses++; s.last = round;
      if (id !== undefined) s.ids.add(id);
      return null;
    },
    ko(side) { st[side].pips = 0; st[side].armed = false; },
    state(side, round) {
      const s = st[side];
      return {
        ult_pips: s.pips, ult_ready: s.pips >= cfg.maxPips && s.uses < cfg.maxUses, ult_armed: s.armed,
        ultimates_remaining: Math.max(0, cfg.maxUses - s.uses), ultimates_used: s.uses,
        ult_used_this_round: s.last !== null && s.last === round
      };
    }
  };
}

test('property: 300 random scripts agree with the shadow model and keep the invariants', () => {
  const r = mulberry32(4242);
  for (let c = 0; c < CASES; c++) {
    const cfg = { maxPips: 1 + Math.floor(r() * 4), maxUses: 1 + Math.floor(r() * 3), cooldown: r() < 0.3 ? Math.floor(r() * 3) : 0 };
    const ledger = Ultimate.createLedger({ maxPips: cfg.maxPips, maxUses: cfg.maxUses, cooldownRounds: cfg.cooldown });
    const model = makeModel(cfg);
    let round = 1;
    let nextId = 1;
    const steps = 20 + Math.floor(r() * 80);
    for (let i = 0; i < steps; i++) {
      const side = r() < 0.5 ? 'player' : 'ai';
      const op = r();
      if (op < 0.4) {
        const id = r() < 0.2 ? Math.max(1, nextId - 1 - Math.floor(r() * 3)) : nextId++;   // sometimes a repeated id
        const got = ledger.registerHit(side, id).counted;
        assert.strictEqual(got, model.hit(side, id), 'case ' + c + ' step ' + i + ': registerHit');
      } else if (op < 0.65) {
        const ctx = { turn: r() < 0.85 ? side : (side === 'player' ? 'ai' : 'player'), side, round, defendTurn: r() < 0.1, dead: r() < 0.05 };
        const got = ledger.arm(side, ctx);
        const want = model.arm(side, ctx);
        assert.strictEqual(got.reason, want, 'case ' + c + ' step ' + i + ': arm ' + JSON.stringify(ctx));
        assert.strictEqual(got.ok, want === null);
      } else if (op < 0.75) {
        ledger.cancel(side);
        model.cancel(side);
      } else if (op < 0.88) {
        const id = r() < 0.5 ? nextId++ : undefined;
        const got = ledger.consume(side, round, id);
        const want = model.consume(side, round, id);
        assert.strictEqual(got.reason, want, 'case ' + c + ' step ' + i + ': consume');
      } else if (op < 0.93) {
        ledger.registerKO(side);
        model.ko(side);
      } else {
        round++;
      }
      for (const sd of ['player', 'ai']) {
        const s = ledger.getState(sd, round);
        assert.deepStrictEqual(s, model.state(sd, round), 'case ' + c + ' step ' + i + ': state of ' + sd);
        assert.ok(s.ult_pips >= 0 && s.ult_pips <= cfg.maxPips, 'pips out of range');
        assert.ok(s.ultimates_used <= cfg.maxUses, 'more uses than allowed');
        assert.strictEqual(s.ultimates_used + s.ultimates_remaining, cfg.maxUses);
        if (s.ult_armed) assert.strictEqual(s.ult_pips, cfg.maxPips, 'an armed unit must have full pips');
        if (s.ult_ready) assert.strictEqual(s.ult_pips, cfg.maxPips);
      }
    }
  }
});

test('property: same script, same results (deterministic)', () => {
  const run = (seed) => {
    const r = mulberry32(seed);
    const l = Ultimate.createLedger();
    const out = [];
    let round = 1;
    for (let i = 0; i < 60; i++) {
      const side = r() < 0.5 ? 'player' : 'ai';
      const op = Math.floor(r() * 5);
      if (op === 0) out.push(l.registerHit(side, Math.floor(r() * 20)));
      else if (op === 1) out.push(l.arm(side, ctxFor(side, round)));
      else if (op === 2) out.push(l.consume(side, round));
      else if (op === 3) out.push(l.cancel(side));
      else round++;
      out.push(l.getState(side, round));
    }
    return JSON.stringify(out);
  };
  for (let seed = 1; seed <= 50; seed++) assert.strictEqual(run(seed), run(seed));
  assert.notStrictEqual(run(1), run(2));
});

// ---------------------------------------------------------------------------

let failed = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('ok   - ' + t.name);
  } catch (err) {
    failed++;
    console.log('FAIL - ' + t.name + '\n       ' + (err && err.stack ? err.stack.split('\n').slice(0, 4).join('\n       ') : err));
  }
}
if (failed > 0) {
  console.log('test_ultimate: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_ultimate: all ' + tests.length + ' tests passed');
