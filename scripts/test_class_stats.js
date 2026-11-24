'use strict';
/* Tests for js/class_stats.js. Node assert only. Run: node scripts/test_class_stats.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const CS = require(path.join(__dirname, '..', 'js', 'class_stats.js'));
const HEROES = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'heroes.json'), 'utf8'));

const KEYS = ['skeleton', 'wizard', 'bat', 'knight', 'bride', 'hunchback', 'reaper', 'hag'];
const tests = [];
function test(name, fn) { tests.push({ name, fn }); }
function near(actual, expected, tolerance, label) {
  assert.ok(Math.abs(actual - expected) <= tolerance, (label || '') + ' got ' + actual + ', want ' + expected);
}

test('eight class keys include the flame-magic necromancer and Ghost Nun page ids', () => {
  assert.deepStrictEqual(CS.CLASS_KEYS, KEYS);
  assert.deepStrictEqual(Object.keys(CS.CLASSES), KEYS);
  const r = CS.CLASSES.reaper;
  assert.deepStrictEqual([r.key, r.name, r.weapon, r.hp, r.dmg, r.dTyp], ['reaper', '死靈法師', 'proj_flame', 143, 22, 22]);
  assert.deepStrictEqual(r.launch, { fwd: 58, up: 110 });
  assert.strictEqual(r.ultKind, 'soulfire_volley');
  assert.strictEqual(r.ultStrikes, 3);
  assert.strictEqual(Object.prototype.hasOwnProperty.call(r.special, 'execute'), false);
  assert.strictEqual(CS.CLASSES.hag.weapon, 'proj_cross');
  assert.strictEqual(CS.CLASSES.necromancer, undefined);
  assert.strictEqual(CS.CLASSES.nun, undefined);
});

test('the default simulator table mirrors every shared page hero value', () => {
  assert.deepStrictEqual(Object.keys(CS.CLASSES).sort(), Object.keys(HEROES).sort());
  for (const key of Object.keys(HEROES)) {
    const actual = CS.CLASSES[key];
    const expected = HEROES[key];
    assert.deepStrictEqual([actual.hp, actual.dmg, actual.weapon], [expected.hp, expected.dmg, expected.weapon], key);
    assert.deepStrictEqual(actual.launch, expected.launch, key + ' launch');
    const expectedHalfWidth = expected.attackHitBox ? expected.attackHitBox.halfWidth : expected.hitBox.halfWidth;
    assert.strictEqual(actual.hitHalfWidth, expectedHalfWidth, key + ' attack half width');
  }
});

test('the default simulator table carries page bleed, poison, and burn status values', () => {
  assert.deepStrictEqual(CS.CLASSES.skeleton.special.bleed, { damage: 2, turns: 2, nonLethal: true });
  assert.deepStrictEqual(CS.CLASSES.hunchback.special.bleed, { damage: 2, turns: 2, nonLethal: true });
  assert.deepStrictEqual(CS.CLASSES.wizard.special.poison, HEROES.wizard.statusOnHit.poison);
  assert.deepStrictEqual(CS.CLASSES.bride.special.poison, HEROES.bride.statusOnHit.poison);
  assert.deepStrictEqual(CS.CLASSES.reaper.special.burn, { damage: 2, turns: 3, nonLethal: true });
});

test('reaper flame constants mirror shared hero values', () => {
  assert.deepStrictEqual(CS.REAPER_FLAME_CONSTANTS, {
    HP: 143, DAMAGE: 22, TYPICAL_DAMAGE: 22, HIT_HALF_WIDTH: 57,
    SPEED_SCALE: 1, GRAVITY_SCALE: 1, WIND_SCALE: 1,
    LAUNCH_FORWARD: 58, LAUNCH_UP: 110, BURN_DAMAGE: 2, BURN_TURNS: 3, ULTIMATE_FLAMES: 3
  });
  assert.strictEqual(CS.CLASSES.reaper.source, 'shared/heroes.json');
  assert.deepStrictEqual(CS.PROVISIONAL.reaper.special, CS.CLASSES.reaper.special);
});

test('tables are frozen and clones remain mutable', () => {
  assert.throws(() => { 'use strict'; CS.CLASSES.reaper.dmg = 1; }, TypeError);
  const copy = CS.cloneTable(CS.CLASSES);
  copy.reaper.dmg = 1;
  assert.strictEqual(CS.CLASSES.reaper.dmg, 22);
});

test('hits to kill and matrix have no stale execute branch', () => {
  assert.strictEqual(CS.hitsToKill('reaper', 'reaper'), 7);
  assert.strictEqual(CS.hitsToKill('reaper', 'knight'), 9);   // knight hp 198 (tank +7 percent, 2026-11-18) / reaper dmg 22: 198 / 22 = 9
  assert.strictEqual(CS.hitsToKill('reaper', 'knight', { execute: true }), 9);
  const violations = CS.validate();
  assert.deepStrictEqual(violations.map(({ kind, attacker, defender, hits }) => ({ kind, attacker, defender, hits })), []);   // with every HP x1.5 (2026-11-16) and the band 5..10 typical, 4..12 hard, the table has no violation
  const matrix = CS.matrix();
  assert.strictEqual(matrix.length, KEYS.length);
  matrix.forEach(row => assert.strictEqual(row.length, KEYS.length));
});

test('flame expected damage has no execute multiplier', () => {
  const detail = CS.expectedDamageDetail('reaper', { aim: 'bot' });
  near(detail.hitProbability, 0.57, 1e-12);
  near(detail.damageWhenHit, 22, 1e-12);
  near(detail.multiplier, 1, 1e-12);
  near(detail.perThrow, 0.57 * 22 * 0.88, 1e-12);
});

test('all expected-damage values remain finite and decline with wider aim spread', () => {
  for (const key of KEYS) {
    let last = Infinity;
    for (const A of [50, 70, 100, 150, 210, 400]) {
      const value = CS.expectedDamage(key, { A });
      assert.ok(Number.isFinite(value) && value > 0, key + ' A=' + A);
      assert.ok(value <= last + 1e-9, key + ' A=' + A);
      last = value;
    }
  }
});

test('three ghost fires total 1.5 times the flame normal damage', () => {
  assert.strictEqual(CS.ultimatePerUnit('reaper'), 33);   // 1.5 x 22
  assert.strictEqual(CS.ultimateOneTarget('reaper'), 33);
  assert.strictEqual(CS.oneShotRisks().some(risk => risk.attacker === 'reaper'), false);
});

test('eight explicit stats remain valid, defense starts at zero, and statsOf exposes only them', () => {
  for (const table of [CS.CLASSES, CS.PROVISIONAL, CS.CURRENT]) {
    for (const key of KEYS) {
      const row = table[key];
      assert.ok(Number.isFinite(row.hp) && row.hp > 0, key + ' hp');
      assert.ok(Number.isFinite(row.attack) && row.attack > 0, key + ' attack');
      assert.strictEqual(row.attack, row.dmg, key + ' attack aliases dmg');
      assert.ok(Number.isFinite(row.defense) && row.defense >= 0 && row.defense <= 0.5, key + ' defense');
      assert.ok(Number.isFinite(row.range) && row.range > 0, key + ' range');
    }
  }
  assert.deepStrictEqual(CS.statsOf('wizard'), { hp: 124, defense: 0, range: CS.CLASSES.wizard.range, attack: 36 });
});

test('the one row-mean exception (2026-11-18, owner: glass cannon +10 percent attack) is exactly the wizard and nothing else', () => {
  const m = CS.matrix();
  const means = m.map(row => row.reduce((x, y) => x + y, 0) / row.length);
  const under5 = KEYS.filter((k, i) => means[i] < 5);
  assert.deepStrictEqual(under5, ['wizard'], 'only the wizard averages under 5 hits to kill');
  assert.ok(means[KEYS.indexOf('wizard')] >= 4.8 && means[KEYS.indexOf('wizard')] < 5, 'the wizard row mean is ' + means[KEYS.indexOf('wizard')]);
  assert.deepStrictEqual(CS.validate(), [], 'validate() accepts the table with the documented 4.8 floor');
});

test('the row-mean floor is 4.8: a row at 4.5 is a violation, the wizard at 4.875 is not (red-team R11A: the floor was unpinned, 4.0 passed too)', () => {
  const table = CS.cloneTable(CS.CLASSES);
  table.wizard.dmg = table.wizard.dTyp = 40;   // 40 damage: every kill takes fewer hits, the row mean drops under 4.8
  const violations = CS.validate({ table }).filter(v => v.kind === 'row_mean');
  assert.deepStrictEqual(violations.map(v => v.attacker), ['wizard'], JSON.stringify(violations));
  assert.ok(violations[0].hits < 4.8, 'row mean ' + violations[0].hits);
  assert.deepStrictEqual(CS.validate().filter(v => v.kind === 'row_mean'), [], 'the real table has no row-mean violation');
});

test('zero defense preserves the existing hits-to-kill matrix', () => {
  const expected = [
    [7, 6, 7, 9, 7, 7, 6, 7], [5, 4, 5, 6, 5, 5, 4, 5],
    [6, 5, 6, 7, 6, 6, 5, 6], [8, 6, 7, 10, 8, 8, 7, 8],
    [5, 5, 5, 7, 5, 6, 5, 6], [8, 7, 8, 11, 8, 9, 8, 9],
    [7, 6, 7, 9, 7, 8, 7, 8], [7, 6, 7, 9, 7, 7, 6, 7]   // roles of 2026-11-18 on the balance of 2026-11-17: skeleton 150/24, wizard 124/36, bat 147/29, knight 198/21, bride 149/40 (typical wave 30), hunchback 157/19, reaper 143/22, hag 158/24; every cell recomputed as ceil(hp / typical damage) outside the code
  ];
  assert.deepStrictEqual(CS.matrix(), expected);
});

test('defense reduces effective damage, raising a hand-checked hits-to-kill case', () => {
  const defended = CS.cloneTable(CS.CLASSES);
  defended.skeleton.defense = 0.2;
  assert.strictEqual(CS.hitsToKill('wizard', 'skeleton'), 5);
  assert.strictEqual(CS.hitsToKill('wizard', 'skeleton', { table: defended }), 6);   // hand check: 150 / (33 x 0.8) = 5.7, so 6 (it was 150 / (30 x 0.8) = 6.25, so 7)
});

test('typical range is positive and increases with speedScale for one launch profile', () => {
  const launch = CS.CLASSES.skeleton.launch;
  let previous = 0;
  for (const speedScale of [0.7, 0.8, 0.9, 1, 1.1]) {
    const range = CS.typicalRange(speedScale, 1, launch);
    assert.ok(range > 0);
    assert.ok(range > previous, 'speedScale ' + speedScale);
    previous = range;
  }
});

test('comparison and calculations are deterministic without ambient entropy or time', () => {
  const before = JSON.stringify([CS.CLASSES, CS.PROVISIONAL]);
  const random = Math.random;
  const DateOriginal = global.Date;
  Math.random = () => { throw new Error('Math.random used'); };
  global.Date = function () { throw new Error('Date used'); };
  try {
    const first = JSON.stringify([CS.matrix(), CS.powerTable({ aim: 'ai' }), CS.compareTables(CS.PROVISIONAL, CS.CLASSES)]);
    const second = JSON.stringify([CS.matrix(), CS.powerTable({ aim: 'ai' }), CS.compareTables(CS.PROVISIONAL, CS.CLASSES)]);
    assert.strictEqual(first, second);
  } finally {
    Math.random = random;
    global.Date = DateOriginal;
  }
  assert.strictEqual(JSON.stringify([CS.CLASSES, CS.PROVISIONAL]), before);
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
  console.log('test_class_stats: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_class_stats: all ' + tests.length + ' tests passed');
