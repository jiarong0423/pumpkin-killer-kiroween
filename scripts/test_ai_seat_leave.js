#!/usr/bin/env node
'use strict';
// ROOM-FLOW R9: the host's AI filler seats never fall under the "a seat that leaves forfeits" rule. The filler says it is the host's (ai_host_token);
// when the relay reports a lost AI seat the pages go on (a teammate takes its units) or, if its team has no seat left, end the match with no result.
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
    this.errors = []; this.joins = []; this.teamSize = 1; this.code = 'ABC234'; this.scene = 'graveyard';
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
      this.joins.push(m);
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

// 3 v 3: red-1 the host (one unit), white-1 a person with the whole white team, then the host presses "fill with AI": red-2 takes left_1 and left_2.
function makeWithRedFiller() {
  const hub = new Hub();
  const mk = extra => loadPage({ team: 3, search: '?relay=ws://hub&team=3' + extra });
  const A = mk(''), C = mk('&room=' + hub.code);
  [A, C].forEach(P => { P.context.WebSocket = function () { return hub.connect(); }; });
  A.eval('relayClaimCount = 1; pickedHero = "skeleton"');
  C.eval('relayJoinSeat = "white"; pickedHero = "knight"');
  A.eval('buildRoomControls()'); A.eval('document.getElementById("room-create").onclick()'); hub.flush();
  C.eval('buildRoomControls()'); pump(hub, [A, C]);
  C.eval('startMatch()'); pump(hub, [A, C]);   // the guest has named its three heroes, so only red has open places
  A.eval('fillOpenSlotsWithAi()'); pump(hub, [A, C]);
  A.eval('startMatch()'); pump(hub, [A, C]);
  return { hub, A, C };
}

// 3 v 3: red-1 the host with the whole red team, the filler takes the whole white team.
function makeWithWhiteFiller(team) {
  const hub = new Hub();
  const A = loadPage({ team, search: '?relay=ws://hub&team=' + team });
  A.context.WebSocket = function () { return hub.connect(); };
  A.eval('pickedHero = "skeleton"');
  A.eval('buildRoomControls()'); A.eval('document.getElementById("room-create").onclick()'); hub.flush(); pump(hub, [A]);
  A.eval('fillOpenSlotsWithAi()'); pump(hub, [A]);
  A.eval('startMatch()'); pump(hub, [A]);
  return { hub, A };
}

const handover = { type: 'seat_left', seat_id: 'red-2', team: 'red', reason: 'disconnect_timeout', ai: true, team_empty: false,
  owners: { left_0: 'red-1', left_1: 'red-1', left_2: 'red-1', right_0: 'white-1', right_1: 'white-1', right_2: 'white-1' } };

check('the filler joins with the host seat token; an ordinary join carries none', () => {
  const { hub } = makeWithRedFiller();
  assert.strictEqual(JSON.stringify(hub.joins.map(j => [j.seat, j.ai_host_token || null])), JSON.stringify([['white', null], ['red', 'tok-red-1']]));
});

check('a lost AI teammate: no forfeit, the units go to the teammate on every page, each in its own frame', () => {
  const { hub, A, C } = makeWithRedFiller();
  assert.strictEqual(A.eval('relaySnap().owners.left_1'), 'red-2', 'before: the filler owns left_1');
  hub.broadcast(handover); hub.flush();
  assert.strictEqual(A.get('gameOver'), null); assert.strictEqual(C.get('gameOver'), null);
  assert.strictEqual(A.eval('relaySnap().owners.left_1'), 'red-1');
  assert.strictEqual(C.eval('relaySnap().owners.right_1'), 'red-1', 'the white page sees red as its right side');
});

check('a page that was waiting for the lost AI unit gets the turn', () => {
  const { hub, A } = makeWithRedFiller();
  A.eval('unitsOf("left")[0].hp = 0; ensureLivingActive("left"); turn = "busy"; relayMateOpen = true;');
  assert.strictEqual(A.eval('relayMyUnitActive()'), false, 'before: the active unit is the filler\'s');
  hub.broadcast(handover); hub.flush();
  assert.strictEqual(A.get('turn'), 'player'); assert.strictEqual(A.get('relayMateOpen'), false);
});

check('a page that still has the lost seat\'s messages queued does not take the turn early', () => {
  const { hub, A } = makeWithRedFiller();
  A.eval('unitsOf("left")[0].hp = 0; ensureLivingActive("left"); turn = "busy"; relayMateOpen = true; relayInbox.push({ type: "action", seq: 100000, seat_id: "red-2" });');
  hub.broadcast(handover); hub.flush();
  assert.strictEqual(A.get('turn'), 'busy'); assert.strictEqual(A.get('relayMateOpen'), true);
});

[1, 3].forEach(team => check('the whole AI team is lost (' + team + ' v ' + team + '): the match ends with no result', () => {
  const { hub, A } = makeWithWhiteFiller(team);
  hub.broadcast({ type: 'seat_left', seat_id: 'white-1', team: 'white', reason: 'disconnect_timeout', ai: true, team_empty: true, owners: {} });
  pump(hub, [A]);
  assert.strictEqual(A.get('gameOver'), 'none'); assert.strictEqual(A.get('turn'), 'over');
  assert.strictEqual(A.eval('resultTextKey()'), 'gameover.noContest');
}));

check('the three new lines exist in both languages', () => {
  ['en', 'zh-TW'].forEach(lang => {
    const table = require('../assets/i18n/' + lang + '.json');
    ['relay.aiTakenOver', 'relay.aiLeft', 'gameover.noContest'].forEach(k => assert.ok(typeof table[k] === 'string' && table[k], lang + ' ' + k));
  });
});

console.log('test_ai_seat_leave: ' + passed + ' passed' + (process.exitCode ? ', FAILED' : ''));
