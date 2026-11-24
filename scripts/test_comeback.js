#!/usr/bin/env node
"use strict";
// JS side of the comeback contract: constants equal shared/comeback.json, results equal shared/comeback_vectors.json (Python twin: scripts/test_comeback.py).
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const C = require(path.join(__dirname, "..", "js", "comeback.js"));
const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "shared", "comeback.json"), "utf8"));
const vec = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "shared", "comeback_vectors.json"), "utf8"));
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log("ok   - " + name); } catch (e) { console.error("FAIL - " + name + "\n       " + e.message); process.exitCode = 1; } }
check("constants equal shared/comeback.json", () => {
  const k = C.CONSTANTS;
  assert.strictEqual(k.NEAR_ENABLED, cfg.near_miss.enabled); assert.strictEqual(k.NEAR_REACH, cfg.near_miss.reach_px); assert.strictEqual(k.NEAR_SCALE, cfg.near_miss.scale);
  assert.strictEqual(k.UNDERDOG_MAX, cfg.underdog.max_bonus); assert.strictEqual(k.UNDERDOG_FULL, cfg.underdog.full_at_deficit);
  assert.strictEqual(k.PITY_PER_MISS, cfg.pity.per_miss); assert.strictEqual(k.PITY_CAP, cfg.pity.cap); assert.strictEqual(k.MAX_TOTAL, cfg.max_total_multiplier);
});
check("near miss vectors", () => { for (const v of vec.nearMiss) assert.strictEqual(C.nearMissDamage(v.base, v.e), v.expected, JSON.stringify(v)); });
check("underdog vectors", () => { for (const v of vec.underdog) assert.strictEqual(C.underdogMultiplier(v.own, v.enemy), v.expected, JSON.stringify(v)); });
check("pity vectors", () => { for (const v of vec.pity) assert.strictEqual(C.pityBonus(v.misses), v.expected, JSON.stringify(v)); });
check("final damage and hp share vectors", () => {
  for (const v of vec.final) assert.strictEqual(C.finalDamage(v.base, v.own, v.enemy, v.misses), v.expected, JSON.stringify(v));
  for (const v of vec.share) assert.strictEqual(C.hpShare(v.units), v.expected, JSON.stringify(v));
});
console.log("test_comeback: " + passed + "/5 checks passed");
