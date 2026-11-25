#!/usr/bin/env node
'use strict';
// Red-team R2A-F1 (2026-11-24): when a non-spectator seat leaves past the grace period (`seat_left`),
// a seat whose owned units are ALL dead (hp <= 0) must NOT end the match (neither forfeit its team nor
// award the other side a win). A seat that still owns at least one living unit (hp > 0) still ends the
// match as before (teammate leaves -> our team forfeits; opponent leaves -> our team wins). Rooms with
// no `owners` map (1v1) or no entry for the leaving seat keep the previous behaviour.
const assert = require('assert');
const { loadPage } = require('./page_harness');

let passed = 0;
function check(name, fn) {
  try {
    fn();
    passed++;
    console.log('ok   - ' + name);
  } catch (e) {
    process.exitCode = 1;
    console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n       ') : e));
  }
}

class Hub {   // minimal in-memory pk_relay.py matching test_page_relay_split.js
  constructor() {
    this.clients = []; this.log = []; this.nextSeq = 1; this.seed = 123456789;
    this.started = false; this.round = 1; this.phase = null; this.firstTeam = 'red';
    this.errors = []; this.teamSize = 1; this.code = 'ABC234'; this.scene = 'graveyard';
  }
  connect() {
    const hub = this, c = { queue: [], entry: null, onmessage: null, onopen: null, onclose: null, onerror: null, readyState: 1 };
    c.send = raw => hub.receive(c, JSON.parse(raw));
    c.close = () => {};
    hub.clients.push(c);
    return c;
  }
  to(c, m) { c.queue.push(JSON.stringify(m)); }
  stamp(m) { m = Object.assign({}, m, { seq: this.nextSeq++ }); this.log.push(m); return m; }
  broadcast(m) { const s = this.stamp(m); this.clients.forEach(c => { if (c.entry) this.to(c, s); }); return s; }
  state() {
    const m = { type: 'room_state', seats: this.clients.filter(c => c.entry).map(c => ({ seat_id: c.entry.seat_id, team: c.entry.team, ready: c.entry.ready, units: c.entry.units })), rules_version: 'relay-v0', started: this.started };
    if (this.teamSize > 1) m.team_size = this.teamSize;
    if (this.started) Object.assign(m, { seed: this.seed, round: this.round, phase: this.phase, first_team: this.firstTeam });
    return m;
  }
  bootstrap(c, withCode) {
    const m = this.state();
    if (withCode) m.code = this.code;
    Object.assign(m, { seat: c.entry.team, seat_id: c.entry.seat_id, seat_token: 'tok-' + c.entry.seat_id, last_seq: this.nextSeq - 1 });
    this.to(c, m);
  }
  receive(c, m) {
    if (m.type === 'create_room') {
      c.entry = { seat_id: 'red-1', team: 'red', units: m.units || [], ready: false };
      if (m.team_size) this.teamSize = m.team_size;
      if (m.scene) this.scene = m.scene;
      this.bootstrap(c, true);
      return;
    }
    if (m.type === 'join') {
      const same = this.clients.filter(x => x.entry && x.entry.team === m.seat).length;
      c.entry = { seat_id: m.seat + '-' + (same + 1), team: m.seat, units: m.units || [], ready: false };
      this.bootstrap(c, true);
      this.log.forEach(x => this.to(c, x));
      this.broadcast(this.state());
      return;
    }
    if (m.type === 'ready') {
      if ('units' in m) c.entry.units = m.units;
      c.entry.ready = true;
      this.broadcast(this.state());
      const players = this.clients.filter(x => x.entry);
      const teams = t => players.filter(x => x.entry.team === t);
      if (!this.started && teams('red').length && teams('white').length && players.every(x => x.entry.ready)) {
        this.started = true; this.round = 1; this.phase = 'red';
        const st = { type: 'start', seed: this.seed, scene: this.scene, first_team: 'red', round: 1, phase: 'red' };
        if (this.teamSize > 1) {
          st.team_size = this.teamSize; st.heroes = {}; st.owners = {};
          [['red', 'left'], ['white', 'right']].forEach(([team, side]) => {
            const seats = teams(team).map(x => x.entry).sort((p, q) => p.seat_id.localeCompare(q.seat_id));
            const listed = [].concat(...seats.map(s => s.units)).slice(0, this.teamSize);
            st.heroes[side] = listed.concat(Array(this.teamSize - listed.length).fill(null));
            if (seats.length === 1) {
              for (let k = 0; k < this.teamSize; k++) st.owners[side + '_' + k] = seats[0].seat_id;
            } else if (seats.every(s => s.units.length) && seats.reduce((n, s) => n + s.units.length, 0) === this.teamSize) {
              let k = 0;
              seats.forEach(s => s.units.forEach(() => { st.owners[side + '_' + k++] = s.seat_id; }));
            }
          });
        }
        this.owners = st.owners || null;
        this.broadcast(st);
      }
    }
  }
  flush() {
    let n = 0;
    this.clients.forEach(c => { while (c.queue.length) { const raw = c.queue.shift(); n++; if (c.onmessage) c.onmessage({ data: raw }); } });
    return n;
  }
}

