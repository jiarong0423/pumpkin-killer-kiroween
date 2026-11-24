#!/usr/bin/env node
'use strict';
// Red-team H1 R1-B8 / R1-B9: pins for decisions of 2026-11-18 that had none. Source-level (the page is one file): the weapon throw-sound table, the weapon draw scale is DRAW ONLY (never in the hit radius or the
// weapon sizes), the supply crate is 112 world px, the heal glow exists and is drawn, the fence draw uses its measured visible-width table.
const assert = require('assert'), fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
let n = 0; const ok = (name, fn) => { fn(); n++; };
ok('THROW_SOUND table', () => assert.match(html, /const THROW_SOUND = \{ proj_spear: "throw_spear", proj_shuriken: "throw_shuriken", proj_dart: "throw_shuriken", proj_dagger: "throw_shuriken", cannonball: "throw_cannon", proj_shield: "throw_shield", proj_pumpkin: "throw_bomb", proj_flame: "throw_flame", proj_soundwave: "throw_soundwave", proj_axe: "throw_axe", proj_cross: "throw_cross" \};/));
ok('bomb and rocket stay separate events', () => { assert.notStrictEqual(html.match(/proj_pumpkin: "(\w+)"/)[1], html.match(/cannonball: "(\w+)"/)[1]); });
ok('WEAPON_DRAW_SCALE is draw only', () => {
  const uses = html.split('\n').map((l, i) => [i + 1, l]).filter(([, l]) => /WEAPON_DRAW_SCALE/.test(l));
  assert.strictEqual(uses.length, 2, 'only the definition and the ctx.scale call: ' + uses.map(u => u[0]).join(','));
  assert.match(uses[0][1], /const WEAPON_DRAW_SCALE = 1\.35;/); assert.match(uses[1][1], /ctx\.scale\(WEAPON_DRAW_SCALE, WEAPON_DRAW_SCALE\)/);
  const radius = html.match(/function projHitRadius\(p\) \{[^\n]*\}/)[0]; assert.ok(!/DRAW_SCALE/.test(radius), 'hit radius does not use the draw scale');
});
ok('crate is 112 world px', () => assert.match(html, /crateSize = Math\.max\(112, 40 \/ ds\)/));
ok('heal glow exists and is drawn', () => { assert.match(html, /function drawHealGlows\(\) \{/); assert.match(html, /\n\s+drawHealGlows\(\);/); });
ok('fence states are drawn at the collision width', () => { assert.match(html, /const FENCE_VIS_FRAC = \{ fence_intact: 0\.98307, fence_damaged: 0\.99605, fence_broken: 0\.99635 \};/); assert.match(html, /dw = FENCE_W \/ FENCE_VIS_FRAC\[fenceKey\]/); });
console.log('test_h1_source_pins: ' + n + ' ok');
