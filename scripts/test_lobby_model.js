#!/usr/bin/env node
'use strict';
// ROOM-FLOW F3/F4/F6/F7/F8/F12: the lobby's pure view model (js/lobby_model.js) from a relay room_state. 1v1, 2v2 and 3v3.
const assert = require('assert');
const L = require('../js/lobby_model.js');
let failed = 0;
function check(name, fn) { try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.error('FAIL - ' + name + '\n       ' + String(e.message).split('\n')[0]); } }
const seat = (id, extra) => Object.assign({ seat_id: id, team: id.split('-')[0], ready: false, units: [], claim: 0, ai: false, name: '', agent: false, invited_by: null }, extra);
const state = (n, seats, extra) => Object.assign({ type: 'room_state', code: 'ABC234', seats, team_size: n > 1 ? n : undefined, started: false, host_seat_id: 'red-1', allow_ai: true, allow_mcp: true, lobby: true, begin: false, invites: [] }, extra);

check('cells: seats in join order, claims, invites and free places; 2v2 host alone shows 1/4', () => {
  const v = L.view(state(2, [seat('red-1', { claim: 1, name: '房主' })]), 'red-1');
  assert.deepStrictEqual(v.teams.red.map(c => c.kind), ['seat', 'free']);
  assert.deepStrictEqual(v.teams.white.map(c => c.kind), ['free', 'free']);
  assert.deepStrictEqual([v.count.seated, v.count.total], [1, 4]);
  assert.strictEqual(v.amHost, true);
  assert.deepStrictEqual(v.free, { red: 1, white: 2 });
});
check('3v3: a seat holding two places, an agent, an open invite, an AI seat; AI not counted', () => {
  const v = L.view(state(3, [seat('red-1', { claim: 2, units: ['bat', 'hag'], ready: true }), seat('red-2', { claim: 1, agent: true, invited_by: 'white-1', name: 'Agent' }),
    seat('white-1', { claim: 1, name: '小白' }), seat('white-2', { claim: 1, ai: true, units: ['knight'], ready: true })], { invites: [{ by: 'white-1', team: 'white', expires_in: 500 }] }), 'white-1');
  assert.deepStrictEqual(v.teams.red.map(c => [c.kind, c.seatId, c.hero, c.locked]), [['seat', 'red-1', 'bat', true], ['seat', 'red-1', 'hag', true], ['seat', 'red-2', null, false]]);
  assert.deepStrictEqual(v.teams.white.map(c => c.kind), ['seat', 'seat', 'invite']);
  assert.strictEqual(v.teams.red[2].invitedByName, '小白');
  assert.deepStrictEqual([v.count.seated, v.count.total], [4, 6]);
  assert.strictEqual(v.amHost, false); assert.strictEqual(v.myInvite.team, 'white'); assert.strictEqual(v.canInvite, false);
});
check('1v1: one cell per side, the host is red', () => {
  const v = L.view(state(1, [seat('red-1'), seat('white-1', { name: 'w' })]), 'white-1');
  assert.deepStrictEqual([v.teams.red.length, v.teams.white.length, v.count.seated, v.count.total], [1, 1, 2, 2]);
  assert.deepStrictEqual(v.free, { red: 0, white: 0 }); assert.strictEqual(v.myTeam, 'white');
});
check('start button: host only; grey until full unless AI may fill; who is still missing', () => {
  const half = state(2, [seat('red-1', { claim: 2, units: ['bat', 'hag'], ready: true }), seat('white-1', { claim: 1, name: '小白' })]);
  let v = L.view(half, 'red-1');
  assert.deepStrictEqual([v.start.shown, v.start.enabled, v.start.fillsWithAi], [true, true, true]);
  v = L.view(Object.assign({}, half, { allow_ai: false }), 'red-1');
  assert.deepStrictEqual([v.start.enabled, v.start.reason], [false, 'not_full']);
  v = L.view(half, 'white-1');
  assert.deepStrictEqual([v.start.enabled, v.start.reason], [false, 'host_only']);
  assert.deepStrictEqual(L.view(Object.assign({}, half, { begin: true }), 'red-1').waiting, [{ kind: 'unlocked', name: '小白', seatId: 'white-1', ai: false }, { kind: 'free', team: 'white', n: 1 }]);
});
check('host-only controls are locked for others; refresh locks once someone else sits', () => {
  const alone = L.view(state(2, [seat('red-1', { claim: 1 })]), 'red-1');
  assert.deepStrictEqual([alone.hostOnly.locked, alone.refresh.enabled], [false, true]);
  const two = state(2, [seat('red-1', { claim: 1 }), seat('white-1', { claim: 1 })]);
  assert.strictEqual(L.view(two, 'red-1').refresh.enabled, false);
  assert.strictEqual(L.view(two, 'white-1').hostOnly.locked, true);
});
check('invite: only with agents allowed, a free place on the own team, one per player, never for an AI or agent seat', () => {
  const s = state(2, [seat('red-1', { claim: 1 }), seat('white-1', { claim: 2 })]);
  assert.strictEqual(L.view(s, 'red-1').canInvite, true);
  assert.strictEqual(L.view(s, 'white-1').canInvite, false, 'team full');
  assert.strictEqual(L.view(Object.assign({}, s, { allow_mcp: false }), 'red-1').canInvite, false);
  assert.strictEqual(L.view(Object.assign({}, s, { invites: [{ by: 'red-1', team: 'red', expires_in: 9 }] }), 'red-1').canInvite, false);
  assert.strictEqual(L.view(state(3, [seat('red-1', { claim: 1 }), seat('red-2', { claim: 1, agent: true, invited_by: 'red-1' })]), 'red-1').canInvite, false, 'one agent per player');
});
check('cell actions: take a free place of my team, change side on the other team, release my extra place', () => {
  const s = state(3, [seat('red-1', { claim: 2 }), seat('white-1', { claim: 1 })]);
  const v = L.view(s, 'red-1');
  assert.deepStrictEqual(v.teams.red.map(c => c.action), ['release', 'release', 'take']);
  assert.deepStrictEqual(v.teams.white.map(c => c.action), [null, 'switch', 'switch']);
  const one = L.view(state(3, [seat('red-1', { claim: 1 })]), 'red-1');
  assert.strictEqual(one.teams.red[0].action, null, 'the last own place is not released');
  const locked = L.view(state(3, [seat('red-1', { claim: 1, ready: true, units: ['bat'] })]), 'red-1');
  assert.strictEqual(locked.teams.red[1].action, null, 'locked: unlock first');
});
check('welcome: the host sees who came in; the guest sees the room; nothing for AI seats or own moves', () => {
  const a = state(2, [seat('red-1')]), b = state(2, [seat('red-1'), seat('white-1', { name: '小白' }), seat('white-2', { ai: true })]);
  assert.deepStrictEqual(L.welcome(a, b, 'red-1'), [{ kind: 'joined', name: '小白', seatId: 'white-1' }]);
  assert.deepStrictEqual(L.welcome(null, b, 'white-1'), [{ kind: 'self', code: 'ABC234' }]);
  const moved = state(2, [seat('white-2'), seat('white-1', { name: '小白' })]);
  assert.deepStrictEqual(L.welcome(b, moved, 'white-2'), []);
});
check('heroes: my picks avoid what my teammates named; a cycle skips taken ones', () => {
  const s = state(3, [seat('red-1', { claim: 2 }), seat('red-2', { claim: 1, units: ['bat'] })]);
  assert.deepStrictEqual(L.takenByMates(s, 'red-1'), ['bat']);
  assert.strictEqual(L.nextHero(['skeleton', 'wizard', 'bat', 'knight'], 'wizard', ['bat'], ['skeleton']), 'knight');
});
check('bad input does not throw', () => {
  [null, {}, { seats: 'x' }, state(2, null)].forEach(s => { const v = L.view(s, 'red-1'); assert.ok(v && v.teams); });
});
console.log('test_lobby_model: ' + (failed ? failed + ' FAILED' : 'OK'));
process.exitCode = failed ? 1 : 0;
