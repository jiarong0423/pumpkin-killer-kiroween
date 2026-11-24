#!/usr/bin/env node
'use strict';
// Two REAL pages (scripts/page_harness.js) play through an in-memory hub that stands in for scripts/pk_relay.py (same message shapes and the same
// turn/phase rules as docs/relay_protocol_20261115.md): create, join, ready, start, action, judge, end_turn, round_hash. No socket, no file written.
// Checks: a throw on page A shows up on page B with the same landing and hp, the judge matches, both end the round with the same round hash,
// the relay's phase and each page's turn agree, the first team is fixed (red opens every round, nobody attacks twice in a row), N = 1 local play never sends a relay message.
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
    if (m.type === 'join') { c.entry = { seat_id: 'white-1', team: m.seat, units: m.units || [], ready: false }; this.bootstrap(c, true); this.log.forEach(x => this.to(c, x)); this.broadcast(this.state()); return; }
    if (!c.entry) return this.err(c, 'join_required');
    if (m.type === 'ready') {
      if ('units' in m) c.entry.units = m.units;
      c.entry.ready = true; this.broadcast(this.state());
      const players = this.clients.filter(x => x.entry);
      if (!this.started && players.length === 2 && players.every(x => x.entry.ready)) { this.started = true; this.round = 1; this.phase = 'red'; const st = { type: 'start', seed: this.seed, scene: this.scene, first_team: 'red', round: 1, phase: 'red' };
        if (this.teamSize > 1) { const red = players.find(x => x.entry.team === 'red').entry, white = players.find(x => x.entry.team === 'white').entry, fill = u => u.concat(Array(this.teamSize - u.length).fill(null)).slice(0, this.teamSize); st.team_size = this.teamSize; st.heroes = { left: fill(red.units), right: fill(white.units) }; st.owners = {}; for (let i = 0; i < this.teamSize; i++) { st.owners['left_' + i] = red.seat_id; st.owners['right_' + i] = white.seat_id; } }
        this.broadcast(st); }
      return;
    }
    if (m.type === 'action') {
      if (!this.valid(c, m)) return this.err(c, 'stale_or_out_of_turn');
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
    const flying = pages.some(P => P.get('projectiles').length > 0 || P.get('diceRoll'));
    if (!busy && !flying && !hub.clients.some(c => c.queue.length) && i > 20) { if (pages.every(P => !P.timers.length)) return i; }
  }
  throw new Error('pump did not settle: ' + pages.map(P => 'timers=' + P.timers.length + ' proj=' + P.get('projectiles').length + ' dice=' + !!P.get('diceRoll') + ' turn=' + P.get('turn')).join(' | ') + ' queue=' + hub.clients.map(c => c.queue.length).join(',') + ' errors=' + hub.errors + ' T=' + pages.map(P => P.timers.map(t => String(t.fn).slice(0, 120).replace(/\s+/g, ' ') + '@' + t.ms).join(';')).join(' || '));
}

function makePair(heroA, heroB, n) {
  const hub = new Hub();
  n = n || 1;
  const A = loadPage({ team: n, search: '?relay=ws://hub&team=' + n });
  const B = loadPage({ team: n, search: '?relay=ws://hub&team=' + n + '&room=' + hub.code });
  [A, B].forEach(P => { P.context.WebSocket = function () { return hub.connect(); }; });
  A.eval('pickedHero = ' + JSON.stringify(heroA)); B.eval('pickedHero = ' + JSON.stringify(heroB));
  A.eval('buildRoomControls()'); A.eval('document.getElementById("room-create").onclick()');   // the Create room button
  hub.flush();
  B.eval('buildRoomControls()');   // the ?room= link auto-joins (the Join button runs the same code)
  pump(hub, [A, B]);
  [A, B].forEach(P => P.eval('startMatch()'));
  pump(hub, [A, B]);
  for (let i = 0; i < 500; i++) [A, B].forEach(P => P.eval('hitStop = 0; updatePhysics(0.01)'));   // the units glide to their seeded start places (a few seconds in the game)
  return { hub, A, B };
}
const landing = P => { const h = P.get('historyTrajectories'); return h.length ? h[h.length - 1] : null; };
// aim at the other unit: the power that lands nearest to it (page's own flight function and wind)
function aimedPower(P) {
  return P.eval(`(() => { let best = 60, bd = 1e9; const u = player, sx = u.x + 58, sy = u.y - 110;
    for (let pw = 30; pw <= 100; pw += 0.5) { const r = relayFlightLanding(sx, sy, pw, 54, 1); const d = Math.abs(r.x - ai.x); if (d < bd) { bd = d; best = pw; } } return best; })()`);
}

