#!/usr/bin/env node
'use strict';
// 20,000 randomised lobby schedules for the computer seats (MOBILE-RATIO-2 follow-up, 2026-11-26): runs the REAL fillOpenSlotsWithAi of a page in a vm against a MODEL of the relay on a virtual clock.
// Per trial: random message delays, some ready messages refused (another seat took the hero) or silently lost (the room was being reset). A trial passes when every computer seat ends up locked.
// Usage: node scripts/sim_filler_lock.js [trials] [seed] [page.html]. It is a model of the relay, not the relay: scripts/test_room_*.py cover the real one.
const fs = require('fs'), path = require('path'), vm = require('vm');
const TRIALS = Number(process.argv[2] || 20000), SEED = Number(process.argv[3] || 7), PAGE = process.argv[4] || path.join(__dirname, '..', 'index.html');
const html = fs.readFileSync(PAGE, 'utf8');
const from = html.indexOf('function fillOpenSlotsWithAi('), to = html.indexOf('\n    function ', from + 40);
if (from < 0 || to < 0) { console.error('sim_filler_lock: function not found'); process.exit(2); }
const source = html.slice(from, to);
function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }

function trial(n) {
  const R = rng(SEED * 100003 + n), team = 1 + Math.floor(R() * 3), pRefuse = R() * 0.5, pLose = R() * 0.25;
  let now = 0, seq = 0; const queue = [];
  const later = (fn, ms) => { const t = { at: now + ms, id: ++seq, fn, dead: false }; queue.push(t); return t; };
  const seats = [{ seat_id: 'red-1', team: 'red', units: ['skeleton'], ready: true, claim: 1 }], clients = [];
  const broadcast = () => { for (const c of clients) if (c.id) later(() => c.on && c.on({ type: 'room_state', seat_id: c.id, seats: JSON.parse(JSON.stringify(seats)), started: false }), 1 + R() * 400); };
  const RelayClient = { relaySocketUrl: v => v, createClient: () => { const c = { id: '', on: null,
    onMessage(f) { c.on = f; },
    join(code, side) { later(() => { c.id = side + '-' + (seats.length + 1); seats.push({ seat_id: c.id, team: side, units: [], ready: false, claim: 1 }); broadcast(); }, 1 + R() * 300); },
    sendReady(m) { later(() => { const s = seats.find(x => x.seat_id === c.id); if (!s) return; const x = R(); if (x < pLose) return; if (x < pLose + pRefuse) { c.on({ type: 'error', code: 'invalid_units' }); return; } s.ready = true; s.units = m.units || ['bat']; broadcast(); }, 1 + R() * 300); },
    close() {} }; clients.push(c); return c; } };
  const ctx = vm.createContext({ relayIsHost: true, relayRoomCode: 'ABC' + n, relayPlaying: false, relayFillers: [], relaySeats: seats, TEAM_N: team, HERO_PROFILES: { skeleton: 1, wizard: 1, bat: 1, reaper: 1, hag: 1, bride: 1, hunchback: 1, knight: 1 },
    RelayClient, relayAddress: 'ws://model', relayClient: { seatToken: () => 'host' }, slotVacancies: () => ({ red: 0, white: 0 }), refreshFillAiButton: () => {}, setRoomStatus: () => {}, T: k => k, updateStartGate: () => {}, WebSocket: function () {}, setTimeout: (f, ms) => later(f, ms || 0), clearTimeout: t => { if (t) t.dead = true; }, Date: { now: () => now } });
  vm.runInContext(source, ctx);
  vm.runInContext('fillOpenSlotsWithAi({ red: ' + (team - 1) + ', white: ' + team + ' })', ctx);
  const fillers = ctx.relayFillers.length;
  let resets = R() < 0.5 ? 1 : 0;   // half of the trials: a rematch resets every lock once, after the first round settled
  for (let steps = 0; steps < 4000; steps++) {
    if (!queue.length) { if (resets-- > 0) { seats.forEach(s => { if (s.seat_id !== 'red-1') { s.ready = false; s.units = []; } }); broadcast(); continue; } break; }
    queue.sort((a, b) => a.at - b.at || a.id - b.id); const t = queue.shift(); if (t.dead) continue; now = t.at; if (now > 60000) break; t.fn();
  }
  return { ok: seats.length === fillers + 1 && seats.every(s => s.ready), computers: fillers, unlocked: seats.filter(s => !s.ready).length };
}
let ok = 0, computers = 0; const bad = [];
const t0 = Date.now();
for (let n = 0; n < TRIALS; n++) { const r = trial(n); computers += r.computers; if (r.ok) ok++; else if (bad.length < 5) bad.push({ n, unlocked: r.unlocked }); }
console.log(JSON.stringify({ page: path.relative(process.cwd(), PAGE), trials: TRIALS, seed: SEED, computerSeats: computers, allLocked: ok, stuck: TRIALS - ok, stuckPercent: +(100 * (TRIALS - ok) / TRIALS).toFixed(3), firstStuck: bad, seconds: (Date.now() - t0) / 1000 }));
process.exit(ok === TRIALS ? 0 : 1);
