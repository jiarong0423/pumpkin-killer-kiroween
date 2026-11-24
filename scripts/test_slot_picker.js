#!/usr/bin/env node
'use strict';
// Unit slot fill, stage 2 (docs/ADR_unit_slot_fill_20261124.md P7): the slot picker in the room panel. The page harness has a stub DOM, so the buttons are
// fakes the test hands to the page; what is checked is the page's own logic: claim count, invite team, link and URL parameters, open-slot subtraction, locking.
const assert = require('assert');
const { loadPage } = require('./page_harness');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n       ') : e)); } }
const FAKES = `window.__claim = [1, 2, 3].map(n => ({ dataset: { claim: String(n) }, classList: { toggle(c, on) { this[c] = !!on; } }, setAttribute() {}, hidden: false, disabled: false, onclick: null }));
  window.__seat = ['', 'red', 'white'].map(s => ({ dataset: { seat: s }, classList: { toggle(c, on) { this[c] = !!on; } }, setAttribute() {}, disabled: false, onclick: null }));
  var q = sel => sel === '[data-claim]' ? window.__claim : window.__seat;
  document.getElementById('slot-picker').querySelectorAll = q; document.getElementById('slot-invite').querySelectorAll = q;`;
const room = (search, team) => { const P = loadPage({ team, search: '?relay=ws://hub&team=' + team + (search || '') }); P.eval(FAKES); P.eval('buildRoomControls()'); return P; };

check('a one-unit room hides the picker; a team room shows it', () => {
  assert.strictEqual(room('', 1).eval('document.getElementById("slot-picker").hidden'), true);
  assert.strictEqual(room('', 3).eval('document.getElementById("slot-picker").hidden'), false);
});

check('claim buttons set how many units this seat sends on ready; all of them means the whole team (null)', () => {
  const P = room('', 3);
  assert.strictEqual(P.eval('relayClaimCount'), null, 'default: the whole team');
  P.eval('window.__claim[1].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), 2); assert.strictEqual(P.eval('relayUnitHeroes().length'), 2);
  P.eval('window.__claim[0].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), 1); assert.strictEqual(P.eval('relayUnitHeroes().length'), 1);
  P.eval('window.__claim[2].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), null); assert.strictEqual(P.eval('relayUnitHeroes().length'), 3);
});

check('a team of two offers only 1 and 2; a claim of 2 is the whole team', () => {
  const P = room('', 2);
  assert.strictEqual(P.eval('window.__claim[2].hidden'), true, 'the third button is hidden');
  P.eval('window.__claim[1].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), null);
});

check('once the match has started the picker is locked', () => {
  const P = room('', 3);
  P.eval('relayPlaying = true; window.__claim[0].onclick(); window.__seat[1].onclick()');
  assert.strictEqual(P.eval('relayClaimCount'), null); assert.strictEqual(P.eval('relayInviteSeat'), '', 'still the default: the friend chooses');
});

check('the invite link: by default the friend chooses a side after clicking (choose=1, no seat); the host may fix red or white (seat=, no choose)', () => {
  const P = room('', 3), link = () => P.eval('joinLink("ABCDE")');
  P.eval('relayIsHost = true; relayRoomCode = "ABCDE"; refreshSlotPicker()');
  assert.ok(/[?&]choose=1/.test(link()) && !/seat=/.test(link()), 'default link: ' + link());
  P.eval('window.__seat[1].onclick()'); assert.ok(/[?&]seat=red/.test(link()) && !/choose=/.test(link()), 'red link: ' + link());
  P.eval('window.__seat[2].onclick()'); assert.ok(/[?&]seat=white/.test(link()) && !/choose=/.test(link()), 'white link: ' + link());
  P.eval('window.__seat[0].onclick()'); assert.ok(/[?&]choose=1/.test(link()) && !/seat=/.test(link()), 'back to "friend picks": ' + link());
  assert.ok(/room=ABCDE/.test(link()), 'the room code stays in the link (the harness location has no other parameters)');
});

check('URL parameters: seat=red and claim=N are honoured, anything invalid is ignored, claim equal to the team size is the whole team', () => {
  const v = (search, team) => { const P = room(search, team); return [P.eval('relayJoinSeat'), P.eval('relayClaimCount')]; };
  assert.deepStrictEqual(v('&seat=red&claim=2', 3), ['red', 2]);
  assert.deepStrictEqual(v('&seat=white&claim=1', 3), ['white', 1]);
  assert.deepStrictEqual(v('&seat=blue&claim=0', 3), ['white', null]);
  assert.deepStrictEqual(v('&claim=3', 3), ['white', null]);
  assert.deepStrictEqual(v('&claim=7', 3), ['white', null]);
  assert.deepStrictEqual(v('&claim=2', 1), ['white', null], 'a one-unit room ignores claim');
  assert.deepStrictEqual(v('&seat=red', 1), ['white', null], 'a one-unit room has one seat per team: seat=red is ignored (red-team R1 A8)');
  assert.deepStrictEqual(v('&seat=red', 3), ['red', null], 'a team room accepts seat=red');
});

check('open slots are the team size minus the units the seats named; never below zero', () => {
  const P = room('', 3), vac = seats => { P.eval('relaySeats = ' + JSON.stringify(seats)); return JSON.parse(P.eval('JSON.stringify(slotVacancies())')); };
  assert.deepStrictEqual(vac([]), { red: 3, white: 3 });
  assert.deepStrictEqual(vac([{ team: 'red', units: ['a'] }]), { red: 2, white: 3 });
  assert.deepStrictEqual(vac([{ team: 'red', units: ['a'] }, { team: 'red', units: ['b', 'c'] }, { team: 'white', units: [] }]), { red: 0, white: 3 });
  assert.deepStrictEqual(vac([{ team: 'red', units: ['a', 'b', 'c'] }, { team: 'red', units: ['d'] }, { team: 'white', units: ['x', 'y', 'z'] }, { team: 'spectator', units: ['q'] }]), { red: 0, white: 0 });
});

console.log('test_slot_picker: ' + passed + ' passed' + (process.exitCode ? ', FAILED' : ''));
