#!/usr/bin/env node
'use strict';
// Owner 2026-11-24: a private room is shared as a link; the friend clicks it and CHOOSES a side before joining (the link carries choose=1). Old links (no choose=, or with seat=) join exactly as before.
// Logic only (the page harness has a stub DOM): when the chooser is shown nothing is sent to the relay; a side button joins with that side; claim buttons set the claim; old links join at once.
const assert = require('assert');
const { loadPage } = require('./page_harness');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n       ') : e)); } }
const FAKES = `window.__sides = ['red', 'white'].map(s => ({ dataset: { side: s }, onclick: null }));
  window.__claims = [1, 2, 3].map(n => ({ dataset: { claim: String(n) }, hidden: false, classList: { toggle() {} }, setAttribute() {}, onclick: null }));
  window.__sent = [];
  var box = document.getElementById('side-chooser'); box.hidden = true; box.querySelectorAll = sel => sel === '[data-side]' ? window.__sides : window.__claims; box.querySelector = () => window.__sides[0];`;
const open = (search, team) => { const P = loadPage({ team, search: '?relay=ws://hub&team=' + team + search }); P.eval(FAKES);
  P.context.WebSocket = function () { window__sockets.push(1); return { send(raw) { P.context.__sent.push(JSON.parse(raw)); }, close() {}, readyState: 1 }; };
  P.eval('buildRoomControls()'); return P; };
const window__sockets = [];
check('a new invite link (choose=1) shows the side chooser and sends nothing to the relay yet', () => {
  window__sockets.length = 0; const P = open('&room=ABCDE&choose=1', 3);
  assert.strictEqual(P.eval('document.getElementById("side-chooser").hidden'), false, 'the chooser is shown');
  assert.strictEqual(P.eval('relayAutoJoined'), false, 'not joined yet'); assert.strictEqual(window__sockets.length, 0, 'no socket opened before the choice');
  assert.strictEqual(P.eval('document.getElementById("side-code").textContent'), 'ABCDE');
});
check('choosing white joins as white, choosing red joins as red, and the chooser closes', () => {
  for (const side of ['white', 'red']) {
    const P = open('&room=ABCDE&choose=1', 3); P.eval('window.__sides.find(b => b.dataset.side === "' + side + '").onclick()');
    assert.strictEqual(P.eval('relayJoinSeat'), side); assert.strictEqual(P.eval('relayAutoJoined'), true, 'joined after the choice'); assert.strictEqual(P.eval('document.getElementById("side-chooser").hidden'), true);
    assert.strictEqual(P.eval('relayRoomCode'), 'ABCDE');
  }
});
check('the claim buttons of the chooser set how many units this guest takes (the whole team is the default)', () => {
  const P = open('&room=ABCDE&choose=1', 3);
  assert.strictEqual(P.eval('relayClaimCount'), null);
  P.eval('window.__claims[1].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), 2);
  P.eval('window.__claims[2].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), null, 'all of them is the whole team');
  P.eval('window.__claims[0].onclick(); window.__sides[0].onclick()'); assert.strictEqual(P.eval('relayClaimCount'), 1); assert.strictEqual(P.eval('relayJoinSeat'), 'red');
});
check('a one-unit room has no claim row', () => {
  const P = open('&room=ABCDE&choose=1', 1);
  assert.strictEqual(P.eval('document.getElementById("side-claim").hidden'), true);
});
check('old links join at once as before: no choose= (white), seat=red (red), and a link with seat= never shows the chooser', () => {
  for (const [search, seat] of [['&room=ABCDE', 'white'], ['&room=ABCDE&seat=red', 'red'], ['&room=ABCDE&choose=1&seat=red', 'red'], ['&room=ABCDE&seat=white', 'white']]) {
    const P = open(search, 3);
    assert.strictEqual(P.eval('relayAutoJoined'), true, search + ': joined at once'); assert.strictEqual(P.eval('relayJoinSeat'), seat, search + ': seat');
    assert.strictEqual(P.eval('document.getElementById("side-chooser").hidden'), true, search + ': no chooser');
  }
});
check('no room in the link: nothing is shown and nothing joins', () => {
  const P = open('', 3);
  assert.strictEqual(P.eval('relayAutoJoined'), false); assert.strictEqual(P.eval('document.getElementById("side-chooser").hidden'), true);
});
console.log('test_choose_side: ' + passed + ' passed' + (process.exitCode ? ', FAILED' : ''));
