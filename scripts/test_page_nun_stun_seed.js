#!/usr/bin/env node
'use strict';
/*
 * R1-1 / gap N10 family: the hag (nun) cross ultimate in a team ROOM must pick its electric-stun victim from the room's seeded stream,
 * not from Math.random. Two pages that draw differently stun different units and their round hashes differ.
 *
 * The scenario runs the page's own `nunPierceFinish` (index.html) twice for the same throw, each time with a different Math.random, with the page
 * in "room live" state. In a room both runs must stun the same unit; outside a room it may differ (the single-device game keeps Math.random).
 * Run: node scripts/test_page_nun_stun_seed.js      Exit 0 = pass, 1 = fail.
 */
const assert = require('assert');
const { loadPage } = require('./page_harness');

function stunnedUnit(randomValue, inRoom, throwId) {
  const P = loadPage({ team: 3 });
  if (inRoom) P.eval('relayPlaying = true; relayClient = {}; relayRoomCode = "TESTRM"; matchSeed = 12345;');
  P.eval('Math.random = function () { return ' + randomValue + '; };');
  P.eval('var __nunP = { throwId: ' + throwId + ', nunTouched: [unitsOf("right")[0], unitsOf("right")[1], unitsOf("right")[2]] }; nunPierceFinish(__nunP);');
  P.timers.forEach(t => { try { t.fn(); } catch (e) { /* only the stun timer matters */ } });
  return P.units('right').filter(u => u.stun).map(u => u.id).join(',');
}

let failed = 0;
function check(name, fn) {
  try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.error('FAIL - ' + name + '\n       ' + String(e && e.message ? e.message : e)); }
}

check('in a room the stunned unit does not depend on Math.random (three different draws, one throw)', () => {
  const picks = [0.01, 0.5, 0.99].map(v => stunnedUnit(v, true, 7));
  picks.forEach(p => assert.ok(p.split(',').length === 1 && p !== '', 'exactly one stunned unit expected, got "' + p + '"'));
  assert.ok(picks[0] === picks[1] && picks[1] === picks[2], 'pages with different Math.random stunned different units: ' + JSON.stringify(picks));
});

check('in a room the pick still depends on the throw (the stream is per throw, so it is not a constant)', () => {
  const picks = new Set();
  for (let id = 1; id <= 40; id++) picks.add(stunnedUnit(0.5, true, id));
  assert.ok(picks.size >= 2, 'forty different throws always stunned the same unit: ' + JSON.stringify([...picks]));
});

check('outside a room the single-device game still draws with Math.random (control)', () => {
  const picks = [0.01, 0.99].map(v => stunnedUnit(v, false, 7));
  assert.ok(picks[0] !== picks[1], 'control failed: outside a room the pick should follow Math.random: ' + JSON.stringify(picks));
});

if (failed) { console.error('test_page_nun_stun_seed: ' + failed + ' FAILED'); process.exit(1); }
console.log('test_page_nun_stun_seed: OK');
