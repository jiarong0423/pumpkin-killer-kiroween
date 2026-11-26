#!/usr/bin/env node
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
const dockCss = fs.readFileSync(path.join(root, "css", "dock.css"), "utf8");
const tests = [];
function test(name, fn) { tests.push([name, fn]); }

function profileBlock(source) {
  const start = source.indexOf("const HERO_PROFILES = {");
  assert.ok(start >= 0, "HERO_PROFILES block is missing");
  let depth = 0, end = -1;
  for (let i = source.indexOf("{", start); i < source.length; i++) {
    if (source[i] === "{") depth++;
    if (source[i] === "}" && --depth === 0) { end = i + 1; break; }
  }
  assert.ok(end > start, "HERO_PROFILES block is not balanced");
  return source.slice(start, end);
}

function heroProfiles() {
  const context = { T: key => key };
  vm.createContext(context);
  vm.runInContext(profileBlock(page).replace("const HERO_PROFILES", "globalThis.HERO_PROFILES") + ";", context);
  return context.HERO_PROFILES;
}

test("R1: canvas text and unit HP bars use display-scale helpers", () => {
  assert.match(page, /function uiScale\(\) \{ return Math\.max\(1, 0\.55 \/ displayScale\(\)\); \}/);
  assert.match(page, /function fs\(px\) \{ return Math\.max\(px, \(typeof pictureOn === "boolean" && pictureOn \? 14 : 11\) \/ displayScale\(\)\); \}/);   // 2026-11-26: larger small text in the single picture
  assert.match(page, /function drawUiText\(/);
  assert.match(page, /ctx\.font = "bold " \+ fs\(px\) \+ "px " \+ FONT_BODY/);
  assert.match(page, /const full = 150 \* uiScale\(\);/);   // the unit bar width is 150 display units (hpBarWidthFor)
  assert.match(page, /hpBarWidth = hpBarWidthFor\(u\), hpBarHeight = 13 \* uiScale\(\)/);
  assert.match(page, /Math\.max\(1[0-6], [6-9] \/ displayScale\(\)\)/);
});

test("R1: portrait rotate cover and touch targets are declared", () => {
  assert.match(page, /@media \(max-width: 900px\) and \(orientation: portrait\) \{ #rotate-hint \{ display: flex; \} \}/);
  assert.match(page, /#rotate-hint \{ display: none; position: absolute; inset: 0;/);
  assert.match(dockCss, /@media \(hover: none\) \{[\s\S]*#top-controls \.skill-btn,[\s\S]*#top-controls #help-btn[\s\S]*width: 44px !important;[\s\S]*height: 44px !important;/);
});

test("R2: hero selector card (carousel), thumbnails, avatar, role, bars, chips and off state exist", () => {
  // Task 227 replaced the 4x2 card grid by one large card with left/right arrows and a strip of eight thumbnails (owner 2026-11-16).
  assert.match(page, /thumb\.className = "hero-thumb"/);
  assert.match(page, /assets\/avatars\/avatar_\$\{shownHero\}\.png/);   // the card shows the hero of the slot being edited
  assert.match(page, /class="role \$\{role\}"/);
  assert.match(page, /class="bar hp"/);
  assert.match(page, /class="bar atk"/);
  assert.match(page, /class="chips"/);
});

test("R2: card numbers use the evaluated HERO_PROFILES values", () => {
  const profiles = heroProfiles();
  assert.deepStrictEqual(Object.keys(profiles).sort(), ["bat", "bride", "hag", "hunchback", "knight", "reaper", "skeleton", "wizard"]);
  for (const [hero, profile] of Object.entries(profiles)) {
    assert.strictEqual(typeof profile.hp, "number", hero + " hp");
    assert.strictEqual(typeof profile.dmg, "number", hero + " dmg");
  }
  assert.match(page, /<em>\$\{hero\.hp\}<\/em>/);
  assert.match(page, /<em>\$\{hero\.dmg\}<\/em>/);
});

test("R3: drawPlate renders avatar, HP and active status chips", () => {
  assert.match(page, /function drawPlate\(side\)/);
  assert.match(page, /images\["avatar_" \+ hero\]/);
  assert.match(page, /unit\.hp \+ "\/" \+ unit\.maxHp/);
  for (const field of ["bleed", "poison", "burn", "weak", "slow", "stun"]) {
    assert.ok(new RegExp("unit\\." + field).test(page), "missing status " + field);
  }
  assert.match(page, /drawPlate\("player"\);/);
  assert.match(page, /drawPlate\("ai"\);/);
});

test("R4-R6: wind, weather notice, starter gate and floater clamp exist", () => {
  // owner 2026-11-16: no wind number and no chip; the ghost is bound to the wind direction (mirrored) and the wisps show it
  assert.doesNotMatch(page, /const windArrow = /);
  assert.match(page, /ctx\.scale\(dir, 1\);\s*\/\/ bound to the wind/);
  assert.match(page, /ttl: 2\.5, fontSize: 18/);
  assert.match(page, /function heroImagesReady\(hero\)/);
  assert.match(page, /function sceneReady\(sceneId\)/);
  assert.match(page, /function uiReady\(\)/);
  assert.match(page, /function loadRestInBackground\(\)/);
  assert.match(page, /const textX = Math\.max\(textWidth \/ 2 \+ 12, Math\.min\(CANVAS_W - textWidth \/ 2 - 12, ft\.x\)\)/);
});

let passed = 0;
for (const [name, fn] of tests) {
  try { fn(); passed++; console.log("ok   - " + name); }
  catch (error) { console.error("FAIL - " + name + "\n       " + error.message); process.exitCode = 1; }
}
console.log("test_ui_polish: " + passed + "/" + tests.length + " checks passed");
