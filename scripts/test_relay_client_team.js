#!/usr/bin/env node
'use strict';
// Team-battle additions to the relay client (2026-11-17): team size, hero lists, unit ids. Socket-free.
const assert = require('assert');
const RelayClient = require('../js/relay_client.js');
const Perspective = require('../js/perspective.js');

function harness(perspective) {
  const raw = [];
  const socket = { sent: raw, send(text) { raw.push(text); }, close() {} };
  const client = RelayClient.createClient({ socketFactory: () => socket, now: () => 0, setTimeoutFn: () => {}, perspective: perspective });
  const sent = () => raw.map(text => JSON.parse(text));
  return { client, socket, raw, sent, receive: message => socket.onmessage({ data: JSON.stringify(message) }) };
}

// One versus one: the wire is byte-identical to relay-v0.
{
  const h = harness();
  h.client.createRoom();
  h.client.createRoom({ teamSize: 1 });
  h.client.join(' ab2cd3 ', 'white');
  h.client.sendReady();
  h.client.sendAction({ round: 1, phase: 'red', unit: 'left_0', kind: 'throw', angle: 54, power: 50 });
  h.client.sendRoundHash(1, 'aaaa');
  assert.deepStrictEqual(h.raw, [
    '{"type":"create_room","seat":"red"}',
    '{"type":"create_room","seat":"red"}',
    '{"type":"join","code":"AB2CD3","seat":"white"}',
    '{"type":"ready"}',
    '{"type":"action","round":1,"phase":"red","unit":"left_0","kind":"throw","angle":54,"power":50}',
    '{"type":"round_hash","round":1,"hash":"aaaa"}'
  ]);
  assert.strictEqual(h.client.state().teamSize, 1);
  h.receive({ type: 'start', seq: 1, seed: 5, scene: 'church', round: 1, phase: 'red' });
  assert.strictEqual(h.client.state().teamSize, 1);
  assert.strictEqual(h.client.state().heroes, null);
}

// Team options on the wire.
{
  const h = harness();
  h.client.createRoom({ teamSize: 2, units: ['skeleton', 'wizard'], scene: 'school', hostSideChoice: 'computer' });
  h.client.join('ZZ9ZZ9', 'white', { units: ['bat', 'hag'] });
  h.client.sendReady({ units: ['bat'], teamSize: 3 });
  assert.deepStrictEqual(h.sent(), [
    { type: 'create_room', seat: 'red', team_size: 2, units: ['skeleton', 'wizard'], scene: 'school', host_side_choice: 'computer' },
    { type: 'join', code: 'ZZ9ZZ9', seat: 'white', units: ['bat', 'hag'] },
    { type: 'ready', team_size: 3, units: ['bat'] }
  ]);
  [0, 4, 2.5, '2', true].forEach(bad => assert.throws(() => h.client.createRoom({ teamSize: bad }), RangeError, String(bad)));
  assert.throws(() => h.client.createRoom({ units: ['a', 'b', 'c', 'd'] }), TypeError);
  assert.throws(() => h.client.sendReady({ units: [''] }), TypeError);
}

// A team match from the right-hand seat: heroes and owners reach the page in its own frame, unit ids go out in world frame.
{
  const h = harness(Perspective.create('right'));
  h.receive({ type: 'room_state', seat: 'white', seat_id: 'white-1', seat_token: 't', seats: [], team_size: 2, started: false });
  assert.strictEqual(h.client.state().teamSize, 2);
  h.receive({
    type: 'start', seq: 1, seed: 77, scene: 'graveyard', round: 1, phase: 'red', team_size: 2,
    heroes: { left: ['skeleton', 'wizard'], right: ['bat', null] },
    owners: { left_0: 'red-1', left_1: 'red-1', right_0: 'white-1', right_1: 'white-1' }
  });
  const state = h.client.state();
  assert.strictEqual(state.teamSize, 2);
  assert.deepStrictEqual(state.heroes, { left: ['bat', null], right: ['skeleton', 'wizard'] }, 'left is the local (white) team');
  assert.deepStrictEqual(state.owners, { right_0: 'red-1', right_1: 'red-1', left_0: 'white-1', left_1: 'white-1' });
  h.client.sendAction({ round: 1, phase: 'white', unit: 'left_1', kind: 'move', die: 3, dirX: 1, result: { x: 100, y: 860 } });
  h.client.sendAction({ round: 1, phase: 'white', unit: 'left_1', kind: 'throw', angle: 54, power: 40, start: { x: 300, y: 700 }, dirX: 1 });
  const wire = h.sent();
  assert.strictEqual(wire[0].unit, 'right_1');
  assert.strictEqual(wire[0].dirX, -1);
  assert.strictEqual(wire[1].unit, 'right_1');
  assert.strictEqual(wire[1].start.x, 1620);
  assert.throws(() => h.client.sendAction({ round: 1, phase: 'white', unit: 'left_2', kind: 'throw' }), /unit must be/, 'index above the team size');
  assert.throws(() => h.client.sendAction({ round: 1, phase: 'white', unit: 'left', kind: 'throw' }), /unit must be/, 'a bare side is not a team unit');
  h.client.sendJudge({ ref: 4, hit: true, unit: 'right_0', damage: 10, hp_after: 90, statuses: [] });
  assert.strictEqual(h.sent()[2].unit, 'left_0');
  assert.throws(() => h.client.sendJudge({ ref: 4, hit: true, damage: 10 }), /unit must be/, 'a hit must name its unit');
  h.client.sendJudge({ ref: 5, hit: false });
  assert.throws(() => h.client.sendRoundHash(1, 'zz'), /8 lowercase hex/);
  h.client.sendRoundHash(1, '0123abcd');
  assert.strictEqual(h.sent().pop().hash, '0123abcd');
  // incoming action: world unit id becomes local
  let incoming;
  h.client.onMessage(message => { incoming = message; });
  h.receive({ type: 'action', seq: 2, round: 1, phase: 'red', unit: 'left_1', kind: 'throw', start: { x: 300, y: 700 }, dirX: 1 });
  assert.strictEqual(incoming.unit, 'right_1');
}

// The helper used by the page.
assert.strictEqual(RelayClient.isTeamUnitId('left_2', 3), true);
assert.strictEqual(RelayClient.isTeamUnitId('left_2', 2), false);
assert.strictEqual(RelayClient.isTeamUnitId('red_1', 3), false);
assert.strictEqual(RelayClient.isTeamUnitId('right', 1), false);
assert.strictEqual(RelayClient.MAX_TEAM_SIZE, 3);
console.log('relay client team options, hero lists and unit ids: ok');