check('the relay says the other seat left (seat grace over): the remaining page wins, a spectator leaving changes nothing', () => {
  const { hub, A, B } = makePair('skeleton', 'wizard');
  hub.broadcast({ type: 'seat_left', seat_id: 'spectator-1', team: 'spectator', reason: 'disconnect_timeout' }); pump(hub, [A, B]);
  assert.strictEqual(A.get('gameOver'), null, 'a spectator leaving is not a result');
  hub.broadcast({ type: 'seat_left', seat_id: 'white-1', team: 'white', reason: 'disconnect_timeout' }); pump(hub, [A, B]);
  assert.strictEqual(A.get('gameOver'), 'player', 'red stays: red wins');
  assert.strictEqual(B.get('gameOver'), null, 'the page of the seat that left is not told it won');
});

check('create, join, ready, start: both pages are in a started room, red opens, white waits; the opponent hero and the seed come through', () => {
  const { hub, A, B } = makePair('skeleton', 'wizard');
  assert.strictEqual(hub.started, true);
  assert.deepStrictEqual(hub.errors, []);
  assert.strictEqual(A.get('relayPlaying'), true); assert.strictEqual(B.get('relayPlaying'), true);
  assert.strictEqual(A.get('matchSeed'), 123456789); assert.strictEqual(B.get('matchSeed'), 123456789);
  assert.strictEqual(A.get('turn'), 'player'); assert.strictEqual(B.get('turn'), 'busy');
  assert.strictEqual(A.get('aiClass'), 'wizard'); assert.strictEqual(B.get('aiClass'), 'skeleton');
  assert.strictEqual(A.eval('ai.maxHp'), B.eval('player.maxHp')); assert.strictEqual(B.eval('ai.maxHp'), A.eval('player.maxHp'));
  assert.strictEqual(A.eval('Math.round(player.targetX)'), 1920 - B.eval('Math.round(ai.targetX)'), 'start places mirror');
  assert.strictEqual(A.eval('seats.right'), 'human');
});