function pump(hub, pages, maxRounds) {
  for (let i = 0; i < (maxRounds || 3000); i++) {
    let busy = hub.flush() > 0;
    pages.forEach(P => {
      const t = P.timers.splice(0).filter(x => !/^function updateStartGate/.test(String(x.fn)));
      if (t.length) busy = true;
      t.forEach(x => x.fn());
      P.eval('hitStop = 0; updatePhysics(0.01)');
    });
    const flying = pages.some(P => P.get('projectiles').length > 0 || P.get('diceRoll') || P.eval('relayInbox.length > 0'));
    if (!busy && !flying && !hub.clients.some(c => c.queue.length) && i > 20) {
      if (pages.every(P => !P.timers.length)) return i;
    }
  }
  throw new Error('pump did not settle');
}

// Red split 1+2 (red-1 owns left_0, red-2 owns left_1 & left_2); White 1 seat (white-1 owns right_0..2).
function makeRedSplit() {
  const hub = new Hub();
  const mk = extra => loadPage({ team: 3, search: '?relay=ws://hub&team=3' + extra });
  const A = mk(''), B = mk('&room=' + hub.code), C = mk('&room=' + hub.code);
  [A, B, C].forEach(P => { P.context.WebSocket = function () { return hub.connect(); }; });
  A.eval('relayClaimCount = 1; pickedHero = "skeleton"');
  B.eval('relayClaimCount = 2; relayJoinSeat = "red"; pickedHero = "wizard"');
  C.eval('pickedHero = "knight"');
  A.eval('buildRoomControls()'); A.eval('document.getElementById("room-create").onclick()'); hub.flush();
  B.eval('buildRoomControls()'); pump(hub, [A, B]);
  C.eval('buildRoomControls()'); pump(hub, [A, B, C]);
  [A, B, C].forEach(P => P.eval('startMatch()'));
  pump(hub, [A, B, C]);
  return { hub, A, B, C };
}

// White split 1+2 (white-1 owns right_0, white-2 owns right_1 & right_2); Red 1 seat (red-1 owns left_0..2).
function makeWhiteSplit() {
  const hub = new Hub();
  const mk = extra => loadPage({ team: 3, search: '?relay=ws://hub&team=3' + extra });
  const R = mk(''), W1 = mk('&room=' + hub.code), W2 = mk('&room=' + hub.code);
  [R, W1, W2].forEach(P => { P.context.WebSocket = function () { return hub.connect(); }; });
  R.eval('pickedHero = "skeleton"');
  W1.eval('relayClaimCount = 1; relayJoinSeat = "white"; pickedHero = "knight"');
  W2.eval('relayClaimCount = 2; relayJoinSeat = "white"; pickedHero = "wizard"');
  R.eval('buildRoomControls()'); R.eval('document.getElementById("room-create").onclick()'); hub.flush();
  W1.eval('buildRoomControls()'); pump(hub, [R, W1]);
  W2.eval('buildRoomControls()'); pump(hub, [R, W1, W2]);
  [R, W1, W2].forEach(P => P.eval('startMatch()'));
  pump(hub, [R, W1, W2]);
  return { hub, R, W1, W2 };
}

