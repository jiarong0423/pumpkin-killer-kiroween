#!/usr/bin/env node
'use strict';
// The start-screen room status line and the Create / Join buttons against a STRICT browser-like WebSocket (red-team R3B-1, R3B-2, R4B-2, R4B-3).
// The other relay page tests use a hub whose sockets are open from the first instant, which cannot show any connection lifecycle bug. This fake behaves like the
// browser: readyState starts at 0 (CONNECTING), send() throws InvalidStateError until open, close and failure call onclose. The harness T() returns the key, so the
// status text is the i18n key. No real network, no timers run unless a test fires them.
const assert = require('assert');
const { loadPage } = require('./page_harness');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack || e).split('\n').slice(0, 4).join('\n       ')); } }

function setup(search) {
  const sockets = [];
  function StrictWS(url) {
    this.url = url; this.readyState = 0; this.sent = []; this.onopen = this.onmessage = this.onclose = this.onerror = null; sockets.push(this);
  }
  StrictWS.prototype.send = function (text) { if (this.readyState !== 1) { const e = new Error('Still in CONNECTING state.'); e.name = 'InvalidStateError'; throw e; } this.sent.push(JSON.parse(text)); };
  StrictWS.prototype.close = function () { if (this.readyState === 3) return; this.readyState = 3; if (this.onclose) this.onclose({}); };
  StrictWS.prototype.open = function () { this.readyState = 1; if (this.onopen) this.onopen({}); };
  StrictWS.prototype.fail = StrictWS.prototype.close;   // a refused connection: the browser fires error then close; the client listens to close
  StrictWS.prototype.message = function (m) { this.onmessage({ data: JSON.stringify(m) }); };
  const P = loadPage({ team: 1, search: '?relay=ws://relay.test' + (search || '') });
  P.context.WebSocket = StrictWS;
  P.eval('buildRoomControls()');
  const status = () => P.eval('(function(){ const el = document.getElementById("room-status"); return el.hidden ? "" : el.textContent; })()');
  const press = id => P.eval('document.getElementById("' + id + '").onclick()');
  return { P, sockets, status, press };
}
const roomState = { type: 'room_state', code: 'ABCD', seat: 'red', seats: [{ seat_id: 'red-1', team: 'red', ready: false }], seat_token: 'tok-1' };

check('create room, server unreachable: "connecting" first, then "unreachable"; nothing throws', () => {
  const { sockets, status, press } = setup();
  press('room-create');
  assert.strictEqual(status(), 'room.connecting'); assert.strictEqual(sockets.length, 1); assert.strictEqual(sockets[0].sent.length, 0, 'nothing is sent while CONNECTING');
  sockets[0].fail();
  assert.strictEqual(status(), 'room.unreachable');
});

check('create room, server answers: create_room is sent once on open, the status line disappears with the room_state', () => {
  const { sockets, status, press } = setup();
  press('room-create'); press('room-create');   // a double press before the socket opens must not send twice
  sockets[0].open();
  assert.deepStrictEqual(sockets[0].sent.map(m => m.type), ['create_room']);
  assert.strictEqual(status(), 'room.connecting', 'still waiting for the room');
  sockets[0].message(roomState);
  assert.strictEqual(status(), '');
  press('room-create');   // a room exists: a further press does nothing
  assert.strictEqual(sockets[0].sent.length, 1);
});

check('a reconnect while the room exists shows no error; losing the room for good does', () => {
  const { P, sockets, status, press } = setup();
  press('room-create'); sockets[0].open(); sockets[0].message(roomState);
  sockets[0].fail();   // the connection drops: the client goes to "reconnecting"
  assert.strictEqual(P.eval('relayClient.state().status'), 'reconnecting');
  assert.strictEqual(status(), '', 'a reconnect of an existing room is not an error banner');
  P.eval('relayClient.close()');   // gave up / left: final state "closed" while the room was confirmed
  assert.strictEqual(status(), 'room.unreachable');
});

check('normal end of a room (endRelayRoom) leaves no error on the start screen', () => {
  const { P, sockets, status, press } = setup();
  press('room-create'); sockets[0].open(); sockets[0].message(roomState);
  P.eval('endRelayRoom()');
  assert.strictEqual(status(), '');
});

check('join by ?room= link with the server down shows "unreachable" at once (not after the 60 s reconnect limit)', () => {
  const { sockets, status } = setup('&room=ABCD');
  assert.strictEqual(status(), 'room.connecting');
  sockets[0].fail();
  assert.strictEqual(status(), 'room.unreachable');
});

check('a client that gave up is replaced: Create room after "closed" opens a new socket and does not throw', () => {
  const { P, sockets, status, press } = setup();
  press('room-create'); sockets[0].fail();
  P.eval('relayClient.close()');   // final "closed"
  press('room-create');
  assert.strictEqual(sockets.length, 2, 'a fresh socket');
  assert.strictEqual(status(), 'room.connecting');
  sockets[1].open();
  assert.deepStrictEqual(sockets[1].sent.map(m => m.type), ['create_room']);
});

check('the relay refuses the create (server_busy): the status says so, the button works again and sends a second create_room', () => {
  const { P, sockets, status, press } = setup();
  press('room-create'); sockets[0].open();
  sockets[0].message({ type: 'error', code: 'server_busy' });
  assert.strictEqual(status(), 'room.refused');
  press('room-create');
  // 2026-11-26 (external review): an error answer to the first create is handled by the client: a busy relay is retried on a fresh socket, and the
  // second press is what that socket sends, once (it used to go out on the refused socket)
  P.timers.splice(0).forEach(x => x.fn());
  assert.ok(sockets.length >= 2, 'a new socket for the retry');
  sockets[sockets.length - 1].open();
  assert.deepStrictEqual(sockets[0].sent.map(m => m.type), ['create_room']);
  assert.deepStrictEqual(sockets[sockets.length - 1].sent.map(m => m.type), ['create_room']);
  assert.strictEqual(status(), 'room.connecting');
});

