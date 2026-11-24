#!/usr/bin/env node
"use strict";

// Static guards for the visible-viewport layout. Browser geometry is covered by measure_phone_layout.mjs.
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
const dockCss = fs.readFileSync(path.join(root, "css", "dock.css"), "utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "manifest.webmanifest"), "utf8"));
let passed = 0;

function check(name, fn) {
  try { fn(); passed++; console.log("ok   - " + name); }
  catch (error) { console.error("FAIL - " + name + "\n       " + error.message); process.exitCode = 1; }
}

function functionSource(name) {
  const start = page.indexOf("function " + name + "(");
  assert.ok(start >= 0, name + " is missing");
  const brace = page.indexOf("{", start);
  let depth = 0;
  for (let i = brace; i < page.length; i++) {
    if (page[i] === "{") depth++;
    if (page[i] === "}" && --depth === 0) return page.slice(start, i + 1);
  }
  assert.fail(name + " is unbalanced");
}

check("stage uses dynamic viewport units rather than bare 100vh", () => {
  const stage = page.slice(page.indexOf("#game-container {"), page.indexOf("canvas {", page.indexOf("#game-container {")));
  assert.ok(!/\b100vh\b/.test(stage), "stage must not use bare 100vh");
  assert.match(page, /100dvh/);
  assert.match(stage, /--visible-viewport-height/);
});

check("visualViewport refits width, height, resize, orientation, and scroll", () => {
  assert.match(page, /function fitVisibleViewport\(\)/);
  assert.match(page, /window\.visualViewport/);
  assert.match(page, /visualViewport\.addEventListener\("resize", fitVisibleViewport/);
  assert.match(page, /visualViewport\.addEventListener\("scroll", fitVisibleViewport/);
  assert.match(page, /window\.addEventListener\("orientationchange", fitVisibleViewport/);
});

check("safe-area insets protect the stage and fixed controls", () => {
  for (const inset of ["safe-area-inset-top", "safe-area-inset-right", "safe-area-inset-bottom", "safe-area-inset-left"]) {
    assert.ok(page.includes(inset) || dockCss.includes(inset), "missing " + inset);
  }
});

check("one 44 px utility menu replaces the overlapping top-control group", () => {
  assert.match(page, /body::before/);
  assert.match(page, /--scene-backdrop/);
  assert.match(page, /function syncSceneBackdrop\(sceneId\)/);
  const match = page.match(/<div id="top-controls">([\s\S]*?)<\/div>/);
  assert.ok(match, "top-controls markup is missing");
  assert.deepStrictEqual(Array.from(match[1].matchAll(/id="([^"]+)"/g), row => row[1]), ["settings-btn"]);
  assert.match(dockCss, /#top-controls #settings-btn/);
  assert.match(dockCss, /width: 44px !important/);
});

check("phone dock uses a 52 px below-stage strip or side-margin controls", () => {
  assert.match(page, /height:52px; min-height:52px; --dock-h:52px/);
  assert.match(page, /html\.has-side-margin #bottom-dock \{ display:contents; \}/);
  assert.match(page, /html\.has-side-margin #bottom-dock \.skill-bar \{[^}]*grid-template-columns:repeat\(2,44px\)/);
  assert.match(page, /html\.has-side-margin #bottom-dock \.dock-readouts \{[^}]*grid-template-columns:96px/);
  assert.match(page, /width:min\(100%, calc\(\(var\(--visible-viewport-height\) - 52px/);
});

check("start selection is a no-scroll carousel with scene tiles", () => {
  assert.match(page, /id="hero-carousel"/);
  assert.match(page, /id="hero-prev"/);
  assert.match(page, /id="hero-next"/);
  assert.match(page, /id="hero-thumbnails"/);
  assert.match(page, /function cyclePickedHero\(step\)/);
  assert.match(page, /e\.code === "ArrowRight" \? 1 : -1/);
  assert.match(page, /#start-screen \{ position:fixed; left:50%; top:50%; width:800px; height:360px; transform:translate\(-50%,-50%\) scale\(var\(--start-fit,1\)\)/);   // one fixed 800 x 360 layout scaled as a picture
  assert.match(page, /#pick-scenes \{ grid-template-rows:repeat\(2,minmax\(44px,1fr\)\)/);
});

check("manifest requests fullscreen landscape presentation", () => {
  assert.strictEqual(manifest.display, "fullscreen");
  assert.deepStrictEqual(manifest.display_override, ["fullscreen", "standalone"]);
  assert.strictEqual(manifest.orientation, "landscape");
});

check("combat and HP labels reject invalid or unbounded numeric output", () => {
  const source = functionSource("formatCombatNumber");
  const formatCombatNumber = new Function(source + "; return formatCombatNumber;")();
  assert.strictEqual(formatCombatNumber(20), "20");
  assert.strictEqual(formatCombatNumber(20.0000000004), "20");
  assert.strictEqual(formatCombatNumber(3.3333333333), "3.3");
  assert.strictEqual(formatCombatNumber(Infinity), "0");
  assert.strictEqual(formatCombatNumber("not-a-number"), "0");
  assert.match(page, /toast\.directHit", \{ dmg: formatCombatNumber\(dmgNow\) \}/);
  assert.match(page, /const safeHeroName = truncateCanvasText\(/);
  assert.match(page, /const hpLabel = formatCombatNumber\(hp\) \+ "\/" \+ formatCombatNumber\(maxHp\)/);
});

check("canvas HUD exposes separate round/weather and countdown rectangles", () => {
  assert.match(page, /window\.__pkHud = Object\.freeze/);
  assert.match(page, /let hudText = roundText, hudText2 = ""/);   // the weather goes on a second row when one row would run under the plates
  assert.match(page, /roundWeather:/);
  assert.match(page, /countdown:/);
});

console.log("test_phone_layout: " + passed + "/9 checks passed");
