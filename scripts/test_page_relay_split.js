#!/usr/bin/env node
'use strict';
// Gap "unit slot fill" (docs/ADR_unit_slot_fill_20261124.md, stage 1): THREE real pages play through an in-memory hub that follows pk_relay.py
// (several seats per team, owners split by unit-list length, an action only from the owning seat). Red is split: page A owns 1 unit, page B owns 2;
// page C is white with 3. Checks: the start message names the owners, the heroes of ALL left units come from `start.heroes`, the page of the seat that
// owns the active unit plays and the other red page waits, a teammate's throw runs on the teammate's page against the same victim, one judge per
// victim unit, no relay error, and every page ends the round with the same round hash.
const assert = require('assert');
const { loadPage } = require('./page_harness');

let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n       ') : e)); } }

class Hub {   // the part of pk_relay.py the pages rely on, in memory
  constructor() { this.clients = []; this.log = []; this.nextSeq = 1; this.seed = 123456789; this.started = false; this.round = 1; this.phase = null; this.firstTeam = 'red'; this.errors = []; this.actions = {}; this.byTurn = new Set(); this.hashes = {}; this.outOfSync = []; this.seen = []; this.teamSize = 1; this.code = 'ABC234'; this.scene = 'graveyard'; }
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
  state() { const m = { type: 'room_state', seats: this.clients.filter(c => c.entry).map(c => ({ seat_id: c.entry.seat_id, team: c.entry.team, ready: c.entry.ready, units: c.entry.units })), rules_version: 'relay-v0', started: this.started };
    if (this.teamSize > 1) m.team_size = this.teamSize; if (this.started) Object.assign(m, { seed: this.seed, round: this.round, phase: this.phase, first_team: this.firstTeam }); return m; }
  bootstrap(c, withCode) { const m = this.state(); if (withCode) m.code = this.code; Object.assign(m, { seat: c.entry.team, seat_id: c.entry.seat_id, seat_token: 'tok-' + c.entry.seat_id, last_seq: this.nextSeq - 1 }); this.to(c, m); }
  err(c, code) { this.errors.push(code); this.to(c, { type: 'error', code }); }
  valid(c, m) { return this.started && m.round === this.round && m.phase === this.phase && c.entry.team === this.phase; }
  receive(c, m) {
    this.seen.push({ from: c.entry && c.entry.seat_id, m });
    if (m.type === 'create_room') { c.entry = { seat_id: 'red-1', team: 'red', units: m.units || [], ready: false }; if (m.team_size) this.teamSize = m.team_size; if (m.scene) this.scene = m.scene; this.bootstrap(c, true); return; }
    if (m.type === 'join') { const same = this.clients.filter(x => x.entry && x.entry.team === m.seat).length; c.entry = { seat_id: m.seat + '-' + (same + 1), team: m.seat, units: m.units || [], ready: false }; this.bootstrap(c, true); this.log.forEach(x => this.to(c, x)); this.broadcast(this.state()); return; }
    if (!c.entry) return this.err(c, 'join_required');
    if (m.type === 'ready') {
      if ('units' in m) c.entry.units = m.units;
      c.entry.ready = true; this.broadcast(this.state());
      const players = this.clients.filter(x => x.entry);
      const teams = t => players.filter(x => x.entry.team === t);
      if (!this.started && teams('red').length && teams('white').length && players.every(x => x.entry.ready)) { this.started = true; this.round = 1; this.phase = 'red'; const st = { type: 'start', seed: this.seed, scene: this.scene, first_team: 'red', round: 1, phase: 'red' };
        if (this.teamSize > 1) { st.team_size = this.teamSize; st.heroes = {}; st.owners = {};
          [['red', 'left'], ['white', 'right']].forEach(([team, side]) => { const seats = teams(team).map(x => x.entry).sort((p, q) => p.seat_id.localeCompare(q.seat_id)); const listed = [].concat(...seats.map(s => s.units)).slice(0, this.teamSize); st.heroes[side] = listed.concat(Array(this.teamSize - listed.length).fill(null));
            if (seats.length === 1) for (let k = 0; k < this.teamSize; k++) st.owners[side + '_' + k] = seats[0].seat_id;
            else if (seats.every(s => s.units.length) && seats.reduce((n, s) => n + s.units.length, 0) === this.teamSize) { let k = 0; seats.forEach(s => s.units.forEach(() => { st.owners[side + '_' + k++] = s.seat_id; })); } }); }
        this.owners = st.owners || {}; this.broadcast(st); }
      return;
    }
    if (m.type === 'action') {
      if (!this.valid(c, m)) return this.err(c, 'stale_or_out_of_turn');
      if (this.owners && this.owners[m.unit] && this.owners[m.unit] !== c.entry.seat_id) return this.err(c, 'unit_not_yours');
      const category = m.kind === 'move' ? 'move' : 'attack', key = c.entry.seat_id + '|' + this.round + '|' + this.phase + '|' + category;
      if (this.byTurn.has(key)) return this.err(c, 'action_already_submitted');
      this.byTurn.add(key);
      const out = {}; ['type', 'round', 'phase', 'unit', 'kind', 'angle', 'power', 'start', 'claimed_landing', 'dirX', 'target', 'die', 'bounce'].forEach(k => { if (k in m) out[k] = m[k]; });
      out.seat_id = c.entry.seat_id; const s = this.stamp(out); this.actions[s.seq] = { team: c.entry.team };
      this.clients.forEach(x => { if (x.entry) this.to(x, s); });
      this.to(c, { type: 'action_ack', seq: s.seq, round: s.round, phase: s.phase });
      return;
    }
    if (m.type === 'judge') {
      const a = this.actions[m.ref]; if (!this.started || !a || a.team === c.entry.team) return this.err(c, 'invalid_judge');
      if (m.hit === true && !('unit' in m)) return this.err(c, 'invalid_unit');
      if ('unit' in m && this.owners && this.owners[m.unit] && this.owners[m.unit] !== c.entry.seat_id) return this.err(c, 'unit_not_yours');
      this.judged = this.judged || new Set(); const jk = m.ref + '|' + m.unit; if (this.judged.has(jk)) return this.err(c, 'duplicate_judge'); this.judged.add(jk);
      const out = {}; ['type', 'ref', 'hit', 'unit', 'damage', 'hp_after', 'statuses', 'knockback'].forEach(k => { if (k in m) out[k] = m[k]; }); out.seat_id = c.entry.seat_id; this.broadcast(out); return;
    }
    if (m.type === 'end_turn') {
      if (!this.valid(c, m)) return this.err(c, 'stale_or_out_of_turn');
      const ended = this.phase, firstOf = r => 'red';   // fixed first team (owner 2026-11-17): red opens every round
      if (ended === firstOf(this.round)) this.phase = ended === 'red' ? 'white' : 'red'; else { this.round += 1; this.phase = firstOf(this.round); }
      this.broadcast({ type: 'end_turn', round: m.round, phase: ended, next_round: this.round, next_phase: this.phase, seat_id: c.entry.seat_id }); return;
    }
    if (m.type === 'round_hash') {
      const h = this.hashes[m.round] || (this.hashes[m.round] = {}); h[c.entry.seat_id] = m.hash;
      this.broadcast({ type: 'round_hash', round: m.round, seat_id: c.entry.seat_id });
      if (new Set(Object.values(h)).size > 1) { this.outOfSync.push(m.round); this.broadcast({ type: 'out_of_sync', round: m.round }); }
      return;
    }
    this.err(c, 'unknown_type');
  }
  flush() { let n = 0; this.clients.forEach(c => { while (c.queue.length) { const raw = c.queue.shift(); n++; if (c.onmessage) c.onmessage({ data: raw }); } }); return n; }
}

