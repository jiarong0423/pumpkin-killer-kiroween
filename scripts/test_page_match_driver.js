#!/usr/bin/env node
'use strict';
// Executed check of scripts/page_match_driver.js: a duel, a 2v2 and a 3v3 played to the end by the real page code in the vm.
const assert = require('assert');
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n       ') : e)); process.exitCode = 1; } }

function play(cfg, pageSize) {
  const P = loadPage({ team: pageSize == null ? cfg.size : pageSize });
  vm.runInContext(D.source, P.context);
  const before = { exec: P.get('executeThrow'), hit: P.get('pushHitReport'), rnd: P.context.Math.random, st: P.context.setTimeout, perf: P.context.performance.now };
  const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify(cfg) + ')', P.context)));
  return { rec, P, before };
}
const mulberry = seed => { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };

const cases = [
  { name: 'duel', cfg: { hero: 'skeleton', size: 1, seed: D.cellSeed(0, 1, 1) }, cap: 60 },
  { name: '2v2', cfg: { hero: 'wizard', size: 2, seed: D.cellSeed(1, 2, 1) }, cap: 24 },
  { name: '3v3', cfg: { hero: 'hag', size: 3, seed: D.cellSeed(7, 3, 1) }, cap: 28 }
];
for (const c of cases) {
  const a = play(c.cfg);
  const r = a.rec;
  check(c.name + ': plays to a winner with the spec fields, sane counters and no error', () => {
    assert.deepStrictEqual(r.errors, []);
    assert.strictEqual(r.end, 'page'); assert.strictEqual(r.size, c.cfg.size); assert.strictEqual(r.seed, c.cfg.seed); assert.strictEqual(r.hero, c.cfg.hero);
    assert.ok(['left', 'right', 'cap_left', 'cap_right'].includes(r.winner), 'winner ' + r.winner);
    assert.ok(r.rounds >= 2 && r.rounds <= c.cap, 'rounds ' + r.rounds);
    assert.ok(r.throws >= r.rounds && r.direct_hits >= 1 && r.direct_hits <= r.throws, 'throws ' + r.throws + ' hits ' + r.direct_hits);
    assert.ok(r.units_left_alive >= 0 && r.units_left_alive <= c.cfg.size && r.units_right_alive >= 0 && r.units_right_alive <= c.cfg.size);
    assert.ok(r.hp_share_left >= 0 && r.hp_share_left <= 1 && r.hp_share_right >= 0 && r.hp_share_right <= 1);
    if (r.winner === 'left') assert.strictEqual(r.units_right_alive, 0); if (r.winner === 'right') assert.strictEqual(r.units_left_alive, 0);
    if (!/^cap_/.test(r.winner)) assert.ok(r.units_left_alive === 0 || r.units_right_alive === 0, 'a kill end leaves one side with no unit');
    assert.strictEqual(r.options.plainOnly, true); assert.strictEqual(r.ultimates_left, 0); assert.strictEqual(r.ultimates_right, 0, 'plainOnly: no ultimate on either side');
    assert.ok(r.options.moves_left === 0 && r.options.moves_right >= 0 && r.options.moves_right <= r.throws, 'only the right AI moves, and it is counted');
    if (c.cfg.size === 1) { assert.strictEqual(r.comeback_hits, 0); assert.strictEqual(r.pity_triggers, 0); assert.strictEqual(r.near_misses, 0); }
    else { assert.ok(Number.isInteger(r.comeback_hits) && Number.isInteger(r.pity_triggers) && Number.isInteger(r.near_misses)); }
  });
  check(c.name + ': right hero and both tiers follow the spec rules (hero (seed*7+3)%8, mulberry32(seed ^ 0x5eed) over [hard, normal, easy])', () => {
    const H = ['skeleton', 'wizard', 'bat', 'knight', 'bride', 'hunchback', 'reaper', 'hag'], T = ['hard', 'normal', 'easy'];
    const rng = mulberry((r.seed ^ 0x5eed) >>> 0);
    assert.strictEqual(r.hero_right, H[(r.seed * 7 + 3) % 8]);
    assert.strictEqual(r.tier_left, T[Math.floor(rng() * 3)]); assert.strictEqual(r.tier_right, T[Math.floor(rng() * 3)]);
  });
  check(c.name + ': the same seed twice gives the identical record (fresh page each time)', () => {
    const b = play(c.cfg).rec; assert.deepStrictEqual(b, r);
  });
  check(c.name + ': the driver restores the page (hooks, Math.random, timers, clock) and leaves the page state at the match end', () => {
    const P = a.P;
    assert.strictEqual(P.get('executeThrow'), a.before.exec); assert.strictEqual(P.get('pushHitReport'), a.before.hit);
    assert.strictEqual(P.context.setTimeout, a.before.st); assert.strictEqual(P.context.Math.random, a.before.rnd); assert.strictEqual(P.context.performance.now, a.before.perf);
    assert.ok(P.get('gameOver') === 'player' || P.get('gameOver') === 'ai');
    assert.strictEqual(P.get('seats').left, 'ai'); assert.strictEqual(P.get('seats').right, 'ai');
  });
}
check('plainOnly false plays the page full AI: the right AI fires ultimates (negative of the plain default)', () => {
  const rich = []; for (let k = 0; k < 6; k++) rich.push(play({ hero: 'skeleton', size: 1, seed: D.cellSeed(0, 1, k), plainOnly: false }).rec);
  assert.ok(rich.every(r => r.options.plainOnly === false && r.errors.length === 0), 'rich records');
  assert.ok(rich.reduce((s, r) => s + r.ultimates_right, 0) > 0, 'the page right AI uses an ultimate in six duels');
  const plain = []; for (let k = 0; k < 6; k++) plain.push(play({ hero: 'skeleton', size: 1, seed: D.cellSeed(0, 1, k) }).rec);
  assert.strictEqual(plain.reduce((s, r) => s + r.ultimates_right, 0), 0);
});
check('different seeds give different matches (the record depends on the seed)', () => {
  const x = play({ hero: 'skeleton', size: 1, seed: 7011 }).rec, y = play({ hero: 'skeleton', size: 1, seed: 7012 }).rec;
  assert.notDeepStrictEqual([x.hero_right, x.tier_left, x.tier_right, x.rounds, x.throws, x.hp_share_right], [y.hero_right, y.tier_left, y.tier_right, y.rounds, y.throws, y.hp_share_right]);
});
check('negative: a page loaded for another team size gives an error record, not a silent wrong match', () => {
  const r = play({ hero: 'skeleton', size: 2, seed: 7021 }, 1).rec;
  assert.strictEqual(r.winner, 'none'); assert.strictEqual(r.throws, 0); assert.ok(r.errors.length === 1 && /team size/.test(r.errors[0]), r.errors.join(';'));
});
check('negative: an unknown hero gives an error record', () => {
  const r = play({ hero: 'dragon', size: 1, seed: 7011 }).rec; assert.ok(/unknown hero/.test(r.errors[0]) && r.winner === 'none');
});
check('negative: the step limit turns an unfinished match into an error record, never a fake winner', () => {
  const r = play({ hero: 'skeleton', size: 1, seed: 7011, maxSteps: 50 }).rec; assert.ok(r.errors.some(e => /step limit/.test(e)), r.errors.join(';')); assert.strictEqual(r.winner, 'none');
});
console.log('test_page_match_driver: ' + passed + ' ok');
