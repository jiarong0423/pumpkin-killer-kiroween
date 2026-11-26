#!/usr/bin/env node
'use strict';

var assert = require('assert');
var RelayClient = require('../js/relay_client.js');

function FakeSocket() {
  this.sent = [];
  this.closed = false;
  this.onopen = null;
  this.onmessage = null;
  this.onclose = null;
  this.onerror = null;
}
FakeSocket.prototype.open = function () { this.onopen(); };
FakeSocket.prototype.send = function (text) { this.sent.push(JSON.parse(text)); };
FakeSocket.prototype.message = function (message) { this.onmessage({ data: JSON.stringify(message) }); };
FakeSocket.prototype.close = function () {
  this.closed = true;
  if (this.onclose) this.onclose();
};

function harness(token) {
  var sockets = [];
  var time = 0;
  var scheduled = [];
  var client = RelayClient.createClient({
    socketFactory: function () { var socket = new FakeSocket(); sockets.push(socket); return socket; },
    now: function () { return time; },
    setTimeoutFn: function (fn, delay) { scheduled.push({ fn: fn, delay: delay }); },
    seatToken: token || ''
  });
  return {
    client: client,
    sockets: sockets,
    advance: function (milliseconds) { time += milliseconds; },
    runNext: function () { assert.ok(scheduled.length, 'expected a reconnect timer'); return scheduled.shift(); },
    timerCount: function () { return scheduled.length; }
  };
}

(function testOrderedMessagesAndGapFill() {
  var h = harness();
  h.sockets[0].open();
  var applied = [];
  h.client.onMessage(function (message) { if (message.seq) applied.push(message.seq); });
  h.sockets[0].message({ type: 'start', seq: 1, seed: 7, scene: 'graveyard', round: 1, phase: 'red' });
  h.sockets[0].message({ type: 'action', seq: 3, round: 1, phase: 'red' });
  assert.deepStrictEqual(applied, [1]);
  h.sockets[0].message({ type: 'end_turn', seq: 2, round: 1, phase: 'red', next_round: 1, next_phase: 'white' });
  assert.deepStrictEqual(applied, [1, 2, 3]);
  assert.deepStrictEqual(h.client.state().log.map(function (message) { return message.seq; }), [1, 2, 3]);
  assert.strictEqual(h.client.state().phase, 'white');
})();

(function testOldRoundIsLoggedButNotApplied() {
  var h = harness();
  h.sockets[0].open();
  var applied = [];
  h.client.onMessage(function (message) { if (message.seq) applied.push(message.seq); });
  h.sockets[0].message({ type: 'start', seq: 1, seed: 8, scene: 'church', round: 2, phase: 'red' });
  h.sockets[0].message({ type: 'action', seq: 2, round: 1, phase: 'white' });
  assert.deepStrictEqual(applied, [1]);
  assert.strictEqual(h.client.state().log.length, 2);
  assert.strictEqual(h.client.state().round, 2);
})();

(function testReconnectUsesTokenAndLastSequence() {
  var h = harness('seat-token');
  h.sockets[0].open();
  h.sockets[0].message({ type: 'start', seq: 1, seed: 1, scene: 'graveyard', round: 1, phase: 'red' });
  h.sockets[0].close();
  assert.strictEqual(h.client.state().status, 'reconnecting');
  var timer = h.runNext();
  assert.strictEqual(timer.delay, 1000);
  h.advance(1000);
  timer.fn();
  assert.strictEqual(h.sockets.length, 2);
  h.sockets[1].open();
  assert.deepStrictEqual(h.sockets[1].sent, [{ type: 'resume', seat_token: 'seat-token', last_seq: 1 }]);
  h.sockets[1].message({ type: 'end_turn', seq: 2, round: 1, phase: 'red', next_round: 1, next_phase: 'white' });
  assert.strictEqual(h.client.state().phase, 'white');
})();

