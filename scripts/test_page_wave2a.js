#!/usr/bin/env node
'use strict';
// EXECUTES the wave-2a page rules of the real index.html script (no browser; scripts/page_harness.js): comeback pack (near miss, underdog, pity, cap 2.3),
// alternating opener, daily seed. Every rule is also run against a mutant of the page script and the mutant must fail.
const assert = require('assert');
const { loadPage } = require('./page_harness');
let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n       ') : e)); } }
function rule(name, scenario, mutants) {
  check(name, () => scenario(loadPage({ bigHitOff: true, team: 3 })));
  for (const [label, edits] of (mutants || [])) check(name + ' [negative: ' + label + ']', () => {
    const M = loadPage({ bigHitOff: true, team: 3, mutate: edits }); let caught = null;
    try { scenario(M); } catch (e) { caught = e; }
    assert.ok(caught instanceof assert.AssertionError, 'mutant must die with an assertion: ' + caught);
  });
}
const GY = 860;
const lost = (P, i) => { const u = P.units('right')[i]; return Math.round((u.maxHp - u.hp) * 10) / 10; };
function fresh(P) { P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1500, 1700, 1850]); P.eval('pityMisses.player = 0; pityMisses.ai = 0; throwHadHit.clear()'); }
const ground = (P, x) => { P.launch(P.projectile({ team: 'player', hero: 'skeleton', x, y: GY - 1, vx: 0, vy: 600 })); P.run(20, 0.01); };
const direct = P => { P.launch(P.projectile({ team: 'player', hero: 'skeleton', x: 1500, y: GY - 60 })); P.run(20, 0.01); };

rule('B1 near miss is OFF (owner 2026-11-18): a ground landing 60 px from the nearest enemy box edge costs no hp, but still counts as a miss for the pity charge', P => {
  fresh(P); ground(P, 1370);
  assert.ok(P.eval('Comeback.nearMissDamage(24, 60)') > 0, 'the formula is dormant, not deleted');
  assert.strictEqual(lost(P, 0), 0, 'no damage without contact'); assert.strictEqual(lost(P, 1), 0);
  assert.strictEqual(P.eval('pityMisses.player'), 1, 'a near miss is a miss for the pity counter');
  fresh(P); ground(P, 800); assert.strictEqual(lost(P, 0), 0); assert.strictEqual(P.eval('pityMisses.player'), 1);
}, [['the near miss switched on again damages the unit', [['if (!Comeback.CONSTANTS.NEAR_ENABLED) return;', 'if (false) return;']]]]);

rule('B3 pity: two misses make the next direct hit 29 x 1.8; the hit resets the counter; the strength stays hidden (no pity text)', P => {
  fresh(P); ground(P, 800); ground(P, 800);
  assert.strictEqual(P.eval('pityMisses.player'), 2);
  assert.ok(!Array.from(P.get('floatTexts')).some(f => /team\.(pity|comeback)|%/.test(f.text)), 'no strength text after misses');
  direct(P); assert.strictEqual(lost(P, 0), 52.2); assert.strictEqual(P.eval('pityMisses.player'), 0);
  direct(P); assert.strictEqual(lost(P, 0), 52.2 + 29, 'the charge is used once');
}, [['no reset after a hit', [['pityMisses[p.team] = 0; throwHadHit.add(p.throwId);', 'throwHadHit.add(p.throwId);']]]]);

rule('B2 underdog and the 2.3 cap: half hp share doubles the hit, with pity 2 the stack is capped at 2.3', P => {
  fresh(P); P.units('left').forEach(u => { u.hp = u.maxHp / 2; });
  direct(P); assert.strictEqual(lost(P, 0), 58);
  fresh(P); P.units('left').forEach(u => { u.hp = u.maxHp / 2; }); P.eval('pityMisses.player = 2');
  direct(P); assert.strictEqual(lost(P, 0), P.eval('Comeback.finalDamage(29, 0.5, 1, 2)')); assert.strictEqual(lost(P, 0), 66.7);
  assert.ok(!Array.from(P.get('floatTexts')).some(f => /team\.(pity|comeback)|%/.test(f.text)), 'owner: the comeback strength is never shown as text');
}, [['the hit ignores the underdog bonus', [['if (TEAM_N > 1) dmgNow = cbDmg(dmgNow, p);', '']]]]);

rule('one unit per team never reads the comeback pack: no near miss, no pity, plain hit', () => {
  const P = loadPage({ team: 1 }); P.reset(); P.place('left', [300]); P.place('right', [1500]);
  ground(P, 1300); assert.strictEqual(lost(P, 0), 0); assert.strictEqual(P.eval('pityMisses.player'), 0);
  P.units('left')[0].hp = 10; direct(P); assert.strictEqual(lost(P, 0), 29);
});

