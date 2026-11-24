#!/usr/bin/env node
'use strict';
// Owner 2026-11-18: the necromancer's evil spell sound ends in an explosion, so it must play only when the flame HITS (hit trigger), never at the cast and never on a miss.
const assert = require('assert');
const { loadPage } = require('./page_harness');
function run(power) {
  const P = loadPage({ team: 1, seed: 8 });
  P.reset(); P.place('left', [300]); P.place('right', [1400]);
  P.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; currentHero = "reaper"; energy.player = 0; ultArmed.player = false; window.__log = []; snd = function (n) { window.__log.push(n); return true; };');
  P.clearWeather(); P.units('right').forEach(u => { u.hp = u.maxHp = 500; u.profile = 'wizard'; });
  P.eval('executeThrow("player", ' + power + ', 40)');
  let s = 0; while (P.get('projectiles').length && s < 900) { P.eval('hitStop = 0; updatePhysics(1/60)'); s++; }
  return { log: Array.from(P.eval('window.__log')), hp: P.units('right')[0].hp };
}
const hit = run(68);      // lands on the target (checked by hp below)
assert.ok(hit.hp < 500 && hit.hp > 0, 'the shot must hit non-fatally for this check: hp ' + hit.hp);
assert.strictEqual(hit.log.filter(n => n === 'impact_flame').length, 1, 'one flame hit sound on a hit: ' + hit.log.join(','));
assert.ok(!hit.log.includes('impact_unit') && !hit.log.includes('impact_unit_heavy'), 'the shared impact sound is replaced by the flame sound');
const miss = run(40);     // far short of the target
assert.strictEqual(miss.hp, 500, 'the short shot must miss');
assert.ok(!miss.log.includes('impact_flame'), 'no flame hit sound on a miss: ' + miss.log.join(','));
console.log('ok   - the flame hit sound plays on a hit only (hit: ' + hit.log.join(',') + ' | miss: ' + miss.log.join(',') + ')');
// Fatal hit check: plays KO sound, not impact_flame (owner 2026-11-19 / H16)
const P_fatal = require('./page_harness').loadPage({ team: 1, seed: 8 });
P_fatal.reset(); P_fatal.place('left', [300]); P_fatal.place('right', [1400]);
P_fatal.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; currentHero = "reaper"; energy.player = 0; ultArmed.player = false; window.__log = []; snd = function (n) { window.__log.push(n); return true; }; sfx.hit = function (n) { window.__log.push(n); };');
P_fatal.clearWeather(); P_fatal.units('right').forEach(u => { u.hp = 1; u.maxHp = 500; u.profile = 'wizard'; });
P_fatal.eval('executeThrow("player", 68, 40)');
let sf = 0; while (P_fatal.get('projectiles').length && sf < 900) { P_fatal.eval('hitStop = 0; updatePhysics(1/60)'); sf++; }
const fatalLog = Array.from(P_fatal.eval('window.__log'));
assert.strictEqual(P_fatal.units('right')[0].hp, 0, 'fatal shot must reduce target hp to 0');
assert.ok(fatalLog.includes('ko'), 'fatal hit plays ko: ' + fatalLog.join(','));
assert.ok(!fatalLog.includes('impact_flame'), 'fatal flame hit must not play impact_flame over ko: ' + fatalLog.join(','));
console.log('ok   - fatal flame hit plays ko only, not impact_flame');
// Non-final fatal hit in 2v2: team still stands, so plays impact_flame and NOT ko (arbitration 2026-11-19)
const P_team = require('./page_harness').loadPage({ team: 2, seed: 8 });
P_team.reset(); P_team.place('left', [300, 500]); P_team.place('right', [1400, 1600]);
P_team.eval('wind = 0; wallHp = 0; turn = "player"; matchStarted = true; currentHero = "reaper"; energy.player = 0; ultArmed.player = false; window.__log = []; snd = function (n) { window.__log.push(n); return true; }; sfx.hit = function (n) { window.__log.push(n); };');
P_team.clearWeather(); P_team.units('right')[0].hp = 1; P_team.units('right')[0].profile = 'wizard'; P_team.units('right')[1].hp = 200;
P_team.eval('executeThrow("player", 68, 40)');
let st = 0; while (P_team.get('projectiles').length && st < 900) { P_team.eval('hitStop = 0; updatePhysics(1/60)'); st++; }
const teamLog = Array.from(P_team.eval('window.__log'));
assert.strictEqual(P_team.units('right')[0].hp, 0, 'first target reduced to 0 hp');
assert.ok(P_team.units('right')[1].hp > 0, 'second teammate stays alive');
assert.strictEqual(teamLog.filter(n => n === 'impact_flame').length, 1, 'non-final 2v2 kill keeps impact_flame: ' + teamLog.join(','));
assert.ok(!teamLog.includes('ko'), 'non-final 2v2 kill must not play match-ending ko: ' + teamLog.join(','));
console.log('ok   - non-final 2v2 fatal flame hit plays impact_flame, not ko');
const src = require('fs').readFileSync(__dirname + '/../index.html', 'utf8');
assert.ok(!/ultCastFx\(u, "reaper"\);\s*snd\("impact_flame"\)/.test(src), 'the cast must not play the hit sound');
console.log('ok   - the cast does not play it');
console.log('test_hit_sound: 4 ok, 0 failed');