// Drive both pages: deliver relay messages, run queued timers, step the real physics, until nothing is left to do.
function pump(hub, pages, maxRounds) {
  for (let i = 0; i < (maxRounds || 6000); i++) {
    let busy = hub.flush() > 0;
    pages.forEach(P => {
      const t = P.timers.splice(0).filter(x => !/^function updateStartGate/.test(String(x.fn))); if (t.length) busy = true; t.forEach(x => x.fn());   // updateStartGate polls forever (asset loading): not game work
      P.eval('hitStop = 0; updatePhysics(0.01)');
    });
    const flying = pages.some(P => P.get('projectiles').length > 0 || P.get('diceRoll') || P.eval('relayInbox.length > 0 || allUnits().some(u => u.animState !== "idle")'));   // a queued message or a throw animation that has not finished is work too (a frozen page catching up)
    if (!busy && !flying && !hub.clients.some(c => c.queue.length) && i > 20) { if (pages.every(P => !P.timers.length)) return i; }
  }
  throw new Error('pump did not settle: ' + pages.map(P => 'timers=' + P.timers.length + ' proj=' + P.get('projectiles').length + ' dice=' + !!P.get('diceRoll') + ' turn=' + P.get('turn')).join(' | ') + ' queue=' + hub.clients.map(c => c.queue.length).join(',') + ' errors=' + hub.errors + ' T=' + pages.map(P => P.timers.map(t => String(t.fn).slice(0, 120).replace(/\s+/g, ' ') + '@' + t.ms).join(';')).join(' || '));
}


