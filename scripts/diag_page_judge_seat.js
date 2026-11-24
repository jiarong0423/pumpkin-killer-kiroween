#!/usr/bin/env node
'use strict';
// DIAGNOSTIC COPY of page_judge_seat.js with the round-hash probe (gap N10); do not use outside scripts/diag_judge_relay_desync.py.
// The page as the judge of an MCP agent's seat (scripts/mcp_stdio_server.py PageJudgeRelay): the REAL index.html in the Node vm of scripts/page_harness.js, joined to a relay
// room over a real WebSocket like any other page seat. The page simulates every throw (its own and the opponent's), judges its own units, hashes the round and ends turns by its own
// rules, so the agent's side agrees with the opposing page by construction. The agent decides only the shots: it sends them here and reads the state back.
//
//   node scripts/page_judge_seat.js --relay ws://127.0.0.1:8765 --code ABC234 --team red --heroes skeleton,wizard,bat [--rng N] [--speed 1] [--gap-ms 130]
// stdin  (one JSON object per line): {"cmd":"throw","angle":54,"power":61.5} | {"cmd":"pass"} | {"cmd":"quit"}
// stdout (one JSON object per line): {"event":"state","state":{...},"records":[...]} whenever something changed (state: __hybridSeat.snapshot(), records: landed throws), {"event":"exit"}.
// The agent never sees this process: the bridge turns the state into the public view. No formula and no constant of the page is sent to the agent.
const readline = require('readline');
const { loadPage } = require('./page_harness');
const core = require('./hybrid_seat_core');

const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf('--' + name); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : def; };
const relay = opt('relay', ''), code = opt('code', ''), team = opt('team', 'red');
const heroes = opt('heroes', '').split(',').filter(Boolean);
const rng = Number(opt('rng', 1)), speed = Number(opt('speed', 1)), gapMs = Number(opt('gap-ms', 130));
if (!relay || !code || !heroes.length || !['red', 'white'].includes(team)) { console.error('usage: page_judge_seat.js --relay ws://host:port --code CODE --team red|white --heroes a,b,c [--rng N] [--speed S]'); process.exit(2); }
if (typeof WebSocket !== 'function') { console.error('page_judge_seat: this Node has no global WebSocket (Node 22 or newer)'); process.exit(2); }

const n = heroes.length;
const P = loadPage({ team: n, search: '?team=' + n + '&relay=' + relay, seed: rng });
P.context.Date = class extends Date {};
core.pacedSocketInstall(gapMs, WebSocket, P.context, Date.now.bind(Date), setTimeout);
P.context.__cfg = { team, heroes, level: 'normal', rngSeed: rng, speed, maxRealSeconds: 1e9, realSetTimeout: setTimeout, manual: true };
P.eval('(' + core.installSource + ')(__cfg)');
P.eval('__hybridSeat.join(' + JSON.stringify(code) + ')');
require('./diag_hash_probe').install(P, 'red-bridge-page');   // diagnostics only (gap N10): the only difference from page_judge_seat.js

let last = '';
const emit = obj => process.stdout.write(JSON.stringify(obj) + '\n');
const timer = setInterval(() => {
  try {
    const state = JSON.parse(JSON.stringify(P.eval('__hybridSeat.snapshot()')));
    const records = JSON.parse(JSON.stringify(P.eval('__hybridSeat.drain()')));
    const key = JSON.stringify(state);
    if (key !== last || records.length) { last = key; emit({ event: 'state', state, records }); }
  } catch (e) { emit({ event: 'error', message: String(e && e.message ? e.message : e) }); }
}, 50);

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', line => {
  let m; try { m = JSON.parse(line); } catch (_) { return; }
  try {
    if (m.cmd === 'throw' || m.cmd === 'ultimate') P.eval('__hybridSeat.submit(' + Number(m.angle) + ',' + Number(m.power) + ',' + (m.cmd === 'ultimate' ? 'true' : 'false') + ')');
    else if (m.cmd === 'pass') P.eval('__hybridSeat.pass()');
    else if (m.cmd === 'quit') { clearInterval(timer); emit({ event: 'exit' }); process.exit(0); }
  } catch (e) { emit({ event: 'error', message: String(e && e.message ? e.message : e) }); }
});
rl.on('close', () => { clearInterval(timer); process.exit(0); });
