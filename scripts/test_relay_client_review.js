#!/usr/bin/env node
'use strict';
// External review (GLM-5.3, DeepSeek V4 Pro, 2026-11-26), client side, with fake sockets: (1) an error answer to the very first create/join is handled
// (a transient one reconnects, a permanent one closes); (2) a broadcast room_state during a resume does not trigger the resend early; (3) a room_state does not
// clear out_of_sync; (4) the relay's localhost origin rule is exact (checked in Python by test_room_lobby, here only the client parts).
const assert = require('assert');
const R = require('../js/relay_client.js');
let failed = 0;
function check(name, fn) { try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.error('FAIL - ' + name + '\n       ' + String(e.message).split('\n')[0]); } }
function rig() {
  const socks = [], timers = [];
  const client = R.createClient({ socketFactory: () => { const s = { readyState: 1, sent: [], send(x) { this.sent.push(JSON.parse(x)); }, close() { this.closed = true; if (this.onclose) this.onclose({}); } }; socks.push(s); return s; },
    now: () => 0, setTimeoutFn: (fn) => { timers.push(fn); return timers.length; } });
  const open = s => s.onopen && s.onopen();
  const say = (s, m) => s.onmessage({ data: JSON.stringify(m) });
  return { client, socks, timers, open, say };
}
check('a transient error answer to the first join reconnects', () => {
  const r = rig(); r.client.join('ABC234', 'white'); r.open(r.socks[0]);
  r.say(r.socks[0], { type: 'error', code: 'server_busy' });
  assert.strictEqual(r.client.state().status, 'reconnecting');
});
check('a permanent error answer to the first create closes the client', () => {
  const r = rig(); r.client.createRoom({}); r.open(r.socks[0]);
  r.say(r.socks[0], { type: 'error', code: 'invalid_scene' });
  assert.strictEqual(r.client.state().status, 'closed');
});
check('a room_state does not clear out_of_sync', () => {
  const r = rig(); r.client.join('ABC234', 'white'); r.open(r.socks[0]);
  r.say(r.socks[0], { type: 'room_state', seat: 'white', seat_id: 'white-1', seat_token: 't', last_seq: 0, started: true, seed: 5, round: 1, phase: 'red' });
  r.say(r.socks[0], { type: 'out_of_sync', round: 1, seq: 1 });
  r.say(r.socks[0], { type: 'room_state', seats: [], started: true, seed: 5 });
  assert.strictEqual(r.client.state().status, 'out_of_sync');
});
check('a broadcast room_state during a resume does not resend before the replay', () => {
  const r = rig(); r.client.join('ABC234', 'white'); r.open(r.socks[0]);
  r.say(r.socks[0], { type: 'room_state', seat: 'white', seat_id: 'white-1', seat_token: 't', last_seq: 0, started: true, seed: 5, round: 1, phase: 'white' });
  r.client.endTurn(1, 'white');
  r.socks[0].close();
  r.timers.splice(0).forEach(fn => fn());
  const s2 = r.socks[1]; r.open(s2);
  const before = s2.sent.length;
  r.say(s2, { type: 'room_state', seats: [], started: true, seed: 5 });   // a broadcast that overtakes the resume answer
  assert.strictEqual(s2.sent.filter(m => m.type === 'end_turn').length, 0, 'no resend yet: ' + JSON.stringify(s2.sent.slice(before)));
});
console.log('test_relay_client_review: ' + (failed ? failed + ' FAILED' : 'OK'));
process.exitCode = failed ? 1 : 0;