rule('D fixed opener (team matches, owner 2026-11-17): the coin side opens EVERY round, so nobody attacks twice in a row; who follows is routed accordingly', P => {
  P.eval('firstOpener = "player"');
  assert.deepStrictEqual([1, 2, 3, 4].map(r => P.eval('openerOfRound(' + r + ')')), ['player', 'player', 'player', 'player']);
  P.eval('firstOpener = "ai"');
  assert.deepStrictEqual([1, 2, 3, 4].map(r => P.eval('openerOfRound(' + r + ')')), ['ai', 'ai', 'ai', 'ai']);
  const queued = fn => P.timers.some(t => t.fn === P.eval(fn));
  P.reset(); P.eval('firstOpener = "ai"; roundNum = 1'); P.timers.length = 0;
  P.eval('routeAfterTurn("ai", 0)'); assert.ok(queued('beginLeftTurnMidRound'), 'the right opener is followed by the left side');
  P.timers.length = 0; P.eval('routeAfterTurn("player", 0)'); assert.ok(queued('resolveRound'), 'the second mover ends the round');
  P.eval('beginLeftTurnMidRound()'); assert.strictEqual(P.get('turn'), 'player');
  let aiStarts = 0; P.context.triggerAITurn = () => { aiStarts++; };
  P.reset(); P.eval('firstOpener = "player"; roundNum = 1'); P.clearWeather(); P.eval('resolveRound()');   // round 2: the coin side (left) opens again
  assert.strictEqual(P.get('roundNum'), 2); assert.strictEqual(P.get('turn'), 'player'); assert.strictEqual(aiStarts, 0);
  P.clearWeather(); P.eval('resolveRound()');   // round 3: still the left side
  assert.strictEqual(P.get('roundNum'), 3); assert.strictEqual(P.get('turn'), 'player'); assert.strictEqual(aiStarts, 0);
  P.reset(); P.eval('roundNum = 1; firstOpener = "ai"'); P.clearWeather(); P.eval('resolveRound()');   // round 2 with coin = right: the right side opens again
  assert.strictEqual(P.get('turn'), 'busy'); assert.strictEqual(aiStarts, 1);
  P.timers.length = 0; P.eval('routeAfterTurn("ai", 0)'); assert.ok(queued('beginLeftTurnMidRound'));
}, [['the opener alternates again', [['const openerOfRound = r => firstOpener === null ? "player" : firstOpener;', 'const openerOfRound = r => firstOpener === null ? "player" : ((r % 2 === 1) === (firstOpener === "player") ? "player" : "ai");']]]]);


const cross = (P, extra) => P.launch(P.projectile({ team: 'player', hero: 'hag', x: 1100, y: GY - 120, vx: 3000, vy: 0, extra: Object.assign({ ultThrow: true, ultNun: true }, extra || {}) }));
rule('P4 nun cross pierce (team matches): it flies through all three enemies in its way, each takes two contacts, exactly one of them is stunned', P => {
  fresh(P); P.place('right', [1500, 1600, 1700]);
  cross(P); P.run(300, 0.01);
  P.timers.slice().forEach(t => t.fn()); P.timers.length = 0;   // the second contact (380 ms) and the stun are queued timers
  const one = Math.round(P.get('HERO_PROFILES').hag.dmg * 0.575 * 10) / 10;
  [0, 1, 2].forEach(i => assert.strictEqual(lost(P, i), Math.round(one * 2 * 10) / 10, 'unit ' + i + ' lost two contacts'));
  assert.strictEqual(P.units('right').filter(u => u.stun).length, 1, 'exactly one stunned');
}, [['the cross stops at the first unit', [['if (p.nunTouched.length < NunUlt.MAX_TARGETS) { p.nunDone = false; hit = false; hitType = "miss"; }', '']]]]);
check('P4 one unit per team: the cross still stops at the unit it touched and stuns it (old rule)', () => {
  const P = loadPage({ team: 1 }); P.reset(); P.place('left', [300]); P.place('right', [1500]);
  cross(P); P.run(300, 0.01); P.timers.slice().forEach(t => t.fn());
  const u = P.units('right')[0]; const one = Math.round(P.get('HERO_PROFILES').hag.dmg * 0.575 * 10) / 10;
  assert.strictEqual(Math.round((u.maxHp - u.hp) * 10) / 10, Math.round(one * 2 * 10) / 10); assert.ok(u.stun);
});

check('D one unit per team keeps the old order whatever the coin says', () => {
  const P = loadPage({ team: 1 }); P.reset(); P.eval('firstOpener = "player"; roundNum = 1'); P.clearWeather(); P.eval('resolveRound()');
  assert.strictEqual(P.get('turn'), 'player', 'round 2 is still opened by the left side at N = 1');
});

check('P3 daily seed: dailySeedOf is the UTC yyyymmdd; startDailyMatch seeds matchSeed from it and sets the code', () => {
  const P = loadPage({ team: 1 });
  assert.strictEqual(P.eval('dailySeedOf(new Date(Date.UTC(2026, 10, 17, 23, 59)))'), 20261117);
  assert.strictEqual(P.eval('dailySeedOf(new Date(Date.UTC(2027, 0, 5, 0, 0)))'), 20270105);
  P.eval('startDailyMatch()');
  assert.strictEqual(P.get('dailyCode'), P.eval('dailySeedOf()')); assert.strictEqual(P.get('matchSeed'), P.eval('dailySeedOf() >>> 0'));
  P.eval('resetGame()'); assert.strictEqual(P.get('dailyCode'), 0, 'an ordinary match clears the code');
});
console.log('test_page_wave2a: ' + passed + ' checks passed');
