#!/usr/bin/env node
"use strict";
// JS side of the team tuning contract: constants equal shared/team_tuning.json, results equal shared/team_tuning_vectors.json (the Python twin is tested by scripts/test_team_tuning.py).
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const T = require(path.join(__dirname, "..", "js", "team_tuning.js"));
const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "shared", "team_tuning.json"), "utf8"));
const vec = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "shared", "team_tuning_vectors.json"), "utf8"));
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log("ok   - " + name); } catch (e) { console.error("FAIL - " + name + "\n       " + e.message); process.exitCode = 1; } }
check("constants equal shared/team_tuning.json", () => {
  assert.deepStrictEqual(T.CONSTANTS.HP_SCALE, { 2: cfg.hp_scale["2"], 3: cfg.hp_scale["3"] });
  assert.strictEqual(T.CONSTANTS.HP_FLOOR_HITS, cfg.hp_floor_hits);
  assert.strictEqual(T.CONSTANTS.RAMP_START, cfg.ramp.start_round);
  assert.strictEqual(T.CONSTANTS.RAMP_PER_ROUND, cfg.ramp.per_round);
  assert.deepStrictEqual(T.CONSTANTS.ROUND_CAP, { 1: cfg.round_cap["1"], 2: cfg.round_cap["2"], 3: cfg.round_cap["3"] });
});
check("team max hp vectors (one unit per team is untouched)", () => {
  for (const v of vec.teamMaxHp) assert.strictEqual(T.teamMaxHp(v.hp, v.dmg, v.n), v.expected, v.hero + " n=" + v.n);
  for (const v of vec.teamMaxHp.filter(x => x.n === 1)) assert.strictEqual(v.expected, v.hp);
});
check("ramp vectors", () => { for (const v of vec.ramp) assert.strictEqual(T.rampMultiplier(v.round, v.n), v.expected, "n=" + v.n + " round " + v.round); });
check("round cap vectors", () => { for (const v of vec.cap) assert.strictEqual(T.roundCap(v.n), v.expected === null ? Infinity : v.expected); });
check("cap winner: larger HP share, then more living units, then the right side", () => { for (const v of vec.capWinner) assert.strictEqual(T.capWinner(v.teams), v.expected); });
console.log("test_team_tuning: " + passed + "/5 checks passed");