// 1v1 room (teamSize = 1 -> relaySnap().owners is null).
function makePair1v1() {
  const hub = new Hub();
  const mk = extra => loadPage({ team: 1, search: '?relay=ws://hub&team=1' + extra });
  const R = mk(''), W = mk('&room=' + hub.code);
  [R, W].forEach(P => { P.context.WebSocket = function () { return hub.connect(); }; });
  R.eval('pickedHero = "skeleton"');
  W.eval('pickedHero = "knight"');
  R.eval('buildRoomControls()'); R.eval('document.getElementById("room-create").onclick()'); hub.flush();
  W.eval('buildRoomControls()'); pump(hub, [R, W]);
  [R, W].forEach(P => P.eval('startMatch()'));
  pump(hub, [R, W]);
  return { hub, R, W };
}

check('(a1) red-2 leaves after all its units are dead (hp <= 0): gameOver stays null for both teammate A and opponent C', () => {
  const { hub, A, C } = makeRedSplit();
  // On A (red frame), red-2 owns left_1 and left_2; on C (white frame), red-2 owns right_1 and right_2.
  A.eval('unitsOf("left")[1].hp = 0; unitsOf("left")[2].hp = 0;');
  C.eval('unitsOf("right")[1].hp = 0; unitsOf("right")[2].hp = 0;');
  hub.broadcast({ type: 'seat_left', seat_id: 'red-2', team: 'red', reason: 'disconnect_timeout' });
  pump(hub, [A, C]);
  assert.strictEqual(A.get('gameOver'), null, 'teammate A must not forfeit when dead seat red-2 leaves');
  assert.strictEqual(C.get('gameOver'), null, 'opponent C must not win when dead seat red-2 leaves');
  assert.notStrictEqual(A.get('turn'), 'over', 'A turn must not be over');
  assert.notStrictEqual(C.get('turn'), 'over', 'C turn must not be over');
});

check('(a2) white-2 leaves after all its units are dead (hp <= 0, including negative hp): gameOver stays null for both R and W1', () => {
  const { hub, R, W1 } = makeWhiteSplit();
  // On R (red frame), white-2 owns right_1 and right_2; on W1 (white frame), white-2 owns left_1 and left_2.
  R.eval('unitsOf("right")[1].hp = 0; unitsOf("right")[2].hp = -5;');
  W1.eval('unitsOf("left")[1].hp = 0; unitsOf("left")[2].hp = -5;');
  hub.broadcast({ type: 'seat_left', seat_id: 'white-2', team: 'white', reason: 'disconnect_timeout' });
  pump(hub, [R, W1]);
  assert.strictEqual(R.get('gameOver'), null, 'opponent R must not win when dead seat white-2 leaves');
  assert.strictEqual(W1.get('gameOver'), null, 'teammate W1 must not forfeit when dead seat white-2 leaves');
});

check('(b1) red-2 leaves with one dead unit and one living unit: teammate A forfeits (ai), opponent C wins (player)', () => {
  const { hub, A, C } = makeRedSplit();
  A.eval('unitsOf("left")[1].hp = 0;');
  C.eval('unitsOf("right")[1].hp = 0;');
  assert.ok(A.eval('unitsOf("left")[2].hp > 0') && C.eval('unitsOf("right")[2].hp > 0'), 'left_2 / right_2 is still alive');
  hub.broadcast({ type: 'seat_left', seat_id: 'red-2', team: 'red', reason: 'disconnect_timeout' });
  pump(hub, [A, C]);
  assert.strictEqual(A.get('gameOver'), 'ai', 'teammate A forfeits when red-2 leaves with a living unit');
  assert.strictEqual(C.get('gameOver'), 'player', 'opponent C wins when red-2 leaves with a living unit');
});

check('(b2) white-2 leaves with all its units alive: teammate W1 forfeits (ai), opponent R wins (player)', () => {
  const { hub, R, W1 } = makeWhiteSplit();
  hub.broadcast({ type: 'seat_left', seat_id: 'white-2', team: 'white', reason: 'disconnect_timeout' });
  pump(hub, [R, W1]);
  assert.strictEqual(W1.get('gameOver'), 'ai', 'teammate W1 forfeits when live seat white-2 leaves');
  assert.strictEqual(R.get('gameOver'), 'player', 'opponent R wins when live seat white-2 leaves');
});

