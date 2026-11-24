#!/usr/bin/env node
'use strict';
/*
 * R1-1, deterministic construction (main window rule 2026-11-23: build the precondition instead of hoping for it).
 * Two copies of the REAL page in room state, same seed and same placed units, throw the hag (nun) cross ultimate with the same aim while Math.random differs
 * (0.01 versus 0.99). A shot is searched first (page.executeThrow + real physics) until the cross touches at least two enemy units; then both pages must pick the same
 * stunned unit and end with the same hit points and status of every unit. Before the fix (rng: Math.random) the two pages stun different units.
 * Run: node scripts/test_page_nun_pierce_pair.js      Exit 0 = pass, 1 = fail.
 */
const assert = require('assert');
const { loadPage } = require('./page_harness');

function setup(randomValue) {
  const P = loadPage({ team: 3 });
  P.eval('relayPlaying = true; relayClient = new Proxy({}, { get: (t, k) => k === "state" ? (() => ({ status: "open", round: 1, phase: "red", seat: "red-1" })) : (() => {}) }); relayRoomCode = "TESTRM"; matchSeed = 4242; wind = 0; matchStarted = true; gameOver = false; turn = "player";');
  P.place('left', [300, 450, 600]);
  P.place('right', [1300, 1450, 1600]);
  P.eval('currentHero = "hag"; unitsOf("left")[0].profile = "hag"; energy.player = 3; ultUsed.player = 0; ultArmed.player = true;');
  P.eval('globalThis.__touched = -1; globalThis.__stunned = null; const __orig = nunPierceFinish; nunPierceFinish = function (p) { globalThis.__touched = p.nunTouched.length; return __orig(p); };');
  P.eval('Math.random = function () { return ' + randomValue + '; };');
  return P;
}

function throwIt(P, angle, power) {
  P.eval('executeThrow("player", ' + power + ', ' + angle + ')');
  P.run(2500, 0.01);
  P.timers.forEach(t => { try { t.fn(); } catch (e) { /* only the stun timer matters */ } });
}

function summary(P) {
  return P.units('right').map(u => [u.id, Math.round(u.hp * 10) / 10, !!u.stun]).concat(P.units('left').map(u => [u.id, Math.round(u.hp * 10) / 10, !!u.stun]));
}

let failed = 0;
function check(name, fn) { try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.error('FAIL - ' + name + '\n       ' + String(e && e.message ? e.message : e)); } }

let found = null;
check('a shot exists that makes the real cross touch two or more enemy units (the construction itself works)', () => {
  outer:
  for (let angle = 25; angle <= 80; angle += 5) {
    for (let power = 40; power <= 115; power += 5) {
      const P = setup(0.5);
      throwIt(P, angle, power);
      const touched = P.get('__touched');
      if (touched >= 2) { found = { angle, power, touched }; break outer; }
    }
  }
  assert.ok(found, 'no angle and power in the grid made the cross touch two enemies; widen the grid or move the units');
  console.log('       aim ' + JSON.stringify(found));
});

check('two pages with different Math.random end with the same stunned unit, hit points and statuses', () => {
  assert.ok(found, 'no aim found');
  const a = setup(0.01), b = setup(0.99);
  throwIt(a, found.angle, found.power);
  throwIt(b, found.angle, found.power);
  assert.ok(a.get('__touched') >= 2 && b.get('__touched') >= 2, 'both pages must touch two or more units: ' + a.get('__touched') + ' / ' + b.get('__touched'));
  const sa = summary(a), sb = summary(b);
  assert.deepStrictEqual(sa, sb, 'the two pages disagree: ' + JSON.stringify(sa) + ' vs ' + JSON.stringify(sb));
  assert.ok(sa.some(row => row[2]), 'nobody was stunned: the stun pick did not run');
});

check('mutant: with the unseeded Math.random the two pages DO disagree (the test can fail)', () => {
  assert.ok(found, 'no aim found');
  const edit = [['rng: relayLive() ? relayStream(p.throwId + 200000) : Math.random', 'rng: Math.random']];
  const mk = v => { const P = loadPage({ team: 3, mutate: edit }); P.eval('relayPlaying = true; relayClient = new Proxy({}, { get: (t, k) => k === "state" ? (() => ({ status: "open", round: 1, phase: "red", seat: "red-1" })) : (() => {}) }); relayRoomCode = "TESTRM"; matchSeed = 4242; wind = 0; matchStarted = true; gameOver = false; turn = "player";'); P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]); P.eval('currentHero = "hag"; unitsOf("left")[0].profile = "hag"; energy.player = 3; ultUsed.player = 0; ultArmed.player = true;'); P.eval('Math.random = function () { return ' + v + '; };'); return P; };
  const a = mk(0.01), b = mk(0.99);
  throwIt(a, found.angle, found.power);
  throwIt(b, found.angle, found.power);
  assert.notDeepStrictEqual(summary(a), summary(b), 'the mutant pages agreed, so this test would not catch the bug');
});

if (failed) { console.error('test_page_nun_pierce_pair: ' + failed + ' FAILED'); process.exit(1); }
console.log('test_page_nun_pierce_pair: OK');
