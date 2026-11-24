'use strict';
// Owner decisions of 2026-11-16 that must not drift: names, the eight heroes, the numbers, the seat rule, the ultimate names.
// Change one on purpose only with the owner's word, then update this file in the same commit.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const zh = JSON.parse(fs.readFileSync(path.join(root, 'assets/i18n/zh-TW.json'), 'utf8'));
const en = JSON.parse(fs.readFileSync(path.join(root, 'assets/i18n/en.json'), 'utf8'));
let passed = 0, total = 0;
function check(name, fn) { total++; try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { console.error('FAIL - ' + name + '\n       ' + e.message); process.exitCode = 1; } }

const block = html.slice(html.indexOf('const HERO_PROFILES = {'), html.indexOf('\n    };', html.indexOf('const HERO_PROFILES = {')) + 7);
const ctx = { T: k => k }; vm.createContext(ctx);
vm.runInContext(block.replace('const HERO_PROFILES', 'HERO_PROFILES'), ctx);
const H = ctx.HERO_PROFILES;

check('exactly eight heroes with the agreed hp and damage', () => {
  const want = { skeleton: [150, 24], wizard: [124, 36], bat: [147, 29], knight: [198, 21], reaper: [143, 22], bride: [149, 40], hunchback: [157, 19], hag: [158, 24] };   // 2026-11-18 owner roles: tank +7 percent hp (knight 185 -> 198, hunchback 147 -> 157), glass cannon +10 percent attack (wizard 33 -> 36, bride 36 -> 40), balanced +7 percent attack (skeleton 22 -> 24, reaper 21 -> 22); bat and hag unchanged. Before:   // every hero's HP x1.5 on 2026-11-16 (owner: 'the HP is too low', matches ended in two or three rounds)
  assert.deepStrictEqual(Object.keys(H).sort(), Object.keys(want).sort());
  for (const [k, [hp, dmg]] of Object.entries(want)) { assert.strictEqual(H[k].hp, hp, k + ' hp'); assert.strictEqual(H[k].dmg, dmg, k + ' dmg'); }
});
check('hero and ultimate names as the owner chose them', () => {
  assert.strictEqual(zh['hero.knight.name'], '南瓜重裝盾衛'); assert.strictEqual(en['hero.knight.name'], 'Heavy Pumpkin Guard');
  assert.strictEqual(en['hero.bat.name'], 'Bat-cat Assassin'); assert.strictEqual(zh['hero.bat.name'], '蝙蝠刺客');
  assert.strictEqual(zh['hero.hag.name'], '銀十字修女'); assert.strictEqual(en['hero.hag.name'], 'Silver Cross Sister');
  assert.strictEqual(zh['ult.knight'], '✨ 大招：銅牆鐵壁'); assert.strictEqual(en['ult.knight'], '✨ Ultimate: Shield Wall');
  assert.strictEqual(zh['ult.shuriken'], '✨ 大招：天女散花'); assert.strictEqual(en['ult.shuriken'], '✨ Ultimate: Scattered Blossoms');
});
check('the product name carries no older game name, and the page titles are as agreed', () => {
  for (const d of [zh, en]) for (const [k, v] of Object.entries(d)) if (typeof v === 'string') assert.ok(!/貓狗|cat-and-dog|cat vs dog/i.test(v), k + ' mentions the older game');
  assert.strictEqual(zh['start.title'], '🎃 南瓜殺手'); assert.strictEqual(en['start.title'], '🎃 Pumpkin Killer');
  assert.ok(!/貓狗|Cat vs Dog|cat-and-dog/i.test(html), 'index.html mentions the older game');
});
check('seat rule: at least one human, no AI against AI', () => {
  const start = html.indexOf('function seatOptionsValid(left, right)');
  assert.ok(start >= 0, 'seatOptionsValid missing');
  let depth = 0, end = -1;
  for (let i = html.indexOf('{', start); i < html.length; i++) {
    if (html[i] === '{') depth++;
    if (html[i] === '}' && --depth === 0) { end = i + 1; break; }
  }
  const fn = new Function(html.slice(start, end) + '; return seatOptionsValid;')();
  assert.strictEqual(fn('ai', 'ai'), false); assert.strictEqual(fn('human', 'ai'), true); assert.strictEqual(fn('human', 'human'), true); assert.strictEqual(fn('ai', 'human'), true); assert.strictEqual(fn('human', 'agent'), true); assert.strictEqual(fn('agent', 'ai'), false);
});
check('items are one use each per side', () => {
  assert.match(html, /double: 1, heavy: 1, heal: 1/);
});
check('normal-attack empowerments: nun 25% shock (-4 s next turn), guard 5% lifesteal on a 50% chance', () => {
  assert.match(html, /const SHOCK_CHANCE = 0\.25, SHOCK_CUT_SECONDS = 4;/);
  assert.match(html, /const LIFESTEAL_CHANCE = 0\.5, LIFESTEAL_SHARE = 0\.05;/);
  assert.ok(/proj_cross" && !p\.ultNun/.test(html) && /proj_shield" && Math\.random\(\) < LIFESTEAL_CHANCE/.test(html));
});
check('fixed AI-level noise multipliers are 2.25, 0.52 and 0.27 (2026-11-19: the owner raised the computer 5-7 percent, normal 0.75 to 0.52 and hard 0.24 to 0.17 together with the hard minimum launch angle 42, then raising MAX_POWER to 115 per owner H15 lifted hard from 0.441 to 0.516 so hard moved 0.17 -> 0.27 restoring 0.451/0.462, scripts/sweep_ai_multiplier.js and scripts/test_ai_angle_min.js; weakened 2026-11-17 to 3 / 1 / 0.45; retuned 2026-11-18 by the owner (the computer was too weak after the hit masks) to x0.75 / x0.75 / x0.53, calibrated by scripts/calibrate_page_ai.js: 0.151 / 0.314 / 0.430 hits per throw)', () => {
  assert.match(html, /const AI_LEVEL_MULTIPLIERS = Object\.freeze\(\{ easy: 2\.25, normal: 0\.52, hard: 0\.27 \}\)/);
  assert.match(html, /const skillChanceFor = side => levelFor\(side\) === "hard" \? 0\.35 : 0\.2/);
});

check('Shield Wall stays three 70 px wide, 18 px high coffin blocks for three enemy throws', () => {
  assert.match(html, /const KNIGHT_ZONE = 70, SHIELD_WALL_COFFIN_HEIGHT = 18, SHIELD_WALL_EXPIRES_AFTER_ATTACKS = 3;/);
});

check('no wind direction arrow is drawn (owner 2026-11-16: "no wind arrow"); the ghost and wisps show the direction', () => {
  assert.ok(!/direction arrow comes back/.test(html) && !/aLen \* ?|ax0 = /.test(html), 'a wind arrow was drawn again');
  assert.match(html, /no number and no chip \(owner 2026-11-16\)/);
});

check('one direction only (owner 2026-11-16: "always fixed at one angle, never reversed again"): the page never flips the world view', () => {
  assert.ok(!/translate\(\s*CANVAS_W\s*,\s*0\s*\)\s*;?\s*(ctx\.)?scale\(\s*-1\s*,\s*1\s*\)/.test(html), 'a whole-canvas mirror was added');
  assert.ok(!/canvas[^\n]{0,40}scaleX\(-1\)|#game-container[^\n]{0,80}scaleX\(-1\)/.test(html), 'the stage is mirrored by CSS');
});

console.log('test_decisions_frozen: ' + passed + '/' + total + ' checks passed');
