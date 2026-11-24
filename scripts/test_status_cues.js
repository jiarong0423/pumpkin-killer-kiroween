#!/usr/bin/env node
'use strict';
// Owner 2026-11-22: stun, slow, shock and weak (frost) had no sound and a weak look. Pins: (1) the four synthesized events exist (no file, source synth-only) and really play through the audio module,
// (2) every real application path calls its cue (head crit -> stun, shuriken -> slow, cross -> shock, javelin -> frost), exactly once per application, (3) the new drawing helpers run on a recording canvas without throwing and
// draw something, and the stun stars are no longer the emoji.
const assert = require('assert'), fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const GameAudio = require('../js/audio.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
for (const k of ['stun', 'slow', 'shock', 'frost']) {
  const e = GameAudio.DEFAULT_EVENT_MAP.events['status_' + k];
  assert.ok(e && e.file === 'assets/audio/sfx/status_' + k + '_owner.ogg' && e.source === 'owner-status-sfx-20261122' && e.synth === 'status_' + k, 'event status_' + k + ' plays the owner file and keeps its synthesized recipe as the fallback');
  assert.ok(fs.existsSync(path.join(__dirname, '..', e.file)), 'the file exists: ' + e.file);
}
assert.ok(!/ctx\.fillText\("⭐"/.test(html), 'the stun emoji is gone');
function logFor(setup) {
  const P = loadPage({ team: 1, seed: 5 }); P.reset(); P.clearWeather(); P.place('left', [300]); P.place('right', [1100]);
  P.eval('wind = 0; wallHp = 0; matchStarted = true; turn = "player"; currentHero = "skeleton"; window.__log = []; Math.random = function () { return 0.05; }; (function () { var os = snd; snd = function (n) { window.__log.push(n); return os.apply(this, arguments); }; })();');
  const foe = P.units('right')[0]; foe.hp = foe.maxHp = 300; foe.profile = 'wizard'; foe.stun = foe.stunLast = foe.slow = foe.shock = false; foe.weak = 0;
  setup(P, foe); P.run(80, 0.01);
  return { log: Array.from(P.eval('window.__log')), foe };
}
const shot = (hero, y) => (P, foe) => { P.eval('currentHero = ' + JSON.stringify(hero) + ';'); P.launch(P.projectile({ hero, team: 'player', x: foe.x - 6, y: foe.y - y, vx: 600 })); };
const frost = logFor(shot('skeleton', 100)); assert.strictEqual(frost.log.filter(n => n === 'status_frost').length, 1, 'javelin -> one frost cue: ' + frost.log); assert.ok(frost.foe.weak > 0);
const slow = logFor(shot('bat', 100)); assert.strictEqual(slow.log.filter(n => n === 'status_slow').length, 1, 'shuriken -> one slow cue: ' + slow.log); assert.ok(slow.foe.slow > 0);
const shock = logFor(shot('hag', 100)); assert.strictEqual(shock.log.filter(n => n === 'status_shock').length, 1, 'cross -> one shock cue: ' + shock.log); assert.ok(shock.foe.shock);
const stun = logFor(shot('skeleton', 180)); assert.strictEqual(stun.log.filter(n => n === 'status_stun').length, 1, 'head hit -> one stun cue: ' + stun.log); assert.ok(stun.foe.stun);
const none = logFor(shot('knight', 100)); assert.ok(!none.log.some(n => /^status_/.test(n)), 'a plain shield hit plays no status cue: ' + none.log);
// gap N9 (2026-11-23): bleed, poison and burn cues play exactly once when the status starts (not again while it is refreshed), and the bleed and burn ticks sound at each round start
for (const k of ['bleed', 'poison', 'burn']) {
  const e = GameAudio.DEFAULT_EVENT_MAP.events['status_' + k];
  assert.ok(e && e.file === null && e.source === 'synth-only' && e.synth === 'status_' + k, 'event status_' + k + ' is synthesized, no file, no licence');
}
for (const k of ['bleed', 'burn']) { const e = GameAudio.DEFAULT_EVENT_MAP.events[k + '_tick']; assert.ok(e && e.file === null && e.source === 'synth-only' && e.synth === k + '_tick', 'event ' + k + '_tick is synthesized'); }
const dotLog = (name, js) => {
  const P = loadPage({ team: 1, seed: 5 }); P.reset(); P.clearWeather(); P.place('left', [300]); P.place('right', [1100]);
  P.eval('wind = 0; wallHp = 0; matchStarted = true; window.__log = []; (function () { var os = snd; snd = function (n) { window.__log.push(n); return os.apply(this, arguments); }; })();');
  const foe = P.units('right')[0]; foe.hp = foe.maxHp = 300; foe.bleed = foe.poison = foe.burn = 0; P.context.__foe = foe;
  P.eval(js); return Array.from(P.eval('window.__log')).filter(n => n === name).length;
};
assert.strictEqual(dotLog('status_bleed', 'applyBleed(__foe, 2); applyBleed(__foe, 3);'), 1, 'bleed cue once, not again on a refresh');
assert.strictEqual(dotLog('status_poison', 'applyPoison(__foe, 2); applyPoison(__foe, 3);'), 1, 'poison cue once, not again on a refresh');
assert.strictEqual(dotLog('status_burn', 'applyBurn(__foe, 2); applyBurn(__foe, 3);'), 1, 'burn cue once, not again on a refresh');
assert.strictEqual(dotLog('bleed_tick', 'applyBleed(__foe, 2); tickBleed(__foe); tickBleed(__foe); tickBleed(__foe);'), 2, 'one bleed tick per remaining turn, none once it has run out');
assert.strictEqual(dotLog('burn_tick', 'applyBurn(__foe, 2); tickBurn(__foe); tickBurn(__foe); tickBurn(__foe);'), 2, 'one burn tick per remaining turn, none once it has run out');
assert.strictEqual(dotLog('poison_tick', 'applyPoison(__foe, 2); tickPoison(__foe); tickPoison(__foe); tickPoison(__foe);'), 2, 'the poison tick is unchanged');
// drawing helpers on a recording canvas
const P = loadPage({ team: 1, seed: 5 }); const calls = [];
const ctx = new Proxy({}, { get: (t, k) => (k in t ? t[k] : (...a) => { calls.push(String(k)); return k === 'createRadialGradient' ? { addColorStop() {} } : undefined; }), set: (t, k, v) => { t[k] = v; return true; } });
P.context.__ctx = ctx; P.eval('drawStunStar(__ctx, 10, -200, 9, 0.4, 0.9); drawShockArcs(__ctx, -112);');
assert.ok(calls.filter(c => c === 'stroke').length >= 7 && calls.includes('fill'), 'the helpers draw: ' + calls.length + ' calls');
console.log('test_status_cues: ok (frost ' + frost.log.filter(n => /status_/.test(n)).join() + ', slow, shock, stun cues once each; helpers ' + calls.length + ' canvas calls)');