check('LATE-JOIN-1: the relay refuses a join into a started room (room_started): the status names it, not the generic refusal', () => {
  const { sockets, status } = setup('&room=ABCD');
  sockets[0].open();
  sockets[0].message({ type: 'error', code: 'room_started' });
  assert.strictEqual(status(), 'room.started');
});

check('a ?room= guest whose code is unknown sees the refusal and the friends panel is opened so it can be seen', () => {
  const { P, sockets, status } = setup('&room=ZZZZ');
  P.eval('window.__added = []; document.getElementById("start-screen").classList = { add: c => window.__added.push(c), remove() {}, contains: () => false, toggle() {} }');   // the harness DOM is a stub: record the class changes
  sockets[0].open();
  sockets[0].message({ type: 'error', code: 'unknown_code' });
  assert.strictEqual(status(), 'room.refused');
  assert.ok(P.eval('window.__added').includes('seats-open'), 'the friends panel is opened');
});

check('the host of a room pressing Join does nothing (no join message)', () => {
  const { P, sockets, press } = setup();
  press('room-create'); sockets[0].open(); sockets[0].message(roomState);
  press('room-join');
  assert.deepStrictEqual(sockets[0].sent.map(m => m.type), ['create_room'], 'no join message from the host');
});

check('a normal room end never opens the friends panel (red-team R6B-1), host and guest alike', () => {
  [ '', '&room=ABCD' ].forEach(search => {
    const { P, sockets, press } = setup(search);
    P.eval('window.__added = []; document.getElementById("start-screen").classList = { add: c => window.__added.push(c), remove() {}, contains: () => false, toggle() {} }');
    if (!search) press('room-create');
    sockets[0].open(); sockets[0].message(roomState);
    P.eval('endRelayRoom()');
    assert.strictEqual(P.eval('JSON.stringify(window.__added)'), '[]', 'no class change after a normal end (' + (search || 'host') + ')');   // JSON: the vm realm has its own Array
  });
});

check('rebuilding the start screen (hero pick, language, return) does not join a ?room= link twice (red-team R6B-2)', () => {
  const { P, sockets } = setup('&room=ABCD');
  sockets[0].open();
  P.eval('buildRoomControls()'); P.eval('buildRoomControls()');
  assert.deepStrictEqual(sockets.map(x => x.sent.filter(m => m.type === 'join').length), [1], 'one join on one socket, no second socket');
});

check('a refused guest sees the panel opened once, not on every later refusal', () => {
  const { P, sockets } = setup('&room=ZZZZ');
  P.eval('window.__added = []; document.getElementById("start-screen").classList = { add: c => window.__added.push(c), remove() {}, contains: () => false, toggle() {} }');
  sockets[0].open();
  sockets[0].message({ type: 'error', code: 'unknown_code' }); sockets[0].message({ type: 'error', code: 'unknown_code' });
  assert.strictEqual(P.eval('JSON.stringify(window.__added)'), '["seats-open"]');
});

check('a late message of a client the page already replaced does not touch the page (red-team R7B-4)', () => {
  const { P, sockets, status, press } = setup();
  press('room-create'); sockets[0].fail();
  P.eval('relayClient.close()');                      // the first client is dead
  press('room-create');                               // a second client, status "connecting"
  assert.strictEqual(status(), 'room.connecting');
  sockets[0].message({ type: 'error', code: 'server_busy' });   // the old socket still delivers something
  assert.strictEqual(status(), 'room.connecting', 'the old client must not set room.refused');
  assert.strictEqual(P.eval('relayCreateSent'), true, 'nor reset the create flag of the new client');
});

check('changing the team size drops the ?room= link before the reload (static: the reload itself needs a real browser) (red-team R7B-3)', () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'index.html'), 'utf8');
  const i = src.indexOf('u.searchParams.set("team", String(n));');
  assert.ok(i > 0 && src.slice(i, i + 200).includes('u.searchParams.delete("room")'));
});

check('a refused ?room= link gives the seats and the perspective back: Start Battle must not run a local human-vs-human match from the right side (red-team R8B-1)', () => {
  const { P, sockets } = setup('&room=ZZZZ');
  assert.strictEqual(P.eval('seats.right'), 'human', 'during the join attempt the right seat is the remote human');
  assert.strictEqual(P.eval('localPerspective.ownSeat'), 'right');
  sockets[0].open();
  sockets[0].message({ type: 'error', code: 'unknown_code' });
  assert.strictEqual(P.eval('seats.right'), 'ai', 'the computer is back on the right');
  assert.strictEqual(P.eval('localPerspective.ownSeat'), 'left', 'the player is on the left again');
});

check('a refused Create gives seats.right back; a confirmed room keeps it', () => {
  let t = setup();
  t.press('room-create'); assert.strictEqual(t.P.eval('seats.right'), 'human');
  t.sockets[0].open(); t.sockets[0].message({ type: 'error', code: 'server_busy' });
  assert.strictEqual(t.P.eval('seats.right'), 'ai');
  t = setup();
  t.press('room-create'); t.sockets[0].open(); t.sockets[0].message(roomState);
  assert.strictEqual(t.P.eval('seats.right'), 'human', 'a confirmed room keeps the remote seat');
});

console.log('room status: ' + passed + ' checks passed');