check('a throw on page A: page B simulates it from the numbers, same landing (mirrored), same hp, the judge agrees, the relay turn passes to B', () => {
  const { hub, A, B } = makePair('skeleton', 'skeleton');
  const power = aimedPower(A);
  A.eval('executeThrow("player", ' + power + ', 54)');   // exactly what the release frame of the human swing calls
  pump(hub, [A, B]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  const la = landing(A), lb = landing(B);
  assert.ok(la && lb, 'both pages recorded a landing');
  assert.ok(Math.abs(la.landingX - (1920 - lb.landingX)) < 1, 'landing x ' + la.landingX + ' vs mirrored ' + (1920 - lb.landingX));
  assert.strictEqual(la.hitType, lb.hitType);
  assert.strictEqual(A.eval('Math.round(ai.hp * 10)'), B.eval('Math.round(player.hp * 10)'), 'victim hp equal on both pages');
  assert.ok(B.eval('player.hp') < B.eval('player.maxHp'), 'the aimed throw really hit (hp ' + B.eval('player.hp') + ')');
  const judge = hub.log.find(m => m.type === 'judge');
  assert.ok(judge && judge.hit === true && judge.hp_after === Math.round(B.eval('player.hp') * 10) / 10, 'judge from the victim page: ' + JSON.stringify(judge));
  const act = hub.log.find(m => m.type === 'action');
  assert.ok(act.claimed_landing && typeof act.claimed_landing.x === 'number' && typeof act.claimed_landing.y === 'number', 'claimed landing sent');
  assert.deepStrictEqual([hub.round, hub.phase], [1, 'white'], 'relay phase moved to white');
  assert.strictEqual(B.get('turn'), 'player', 'page B has the turn'); assert.strictEqual(A.get('turn'), 'busy');
  assert.strictEqual(A.get('relayClient').state().status === 'out_of_sync', false);
});

check('a full round: both throw, one round hash each, equal; round 2 starts with red again (fixed opener), no relay error', () => {
  const { hub, A, B } = makePair('skeleton', 'bat');
  A.eval('executeThrow("player", ' + aimedPower(A) + ', 54)'); pump(hub, [A, B]);
  B.eval('executeThrow("player", ' + aimedPower(B) + ', 54)'); pump(hub, [A, B]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.deepStrictEqual(Object.keys(hub.hashes[1]).sort(), ['red-1', 'white-1'], 'both pages sent the hash of round 1');
  assert.strictEqual(hub.hashes[1]['red-1'], hub.hashes[1]['white-1'], 'same round hash: ' + JSON.stringify(hub.hashes[1]));
  assert.deepStrictEqual(hub.outOfSync, []);
  assert.deepStrictEqual([hub.round, hub.phase], [2, 'red'], 'round 2: red opens again');
  assert.strictEqual(A.get('roundNum'), 2); assert.strictEqual(B.get('roundNum'), 2);
  assert.strictEqual(A.get('turn'), 'player'); assert.strictEqual(B.get('turn'), 'busy');
  assert.strictEqual(A.eval('Math.round(player.hp * 10)'), B.eval('Math.round(ai.hp * 10)')); assert.strictEqual(A.eval('Math.round(ai.hp * 10)'), B.eval('Math.round(player.hp * 10)'));
  assert.strictEqual(A.eval('wind'), -B.eval('wind'), 'the round wind comes from the seed, mirrored');
});

check('round 2 and 3: red opens every round and white follows (nobody throws twice in a row); hashes keep matching; a move (die) is applied on the other page', () => {
  const { hub, A, B } = makePair('skeleton', 'skeleton');
  A.eval('executeThrow("player", ' + aimedPower(A) + ', 54)'); pump(hub, [A, B]);
  B.eval('executeThrow("player", ' + aimedPower(B) + ', 54)'); pump(hub, [A, B]);
  // round 2: red opens again. Red moves first (die 3, forward), then throws.
  A.eval('startDiceRoll("player", 1)'); A.eval('diceRoll.final = 3'); pump(hub, [A, B]);
  const ax = A.eval('Math.round(player.targetX)'), bx = B.eval('Math.round(ai.targetX)');
  assert.strictEqual(bx, 1920 - ax, 'the move arrived: target x mirrored (' + bx + ' vs ' + ax + ')');
  A.eval('executeThrow("player", ' + aimedPower(A) + ', 54)'); pump(hub, [A, B]);
  assert.deepStrictEqual([hub.round, hub.phase], [2, 'white'], 'white is the second mover of round 2');
  assert.strictEqual(B.get('turn'), 'player');
  B.eval('executeThrow("player", ' + aimedPower(B) + ', 54)'); pump(hub, [A, B]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.deepStrictEqual([hub.round, hub.phase], [3, 'red'], 'round 3: red opens again');
  assert.strictEqual(hub.hashes[2]['red-1'], hub.hashes[2]['white-1'], 'round 2 hash equal');
  assert.deepStrictEqual(hub.outOfSync, []);
  assert.strictEqual(A.get('turn'), 'player'); assert.strictEqual(B.get('turn'), 'busy');
});


check('a turn that runs out of time passes the turn through end_turn on both pages; a timeout of the second mover ends the round', () => {
  const { hub, A, B } = makePair('skeleton', 'skeleton');
  A.eval('turnTimer = 0.001'); pump(hub, [A, B]);   // red times out: no throw, only end_turn
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  assert.deepStrictEqual([hub.round, hub.phase], [1, 'white']);
  assert.strictEqual(B.get('turn'), 'player'); assert.strictEqual(A.get('turn'), 'busy');
  B.eval('turnTimer = 0.001'); pump(hub, [A, B]);   // white (second mover) times out: the round ends, round 2 opens with red again
  assert.deepStrictEqual([hub.round, hub.phase], [2, 'red']);
  assert.strictEqual(A.get('roundNum'), 2); assert.strictEqual(B.get('roundNum'), 2);
  assert.strictEqual(A.get('turn'), 'player'); assert.strictEqual(B.get('turn'), 'busy');
  assert.strictEqual(hub.hashes[1]['red-1'], hub.hashes[1]['white-1']);
  assert.deepStrictEqual(hub.outOfSync, []);
});

check('a turn clock that runs out while the own throw is still in the air does not pass the turn a second time (stun and shock leave 3 s, a flight lasts longer)', () => {
  const { hub, A, B } = makePair('skeleton', 'skeleton');
  A.eval('turnTimer = 0.05');   // almost nothing left at the moment of the throw
  A.eval('executeThrow("player", ' + aimedPower(A) + ', 54)'); pump(hub, [A, B]);
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  const ends = hub.log.filter(m => m.type === 'end_turn' && m.round === 1 && m.phase === 'red');
  assert.strictEqual(ends.length, 1, 'red ended its turn once, not ' + ends.length + ' times');
  assert.deepStrictEqual([hub.round, hub.phase], [1, 'white']);
});

check('every hero pair, five rounds each with moves and ultimates: no relay error, never a hash difference, same winner on both pages', () => {
  const H = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];
  const pairs = []; H.forEach((a, i) => { pairs.push([a, a]); pairs.push([a, H[(i + 1) % 8]]); });
  pairs.forEach(([a, b]) => {
    const { hub, A, B } = makePair(a, b);
    for (let r = 0; r < 5 && !A.get('gameOver') && !B.get('gameOver'); r++) for (let k = 0; k < 2 && !A.get('gameOver') && !B.get('gameOver'); k++) {
      const P = [A, B].find(x => x.get('turn') === 'player'), Q = [A, B].find(x => x !== P);
      assert.ok(P, a + ' vs ' + b + ': somebody has the turn (round ' + r + ')');
      if ((r === 1 || r === 3) && !['knight', 'reaper'].includes(P.get('currentHero'))) { P.eval('energy.player = 3; ultUsed.player = 0; ultArmed.player = true'); Q.eval('energy.ai = 3; ultUsed.ai = 0'); }
      if (r === 2) { P.eval('startDiceRoll("player", ' + (k ? 1 : -1) + ')'); pump(hub, [A, B]); }
      P.eval('executeThrow("player", ' + (aimedPower(P) + (r * 3 + k * 5) % 7 - 3) + ', 54)'); pump(hub, [A, B]);
    }
    assert.deepStrictEqual(hub.errors, [], a + ' vs ' + b + ' relay errors');
    assert.deepStrictEqual(hub.outOfSync, [], a + ' vs ' + b + ' out of sync in rounds ' + hub.outOfSync);
    const ga = A.get('gameOver'), gb = B.get('gameOver');
    assert.strictEqual(ga === null, gb === null, a + ' vs ' + b + ': both pages agree whether the match is over');
    if (ga) assert.strictEqual(ga === 'player', gb === 'ai', 'same winner');
  });
});

check('2 v 2 over the hub: team size and heroes arrive, units rotate in step, ids on the wire are unit ids, the team round hash matches on both pages', () => {
  const { hub, A, B } = makePair('skeleton', 'wizard', 2);
  assert.deepStrictEqual(hub.errors, []);
  assert.strictEqual(A.get('relayPlaying'), true); assert.strictEqual(B.get('relayPlaying'), true);
  assert.strictEqual(A.get('aiClass'), 'wizard'); assert.strictEqual(B.get('aiClass'), 'skeleton');
  for (let k = 0; k < 4; k++) {
    const P = [A, B].find(x => x.get('turn') === 'player'); assert.ok(P, 'turn ' + k);
    P.eval('executeThrow("player", ' + aimedPower(P) + ', 54)'); pump(hub, [A, B]);
  }
  assert.deepStrictEqual(hub.errors, [], 'relay errors: ' + hub.errors);
  const acts = hub.log.filter(m => m.type === 'action');
  assert.deepStrictEqual(acts.map(m => m.unit), ['left_0', 'right_0', 'left_1', 'right_1'], 'wire unit ids in world frame, each team rotates after its throw, red opens every round: ' + acts.map(m => m.unit));
  assert.deepStrictEqual([hub.round, hub.phase], [3, 'red']);
  assert.strictEqual(hub.hashes[1]['red-1'], hub.hashes[1]['white-1'], 'round 1 team hash: ' + JSON.stringify(hub.hashes[1]));
  assert.strictEqual(hub.hashes[2]['red-1'], hub.hashes[2]['white-1'], 'round 2 team hash');
  assert.deepStrictEqual(hub.outOfSync, []);
  ['left', 'right'].forEach(side => assert.deepStrictEqual(A.units(side).map(u => Math.round(u.hp * 10)), B.units(side === 'left' ? 'right' : 'left').map(u => Math.round(u.hp * 10)), 'unit hp equal (' + side + ')'));
});

check('one page against the computer never touches the relay: no relay message, the old coin and order', () => {
  const P = loadPage({ team: 1 });
  assert.strictEqual(P.eval('relayLive()'), false);
  P.eval('firstOpener = "player"; roundNum = 1'); P.clearWeather(); P.eval('resolveRound()');
  assert.strictEqual(P.get('turn'), 'player', 'N = 1 local: the left side opens round 2');
  assert.strictEqual(P.eval('relayClient'), null);
});
console.log('test_page_relay_pair: ' + passed + ' checks passed');