(function testResumeSnapshotAheadOfTheLogKeepsTheMissedRound() {
  var h = harness('seat-token');
  h.sockets[0].open();
  var applied = [];
  h.client.onMessage(function (message) { if (message.seq) applied.push(message.seq); });
  h.sockets[0].message({ type: 'start', seq: 1, seed: 1, scene: 'graveyard', round: 4, phase: 'red' });
  h.sockets[0].close();
  var timer = h.runNext(); h.advance(1000); timer.fn(); h.sockets[1].open();
  h.sockets[1].message({ type: 'room_state', seat: 'white', started: true, seed: 1, round: 5, phase: 'white', first_seq: 1, last_seq: 4 });
  h.sockets[1].message({ type: 'room_state', seat: 'white', started: true, seed: 1, round: 5, phase: 'white' });   // a broadcast during the replay
  h.sockets[1].message({ type: 'action', seq: 2, round: 4, phase: 'white' });
  h.sockets[1].message({ type: 'end_turn', seq: 3, round: 4, phase: 'white', next_round: 5, next_phase: 'red' });
  h.sockets[1].message({ type: 'end_turn', seq: 4, round: 5, phase: 'red', next_round: 5, next_phase: 'white' });
  assert.deepStrictEqual(applied, [1, 2, 3, 4]);
  assert.strictEqual(h.client.state().round, 5);
  assert.strictEqual(h.client.state().phase, 'white');
})();

(function testReconnectGivesUpAfterSixtySeconds() {
  var h = harness('token');
  h.sockets[0].open();
  h.sockets[0].close();
  while (h.client.state().status !== 'closed') {
    var timer = h.runNext();
    h.advance(timer.delay);
    timer.fn();
    if (h.client.state().status === 'reconnecting' && h.sockets.length > 1) h.sockets[h.sockets.length - 1].close();
  }
  assert.ok(h.sockets.length > 2);
  assert.strictEqual(h.client.state().status, 'closed');
})();

(function testRoundHashMismatchIsVisible() {
  var h = harness();
  h.sockets[0].open();
  h.sockets[0].message({ type: 'start', seq: 1, seed: 3, scene: 'school', round: 1, phase: 'red' });
  h.sockets[0].message({ type: 'round_hash', seq: 2, round: 1, seat_id: 'red-1', hash: 'aaaa' });
  h.sockets[0].message({ type: 'round_hash', seq: 3, round: 1, seat_id: 'white-1', hash: 'bbbb' });
  assert.strictEqual(h.client.state().status, 'out_of_sync');
})();

(function testRelayAddressPathsArePreserved() {
  assert.strictEqual(RelayClient.relaySocketUrl('wss://host/relay'), 'wss://host/relay');
  assert.strictEqual(RelayClient.relaySocketUrl('wss://host'), 'wss://host/ws');
  assert.strictEqual(RelayClient.relaySocketUrl('ws://localhost:8765/'), 'ws://localhost:8765/ws');
})();

(function testJoinCodeIsTrimmedAndUpperCased() {
  var h = harness(); h.sockets[0].open();
  h.client.join(' ab2cd3 ', 'white');
  assert.deepStrictEqual(h.sockets[0].sent[0], { type: 'join', code: 'AB2CD3', seat: 'white' });
})();

console.log('relay client paths: ok');
console.log('relay client ordering: ok');
console.log('relay client reconnect and hash checks: ok');

// Red-team R3B-1: a real browser WebSocket throws InvalidStateError on send() while CONNECTING (readyState 0). The page's first Create room press
// lands exactly there. This fake behaves like the browser; the other fakes above are 'open' from the start and could never show the problem.
(function () {
  var made = [];
  function StrictSocket() { this.sent = []; this.readyState = 0; this.onopen = null; this.onmessage = null; this.onclose = null; this.onerror = null; made.push(this); }
  StrictSocket.prototype.send = function (text) {
    if (this.readyState !== 1) { var e = new Error('Failed to execute send on WebSocket: Still in CONNECTING state.'); e.name = 'InvalidStateError'; throw e; }
    this.sent.push(JSON.parse(text));
  };
  StrictSocket.prototype.close = function () { this.readyState = 3; if (this.onclose) this.onclose(); };
  var client = RelayClient.createClient({ socketFactory: function () { return new StrictSocket(); }, now: function () { return 0; }, setTimeoutFn: function () {} });
  assert.doesNotThrow(function () { client.createRoom({ scene: 'forest' }); }, 'createRoom while CONNECTING must queue, not throw');
  assert.strictEqual(made[0].sent.length, 0, 'nothing is sent before the socket opens');
  made[0].readyState = 1; made[0].onopen();
  assert.strictEqual(made[0].sent.length, 1, 'the queued create_room goes out on open');
  assert.strictEqual(made[0].sent[0].type, 'create_room');
  // a socket that closes before it opens drops the queued message (no stale create_room on the next socket)
  var made2 = made.length;
  var c2 = RelayClient.createClient({ socketFactory: function () { return new StrictSocket(); }, now: function () { return 0; }, setTimeoutFn: function () {} });
  c2.createRoom({}); made[made2].close();
  assert.strictEqual(made[made2].sent.length, 0);
})();

