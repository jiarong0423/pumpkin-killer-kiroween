'use strict';
/* Tests for the DOM-free knight A/B/C shield state machine. Run: node scripts/test_knight_ult.js */
const assert = require('assert');
const path = require('path');
const KnightUlt = require(path.join(__dirname, '..', 'js', 'knight_ult.js'));

const K = KnightUlt;
const R = K.REASONS;
const CASES = 300;
const remembered = [
  [{ x: 0, y: 600 }, { x: 600, y: 600 }],
  [{ x: 0, y: 650 }, { x: 600, y: 650 }]
];

function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function ctx(extra) {
  return Object.assign({ ownTurn: true, defendMode: true, dead: false, rememberedPaths: remembered }, extra || {});
}
function line(a, b) { return [{ x: a, y: 600 }, { x: b, y: 600 }]; }
function ready(extra) {
  return K.createKnightUlt(Object.assign({ pips: 3, knightId: 'knight', teamIds: ['knight', 'teammate'] }, extra || {}));
}
function attack(extra) {
  return Object.assign({ projectilePath: line(0, 0), targetId: 'knight' }, extra || {});
}
function placeAndLock(ult, s, pathId) {
  assert.strictEqual(ult.place(pathId === undefined ? 0 : pathId, s).ok, true);
  return ult.lock();
}
function lockPlan(ult, positions) {
  assert.strictEqual(ult.begin(ctx()).ok, true);
  for (const s of positions) placeAndLock(ult, s);
  if (positions.length < 3) ult.endTurn();
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

test('requirement 10: placement needs three pips, own turn, defend mode, and remembered paths', () => {
  assert.strictEqual(K.REQUIRED_PIPS, 3);
  const ult = K.createKnightUlt({ knightId: 'knight', teamIds: ['knight'] });
  assert.strictEqual(ult.begin(ctx()).reason, R.NOT_READY);
  ult.setPips(3);
  assert.strictEqual(ult.begin(ctx({ ownTurn: false })).reason, R.WRONG_PHASE);
  assert.strictEqual(ult.begin(ctx({ defendMode: false })).reason, R.NOT_DEFENDING);
  assert.strictEqual(ult.begin(ctx({ rememberedPaths: [] })).reason, R.NO_PATHS);
  assert.strictEqual(ult.begin(ctx()).ok, true);
  assert.strictEqual(ult.place(0, 0.5).ok, true);
  assert.strictEqual(ult.place(8, 0.5).reason, R.BAD_PATH);
  assert.strictEqual(ult.place(0, -0.01).reason, R.BAD_POINT);
  assert.strictEqual(ult.place(0, 1.01).reason, R.BAD_POINT);
});

test('requirement 11: third lock spends pips and a pre-third cancel is free', () => {
  const cancelled = ready();
  assert.strictEqual(cancelled.begin(ctx()).ok, true);
  placeAndLock(cancelled, 0.2);
  assert.strictEqual(cancelled.cancel().ok, true);
  assert.deepStrictEqual(cancelled.getStatus(), { state: 'idle', pips: 3, uses: 0, pointsPlaced: 0, attacksAnswered: 0 });

  const ult = ready();
  assert.strictEqual(ult.begin(ctx()).ok, true);
  assert.strictEqual(placeAndLock(ult, 0.2).spent, false);
  assert.strictEqual(placeAndLock(ult, 0.5).spent, false);
  const third = placeAndLock(ult, 0.8);
  assert.deepStrictEqual(third, { ok: true, reason: null, spent: true, uses: 1, pointsPlaced: 3 });
  assert.strictEqual(ult.getStatus().pips, 0);
  assert.strictEqual(ult.getStatus().uses, 1);
  assert.strictEqual(ult.getStatus().state, 'locked');
});

test('requirement 12: ending early keeps committed points and spends only with one or more points', () => {
  const none = ready();
  none.begin(ctx());
  assert.deepStrictEqual(none.endTurn(), { ok: true, reason: null, spent: false, pointsPlaced: 0 });
  assert.strictEqual(none.getStatus().pips, 3);
  assert.strictEqual(none.getStatus().uses, 0);

  const partial = ready();
  partial.begin(ctx());
  placeAndLock(partial, 0.2);
  assert.deepStrictEqual(partial.endTurn(), { ok: true, reason: null, spent: true, uses: 1, pointsPlaced: 1 });
  assert.deepStrictEqual(partial.publicView(), { ult_points_left: 1 });
  assert.strictEqual(partial.getStatus().pips, 0);
});

test('requirement 13: the oldest unused point is checked first using the 70 px zone', () => {
  assert.strictEqual(K.POINT_HALF_WIDTH, 70);
  const ult = ready();
  lockPlan(ult, [0.2, 0.5, 0.8]);
  const skipOldest = ult.answer(attack({ throwId: 'one', projectilePath: line(290, 310), time: 2 }));
  assert.strictEqual(skipOldest.blocked, false, 'B cannot jump ahead of A');
  assert.strictEqual(ult.publicView().ult_points_left, 3);
  const blockA = ult.answer(attack({ throwId: 'two', projectilePath: line(49, 51), time: 3 }));
  assert.strictEqual(blockA.blocked, true, 'the zone includes its 70 px edge');
  assert.strictEqual(blockA.reveal.x, 120);
  const blockB = ult.answer(attack({ throwId: 'three', projectilePath: line(299, 301), time: 4 }));
  assert.strictEqual(blockB.blocked, true);
  assert.strictEqual(blockB.reveal.x, 300);
  assert.deepStrictEqual(ult.publicView(), { ult_points_left: 0 }, 'three relevant attacks expire the remaining plan');
});

test('requirement 14: one point blocks at most one first projectile, never an extra projectile', () => {
  const ult = ready();
  lockPlan(ult, [0.5]);
  const extra = ult.answer(attack({ throwId: 1, projectileIndex: 1, projectilePath: line(290, 310), time: 1 }));
  assert.deepStrictEqual(extra, { ok: true, reason: R.NOT_FIRST_PROJECTILE, blocked: false });
  assert.strictEqual(ult.getStatus().attacksAnswered, 0);
  const first = ult.answer(attack({ throwId: 1, projectileIndex: 0, projectilePath: line(290, 310), time: 2 }));
  assert.strictEqual(first.blocked, true);
  assert.strictEqual(ult.answer(attack({ throwId: 1, projectileIndex: 2, projectilePath: line(290, 310), time: 2.1 })).blocked, false);
  assert.strictEqual(ult.answer(attack({ throwId: 1, projectileIndex: 0, projectilePath: line(290, 310), time: 2.2 })).reason, R.NOT_LOCKED);
});

test('requirement 15: public state contains only the remaining count and a block reveal lasts 1.4 seconds', () => {
  const ult = ready();
  lockPlan(ult, [0.5]);
  const publicState = ult.publicView();
  assert.deepStrictEqual(Object.keys(publicState), ['ult_points_left']);
  assert.strictEqual(JSON.stringify(publicState).includes('x'), false);
  assert.strictEqual(JSON.stringify(publicState).includes('y'), false);
  const block = ult.answer(attack({ projectilePath: line(290, 310), time: 10 }));
  assert.deepStrictEqual(block.reveal, { x: 300, y: 600 });
  assert.strictEqual(block.reveal_seconds, 1.4);
  assert.deepStrictEqual(ult.getReveal(11.4), { position: { x: 300, y: 600 }, until: 11.4 });
  assert.strictEqual(ult.getReveal(11.401), null);
  assert.deepStrictEqual(ult.publicView(), { ult_points_left: 0 });
});

test('requirement 16: unused points expire after three enemy attacks or immediately on a knockout', () => {
  const expires = ready();
  lockPlan(expires, [0.2, 0.5, 0.8]);
  for (let i = 0; i < 3; i++) {
    assert.strictEqual(expires.answer(attack({ throwId: i, projectilePath: line(800, 900), time: i })).blocked, false);
  }
  assert.deepStrictEqual(expires.publicView(), { ult_points_left: 0 });
  assert.strictEqual(expires.getStatus().state, 'spent');

  const ko = ready();
  lockPlan(ko, [0.2, 0.5]);
  assert.strictEqual(ko.registerKO().ok, true);
  assert.strictEqual(ko.getStatus().pips, 0, 'a knockout loses the armed pips');
  assert.deepStrictEqual(ko.publicView(), { ult_points_left: 0 });
  assert.strictEqual(ko.getStatus().state, 'spent');
});

test('requirement 17: identical inputs give identical outputs', () => {
  const run = () => {
    const ult = ready();
    const out = [ult.begin(ctx())];
    for (const s of [0.2, 0.5, 0.8]) out.push(ult.place(0, s), ult.lock());
    out.push(ult.answer(attack({ projectilePath: line(115, 125), time: 4 })));
    out.push(ult.answer(attack({ throwId: 'b', projectilePath: line(1000, 1100), time: 5 })));
    out.push(ult.getReveal(5), ult.publicView(), ult.getStatus());
    return JSON.stringify(out);
  };
  assert.strictEqual(run(), run());
});

test('requirement 21: placement allows back-and-forth positions', () => {
  const ult = ready();
  assert.strictEqual(ult.begin(ctx()).ok, true);
  placeAndLock(ult, 0.8);
  placeAndLock(ult, 0.2);
  placeAndLock(ult, 0.5);
  const first = ult.answer(attack({ projectilePath: line(475, 485) }));
  assert.strictEqual(first.blocked, true, 'A is at s=0.8 even though B is earlier at s=0.2');
  assert.deepStrictEqual(first.reveal, { x: 480, y: 600 });
  const same = ready();
  assert.strictEqual(same.begin(ctx()).ok, true);
  placeAndLock(same, 0.5); placeAndLock(same, 0.5); placeAndLock(same, 0.5);
  assert.strictEqual(same.getStatus().pointsPlaced, 3, 'two points may share a position');
});

test('requirement 22: point protects a teammate', () => {
  const ult = ready();
  lockPlan(ult, [0.5]);
  const block = ult.answer(attack({ projectilePath: line(290, 310), targetId: 'teammate' }));
  assert.strictEqual(block.blocked, true, 'the projectile need not pass near the knight');

  const oneVsOne = K.createKnightUlt({ pips: 3, knightId: 'knight', teamIds: ['knight'] });
  lockPlan(oneVsOne, [0.5]);
  assert.strictEqual(oneVsOne.answer(attack({ projectilePath: line(290, 310), targetId: 'teammate' })).blocked, false);
});

test('requirement 22: attack aimed at another team is not blocked', () => {
  const ult = ready();
  lockPlan(ult, [0.5]);
  const miss = ult.answer(attack({ projectilePath: line(290, 310), targetId: 'enemy' }));
  assert.strictEqual(miss.blocked, false);
  assert.deepStrictEqual(ult.publicView(), { ult_points_left: 1 }, 'another team does not consume a point');
  assert.strictEqual(ult.answer(attack({ projectilePath: line(290, 310), targetId: 'teammate' })).blocked, true);
});

test('no Math.random, Date, DOM, or implicit clock is used', () => {
  const random = Math.random;
  const OriginalDate = global.Date;
  Math.random = () => { throw new Error('Math.random used'); };
  global.Date = function () { throw new Error('Date used'); };
  global.Date.now = () => { throw new Error('Date.now used'); };
  try {
    const ult = ready();
    ult.begin(ctx());
    placeAndLock(ult, 0.2);
    ult.endTurn();
    ult.answer(attack({ projectilePath: line(110, 130), time: 0 }));
  } finally {
    Math.random = random;
    global.Date = OriginalDate;
  }
});

function makeShadow() {
  return { pips: 3, uses: 0, state: 'idle', points: [], pending: null, answered: 0, throws: new Set() };
}
function shadowStatus(s) {
  return { state: s.state, pips: s.pips, uses: s.uses, pointsPlaced: s.points.length, attacksAnswered: s.answered };
}
function shadowPublic(s) { return { ult_points_left: s.state === 'locked' ? s.points.length : 0 }; }
function shadowBegin(s) {
  if ((s.state === 'idle' || s.state === 'spent') && s.uses < 2 && s.pips >= 3) {
    s.state = 'placing'; s.points = []; s.pending = null; s.answered = 0; s.throws = new Set(); return true;
  }
  return false;
}
function shadowPlace(s, position) {
  if (s.state !== 'placing') return false;
  s.pending = position * 600;
  return true;
}
function shadowLock(s) {
  if (s.state !== 'placing' || s.pending === null) return false;
  s.points.push(s.pending); s.pending = null;
  if (s.points.length === 3) { s.state = 'locked'; s.pips = 0; s.uses++; }
  return true;
}
function shadowEnd(s) {
  if (s.state !== 'placing') return;
  s.pending = null;
  if (s.points.length) { s.state = 'locked'; s.pips = 0; s.uses++; } else s.state = 'idle';
}
function shadowAnswer(s, throwId, projectileIndex, targetId, x) {
  if (s.state !== 'locked' || projectileIndex !== 0) return false;
  if (targetId !== 'knight' && targetId !== 'teammate') return false;
  if (s.throws.has(throwId)) return false;
  s.throws.add(throwId); s.answered++;
  const block = s.points.length > 0 && Math.abs(s.points[0] - x) <= 70;
  if (block) s.points.shift();
  if (s.answered === 3 || s.points.length === 0) { s.points = []; s.state = 'spent'; }
  return block;
}

test('property: 300 seeded scripts agree with a shadow model and keep hidden-point invariants', () => {
  const r = mulberry32(100);
  for (let c = 0; c < CASES; c++) {
    const ult = ready();
    const twin = ready();
    const model = makeShadow();
    let throwId = 0;
    let planCapacity = 0;
    let planBlocks = 0;
    for (let step = 0; step < 60; step++) {
      const op = Math.floor(r() * 5);
      if (op === 0) {
        if ((model.state === 'idle' || model.state === 'spent') && model.uses < 2) {
          model.pips = 3;
          assert.deepStrictEqual(ult.setPips(3), twin.setPips(3), 'setPips deterministic');
        }
        const expected = shadowBegin(model);
        const got = ult.begin(ctx());
        assert.deepStrictEqual(got, twin.begin(ctx()), 'begin deterministic');
        assert.strictEqual(got.ok, expected, 'begin case ' + c + ' step ' + step);
        if (expected) { planCapacity = 0; planBlocks = 0; }
      } else if (op === 1) {
        const position = [0.2, 0.5, 0.8][Math.floor(r() * 3)];
        const gotPlace = ult.place(0, position);
        assert.deepStrictEqual(gotPlace, twin.place(0, position), 'place deterministic');
        const expected = shadowPlace(model, position);
        assert.strictEqual(gotPlace.ok, expected, 'place case ' + c + ' step ' + step);
        if (expected) {
          const shadowDidLock = shadowLock(model);
          const got = ult.lock();
          assert.deepStrictEqual(got, twin.lock(), 'lock deterministic');
          assert.strictEqual(got.ok, shadowDidLock, 'lock case ' + c + ' step ' + step);
          if (got.ok) planCapacity++;
        }
      } else if (op === 2) {
        shadowEnd(model);
        assert.deepStrictEqual(ult.endTurn(), twin.endTurn(), 'endTurn deterministic');
      } else if (op === 3) {
        const x = [120, 300, 480, 900][Math.floor(r() * 4)];
        const index = r() < 0.2 ? 1 : 0;
        const id = r() < 0.2 ? throwId : ++throwId;
        const targetId = r() < 0.25 ? 'enemy' : (r() < 0.5 ? 'knight' : 'teammate');
        const expected = shadowAnswer(model, id, index, targetId, x);
        const action = attack({ throwId: id, projectileIndex: index, projectilePath: line(x - 1, x + 1), targetId, time: step });
        const got = ult.answer(action);
        assert.deepStrictEqual(got, twin.answer(action), 'answer deterministic');
        assert.strictEqual(got.blocked, expected, 'answer case ' + c + ' step ' + step);
        if (got.blocked) {
          planBlocks++;
          assert.ok(planBlocks <= planCapacity, 'a point answered more than one attack');
        }
      } else if (model.state === 'placing') {
        model.state = 'idle'; model.points = []; model.pending = null;
        assert.deepStrictEqual(ult.cancel(), twin.cancel(), 'cancel deterministic');
      }
      assert.deepStrictEqual(ult.getStatus(), twin.getStatus(), 'status deterministic');
      assert.deepStrictEqual(ult.getStatus(), shadowStatus(model), 'state case ' + c + ' step ' + step);
      const view = ult.publicView();
      assert.deepStrictEqual(view, twin.publicView(), 'public view deterministic');
      assert.deepStrictEqual(view, shadowPublic(model), 'public case ' + c + ' step ' + step);
      assert.ok(view.ult_points_left >= 0 && view.ult_points_left <= 3, 'point count out of range');
      assert.strictEqual(Object.keys(view).length, 1, 'public view must not expose positions');
      assert.strictEqual(JSON.stringify(view).includes('x'), false, 'public view leaked x');
      assert.strictEqual(JSON.stringify(view).includes('y'), false, 'public view leaked y');
    }
  }
});

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
if (failed) {
  console.log('test_knight_ult: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_knight_ult: all ' + tests.length + ' tests passed');
