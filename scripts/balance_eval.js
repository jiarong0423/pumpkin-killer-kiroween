#!/usr/bin/env node
"use strict";
// Evaluate a given set of hp/dmg multipliers on a COPY of the class table (isolation, writes nothing but a log line).
// Usage: node scripts/balance_eval.js --matches 600 --seed 21 knight:hp:0.9 knight:dmg:0.93 hunchback:hp:0.88
const fs = require("fs");
const path = require("path");
const Sim = require(path.join(__dirname, "sim_balance.js"));
const CS = require(path.join(__dirname, "..", "js", "class_stats.js"));
const args = process.argv.slice(2);
let matches = 600, seed = 21; const adj = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--matches") matches = Number(args[++i]); else if (args[i] === "--seed") seed = Number(args[++i]); else adj.push(args[i]);
}
const t = CS.cloneTable(CS.CLASSES);
for (const a of adj) {
  const m = /^([a-z]+):(hp|dmg):([0-9.]+)$/.exec(a);
  if (!m || !t[m[1]]) { console.error("bad adjustment " + a); process.exit(2); }
  const f = Number(m[3]); const o = t[m[1]];
  o[m[2]] = Math.round(o[m[2]] * f * 10) / 10;
  if (m[2] === "dmg") { o.attack = o.dmg; o.dTyp = Math.round(o.dTyp * f * 10) / 10; }
}
const r = Sim.runPairings({ table: t, matchesPerPairing: matches, seed });
const keys = CS.CLASS_KEYS, avg = {};
keys.forEach((a, i) => { let s = 0; keys.forEach((b, j) => { if (i !== j) s += r.winRates[i][j] * 100; }); avg[a] = +(s / (keys.length - 1)).toFixed(1); });
const line = "eval " + adj.join(" ") + " | avg win % " + JSON.stringify(avg) + " | rounds " + r.avgRoundsOverall.toFixed(2) + " timeouts " + r.timeouts + " | knight vs hunchback " + (r.winRates[keys.indexOf("knight")][keys.indexOf("hunchback")] * 100).toFixed(1);
fs.mkdirSync(path.join(__dirname, "..", "logs_local"), { recursive: true });
fs.appendFileSync(path.join(__dirname, "..", "logs_local", "balance_eval.log"), new Date().toISOString() + " " + line + "\n");
console.log(line);
