#!/usr/bin/env node
'use strict';
// S03 (2026-11-27): a page reloaded in the middle of a lobby match resumes its old seat, learns the match already started and leaves.
// The relay replays the old match on the same socket; none of it may reach the page (before the fix: it entered the old match for 1.2 s and
// raised a false "relay judge differs").
const assert = require('assert');
const { loadPage } = require('./page_harness');

const P = loadPage({ team: 1, search: '?relay=ws://127.0.0.1:1' });
const sockets = [], warnings = [];
P.context.WebSocket = function () { const s = { readyState: 1, sent: [], send(t) { this.sent.push(JSON.parse(t)); }, close() { this.readyState = 3; } }; sockets.push(s); return s; };
P.context.console.warn = (...a) => warnings.push(a.join(' '));
P.context.sessionStorage.getItem = () => JSON.stringify({ code: 'OLD123', token: 'tok-1' });
P.eval('lobbyResumeTried = false; lobbyStart("Host", { code: "OLD123" })');
assert.strictEqual(sockets.length, 1, 'one socket opened');
const socket = sockets[0];
const deliver = message => { if (socket.onmessage) socket.onmessage({ data: JSON.stringify(message) }); };
socket.onopen();
assert.strictEqual(socket.sent[0].type, 'resume', 'the stored seat is resumed');
const seats = [{ seat_id: 'red-1', team: 'red', units: ['skeleton'] }, { seat_id: 'white-1', team: 'white', units: ['skeleton'] }];
deliver({ type: 'room_state', code: 'OLD123', seat: 'red', seat_id: 'red-1', seat_token: 'tok-1', seats, started: true, seed: 5, round: 1, phase: 'red', scene: 'graveyard', first_seq: 1, last_seq: 4 });
deliver({ type: 'start', seq: 1, seed: 5, scene: 'graveyard', round: 1, phase: 'red', first_team: 'red' });
deliver({ type: 'action', seq: 2, seat_id: 'red-1', round: 1, phase: 'red', kind: 'throw', angle: 45, power: 60, start: { x: 400, y: 750 }, dirX: 1 });
deliver({ type: 'end_turn', seq: 3, seat_id: 'red-1', round: 1, phase: 'red', next_round: 1, next_phase: 'white' });
deliver({ type: 'judge', seq: 4, seat_id: 'white-1', ref: 2, hit: true, unit: 'left_0', hp_after: 1, damage: 20 });
assert.strictEqual(P.eval('relayPlaying'), false, 'the replayed start does not put the page into the old match');
assert.strictEqual(P.eval('matchStarted'), false);
assert.ok(!warnings.some(w => /judge differs/.test(w)), 'no false out-of-sync: ' + warnings.join(' | '));
assert.ok(socket.sent.some(m => m.type === 'leave'), 'the old seat is still released at once');
console.log('test_refresh_mid_match: OK');
