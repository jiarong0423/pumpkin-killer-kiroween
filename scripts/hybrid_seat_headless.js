#!/usr/bin/env node
'use strict';
// Headless page seat of the hybrid room test: the REAL index.html in the Node vm of scripts/page_harness.js, joined to a relay room over a
// REAL WebSocket (Node's global WebSocket), playing a whole team with the page's own computer shot (scripts/hybrid_seat_core.js).
//
//   node scripts/hybrid_seat_headless.js --relay ws://127.0.0.1:8765 --code ABC234 --team red --heroes skeleton,wizard,bat --level normal --rng 7
//        [--speed 0] [--max-s 300] [--gap-ms 130] [--claim K]   (K: the seat names only its first K heroes and plays only those units; default the whole team)
// Prints one line "HYBRID_SEAT_RESULT {json}" when the match is over; exit code 0 when the match reached a winner, 1 otherwise.
// Needs a relay socket, so it cannot start in the Claude Bash sandbox: the runner (scripts/run_hybrid_room.py) starts it from the owner's terminal.
const path = require('path');
const { loadPage } = require('./page_harness');
const core = require('./hybrid_seat_core');

const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf('--' + name); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : def; };
const relay = opt('relay', ''), code = opt('code', ''), team = opt('team', 'red'), level = opt('level', 'normal');
const heroes = opt('heroes', '').split(',').filter(Boolean);
const rng = Number(opt('rng', 1)), speed = Number(opt('speed', 0)), maxS = Number(opt('max-s', 300)), gapMs = Number(opt('gap-ms', 130));
if (!relay || !code || !heroes.length || !['red', 'white'].includes(team)) { console.error('usage: hybrid_seat_headless.js --relay ws://host:port --code CODE --team red|white --heroes a,b,c [--level easy|normal|hard] [--rng N] [--speed S] [--max-s N] [--gap-ms N]'); process.exit(2); }
if (typeof WebSocket !== 'function') { console.error('hybrid_seat_headless: this Node has no global WebSocket (Node 22 or newer)'); process.exit(2); }

const n = heroes.length;
const P = loadPage({ team: n, search: '?team=' + n + '&relay=' + relay, seed: rng });
P.context.Date = class extends Date {};   // the core fakes Date.now; the sandbox must not share the host's Date
core.pacedSocketInstall(gapMs, WebSocket, P.context, Date.now.bind(Date), setTimeout);
P.context.__cfg = { team, heroes, level, rngSeed: rng, speed, maxRealSeconds: maxS, realSetTimeout: setTimeout, claim: Number(opt('claim', 0)) };
P.eval('(' + core.installSource + ')(__cfg)');
P.eval('__hybridSeat.join(' + JSON.stringify(code) + ')');

const started = Date.now();
const heartbeat = setInterval(() => { try { console.error(new Date().toISOString().slice(11, 19) + ' ' + team + ' ' + JSON.stringify(P.eval('__hybridSeat.status()'))); } catch (e) { console.error('status failed: ' + e); } }, 5000);   // progress line in the seat log
const poll = setInterval(() => {
  let result = null;
  try { result = P.get('__hybridSeatResult'); } catch (e) { result = { reason: 'exception', errors: [String(e)] }; }
  if (result || Date.now() - started > (maxS + 20) * 1000) {
    clearInterval(poll); clearInterval(heartbeat);
    if (!result) result = { reason: 'host_timeout', errors: ['host gave up'] };
    console.log('HYBRID_SEAT_RESULT ' + JSON.stringify(result));
    process.exit(result.reason === 'game_over' && !(result.errors || []).length ? 0 : 1);
  }
}, 200);