// Red-team R4B-1 / R4B-3 (strict browser-like sockets, a controllable timer):
// (a) a client WITHOUT a seat token whose first socket fails replays its first message (create_room) on the next socket; there is nothing to resume;
// (b) a seated client resumes FIRST on a reconnect socket and only then sends what was queued while it was between sockets.
(function () {
  function make() {
    var made = [], timers = [];
    function Strict() { this.sent = []; this.readyState = 0; this.onopen = this.onmessage = this.onclose = this.onerror = null; made.push(this); }
    Strict.prototype.send = function (text) { if (this.readyState !== 1) { var e = new Error('Still in CONNECTING state.'); e.name = 'InvalidStateError'; throw e; } this.sent.push(JSON.parse(text)); };
    Strict.prototype.open = function () { this.readyState = 1; this.onopen(); };
    Strict.prototype.drop = function () { this.readyState = 3; this.onclose(); };
    Strict.prototype.message = function (m) { this.onmessage({ data: JSON.stringify(m) }); };
    var client = RelayClient.createClient({ socketFactory: function () { return new Strict(); }, now: function () { return 0; }, setTimeoutFn: function (fn) { timers.push(fn); } });
    return { made: made, timers: timers, client: client };
  }
  var a = make();
  a.client.createRoom({});
  a.made[0].drop();                                   // connection refused before it ever opened
  assert.strictEqual(a.client.state().status, 'reconnecting');
  a.timers.shift()();                                  // the reconnect timer fires: a second socket
  a.made[1].open();
  assert.deepStrictEqual(a.made[1].sent.map(function (m) { return m.type; }), ['create_room'], 'no token: the first message is replayed, no resume');

  var b = make();
  b.made[0].open();
  b.client.createRoom({});
  b.made[0].message({ type: 'room_state', code: 'ABCD', seat: 'red', seat_token: 'tok-1', seats: [] });
  b.made[0].drop();                                    // seated, then the connection drops
  assert.doesNotThrow(function () { b.client.endTurn(1, 'red'); }, 'a send between two sockets waits instead of throwing');
  b.timers.shift()();
  b.made[1].open();
  assert.deepStrictEqual(b.made[1].sent.map(function (m) { return m.type; }), ['resume', 'end_turn'], 'resume first, then the queued message');
  assert.strictEqual(b.made[1].sent[0].seat_token, 'tok-1');
})();
console.log('relay client reconnect order and replay: ok');
console.log('relay client connecting-socket queue: ok');