function makeTrio() {
  const hub = new Hub();
  const mk = extra => loadPage({ team: 3, search: '?relay=ws://hub&team=3' + extra });
  const A = mk(''), B = mk('&room=' + hub.code), C = mk('&room=' + hub.code);
  [A, B, C].forEach(P => { P.context.WebSocket = function () { return hub.connect(); }; });
  A.eval('relayClaimCount = 1; pickedHero = "skeleton"'); B.eval('relayClaimCount = 2; relayJoinSeat = "red"; pickedHero = "wizard"'); C.eval('pickedHero = "knight"');
  A.eval('buildRoomControls()'); A.eval('document.getElementById("room-create").onclick()'); hub.flush();
  B.eval('buildRoomControls()'); pump(hub, [A, B]);
  C.eval('buildRoomControls()'); pump(hub, [A, B, C]);
  [A, B, C].forEach(P => P.eval('startMatch()'));
  pump(hub, [A, B, C]);
  for (let i = 0; i < 500; i++) [A, B, C].forEach(P => P.eval('hitStop = 0; updatePhysics(0.01)'));
  return { hub, A, B, C };
}

check('start: three seats, red split 1+2, the owners are named and every page is in a started room', () => {
  const { hub, A, B, C } = makeTrio();
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.strictEqual(hub.started, true, 'the relay started');
  assert.deepStrictEqual(hub.owners, { left_0: 'red-1', left_1: 'red-2', left_2: 'red-2', right_0: 'white-1', right_1: 'white-1', right_2: 'white-1' });
  [A, B, C].forEach((P, i) => assert.strictEqual(P.get('relayPlaying'), true, 'page ' + 'ABC'[i] + ' is playing'));
});

check('every page builds the same two teams from start.heroes (the left team is the local team in each page frame)', () => {
  const { A, B, C } = makeTrio();
  const left = P => JSON.stringify(P.eval('unitsOf("left").map(u => u.profile)')), right = P => JSON.stringify(P.eval('unitsOf("right").map(u => u.profile)'));
  assert.strictEqual(left(A), left(B), 'A and B hold the same red team: ' + left(A) + ' vs ' + left(B));
  assert.strictEqual(left(A), right(C), 'C sees red as its right team: ' + right(C));
  assert.strictEqual(right(A), left(C), 'A sees white as its right team');
});

check('turn: the seat that owns the active red unit plays, its teammate waits', () => {
  const { A, B } = makeTrio();
  assert.strictEqual(A.get('turn'), 'player', 'A owns left_0, which is active first');
  assert.strictEqual(B.get('turn'), 'busy', 'B waits for its teammate');
});