check('(c1) 1v1 room (owners is null): opponent leaving still awards a win as before', () => {
  const { hub, R } = makePair1v1();
  assert.strictEqual(R.eval('relaySnap().owners'), null, '1v1 room has no owners map');
  hub.broadcast({ type: 'seat_left', seat_id: 'white-1', team: 'white', reason: 'disconnect_timeout' });
  pump(hub, [R]);
  assert.strictEqual(R.get('gameOver'), 'player', '1v1 opponent leaving still ends match in our win');
});

check('(c2) team room with a seat_id absent from owners: falls back to previous behaviour', () => {
  const { hub, A, C } = makeRedSplit();
  hub.broadcast({ type: 'seat_left', seat_id: 'red-9', team: 'red', reason: 'disconnect_timeout' });
  pump(hub, [A, C]);
  assert.strictEqual(A.get('gameOver'), 'ai', 'unlisted teammate seat keeps old forfeit rule');
  assert.strictEqual(C.get('gameOver'), 'player', 'unlisted opponent seat keeps old win rule');
});

// ROOM-FLOW R9b: a departure can arrive while this page is still playing out the last throw (the leaver finished first, or a resume replays the log),
// so it is judged only after the screen has been still for 3 s (six 500 ms looks).
function tick(P, times) {
  for (let i = 0; i < times; i++) P.timers.splice(0).filter(x => !/^function updateStartGate/.test(String(x.fn))).forEach(x => x.fn());
}
const leftNow = { type: 'seat_left', seat_id: 'white-1', team: 'white', reason: 'left' };

check('(d1) a leave that arrives before the last throw has landed does not flip the result', () => {
  const { hub, R } = makePair1v1();
  tick(R, 3); R.eval('relayIncoming = 1');
  hub.broadcast(leftNow); hub.flush();
  assert.strictEqual(R.get('gameOver'), null, 'not judged on arrival');
  tick(R, 100);
  assert.strictEqual(R.get('gameOver'), null, 'not judged while the throw is in the air');
  R.eval('relayIncoming = 0; gameOver = "ai"; turn = "over"');   // the throw lands and the leaver has won
  tick(R, 20);
  assert.strictEqual(R.get('gameOver'), 'ai', 'the landed throw decides, not the departure');
});

check('(d2) on a still screen the leave rule applies after the quiet time, not at once', () => {
  const { hub, R } = makePair1v1();
  tick(R, 3);
  hub.broadcast(leftNow); hub.flush();
  tick(R, 5);
  assert.strictEqual(R.get('gameOver'), null, 'five quiet looks are not enough');
  tick(R, 1);
  assert.strictEqual(R.get('gameOver'), 'player'); assert.strictEqual(R.get('turn'), 'over');
});

check('(d3) movement restarts the quiet time', () => {
  const { hub, R } = makePair1v1();
  tick(R, 3);
  hub.broadcast(leftNow); hub.flush(); tick(R, 4);
  R.eval('relayIncoming = 1'); tick(R, 1); R.eval('relayIncoming = 0'); tick(R, 5);
  assert.strictEqual(R.get('gameOver'), null);
  tick(R, 1);
  assert.strictEqual(R.get('gameOver'), 'player');
});

check('(d4) a queued message that never gets its turn cannot hold the departure back for ever', () => {
  const { hub, A, C } = makeRedSplit();
  tick(C, 3); C.eval('relayInbox.push({ type: "action", seq: 100000, seat_id: "red-2", round: 99, phase: "red" })');
  hub.broadcast({ type: 'seat_left', seat_id: 'red-2', team: 'red', reason: 'left' }); hub.flush();
  tick(C, 39);
  assert.strictEqual(C.get('gameOver'), null);
  tick(C, 1);
  assert.strictEqual(C.get('gameOver'), 'player');
  void A;
});

check('(d5) a second match or a closed room drops a departure that was still waiting', () => {
  const { hub, R } = makePair1v1();
  tick(R, 3);
  hub.broadcast(leftNow); hub.flush();
  R.eval('endRelayRoom()'); tick(R, 20);
  assert.strictEqual(R.get('gameOver'), null);
});

console.log('test_seat_leave_dead: ' + passed + ' passed' + (process.exitCode ? ', FAILED' : ''));