// Connection scenario matrix (red-team R5A-1..4 and the source diagnosis of round 5): strict browser-like sockets, a controllable clock and timer.
(function () {
  function make() {
    var env = { made: [], timers: [], time: 0 };
    function Strict() { this.sent = []; this.readyState = 0; this.onopen = this.onmessage = this.onclose = this.onerror = null; env.made.push(this); }
    Strict.prototype.send = function (text) { if (this.readyState !== 1) { var e = new Error('Still in CONNECTING state.'); e.name = 'InvalidStateError'; throw e; } this.sent.push(JSON.parse(text)); };
    Strict.prototype.open = function () { this.readyState = 1; this.onopen(); };
    Strict.prototype.drop = function () { this.readyState = 3; this.onclose(); };
    Strict.prototype.close = function () { this.readyState = 3; };
    Strict.prototype.message = function (m) { this.onmessage({ data: JSON.stringify(m) }); };
    env.client = RelayClient.createClient({ socketFactory: function () { return new Strict(); }, now: function () { return env.time; }, setTimeoutFn: function (fn, ms) { env.timers.push({ fn: fn, ms: ms }); } });
    env.types = function (i) { return env.made[i].sent.map(function (m) { return m.type; }); };
    env.fire = function () { env.timers.shift().fn(); };
    return env;
  }
  var lobby = { type: 'room_state', code: 'ABCD', seat: 'red', seat_token: 'tok-1', seats: [] };

  // S1 (R5A-1): the first message was SENT, the connection drops before any room_state: it is replayed on the next socket (create_room and join alike)
  ['create', 'join'].forEach(function (kind) {
    var e = make(); e.made[0].open();
    if (kind === 'create') e.client.createRoom({}); else e.client.join('ABCD', 'white');
    assert.strictEqual(e.made[0].sent.length, 1);
    e.made[0].drop(); e.fire(); e.made[1].open();
    assert.deepStrictEqual(e.types(1), [kind === 'create' ? 'create_room' : 'join'], kind + ' replayed once on the new socket');
    e.made[1].message(lobby);                          // answered: a token arrived, the replay stops
    assert.strictEqual(e.client.state().status, 'waiting');
    e.made[1].drop(); e.fire(); e.made[2].open();
    assert.deepStrictEqual(e.types(2), ['resume'], 'after the token only a resume is sent');
  });

  // S2 (R5A-2): a second drop more than 60 s after the first is a NEW outage: reconnecting with the first backoff, not closed
  (function () {
    var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(lobby);
    e.made[0].drop(); var firstDelay = e.timers[0].ms; e.fire(); e.made[1].open(); e.made[1].message(lobby);
    e.time = 100000;
    e.made[1].drop();
    assert.strictEqual(e.client.state().status, 'reconnecting', 'a drop after a long healthy time does not end the client');
    assert.strictEqual(e.timers[0].ms, firstDelay, 'the backoff starts again');
  })();

  // S3 (R5A-3): a lobby room (no start yet): a successful resume ends 'reconnecting'; a later error does not close the client
  (function () {
    var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(lobby);
    e.made[0].drop(); e.fire(); e.made[1].open();
    assert.strictEqual(e.client.state().status, 'reconnecting');
    e.made[1].message(lobby);
    assert.strictEqual(e.client.state().status, 'waiting');
    e.made[1].message({ type: 'error', code: 'rate_limited' });
    assert.strictEqual(e.client.state().status, 'waiting', 'an error after the answer is only a message');
  })();

  // S4 (R5A-4): a message queued between two sockets survives a socket that closes before it opens
  (function () {
    var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(lobby);
    e.made[0].drop();
    e.client.endTurn(1, 'red');                        // between sockets
    e.fire(); e.made[1].drop();                        // the next socket dies before it opens
    e.fire(); e.made[2].open();
    assert.deepStrictEqual(e.types(2), ['resume', 'end_turn']);
  })();

  // S5: an error while the answer to a resume is pending ends the client (the relay refused the seat), and the socket is released
  (function () {
    var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(lobby);
    e.made[0].drop(); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'error', code: 'invalid_seat_token' });
    assert.strictEqual(e.client.state().status, 'closed');
    assert.strictEqual(e.made[1].readyState, 3, 'the socket was closed');
    assert.throws(function () { e.client.endTurn(1, 'red'); }, /not open/);
  })();

  // S7 (R6A-1): a transient refusal (the relay has not yet noticed the old socket: seat_in_use) is retried with the backoff; a final one (resume_expired) closes
  (function () {
    var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(lobby);
    e.made[0].drop(); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'error', code: 'seat_in_use' });
    assert.strictEqual(e.client.state().status, 'reconnecting', 'transient: still trying');
    assert.strictEqual(e.timers.length, 1, 'a new attempt is scheduled');
    e.fire(); e.made[2].open(); e.made[2].message(lobby);
    assert.strictEqual(e.client.state().status, 'waiting');
    e.made[2].drop(); e.fire(); e.made[3].open();
    e.made[3].message({ type: 'error', code: 'resume_expired' });
    assert.strictEqual(e.client.state().status, 'closed', 'final: the relay dropped the seat');
  })();

  // S8..S11 (R6A-2): messages written to a socket that then died are resent after the resume once the replayed log has been applied, unless their echo is in the replay
  (function () {
    var seated = { type: 'room_state', code: 'ABCD', seat: 'red', seat_id: 'red-1', seat_token: 'tok-1', seats: [], last_seq: 0 };
    function seatedEnv() { var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(seated); return e; }
    // S8: the relay never got them
    var e = seatedEnv();
    e.client.sendAction({ kind: 'throw', power: 50 }); e.client.endTurn(1, 'red');
    assert.deepStrictEqual(e.types(0), ['create_room', 'action', 'end_turn']);
    e.made[0].drop(); e.fire(); e.made[1].open();
    assert.deepStrictEqual(e.types(1), ['resume'], 'resume first');
    e.made[1].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 0 });
    assert.deepStrictEqual(e.types(1), ['resume', 'action', 'end_turn'], 'both lost messages are sent again after the answer');
    // their echoes now arrive: nothing is sent a third time after another drop
    e.made[1].message({ type: 'action', seq: 1, seat_id: 'red-1' }); e.made[1].message({ type: 'end_turn', seq: 2, seat_id: 'red-1' });
    e.made[1].drop(); e.fire(); e.made[2].open(); e.made[2].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 2 });
    assert.deepStrictEqual(e.types(2), ['resume'], 'acknowledged by their echo: not resent');

    // S9: the relay did get the action (its echo is in the replay), the end_turn was lost: only the end_turn is resent, and only after the replay was applied
    e = seatedEnv();
    e.client.sendAction({ kind: 'throw', power: 50 }); e.client.endTurn(1, 'red');
    e.made[0].drop(); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 1 });
    assert.deepStrictEqual(e.types(1), ['resume'], 'the replay is not applied yet: wait');
    e.made[1].message({ type: 'action', seq: 1, seat_id: 'red-1' });
    assert.deepStrictEqual(e.types(1), ['resume', 'end_turn'], 'only the unacknowledged one');

    // S10: a message that waited between two sockets is written once (by the outbox), not twice
    e = seatedEnv();
    e.made[0].drop(); e.client.endTurn(1, 'red'); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 0 });
    assert.deepStrictEqual(e.types(1), ['resume', 'end_turn']);

    // S12: a message that waited in the outbox, was written on the next socket and then lost again (second drop, no echo) is resent after the second resume
    e = seatedEnv();
    e.made[0].drop(); e.client.endTurn(1, 'red'); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 0 });
    e.made[1].drop(); e.fire(); e.made[2].open();
    e.made[2].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 0 });
    assert.deepStrictEqual(e.types(2), ['resume', 'end_turn']);

    // S13: the OTHER seat's echo does not acknowledge my message
    e = seatedEnv();
    e.client.endTurn(1, 'red');
    e.made[0].message({ type: 'end_turn', seq: 1, seat_id: 'white-1' });
    e.made[0].drop(); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 1 });
    assert.deepStrictEqual(e.types(1), ['resume', 'end_turn']);

    // S14 (R7A-2): a message written on a socket that the client then abandons after a transient error (seat_in_use) counts as lost and is resent after the next resume
    e = seatedEnv();
    e.made[0].drop(); e.client.endTurn(1, 'red'); e.fire(); e.made[1].open();
    assert.deepStrictEqual(e.types(1), ['resume', 'end_turn']);
    e.made[1].message({ type: 'error', code: 'seat_in_use' });
    e.fire(); e.made[2].open();
    e.made[2].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 0 });
    assert.deepStrictEqual(e.types(2), ['resume', 'end_turn'], 'the end_turn written on the abandoned socket is sent again');

    // S11: judge is never resent
    e = seatedEnv();
    e.client.sendJudge({ hit: false });
    e.made[0].drop(); e.fire(); e.made[1].open();
    e.made[1].message({ type: 'room_state', seat: 'red', seat_id: 'red-1', seats: [], last_seq: 0 });
    assert.deepStrictEqual(e.types(1), ['resume']);
  })();

  // S6: the outbox is bounded (16); close() empties it and a later socket event sends nothing
  (function () {
    var e = make(); e.made[0].open(); e.client.createRoom({}); e.made[0].message(lobby);
    e.made[0].drop();
    for (var i = 1; i <= 20; i++) e.client.endTurn(i, 'red');
    e.fire(); e.made[1].open();
    var types = e.types(1);
    assert.strictEqual(types.length, 1 + 16, 'resume plus the newest 16');
    assert.strictEqual(e.made[1].sent[1].round, 5, 'the oldest 4 were dropped');
  })();
})();
console.log('relay client connection scenario matrix: ok');
