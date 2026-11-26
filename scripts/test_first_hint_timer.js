#!/usr/bin/env node
'use strict';
// Red team (polish) P3, 2026-11-26: the first-turn hint pauses the turn clock only in local play; in a room the other side would wait, so the clock runs.
const assert = require('assert');
const { loadPage } = require('./page_harness');
function run(room) {
  const P = loadPage({ team: 1 });
  P.eval('resetGame(); seats = { left: "human", right: "ai", level: seats.level }; matchStarted = true; turn = "player"; turnTimer = 12; gameOver = null;');
  P.eval('document.getElementById("first-hint").hidden = false;');
  if (room) P.eval('relayPlaying = true; relayRoomCode = "ABC234"; relayClient = { state: () => ({ status: "playing", seat: "red", round: 1, phase: "red", owners: null }), close() {} };');
  for (let i = 0; i < 60; i++) P.eval('hitStop = 0; updatePhysics(1/60)');
  return { open: P.eval('firstHintOpen()'), live: P.eval('relayLive()'), timer: P.eval('turnTimer') };
}
const local = run(false), room = run(true);
assert.ok(local.open && !local.live && local.timer === 12, 'local play: the hint pauses the clock ' + JSON.stringify(local));
assert.ok(room.open && room.live && room.timer < 11.1, 'a room: the clock runs under the hint ' + JSON.stringify(room));
console.log('test_first_hint_timer: OK (local paused at 12, room ran to ' + room.timer.toFixed(2) + ')');
