#!/usr/bin/env node
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
const en = JSON.parse(fs.readFileSync(path.join(root, "assets", "i18n", "en.json"), "utf8"));
const zh = JSON.parse(fs.readFileSync(path.join(root, "assets", "i18n", "zh-TW.json"), "utf8"));
let passed = 0;

function check(name, fn) {
  try { fn(); passed++; console.log("ok   - " + name); }
  catch (error) { console.error("FAIL - " + name + "\n       " + error.message); process.exitCode = 1; }
}
function sourceOf(name) {
  const start = page.indexOf("function " + name + "(");
  assert.ok(start >= 0, name + " is missing");
  const brace = page.indexOf("{", start);
  let depth = 0;
  for (let i = brace; i < page.length; i++) {
    if (page[i] === "{") depth++;
    else if (page[i] === "}" && --depth === 0) return page.slice(start, i + 1);
  }
  assert.fail(name + " has unbalanced braces");
}

check("one gear button opens one settings sheet", () => {
  assert.match(page, /id="settings-btn"/);
  assert.match(page, /id="settings-sheet"[^>]*role="dialog"/);
  assert.match(sourceOf("toggleSettings"), /settings-sheet/);
  assert.match(sourceOf("toggleSettings"), /settings-backdrop/);
});

check("settings values use guarded localStorage persistence", () => {
  const read = sourceOf("readSettings"), save = sourceOf("saveSettings");
  assert.match(read, /try\s*\{/);
  assert.match(read, /localStorage\.getItem\(SETTINGS_STORAGE_KEY\)/);
  assert.match(read, /catch\s*\(_\)/);
  assert.match(save, /try\s*\{\s*localStorage\.setItem\(SETTINGS_STORAGE_KEY/);
  assert.match(save, /catch\s*\(_\)/);
});

check("effects, music, reduce motion, language, and AI level are present", () => {
  for (const id of ["sound-btn", "settings-effects-volume", "settings-music-volume", "settings-reduce-motion", "lang-btn"]) assert.ok(page.includes('id="' + id + '"'), id + " is missing");
  assert.match(page, /class="settings-ai-level"/);
  assert.match(sourceOf("applyAudioSettings"), /setVolumes\(\{ sfx:/);
  assert.match(sourceOf("applyAudioSettings"), /music: settingsState\.musicVolume/);
  assert.match(sourceOf("reduceMotionEnabled"), /settingsState\.reduceMotion/);
});

check("reduced motion gates shake, hit flashes, and particle burst size", () => {
  assert.match(sourceOf("setScreenShake"), /!reduceMotionEnabled\(\)/);
  assert.match(page, /!reduceMotionEnabled\(\) && pose\.flash > 0\.02/);
  assert.match(sourceOf("spawnParticles"), /Math\.min\(count, 6\)/);
  assert.match(sourceOf("fxEmit"), /reduceMotionEnabled\(\) \? 0\.55/);
});

check("Escape and outside taps close the sheet", () => {
  assert.match(page, /settings-backdrop"\)\.addEventListener\("click", closeSettings\)/);
  assert.match(page, /if \(e\.code === "Escape"\) \{ closeSettings\(\);/);
});

check("settings sheet uses literal i18n keys in both dictionaries", () => {
  const keys = ["settings.open", "settings.tip", "settings.title", "settings.close", "settings.effectsVolume", "settings.musicVolume", "settings.reduceMotion", "settings.language", "settings.aiLevel", "settings.on", "settings.off", "settings.chinese"];
  for (const key of keys) {
    assert.ok(page.includes(key), key + " is not literal in index.html");
    assert.strictEqual(typeof en[key], "string", key + " missing from en.json");
    assert.strictEqual(typeof zh[key], "string", key + " missing from zh-TW.json");
  }
});

check("settings sheet uses centred translucent 44 px controls and aligned 52 px rows", () => {
  assert.match(page, /#settings-sheet \{[^}]*width:clamp\(360px,58vw,640px\)[^}]*background:rgba\(20,12,38,\.78\)/);
  assert.match(page, /#settings-backdrop \{[^}]*rgba\(5,2,10,\.33\)/);
  assert.match(page, /\.settings-row \{[^}]*min-height:52px; height:52px/);
  assert.match(page, /\.settings-row button \{[^}]*height:44px; min-height:44px/);
  assert.match(page, /id="music-mute-btn"/);
  assert.match(page, /id="lang-en-btn"/);
  assert.match(page, /settings\.howToPlay/);
  assert.match(page, /settings\.restart/);
  assert.match(page, /settings\.relayNote/);
  assert.match(sourceOf("toggleSettings"), /container\.classList\.toggle\("settings-open", open\)/);
  assert.match(sourceOf("toggleSettings"), /else if \(button\) button\.focus\(\)/);
  assert.match(sourceOf("trapSettingsFocus"), /event\.code !== "Tab"/);
});

console.log("test_ui_settings: " + passed + "/7 checks passed");
