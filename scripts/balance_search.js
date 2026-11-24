#!/usr/bin/env node
"use strict";
// Isolation search for the 1 v 1 class balance. It never writes a canonical file: it scales hp and dmg of each class in a COPY of the class table (the same way
// `sim_balance.js --adjust` does: dmg also moves attack and dTyp), runs the seeded pairing simulation, and keeps the change that lowers the miss of two targets:
// every class averages 45 to 55 percent against the others and every pairing sits in 40 to 60. Coordinate descent, common seed for every evaluation (fair comparison).
// Usage: node scripts/balance_search.js [--matches 120] [--sweeps 4] [--max 0.25] [--seed 5]
// Output: docs/balance_candidate_20261117.json (multipliers and the resulting table), logs_local/balance_search.log (one line per accepted step). Exit 1 if nothing improves.
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..");
const Sim = require(path.join(__dirname, "sim_balance.js"));
const CS = require(path.join(root, "js", "class_stats.js"));
const argv = process.argv.slice(2);
const opt = { matches: 120, sweeps: 4, max: 0.25, seed: 5, only: "" };
for (let i = 0; i < argv.length; i += 2) { const k = argv[i].replace(/^--/, ""); if (!(k in opt)) { console.error("unknown option " + argv[i]); process.exit(2); } opt[k] = k === "only" ? String(argv[i + 1]) : Number(argv[i + 1]); }   // --only knight,hunchback: only those classes may change
const logFile = path.join(root, "logs_local", "balance_search.log");
fs.mkdirSync(path.dirname(logFile), { recursive: true });
const log = line => fs.appendFileSync(logFile, new Date().toISOString() + " " + line + "\n");
const KEYS = CS.CLASS_KEYS.slice();
const base = CS.cloneTable(CS.CLASSES);

function build(mult) {
  const t = CS.cloneTable(base);
  for (const k of KEYS) {
    t[k].hp = Math.round(base[k].hp * mult[k].hp * 10) / 10;
    const m = mult[k].dmg;
    t[k].dmg = Math.round(base[k].dmg * m * 10) / 10; t[k].attack = t[k].dmg; t[k].dTyp = Math.round(base[k].dTyp * m * 10) / 10;
  }
  return t;
}
function score(mult, matches) {
  const r = Sim.runPairings({ table: build(mult), matchesPerPairing: matches, seed: opt.seed });
  const wr = r.winRates;
  let pair = 0, avgMiss = 0;
  const avgs = {};
  KEYS.forEach((a, i) => {
    let sum = 0;
    KEYS.forEach((b, j) => { if (i === j) return; const w = wr[i][j] * 100; sum += w; const d = Math.max(0, Math.abs(w - 50) - 10); pair += d * d; });
    avgs[a] = sum / (KEYS.length - 1);
    const dm = Math.max(0, Math.abs(avgs[a] - 50) - 5); avgMiss += dm * dm;
  });
  return { value: pair / 100 + avgMiss, avgs, rounds: r.overallAvgRounds !== undefined ? r.overallAvgRounds : null, timeouts: r.timeouts };
}
let mult = {}; KEYS.forEach(k => { mult[k] = { hp: 1, dmg: 1 }; });
let cur = score(mult, opt.matches);
log("start value " + cur.value.toFixed(1) + " avgs " + JSON.stringify(Object.fromEntries(Object.entries(cur.avgs).map(([k, v]) => [k, +v.toFixed(1)]))));
let improved = false;
for (let sweep = 0; sweep < opt.sweeps; sweep++) {
  const step = 0.08 / (1 + sweep * 0.7);
  let any = false;
  const movable = opt.only ? opt.only.split(",") : KEYS;
  for (const k of movable) for (const f of ["hp", "dmg"]) for (const dir of [-1, 1]) {
    const trial = JSON.parse(JSON.stringify(mult));
    trial[k][f] = Math.min(1 + opt.max, Math.max(1 - opt.max, trial[k][f] + dir * step));
    if (trial[k][f] === mult[k][f]) continue;
    const s = score(trial, opt.matches);
    if (s.value < cur.value - 0.5) { mult = trial; cur = s; any = improved = true; log("sweep " + sweep + " " + k + "." + f + " -> " + mult[k][f].toFixed(3) + " value " + s.value.toFixed(1)); }
  }
  if (!any) break;
}
const final = score(mult, opt.matches * 4);   // a fresh, larger check of the result
const out = { made: "2026-11-17", method: "balance_search.js coordinate descent, isolation only", matchesPerPairingSearch: opt.matches, matchesPerPairingFinal: opt.matches * 4, seed: opt.seed, limit: opt.max, multipliers: mult, resultingStats: Object.fromEntries(KEYS.map(k => [k, { hp: build(mult)[k].hp, dmg: build(mult)[k].dmg }])), averages: Object.fromEntries(Object.entries(final.avgs).map(([k, v]) => [k, +v.toFixed(1)])), finalValue: +final.value.toFixed(1), timeouts: final.timeouts };
fs.writeFileSync(path.join(root, "docs", "balance_candidate_20261117.json"), JSON.stringify(out, null, 2) + "\n");
log("done final value " + final.value.toFixed(1) + " averages " + JSON.stringify(out.averages));
console.log("balance_search: " + (improved ? "improved" : "no improvement") + " final value " + final.value.toFixed(1) + " averages " + JSON.stringify(out.averages));
process.exit(improved ? 0 : 1);
