#!/usr/bin/env node
'use strict';
// Owner 2026-11-23: only the two pumpkin roles (wizard, knight) get the Kenney CC0 face glow (two small kn_halo eye halos plus one soft flicker). No other role gets a face glow from the pumpkin preset.
const assert = require('assert');
const { loadPage } = require('./page_harness');
const P = loadPage({ team: 1, seed: 5 }); P.reset();
const emitted = hero => JSON.parse(P.eval('(function(){ fxSys.clear(); faceGlow({ x: 300, y: 400 }, ' + JSON.stringify(hero) + ', 1); var ps = fxSys.particles; ps = typeof ps === "function" ? ps() : ps; return JSON.stringify(Array.prototype.map.call(ps, function (p) { return [p.shape, p.sprite || "", p.size]; })); })()'));
for (const hero of ['wizard', 'knight']) {
  const ps = emitted(hero);
  assert.strictEqual(ps.filter(p => p[0] === 'glow').length, 1, hero + ': one soft flicker');
  const halos = ps.filter(p => p[0] === 'sprite' && p[1] === 'kn_halo');
  assert.strictEqual(halos.length, 2, hero + ': two eye halos');
  assert.ok(halos.every(p => p[2] <= 11), hero + ': halos stay small (radius <= 11 after the page FX scale): ' + halos.map(p => p[2]));
  assert.ok(ps.filter(p => p[0] === 'glow').every(p => p[2] <= 16), hero + ': the flicker is smaller than the old 14 to 22 (before the page FX scale)');
}
for (const hero of ['bat', 'reaper', 'bride', 'hunchback', 'hag']) assert.strictEqual(emitted(hero).length, 0, hero + ': no face glow was added');
console.log('test_face_glow: ok (wizard and knight: 1 flicker + 2 halos, radius <= 11; five other roles unchanged)');
