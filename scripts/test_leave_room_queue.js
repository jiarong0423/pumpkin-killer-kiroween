#!/usr/bin/env node
'use strict';
// Leaving a room with a relay message still queued must not break the next physics step (2026-11-27: the main loop threw and the picture froze).
const assert = require('assert');
const { loadPage } = require('./page_harness');
const P = loadPage({ team: 2 });
P.eval('relayClient = { state: () => ({ seat: "red" }), close() {} }; relayRoomCode = "ABC234"; relayPlaying = true; relayQueueMode = true; relayInbox.push({ type: "end_turn", seq: 9, seat_id: "white-1", round: 9, phase: "white" })');
P.eval('leaveRoomNow()');
assert.strictEqual(P.eval('relayInbox.length'), 0, 'the left room keeps no queued message');
P.eval('updatePhysics(0.016)');
P.eval('relayQueueMode = true; relayInbox.push({ type: "end_turn", seq: 10, seat_id: "white-1" })');   // a late message with no room
P.eval('updatePhysics(0.016)');
console.log('test_leave_room_queue: OK');