check('a throw by A: B (teammate) and C (victim) simulate it; one judge per hit unit; the relay passes the phase to white', () => {
  const { hub, A, B, C } = makeTrio();
  A.eval('executeThrow("player", 70, 54)');
  pump(hub, [A, B, C]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  const act = hub.log.find(m => m.type === 'action');
  assert.ok(act && act.unit === 'left_0' && act.seat_id === 'red-1', 'the action names the unit and seat: ' + JSON.stringify(act));
  const judges = hub.log.filter(m => m.type === 'judge');
  const byUnit = {}; judges.forEach(j => { byUnit[j.unit || 'miss'] = (byUnit[j.unit || 'miss'] || 0) + 1; });
  assert.ok(Object.values(byUnit).every(n => n === 1), 'no unit is judged twice: ' + JSON.stringify(byUnit));
  assert.strictEqual(B.get('projectiles').length, 0, 'B finished simulating');
  assert.strictEqual(hub.phase, 'white', 'the phase moved to white');
});

check('white answers, then round 2: B owns the next red unit and plays, A waits; all three pages share the round hash', () => {
  const { hub, A, B, C } = makeTrio();
  A.eval('executeThrow("player", 70, 54)'); pump(hub, [A, B, C]);
  C.eval('executeThrow("player", 70, 54)'); pump(hub, [A, B, C]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.strictEqual(hub.round, 2, 'round 2 started');
  assert.strictEqual(B.get('turn'), 'player', 'B owns left_1 and plays');
  assert.strictEqual(A.get('turn'), 'busy', 'A waits');
  assert.deepStrictEqual(hub.outOfSync, [], 'no out_of_sync: ' + hub.outOfSync);
});

check('a teammate\'s move (die) is applied on the waiting page and does not unlock it; the throw that follows still finds the same state', () => {
  const { hub, A, B, C } = makeTrio();
  A.eval('startDiceRoll("player", 1)'); A.eval('diceRoll.final = 3'); pump(hub, [A, B, C]);
  assert.strictEqual(B.eval('Math.round(unitsOf("left")[0].targetX)'), A.eval('Math.round(unitsOf("left")[0].targetX)'), 'B shows the same moved place for left_0');
  assert.strictEqual(B.get('turn'), 'busy', 'the teammate\'s move must not give B the turn');
  A.eval('executeThrow("player", 70, 54)'); pump(hub, [A, B, C]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.strictEqual(hub.phase, 'white');
});

check('a teammate\'s turn that runs out of time (end_turn without a throw) closes the turn on the waiting page too', () => {
  const { hub, A, B, C } = makeTrio();
  A.eval('turnTimer = 0.001'); pump(hub, [A, B, C]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.strictEqual(hub.phase, 'white', 'the relay moved on');
  C.eval('executeThrow("player", 60, 54)'); pump(hub, [A, B, C]);
  assert.strictEqual(hub.round, 2);
  assert.strictEqual(B.get('turn'), 'player', 'B owns the next red unit');
});

check('six rounds, the turn passes A, B, B, A, B, B: no relay error, no out_of_sync, every page holds the same hit points', () => {
  const { hub, A, B, C } = makeTrio();
  const order = [];
  for (let r = 0; r < 6 && !A.get('gameOver'); r++) {
    const mine = [A, B].filter(P => P.get('turn') === 'player');
    assert.strictEqual(mine.length, 1, 'exactly one red page owns the turn in round ' + (r + 1) + ': ' + mine.length);
    order.push(mine[0] === A ? 'A' : 'B');
    mine[0].eval('executeThrow("player", 70, 54)'); pump(hub, [A, B, C]);
    if (A.get('gameOver')) break;
    C.eval('executeThrow("player", 60, 54)'); pump(hub, [A, B, C]);
  }
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.deepStrictEqual(hub.outOfSync, [], 'out_of_sync rounds: ' + hub.outOfSync);
  assert.deepStrictEqual(order.slice(0, 6), ['A', 'B', 'B', 'A', 'B', 'B'].slice(0, order.length), 'turn order ' + order);
  const hp = (P, side) => JSON.stringify(P.eval('unitsOf("' + side + '").map(u => Math.round(u.hp * 10))'));
  assert.strictEqual(hp(A, 'left'), hp(B, 'left'), 'A and B agree on red hp');
  assert.strictEqual(hp(A, 'left'), hp(C, 'right'), 'C agrees on red hp');
  assert.strictEqual(hp(A, 'right'), hp(C, 'left'), 'A and C agree on white hp');
  assert.strictEqual(hp(B, 'right'), hp(C, 'left'), 'B and C agree on white hp');
});

// A page that is slow (its animation has not run) while the others carry on must not stall the room: the relay moves on at the speed of the fastest seats.
// Page B is frozen (never stepped) for the whole of round 1; A throws, C throws, round 2 opens with B's unit. Without ordered handling B applies A's and C's throws at once, the two flights overlap and B waits for ever.
function stepSome(hub, pages, n) { for (let i = 0; i < n; i++) { hub.flush(); pages.forEach(P => { const t = P.timers.splice(0).filter(x => !/^function updateStartGate/.test(String(x.fn))); t.forEach(x => x.fn()); P.eval('hitStop = 0; updatePhysics(0.01)'); }); } }
check('a slow page: B is frozen for round 1 while A and C play it; after B catches up it owns round 2, nothing is stuck, hashes agree', () => {
  const { hub, A, B, C } = makeTrio();
  A.eval('executeThrow("player", 70, 54)'); stepSome(hub, [A, C], 900);
  C.eval('executeThrow("player", 60, 54)'); stepSome(hub, [A, C], 900);
  assert.strictEqual(hub.round >= 2, true, 'the relay moved to round 2 without B: round ' + hub.round + ' phase ' + hub.phase);
  pump(hub, [A, B, C]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.strictEqual(B.get('roundNum'), hub.round, 'B reached the relay round (page round ' + B.get('roundNum') + ', relay round ' + hub.round + ')');
  assert.strictEqual(B.get('turn'), 'player', 'B owns left_1 and has the turn (turn ' + B.get('turn') + ', mateFlight ' + B.eval('relayMateFlight') + ', incoming ' + B.eval('relayIncoming') + ')');
  const hp = (P, side) => JSON.stringify(P.eval('unitsOf("' + side + '").map(u => Math.round(u.hp * 10))'));
  assert.strictEqual(hp(B, 'left'), hp(A, 'left'), 'B agrees with A on red hp after catching up');
  assert.strictEqual(hp(B, 'right'), hp(C, 'left'), 'B agrees with C on white hp after catching up');
  assert.deepStrictEqual(hub.outOfSync, [], 'out_of_sync: ' + hub.outOfSync);
});

// red-team R1 A1 and A2 (2026-11-24)
check('leaving a room clears the teammate flags: a flag left over must not stall the next room', () => {
  const { hub, A } = makeTrio();
  A.eval('relayMateFlight = true; relayMateOpen = true; endRelayRoom()');
  assert.strictEqual(A.eval('relayMateFlight'), false, 'relayMateFlight is false after endRelayRoom');
  assert.strictEqual(A.eval('relayMateOpen'), false, 'relayMateOpen is false after endRelayRoom');
  assert.strictEqual(A.eval('relayInbox.length'), 0);
  assert.strictEqual(A.eval('relayQueueMode'), false);
});

check('a teammate seat that left: this team forfeits on its page, the other team wins; a spectator leaving changes nothing', () => {
  const { hub, A, C } = makeTrio();
  hub.broadcast({ type: 'seat_left', seat_id: 'spectator-1', team: 'spectator', reason: 'disconnect_timeout' }); pump(hub, [A, C]);
  assert.strictEqual(A.get('gameOver'), null, 'a spectator leaving is not a result');
  hub.broadcast({ type: 'seat_left', seat_id: 'red-2', team: 'red', reason: 'disconnect_timeout' }); pump(hub, [A, C]);
  assert.strictEqual(A.get('gameOver'), 'ai', 'the page of the red teammate that stayed: red forfeits');
  assert.strictEqual(C.get('gameOver'), 'player', 'the white page: white wins');
});

console.log('test_page_relay_split: ' + passed + ' passed' + (process.exitCode ? ', FAILED' : ''));
