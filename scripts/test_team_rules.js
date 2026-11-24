#!/usr/bin/env node
"use strict";
// Guards the team-battle rules written in docs/TEAM_RULES_20261117.md against silent regressions (static checks on index.html plus the measured hit range).
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const root = path.join(__dirname, "..");
const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log("ok   - " + name); } catch (e) { console.error("FAIL - " + name + "\n       " + e.message); process.exitCode = 1; } }
const count = (re) => (page.match(re) || []).length;

check("rule 1: player and ai are re-pointed at the active unit", () => {
  assert.match(page, /let player = \{/); assert.match(page, /let ai = \{/);
  assert.match(page, /function setActiveUnit\(side, unit\)/);
});
check("rule 3: rotation scans cyclically and skips dead units, and every ended turn rotates", () => {
  assert.match(page, /function nextLivingAfter\(side, from\)/);
  assert.match(page, /function rotateAfterTurn\(team\)/);
  assert.ok(count(/rotateAfterTurn\(/g) >= 7, "rotateAfterTurn call sites: " + count(/rotateAfterTurn\(/g));   // definition, advanceAfterAttack, timeout, player defend, AI defend, two skipped turns
});
check("rule 4: the shot hits the first living enemy unit it touches, nearest first", () => {
  assert.match(page, /const touches = \(opp\) => \{/);
  assert.match(page, /foes\.filter\(u => u\.hp > 0 && touches\(u\)\)\.sort\(\(a, b\) => Math\.abs\(p\.x - a\.x\) - Math\.abs\(p\.x - b\.x\)\)\[0\]/);
});
check("rule 5: area effects reach every living enemy unit in range", () => {
  assert.match(page, /unitsOf\(p\.team === "player" \? "right" : "left"\)\.forEach\(vic =>/);       // wizard blast
  assert.match(page, /p\.weapon === "proj_soundwave" && !p\.splashDone/);                              // wave
  assert.match(page, /unitsOf\(p\.team === "player" \? "right" : "left"\)\.forEach\(v =>/);          // bat swarm
});
check("rule 6: status ticks and animation loops cover every unit", () => {
  assert.match(page, /allUnits\(\)\.forEach\(u => \{ if \(u\.hp > 0\) \{ tickPoison\(u\); tickBleed\(u\); tickBurn\(u\); \} \}\)/);
  assert.ok(count(/allUnits\(\)\.forEach\(u => /g) >= 5);
});
check("rule 7: the match ends only when a whole team has fallen", () => {
  assert.match(page, /const teamDown = side => unitsOf\(side\)\.every\(u => u\.hp <= 0\)/);
  assert.strictEqual(count(/teamDown\(sideOfUnit\(/g), 5);   // 5 since 2026-11-19: four win checks plus the hit-sound guard `if (!teamDown(sideOfUnit(opp)))` (a fatal hit that does not end the match no longer plays the long hit sound); checked in the backwards review of 2026-11-21
  assert.ok(!/if \(opp\.hp <= 0 && !gameOver\)/.test(page), "the old single-unit win check is back");
});
check("rule 2: units not on turn stand still; every unit has its own ring colour", () => {
  assert.match(page, /\(TEAM_N > 1 && u !== unitOf\(sideOfUnit\(u\)\)\) \? 0 :/);
  assert.match(page, /const UNIT_RING_COLORS = \{ left_0: "#ffd32a"/);
});
check("a double shot keeps its thrower", () => {
  assert.match(page, /function executeThrow\(shooter, power, requestedAngle, thrower\)/);
  assert.ok(count(/executeThrow\(team, Math\.min\(MAX_POWER, power \* 1\.04\), firedAngle, unit\)|executeThrow\("ai", Math\.min\(MAX_POWER, aim\.power \* 1\.04\), aim\.angle, aiShooter\)|executeThrow\("player", Math\.min\(MAX_POWER, shot\.power \* 1\.04\), shot\.angle, leftShooter\)/g) === 3);   // the second shot of a double is capped at MAX_POWER (115) at all 3 sites (human, right AI, left AI) since 2026-11-19
});
check("a moving unit never stops within 120 px of a living teammate; reports name the nearest enemy unit", () => {
  assert.match(page, /Math\.abs\(cx - m\.targetX\) < 120/);
  assert.match(page, /function reportTarget\(p\) \{[\s\S]*foes\.reduce\(\(a, b\) => Math\.abs\(a\.x - p\.x\) <= Math\.abs\(b\.x - p\.x\) \? a : b\)/);
});
check("the measured hit range equals the formula (scripts/probe_hit_range.js)", () => {
  const r = spawnSync(process.execPath, [path.join(__dirname, "probe_hit_range.js")], { encoding: "utf8" });
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
});
console.log("test_team_rules: " + passed + "/10 checks passed");
