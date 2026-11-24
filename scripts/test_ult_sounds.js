#!/usr/bin/env node
'use strict';
// The ultimate sounds (owner 2026-11-18, pumpkin_slayer_ultimates_sfx): each role's ultimate plays its own cast sound when it is released; skeleton, wizard and bride have a separate "_hit" part (the impact) that plays only when the move lands.
const assert = require('assert');
const { loadPage } = require('./page_harness');
function fire(hero, power, angle, enemy) {
  const P = loadPage({ team: 1, seed: 9 });
  P.reset(); P.place('left', [300]); P.place('right', [enemy || 1400]);
  P.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; currentHero = ' + JSON.stringify(hero) + '; energy.player = 3; ultUsed.player = 0; ultArmed.player = true; window.__log = []; snd = function (n) { window.__log.push(n); return true; };');
  P.clearWeather(); P.units('right').forEach(u => { u.hp = u.maxHp = 500; u.profile = 'wizard'; });
  P.eval('executeThrow("player", ' + power + ', ' + angle + ')');
  let s = 0; while (P.get('projectiles').length && s < 900) { P.eval('hitStop = 0; updatePhysics(1/60)'); s++; }
  return { log: Array.from(P.eval('window.__log')), hp: P.units('right')[0].hp };
}
const count = (log, n) => log.filter(x => x === n).length;
// casts: one cast sound per ultimate
for (const [hero, power] of [['skeleton', 68], ['wizard', 69], ['bat', 69], ['reaper', 68], ['bride', 66], ['hunchback', 67], ['hag', 68]]) {
  const r = fire(hero, power, 40);
  assert.strictEqual(count(r.log, 'ult_' + hero), 1, hero + ' cast sound once: ' + r.log.join(','));
}
console.log('ok   - every thrown ultimate plays its cast sound exactly once (7 roles)');
// hit parts: only when the move lands
let r = fire('skeleton', 68, 40); assert.strictEqual(count(r.log, 'ult_skeleton_hit'), 1, 'skeleton blast once on a hit: ' + r.log.join(','));
r = fire('skeleton', 40, 40); assert.strictEqual(count(r.log, 'ult_skeleton_hit'), 0, 'no skeleton blast on a miss: ' + r.log.join(','));
r = fire('wizard', 69, 40); assert.strictEqual(count(r.log, 'ult_wizard_hit'), 1, 'wizard blast once: ' + r.log.join(','));
r = fire('wizard', 40, 40); assert.strictEqual(count(r.log, 'ult_wizard_hit'), 0, 'no wizard blast sound on a miss: ' + r.log.join(','));
r = fire('bat', 69, 40); assert.strictEqual(count(r.log, 'ult_bat_hit'), 1, 'bat ult hit once on a hit: ' + r.log.join(','));
r = fire('bat', 40, 40); assert.strictEqual(count(r.log, 'ult_bat_hit'), 0, 'no bat ult hit on a miss: ' + r.log.join(','));
r = fire('reaper', 68, 40); assert.strictEqual(count(r.log, 'ult_reaper_hit'), 1, 'reaper ult hit once on a hit: ' + r.log.join(','));
r = fire('reaper', 40, 40); assert.strictEqual(count(r.log, 'ult_reaper_hit'), 0, 'no reaper ult hit on a miss: ' + r.log.join(','));
r = fire('bride', 71, 40, 1396); assert.strictEqual(count(r.log, 'ult_bride_hit'), 1, 'bride swarm sound on a precise hit: ' + r.log.join(','));
r = fire('bride', 66, 40); assert.strictEqual(count(r.log, 'ult_bride_hit'), 1, 'the swarm sound also on a non-precise hit (any hit of the armed wave): ' + r.log.join(','));
{ const P = loadPage({ team: 1, seed: 9 }); P.reset(); P.place('left', [300]); P.place('right', [1400]); P.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; currentHero = "bride"; energy.player = 3; ultUsed.player = 0; ultArmed.player = true; window.__log = []; snd = function (n) { window.__log.push(n); return true; };'); P.clearWeather(); P.units('right')[0].hp = 10; P.eval('executeThrow("player", 66, 40)'); let s = 0; while (P.get('projectiles').length && s < 900) { P.eval('hitStop = 0; updatePhysics(1/60)'); s++; } assert.strictEqual(count(Array.from(P.eval('window.__log')), 'ult_bride_hit'), 1, 'bride ult hit plays even when initial wave contact is fatal'); }
r = fire('bride', 50, 40); assert.strictEqual(count(r.log, 'ult_bride_hit'), 0, 'no swarm sound when the wave touches nobody: ' + r.log.join(','));
r = fire('hunchback', 67, 40); assert.strictEqual(count(r.log, 'ult_hunchback_hit'), 1, 'hunchback ult hit once on a hit: ' + r.log.join(','));
r = fire('hunchback', 40, 40); assert.strictEqual(count(r.log, 'ult_hunchback_hit'), 0, 'no hunchback ult hit on a miss: ' + r.log.join(','));
r = fire('hag', 68, 40); assert.strictEqual(count(r.log, 'ult_hag_hit'), 1, 'hag ult hit once on a hit: ' + r.log.join(','));
r = fire('hag', 40, 40); assert.strictEqual(count(r.log, 'ult_hag_hit'), 0, 'no hag ult hit on a miss: ' + r.log.join(','));
console.log('ok   - the "_hit" parts play only when the move lands (all 7 thrown ultimates)');
const src = require('fs').readFileSync(__dirname + '/../index.html', 'utf8');
assert.strictEqual((src.match(/snd\("ult_knight"\)/g) || []).length, 2, 'the knight wall sound at both lock points (player and computer)');
console.log('ok   - the knight wall sound is set at both lock points');
console.log('test_ult_sounds: 3 ok, 0 failed');
