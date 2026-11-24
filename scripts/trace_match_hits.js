#!/usr/bin/env node
'use strict';
// DATA ONLY, REAL MATCHES. Full computer-vs-computer matches (1, 2 and 3 units per team) are played by the real page code in the vm (scripts/page_match_driver.js); inside them EVERY physics step of EVERY projectile
// is recorded against every living enemy unit near it: shot centre, the unit where it stood when the step began, hp before / after, the weapon's hit radius, and the STATE OF THE FENCE before and after the step
// (owner 2026-11-18: "the simulations never covered the attack paths after the wall is destroyed"). Plain throws and ultimates both (plainOnly false); area effects (bride wave, wizard blast, swarm) are recorded and
// flagged so the judge can leave them out. scripts/check_hit_trace.py judges the records (use --by-wall in scripts/check_match_hits.py for the split).
// usage: node scripts/trace_match_hits.js --wall natural|down|mid --matches 40 --out logs_local/hit_trace/matches.jsonl
const fs = require('fs'), path = require('path'), vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const N = +arg('matches', 40), OUT = arg('out', 'logs_local/hit_trace/matches.jsonl'), PLAIN = process.argv.includes('--plain'), WALL = arg('wall', 'natural');   // natural | down (fence gone from tick 0, held down) | mid (fence forced down from a per-match tick 200..2400)
fs.mkdirSync(path.dirname(OUT), { recursive: true }); const fd = fs.openSync(OUT, 'w');
const HEROES = ['skeleton', 'wizard', 'bat', 'knight', 'bride', 'hunchback', 'reaper', 'hag'];
const HOOK = require('./match_hit_hook');
let recs = 0, matches = 0, brokeMatches = 0, errors = 0;
for (let size of [1, 2, 3]) for (let m = 0; m < N; m++) {
  const hero = HEROES[(m * 3 + size) % 8], seed = D.cellSeed(m, size, 5);
  const P = loadPage({ team: size });
  vm.runInContext(D.source, P.context);
  vm.runInContext(HOOK, P.context);
  const mid = matches; vm.runInContext('window.__mid = ' + mid + '; window.__wallMode = ' + JSON.stringify(WALL) + '; window.__wallAt = ' + (200 + (m * 337) % 2200), P.context);
  const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify({ hero, size, seed, plainOnly: PLAIN }) + ')', P.context)));
  errors += rec.errors.length;
  const list = vm.runInContext('window.__rec', P.context); let broke = false;
  for (const r of Array.from(list)) { if (r.w0 > 0 && r.w1 <= 0) broke = true; fs.writeSync(fd, JSON.stringify(Object.assign({}, r, { size })) + '\n'); recs++; }
  if (broke) brokeMatches++; matches++;
}
fs.closeSync(fd);
console.log(JSON.stringify({ matches, matchesWhereTheFenceWasBroken: brokeMatches, records: recs, matchErrors: errors, out: OUT }));
