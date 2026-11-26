#!/usr/bin/env node
'use strict';
// EXECUTES the team-battle rules of the real index.html script (no browser): see scripts/page_harness.js.
// Every rule has a positive check on the real page and a negative check: the same assertion is run against a mutant of the
// page script (the rule deliberately broken by one exact text edit) and MUST fail with an AssertionError, otherwise the test
// itself is worthless. Writes no file on success; on failure the messages go to stdout and to logs_local/test_page_team_exec.log.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { loadPage } = require('./page_harness');

const results = []; let passed = 0, failed = 0;
const t0 = Date.now();
function check(name, fn) {
  try { fn(); passed++; console.log('ok   - ' + name); results.push('ok   - ' + name); }
  catch (e) { failed++; process.exitCode = 1; const m = 'FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n       ') : e); console.error(m); results.push(m); }
}
// rule(name, scenario(P), mutations): positive on the real page, negative on each mutant (every one must make the scenario throw an AssertionError).
function rule(name, scenario, mutants) {
  check(name, () => scenario(loadPage({ bigHitOff: true, team: 3 })));
  for (const [label, edits] of (mutants || [])) {
    check(name + ' [negative: ' + label + ' must be caught]', () => {
      const M = loadPage({ bigHitOff: true, team: 3, mutate: edits });          // a missing mutation target throws here (outside assert.throws): a refactor cannot fake a pass
      let caught = null;
      try { scenario(M); } catch (e) { caught = e; }
      assert.ok(caught, 'mutant survived: the scenario passed although the rule is broken (' + label + ')');
      assert.ok(caught instanceof assert.AssertionError, 'mutant died for the wrong reason (not an assertion): ' + caught);
    });
  }
}
const near = (a, b, m) => assert.ok(Math.abs(a - b) < 1e-9, (m || 'value') + ': ' + a + ' !== ' + b);
const GY = 860;

// ---------------------------------------------------------------- the load itself
check('the real inline script and every js/*.js load in a vm; ?team=3 builds three units per side', () => {
  const P = loadPage({ bigHitOff: true, team: 3 });
  assert.strictEqual(P.eval('TEAM_N'), 3);
  assert.deepStrictEqual(P.units('left').map(u => u.id), ['left_0', 'left_1', 'left_2']);
  assert.deepStrictEqual(P.units('right').map(u => u.id), ['right_0', 'right_1', 'right_2']);
  assert.ok(P.loadedScripts.length >= 25, 'scripts loaded: ' + P.loadedScripts.length);
  assert.strictEqual(P.eval('typeof updatePhysics + typeof stepDice + typeof resolveRound'), 'functionfunctionfunction');
  assert.strictEqual(loadPage({}).eval('TEAM_N'), 1);
});

// ---------------------------------------------------------------- rule 3: rotation order, dead units skipped
rule('rotation: left_0 -> left_1 -> left_2 -> left_0, a dead unit is skipped, the pointer follows', P => {
  P.place('left', [300, 450, 600]);
  assert.strictEqual(P.activeId('left'), 'left_0');
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_1'); assert.strictEqual(P.eval('player').id, 'left_1');
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_2');
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_0');
  P.units('left')[1].hp = 0;                                               // left_1 has fallen
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_2', 'left_1 is dead: left_0 -> left_2');
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_0', 'cyclic: left_2 -> left_0');
  P.units('left')[2].hp = 0;                                               // only left_0 lives
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_0', 'one living unit keeps the turn');
  assert.strictEqual(P.eval('nextLivingAfter("right", unitOf("right"))').id, 'right_1');
  P.units('right').forEach(u => { u.hp = 0; });
  assert.strictEqual(P.eval('nextLivingAfter("right", unitOf("right"))'), null, 'a whole team down: nobody is due');
}, [['dead unit is not skipped', [['const u = units[(start + k) % units.length]; if (u.hp > 0) return u; }', 'const u = units[(start + k) % units.length]; return u; }']]]]);

rule('rotateAfterTurn: a finished turn rotates the thrower team only while the match runs', P => {
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.eval('rotateAfterTurn("player")');
  assert.strictEqual(P.activeId('left'), 'left_1'); assert.strictEqual(P.activeId('right'), 'right_0', 'the other team does not rotate');
  P.eval('rotateAfterTurn("ai")'); assert.strictEqual(P.activeId('right'), 'right_1');
  P.eval('gameOver = "player"; rotateAfterTurn("player")');
  assert.strictEqual(P.activeId('left'), 'left_1', 'after the match ended nothing rotates');
}, [['no rotation', [['{ rotateTeam(team === "player" ? "left" : "right"); ensureLivingActive(', '{ ensureLivingActive(']]]]);

// ---------------------------------------------------------------- ensureLivingActive
rule('ensureLivingActive: the unit that was due fell while the other team threw -> the next living one takes over', P => {
  P.place('left', [300, 450, 600]);
  P.units('left')[0].hp = 0;                                               // left_0 (active) is killed
  P.eval('ensureLivingActive("left")');
  assert.strictEqual(P.activeId('left'), 'left_1'); assert.strictEqual(P.eval('player').id, 'left_1'); assert.strictEqual(P.get('activeIndex').left, 1);
  P.units('left')[1].hp = 0; P.eval('ensureLivingActive("left")'); assert.strictEqual(P.activeId('left'), 'left_2');
  P.units('left')[0].hp = 77; P.eval('ensureLivingActive("left")'); assert.strictEqual(P.activeId('left'), 'left_2', 'a living active unit is left alone');
  // through the real rotateAfterTurn: the OTHER team's due unit has fallen
  P.place('right', [1300, 1450, 1600]); P.units('right')[0].hp = 0;
  P.eval('rotateAfterTurn("player")');
  assert.strictEqual(P.activeId('right'), 'right_1', 'rotateAfterTurn repairs the other team pointer');
}, [['ensureLivingActive does nothing', [['if (units.length < 2 || unitOf(side).hp > 0) return;', 'return;']]],
    ['rotateAfterTurn forgets the other team', [['ensureLivingActive(team === "player" ? "right" : "left"); }   // the other team', '}   // the other team']]]]);

// ---------------------------------------------------------------- rule 7: teamDown and the last kill sets gameOver
rule('teamDown is true only when EVERY unit is down; a kill of the last unit by a real shot sets gameOver, a kill of a non-last unit does not', P => {
  P.place('left', [300, 450, 700]); P.place('right', [1300, 1450, 1600]);
  assert.strictEqual(P.eval('teamDown("left")'), false);
  P.units('left')[0].hp = 0; P.units('left')[1].hp = 0; assert.strictEqual(P.eval('teamDown("left")'), false, 'one unit still lives');
  P.units('left')[2].hp = 0; assert.strictEqual(P.eval('teamDown("left")'), true);
  // non-last kill: the AI kills left_2 (hp 5) while left_0 lives -> the match goes on
  P.place('left', [300, 450, 700]); P.units('left')[2].hp = 5;
  P.launch(P.projectile({ team: 'ai', hero: 'skeleton', x: 700, y: GY - 60 })); P.run(5);
  assert.strictEqual(P.units('left')[2].hp, 0); assert.strictEqual(P.get('gameOver'), null, 'two teammates still live: no game over');
  // last kill: left_0 and left_1 already down, left_2 dies -> gameOver = "ai"
  P.reset(); P.place('left', [300, 450, 700]); P.units('left')[0].hp = 0; P.units('left')[1].hp = 0; P.units('left')[2].hp = 5;
  P.launch(P.projectile({ team: 'ai', hero: 'skeleton', x: 700, y: GY - 60 })); P.run(5);
  assert.strictEqual(P.units('left')[2].hp, 0); assert.strictEqual(P.get('gameOver'), 'ai'); assert.strictEqual(P.get('turn'), 'over');
}, [['teamDown uses some() instead of every()', [['const teamDown = side => unitsOf(side).every(u => u.hp <= 0);', 'const teamDown = side => unitsOf(side).some(u => u.hp <= 0);']]],
    ['the shot ends the match on the first kill (old single-unit check)', [['if (teamDown(sideOfUnit(opp)) && !gameOver) { gameOver = p.team;', 'if (opp.hp <= 0 && !gameOver) { gameOver = p.team;']]]]);

rule('after a shot lands the thrower team rotates to its next living unit (real hit loop -> advanceAfterAttack -> rotateAfterTurn)', P => {
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]); P.units('left')[1].hp = 0;   // left_1 dead: left_0 -> left_2
  P.launch(P.projectile({ team: 'player', hero: 'skeleton', x: 1300, y: GY - 60 })); P.run(5);
  assert.ok(P.units('right')[0].hp < P.units('right')[0].maxHp, 'the shot hit right_0');
  assert.strictEqual(P.activeId('left'), 'left_2', 'the thrower team rotated past the dead unit');
  assert.strictEqual(P.activeId('right'), 'right_0');
}, [['the dead unit is not skipped', [['const u = units[(start + k) % units.length]; if (u.hp > 0) return u; }', 'const u = units[(start + k) % units.length]; return u; }']]]]);

// ---------------------------------------------------------------- rule 4: the shot hits the nearest living unit it touches
rule('a shot touching two boxes hits the nearest living unit (not the first in team order); a dead unit is skipped', P => {
  P.place('right', [1330, 1300, 1700]);                                  // right_1 is nearer to x = 1305 although right_0 is first in the array
  const dmgSeen = () => P.units('right').map(u => u.maxHp - u.hp);
  P.launch(P.projectile({ team: 'player', hero: 'skeleton', x: 1305, y: GY - 60 })); P.run(5);
  let d = dmgSeen(); assert.ok(d[1] > 0, 'nearest unit (right_1) is hit'); assert.strictEqual(d[0], 0, 'the farther box is untouched'); assert.strictEqual(d[2], 0);
  P.reset(); P.place('right', [1330, 1300, 1700]); P.units('right')[1].hp = 0;   // nearest is dead: the next box takes it
  P.launch(P.projectile({ team: 'player', hero: 'skeleton', x: 1305, y: GY - 60 })); P.run(5);
  d = dmgSeen(); assert.ok(d[0] > 0, 'the dead unit is skipped, right_0 takes the hit'); assert.strictEqual(P.units('right')[1].hp, 0);
  // a flying shot crossing two boxes: left to right it meets the nearer box first
  P.reset(); P.place('right', [1300, 1330, 1700]);
  P.launch(P.projectile({ team: 'player', hero: 'skeleton', x: 1100, y: GY - 60, vx: 900, vy: 0 })); P.run(200, 0.01);
  d = dmgSeen(); assert.ok(d[0] > 0 && d[1] === 0, 'the flying shot hit the first box on its way: ' + d);
}, [['the farthest box is chosen', [['.sort((a, b) => Math.abs(p.x - a.x) - Math.abs(p.x - b.x))[0]', '.sort((a, b) => Math.abs(p.x - b.x) - Math.abs(p.x - a.x))[0]']]],
    ['dead units can be hit', [['foes.filter(u => u.hp > 0 && touches(u))', 'foes.filter(u => touches(u))']]]]);

// ---------------------------------------------------------------- rule 5: area effects
rule('wizard blast: every living enemy unit within 234 px of the landing point takes ultBlast, units beyond and dead units do not', P => {
  P.place('right', [1269, 1731, 1737]);                                  // 231 / 231 / 237 px from x = 1500
  const hero = P.get('HERO_PROFILES').wizard, blast = Math.round(hero.dmg * 1.5 * 10) / 10;
  const p = P.launch(P.projectile({ team: 'player', hero: 'wizard', x: 1500, y: GY - 5, vy: 400, extra: { ultBlast: blast, ultThrow: true } }));
  P.run(5);
  assert.ok(Math.abs(p.x - 1500) < 1.5, 'wind drift stays below 1.5 px: ' + p.x);
  const [a, b, c] = P.units('right');
  near(a.hp, a.maxHp - blast, 'unit 231 px left'); near(b.hp, b.maxHp - blast, 'unit 231 px right'); assert.strictEqual(c.hp, c.maxHp, 'unit 237 px away is outside');
  assert.strictEqual(P.get('gameOver'), null);
  // dead unit stays at 0, edge units still hit
  P.reset(); P.place('right', [1269, 1731, 1737]); P.units('right')[1].hp = 0;
  P.launch(P.projectile({ team: 'player', hero: 'wizard', x: 1500, y: GY - 5, vy: 400, extra: { ultBlast: blast, ultThrow: true } })); P.run(5);
  near(P.units('right')[0].hp, P.units('right')[0].maxHp - blast); assert.strictEqual(P.units('right')[1].hp, 0); assert.strictEqual(P.units('right')[2].hp, P.units('right')[2].maxHp);
  assert.ok(!Array.from(P.get('floatTexts')).some(f => f.x === 1731), 'no blast number over the dead unit');
  // the blast ends the match only when it takes the LAST living unit
  P.reset(); P.place('right', [1400, 1500, 1600], 20);                   // all three inside, 20 hp each, blast = 49.5
  P.launch(P.projectile({ team: 'player', hero: 'wizard', x: 1500, y: GY - 5, vy: 400, extra: { ultBlast: blast, ultThrow: true } })); P.run(5);
  assert.deepStrictEqual(P.hp('right'), [0, 0, 0]); assert.strictEqual(P.get('gameOver'), 'player');
  P.reset(); P.place('right', [1400, 1500, 1900], 20);                   // the third stands outside and lives on
  P.launch(P.projectile({ team: 'player', hero: 'wizard', x: 1500, y: GY - 5, vy: 400, extra: { ultBlast: blast, ultThrow: true } })); P.run(5);
  assert.deepStrictEqual(P.hp('right'), [0, 0, 20]); assert.strictEqual(P.get('gameOver'), null, 'one enemy unit outside the blast lives: no game over');
}, [['only the active unit is hit (old single-unit blast)', [['unitsOf(p.team === "player" ? "right" : "left").forEach(vic => {', '[p.team === "player" ? ai : player].forEach(vic => {']]],
    ['radius shrunk to 120 px', [['Math.abs(vic.x - bx) <= 234', 'Math.abs(vic.x - bx) <= 120']]],
    ['dead units are blasted', [['if (Math.abs(vic.x - bx) <= 234 && vic.hp > 0 && !gameOver)', 'if (Math.abs(vic.x - bx) <= 234 && !gameOver)']]]]);

rule('bride wave splash: 100 / 75 / 50 percent by each unit\'s own distance to the wave centre; outside 105 px and dead units take nothing; one splash per shot', P => {
  const D = P.get('HERO_PROFILES').bride.dmg, pct = x => Math.round(D * x * 10) / 10;
  P.place('right', [1520, 1440, 1590]);                                   // dx 20 (primary, 100%), 60 (75%), 90 (50%) from x = 1500
  const p = P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20 })); P.run(5);
  assert.ok(Math.abs(p.x - 1500) < 1.5, 'wave centre ' + p.x);
  const [a, b, c] = P.units('right');
  near(a.maxHp - a.hp, pct(1), 'dx 20 -> 100%'); near(b.maxHp - b.hp, pct(0.75), 'dx 60 -> 75%'); near(c.maxHp - c.hp, pct(0.5), 'dx 90 -> 50%');
  assert.ok(a.poison > 0 && b.poison > 0 && c.poison > 0, 'the wave poisons every unit it damages');
  assert.strictEqual(p.splashDone, true);
  P.reset(); P.place('right', [1520, 1620, 1440]); P.units('right')[2].hp = 0;     // dx 120 is out of range, the dead one stays dead
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20 })); P.run(5);
  const [a2, o2, d2] = P.units('right');
  near(a2.maxHp - a2.hp, pct(1)); assert.strictEqual(o2.hp, o2.maxHp, 'dx 120 > 105: untouched'); assert.strictEqual(d2.hp, 0);
  assert.strictEqual(d2.animState, 'idle', 'a dead unit does not play the hit reaction');
  assert.ok(!Array.from(P.get('floatTexts')).some(f => f.x === d2.x), 'no damage number over the dead unit');
}, [['no splash at all (only the unit that took the hit)', [['if (u === opp || u.hp <= 0 || dxw > WAVE_HALF_WIDTH) return;', 'return;']]],
    ['flat damage instead of the stepped falloff', [['const waveDamage = (dx, dmg) => SoundWave.damageAt(dx, dmg);', 'const waveDamage = (dx, dmg) => dmg;']]],
    ['dead units are splashed', [['if (u === opp || u.hp <= 0 || dxw > WAVE_HALF_WIDTH) return;', 'if (u === opp || dxw > WAVE_HALF_WIDTH) return;']]]]);

rule2('bride wave falloff in cells of 35 px (owner 2026-11-18): 100 / 75 / 50 percent to 35 / 70 / 105 px, on BOTH sides of the wave centre, one cell edge at a time', mk => {
  const P = mk({});
  const D = P.get('HERO_PROFILES').bride.dmg, pct = x => Math.round(D * x * 10) / 10;
  P.place('right', [1500, 1700, 1850]);
  P.place('right', [1500, 1534, 1431]);                                      // primary at the centre; others at +34 (cell 1) and -69 (cell 2)
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20 })); P.run(5);
  let r = P.units('right');
  near(r[1].maxHp - r[1].hp, pct(1), '+34 px: cell 1, 100 percent'); near(r[2].maxHp - r[2].hp, pct(0.75), '-69 px: cell 2, 75 percent');
  P.reset(); P.place('right', [1500, 1536, 1428]);                           // +36 and -72: just past each cell edge
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20 })); P.run(5);
  r = P.units('right');
  near(r[1].maxHp - r[1].hp, pct(0.75), '+36 px is in cell 2'); near(r[2].maxHp - r[2].hp, pct(0.5), '-72 px is in cell 3');
  P.reset(); P.place('right', [1500, 1604, 1393]);                           // +104 and -107
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20 })); P.run(5);
  r = P.units('right');
  near(r[1].maxHp - r[1].hp, pct(0.5), '+104 px is the last cell'); assert.strictEqual(r[2].hp, r[2].maxHp, '-107 px is outside');
}, [{ label: 'the second edge is 75 px again (the invented 40 / 75 edges)', e: { files: { 'js/sound_wave.js': [['{ maxDistance: 2 * CELL, multiplier: 0.75 },', '{ maxDistance: 75, multiplier: 0.75 },']] } } },
    { label: 'the first edge is 40 px again', e: { files: { 'js/sound_wave.js': [['{ maxDistance: CELL, multiplier: 1 },', '{ maxDistance: 40, multiplier: 1 },']] } } }].map(m => [m.label, m.e]));

rule('bride ultimate bat swarm: ANY hit of the armed wave (also at 60 px from its centre) damages EVERY living enemy unit wherever it stands; a wave that touches nobody calls no swarm', P => {
  const D = P.get('HERO_PROFILES').bride.dmg, swarm = Math.round(D * 1.3 * 10) / 10, wave = Math.round(D * 10) / 10;
  P.place('right', [1520, 1100, 1900]);                                   // primary dx 20; the others are 400 px away: only the swarm reaches them
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
  let [a, b, c] = P.units('right');
  near(a.maxHp - a.hp, wave + swarm, 'primary: wave + swarm'); near(b.maxHp - b.hp, swarm, 'far unit: swarm'); near(c.maxHp - c.hp, swarm, 'far unit: swarm');
  P.reset(); P.place('right', [1520, 1100, 1900]); P.units('right')[2].hp = 0;
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
  [a, b, c] = P.units('right'); near(b.maxHp - b.hp, swarm); assert.strictEqual(c.hp, 0, 'a dead unit is skipped');
  assert.ok(!Array.from(P.get('floatTexts')).some(f => f.x === c.x && /^-/.test(f.text)), 'no swarm number over the dead unit');
  P.reset(); P.place('right', [1560, 1100, 1900]);                        // dx 60: the wave hits (75 percent) and, since 2026-11-18, the swarm comes too
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
  [a, b, c] = P.units('right'); near(b.maxHp - b.hp, swarm, 'swarm also after a hit at 60 px'); near(c.maxHp - c.hp, swarm);
  P.reset(); P.place('right', [1900, 1100, 1700]);                        // the wave lands 400 px from the nearest unit: it touches nobody, no swarm
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
  [a, b, c] = P.units('right'); assert.strictEqual(a.hp, a.maxHp, 'a miss: no swarm'); assert.strictEqual(b.hp, b.maxHp); assert.strictEqual(c.hp, c.maxHp);
}, [['the swarm only hits the unit that took the wave', [['unitsOf(p.team === "player" ? "right" : "left").forEach(v => {', '[opp].forEach(v => {']]],
    ['the 55 px precision window comes back', [['if (p.ultSwarm && opp.hp > 0) {', 'if (p.ultSwarm && Math.abs(p.x - opp.x) < 55 && opp.hp > 0) {']]],
    ['dead units are swarmed', [['if (v.hp <= 0) return;\n                const swarmHit', 'const swarmHit']]]]);

// ---------------------------------------------------------------- rare big hits on the page's own damage sites
check('big-hit rule: a normal throw (wave + swarm) takes at most half of a full bar from each unit; a passing throw is not limited', () => {
  for (const passes of [false, true]) {
    const P = loadPage({ team: 3 });
    P.eval('Determinism = Object.assign({}, Determinism, { bigHitPass: function () { return ' + passes + '; } });');
    P.reset(); P.place('right', [1560, 1100, 1900]); P.clearWeather();
    P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
    const u = P.units('right')[0], lost = u.maxHp - u.hp;
    if (passes) assert.ok(lost > u.maxHp / 2, 'passing throw: ' + lost + ' of ' + u.maxHp);
    else assert.ok(lost > 0 && lost <= u.maxHp / 2 + 0.05, 'limited throw: ' + lost + ' of ' + u.maxHp);
  }
});

// ---------------------------------------------------------------- AI target and report target
rule('aiTarget: the nearest LIVING enemy unit to the AI; with one living unit that unit', P => {
  P.place('left', [400, 900, 1300]); P.place('right', [1500, 1500, 1500]);
  assert.strictEqual(P.eval('aiTarget()').id, 'left_2', 'nearest to x = 1500');
  P.units('left')[2].hp = 0; assert.strictEqual(P.eval('aiTarget()').id, 'left_1', 'a dead nearest unit is skipped');
  P.units('left')[1].hp = 0; P.eval('ensureLivingActive("left")'); assert.strictEqual(P.eval('aiTarget()').id, 'left_0', 'the last living unit');
  P.reset(); P.place('left', [1300, 900, 400]); assert.strictEqual(P.eval('aiTarget()').id, 'left_0', 'nearest does not depend on team order');
}, [['the farthest unit is targeted', [['Math.abs(a.x - ai.x) <= Math.abs(b.x - ai.x) ? a : b', 'Math.abs(a.x - ai.x) >= Math.abs(b.x - ai.x) ? a : b']]],
    ['dead units are targeted', [['const live = unitsOf("left").filter(u => u.hp > 0);', 'const live = unitsOf("left");']]]]);

rule('reportTarget: the living enemy unit nearest to the shot, dead units ignored', P => {
  P.place('right', [1200, 1500, 1260]); P.units('right')[2].hp = 0;
  assert.strictEqual(P.eval('reportTarget({ team: "player", x: 1250 })').id, 'right_0', 'right_2 is nearer but dead');
  assert.strictEqual(P.eval('reportTarget({ team: "player", x: 1450 })').id, 'right_1');
  P.place('left', [400, 700, 1000]);
  assert.strictEqual(P.eval('reportTarget({ team: "ai", x: 650 })').id, 'left_1');
}, [['the farthest unit is reported', [['Math.abs(a.x - p.x) <= Math.abs(b.x - p.x) ? a : b', 'Math.abs(a.x - p.x) >= Math.abs(b.x - p.x) ? a : b']]],
    ['dead units are reported', [['const foes = unitsOf(p.team === "player" ? "right" : "left").filter(u => u.hp > 0);\n      if (foes.length < 2)', 'const foes = unitsOf(p.team === "player" ? "right" : "left");\n      if (foes.length < 2)']]]]);

// ---------------------------------------------------------------- move clamp (stepDice)
function dice(P, owner, dir, steps) { P.eval('diceRoll = { owner: "' + owner + '", dir: ' + dir + ', t: 1, final: ' + steps + ', shown: ' + steps + ', applied: false, afterT: 0 }; stepDice(0.01);'); }
rule('move clamp: a unit never stops within 120 px of a living teammate and steps back to the nearest free spot; a dead teammate does not block; the zone limits still hold', P => {
  P.place('left', [340, 500, 640]);                                      // left_0 walks forward 5 x 36 = 180 px: 520 would sit 20 px from left_1
  dice(P, 'player', 1, 5);
  const u = P.units('left')[0];
  for (const m of P.units('left').slice(1)) assert.ok(Math.abs(u.targetX - m.targetX) >= 120, 'distance to ' + m.id + ': ' + Math.abs(u.targetX - m.targetX));
  assert.ok(u.targetX > 340 && u.targetX < 520, 'moved forward but not the full roll: ' + u.targetX);
  P.reset(); P.place('left', [340, 500, 640]); P.units('left')[1].hp = 0; P.units('left')[2].hp = 0;   // both mates are down: free walk
  dice(P, 'player', 1, 5); near(P.units('left')[0].targetX, 520, 'no living mate: the full 180 px');
  P.reset(); P.place('left', [260, 620, 680]); P.units('left')[1].hp = 0;                              // backwards against the left zone edge (110 since 2026-11-17, was 240) with left_2 far away
  dice(P, 'player', -1, 6); near(P.units('left')[0].targetX, 110, 'zone floor 110');
  P.reset(); P.place('right', [1600, 1400, 1250]);                                                    // AI team: right_0 walks toward the enemy (-x) 4 x 36 px: 1456 would sit 56 px from right_1
  P.setActive('right', 0); dice(P, 'ai', 1, 4);
  const r = P.units('right'); assert.ok(Math.abs(r[0].targetX - r[1].targetX) >= 120 && Math.abs(r[0].targetX - r[2].targetX) >= 120, 'AI team keeps 120 px too: ' + r[0].targetX);
  assert.ok(r[0].targetX < 1600 && r[0].targetX >= 1520, 'AI unit moved toward the enemy as far as the rule allows: ' + r[0].targetX);
}, [['no minimum distance', [['Math.abs(cx - m.targetX) < 120', 'Math.abs(cx - m.targetX) < 0']]],
    ['minimum distance only 20 px', [['Math.abs(cx - m.targetX) < 120', 'Math.abs(cx - m.targetX) < 20']]],
    ['dead teammates block the way', [['unitsOf(d.owner === "player" ? "left" : "right").filter(m => m !== u && m.hp > 0)', 'unitsOf(d.owner === "player" ? "left" : "right").filter(m => m !== u)']]]]);

// ---------------------------------------------------------------- status ticks reach benched units
rule('round start: poison / bleed / burn tick on EVERY living unit of both teams, benched ones included; dead units are not touched', P => {
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  const L = P.units('left'), R = P.units('right');
  assert.strictEqual(P.activeId('left'), 'left_0'); assert.strictEqual(P.activeId('right'), 'right_0');
  L[1].poison = 2; L[2].bleed = 1; R[1].burn = 2; R[2].poison = 1; L[0].poison = 1;            // left_1, left_2, right_1, right_2 are on the bench
  R[0].poison = 2; R[0].hp = 0;                                                                // a dead unit keeps its counter
  const roundBefore = P.get('roundNum');
  P.eval('resolveRound()');
  assert.strictEqual(P.get('roundNum'), roundBefore + 1, 'the round really resolved');
  const dmg = P.get('POISON_DMG'), bleed = P.get('BLEED_DMG'), burn = P.get('BURN_DMG');
  near(L[1].hp, L[1].maxHp - dmg, 'benched poisoned unit'); assert.strictEqual(L[1].poison, 1);
  near(L[2].hp, L[2].maxHp - bleed, 'benched bleeding unit'); assert.strictEqual(L[2].bleed, 0);
  near(R[1].hp, R[1].maxHp - burn, 'benched burning unit'); assert.strictEqual(R[1].burn, 1);
  near(R[2].hp, R[2].maxHp - dmg, 'benched poisoned unit (AI team)');
  near(L[0].hp, L[0].maxHp - dmg, 'active unit');
  assert.strictEqual(R[0].poison, 2, 'a dead unit is not ticked'); assert.strictEqual(R[0].hp, 0);
}, [['only the two active units tick', [['allUnits().forEach(u => { if (u.hp > 0) { tickPoison(u); tickBleed(u); tickBurn(u); } });', '[player, ai].forEach(u => { if (u.hp > 0) { tickPoison(u); tickBleed(u); tickBurn(u); } });']]],
    ['dead units tick too', [['allUnits().forEach(u => { if (u.hp > 0) { tickPoison(u); tickBleed(u); tickBurn(u); } });', 'allUnits().forEach(u => { { tickPoison(u); tickBleed(u); tickBurn(u); } });']]]]);

rule('physics step: every unit (benched ones too) eases toward its targetX and counts down its resupply', P => {
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.units('left')[2].targetX = 700; P.units('right')[1].targetX = 1350; P.units('left')[1].resupply = 0.05; P.units('left')[1].armed = false;
  P.eval('hitStop = 0; updatePhysics(0.1)');
  assert.ok(P.units('left')[2].x > 600 && P.units('right')[1].x < 1450, 'benched units move');
  P.eval('hitStop = 0; updatePhysics(0.1)');
  assert.strictEqual(P.units('left')[1].armed, true, 'benched unit re-armed');
}, [['only player and ai are interpolated', [['allUnits().forEach(u => { u.x += (u.targetX - u.x) * 4.0 * dt; });', '[player, ai].forEach(u => { u.x += (u.targetX - u.x) * 4.0 * dt; });']]],
    ['only player and ai are resupplied', [['      allUnits().forEach(u => {\n        if (u.resupply > 0) {', '      [player, ai].forEach(u => {\n        if (u.resupply > 0) {']]]]);

// ---------------------------------------------------------------- one end-to-end: the page's own executeThrow builds the shot
check('end to end: the real executeThrow builds p, the real physics lands it, the thrower team rotates (no projectile hand-built)', () => {
  const P = loadPage({ bigHitOff: true, team: 3 });
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.eval('wind = 0'); P.eval('turn = "player"; matchStarted = true;');
  P.eval('executeThrow("player", 60, 54)');
  const p = P.get('projectiles')[0];
  assert.ok(p && p.team === 'player' && Array.isArray(p.trail) && Array.isArray(p.recordedPath) && p.flightDir === 1 && typeof p.startX === 'number' && p.dmg > 0 && p.wLen > 0 && p.wThick > 0, 'shape of the pushed projectile');
  P.run(2000, 0.01);
  assert.strictEqual(P.get('projectiles').length, 0, 'the shot landed');
  assert.strictEqual(P.activeId('left'), 'left_1', 'the throw used the turn of left_0 and the team rotated');
});

// ================================================================ round 2: tuning, ramp, round cap, selector, double shot
// Independent source of the numbers: shared/team_tuning.json (read from disk), not the js module the page uses.
const TUNE = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'team_tuning.json'), 'utf8'));
const r1 = x => Math.round(x * 10) / 10;
const expHp = (hp, dmg, n) => n === 1 ? hp : Math.round(Math.max(hp * TUNE.hp_scale[String(n)], TUNE.hp_floor_hits * dmg));
const expRamp = (round, n) => (n === 1 || round < TUNE.ramp.start_round) ? 1 : Math.round((1 + TUNE.ramp.per_round * (round - (TUNE.ramp.start_round - 1))) * 1e6) / 1e6;
// rule2: like rule(), but the scenario builds its own pages: scenario(mk) with mk(opts) = loadPage({team: 3, ...opts, mutate}).
function rule2(name, scenario, mutants) {
  check(name, () => scenario(o => loadPage(Object.assign({ bigHitOff: true, team: 3 }, o))));
  for (const [label, edits] of (mutants || [])) {
    check(name + ' [negative: ' + label + ' must be caught]', () => {
      const mut = Array.isArray(edits) ? { mutate: edits } : { mutate: edits.page || [], mutateFiles: edits.files || {} };   // edits: [[from,to]] for the page script, or { page: [...], files: { 'js/x.js': [...] } }
      loadPage(Object.assign({ bigHitOff: true, team: 3 }, mut));                  // a missing target throws here, outside the expectation
      let caught = null;
      try { scenario(o => loadPage(Object.assign({ bigHitOff: true, team: 3 }, o, mut))); } catch (e) { caught = e; }
      assert.ok(caught, 'mutant survived: ' + label);
      assert.ok(caught instanceof assert.AssertionError, 'mutant died for the wrong reason (not an assertion): ' + caught);
    });
  }
}
const HEROES = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];

// ---------------------------------------------------------------- (1) team hp
rule2('team hp: after applyClassStats every unit of a side has hp = maxHp = teamMaxHp(hero hp, hero dmg, N) (shared/team_tuning.json); N = 1 keeps the plain hero hp; switchHero re-applies it to ALL left units', mk => {
  for (const N of [1, 2, 3]) {
    const P = mk({ team: N });
    const H = P.get('HERO_PROFILES');
    assert.strictEqual(P.units('left').length, N);
    for (const hero of HEROES) {
      const other = HEROES[(HEROES.indexOf(hero) + 3) % HEROES.length];
      P.eval('currentHero = ' + JSON.stringify(hero) + '; aiClass = ' + JSON.stringify(other) + '; applyClassStats()');
      for (const u of P.units('left')) { assert.strictEqual(u.maxHp, expHp(H[hero].hp, H[hero].dmg, N), 'N=' + N + ' left ' + hero + ' maxHp of ' + u.id); assert.strictEqual(u.hp, u.maxHp); }
      for (const u of P.units('right')) { assert.strictEqual(u.maxHp, expHp(H[other].hp, H[other].dmg, N), 'N=' + N + ' right ' + other + ' maxHp of ' + u.id); assert.strictEqual(u.hp, u.maxHp); }
      if (N === 1) assert.strictEqual(P.units('left')[0].hp, H[hero].hp, 'N = 1: the plain hero hp');
    }
    // switchHero: every left unit (benched too) gets the new hero's hp, even after damage
    P.units('left').forEach(u => { u.hp = 3; });
    P.eval('switchHero("knight", true)');
    for (const u of P.units('left')) { assert.strictEqual(u.maxHp, expHp(H.knight.hp, H.knight.dmg, N), 'switchHero maxHp ' + u.id); assert.strictEqual(u.hp, u.maxHp, 'switchHero refills ' + u.id); }
    assert.strictEqual(P.get('currentHero'), 'knight');
  }
  // the formula spelled out from the json (3 units, wizard): max(hp x scale, floor hits x dmg), rounded
  const Q = mk({ team: 3 }); Q.eval('currentHero = "wizard"; applyClassStats()');
  const W = Q.get('HERO_PROFILES').wizard;
  assert.strictEqual(Q.units('left')[2].maxHp, Math.round(Math.max(W.hp * TUNE.hp_scale['3'], TUNE.hp_floor_hits * W.dmg)));
  assert.ok(Q.units('left')[2].maxHp <= W.hp && Q.units('left')[2].maxHp >= TUNE.hp_floor_hits * W.dmg - 1, 'a team unit stays between the damage floor and the hero table hp');
}, [['switchHero updates only the active unit', [['unitsOf("left").forEach((u, i) => { const hp0 = HERO_PROFILES[leftHeroes[i]] || pp0; u.maxHp = unitStartHp(hp0); u.hp = u.maxHp; });', '[player].forEach((u, i) => { const hp0 = HERO_PROFILES[leftHeroes[i]] || pp0; u.maxHp = unitStartHp(hp0); u.hp = u.maxHp; });']]],
    ['applyClassStats updates only the first unit of the left team', [['unitsOf("left").forEach((u, i) => { const hp0 = HERO_PROFILES[leftHeroes[i]] || pp; if (hp0) { u.maxHp = unitStartHp(hp0); u.hp = u.maxHp; } });', 'unitsOf("left").slice(0, 1).forEach((u, i) => { const hp0 = HERO_PROFILES[leftHeroes[i]] || pp; if (hp0) { u.maxHp = unitStartHp(hp0); u.hp = u.maxHp; } });']]],
    ['applyClassStats leaves the right team out', [['unitsOf("right").forEach((u, i) => { const hp1 = HERO_PROFILES[rightHeroes[i]] || ap; if (hp1) { u.maxHp = unitStartHp(hp1); u.hp = u.maxHp; } });', 'unitsOf("right").slice(0, 1).forEach((u, i) => { const hp1 = HERO_PROFILES[rightHeroes[i]] || ap; if (hp1) { u.maxHp = unitStartHp(hp1); u.hp = u.maxHp; } });']]],
    ['team matches use the plain hero hp', [['const unitStartHp = prof => TEAM_N > 1 ? TeamTuning.teamMaxHp(prof.hp, prof.dmg, TEAM_N) : prof.hp;', 'const unitStartHp = prof => prof.hp;']]]]);

// ---------------------------------------------------------------- (2) late-round damage ramp
function lethalSafe(P, side, xs) { return P.place(side, xs, 300); }
rule2('ramp: a real hit, the wizard blast, the wave (primary + splash) and the bat swarm are multiplied from the json start_round on (x1 before, +per_round per round from it; rounds start-1, start, start+3); nothing at N = 1 even late', mk => {
  const run = (N, round) => {
    const P = mk({ team: N }); const H = P.get('HERO_PROFILES'), mult = expRamp(round, N);
    const setRound = () => { P.eval('roundNum = ' + round); P.clearWeather(); };
    const hits = {};
    // normal hit (skeleton javelin at 22)
    P.reset(); setRound(); lethalSafe(P, 'right', [1300, 1450, 1600]);
    P.launch(P.projectile({ team: 'player', hero: 'skeleton', x: 1300, y: GY - 60 })); P.run(5);
    const u0 = P.units('right')[0]; near(u0.maxHp - u0.hp, r1(H.skeleton.dmg * mult), 'N=' + N + ' round ' + round + ' normal hit');
    // blast: 234 px, 3 units inside (N = 1 uses the single unit)
    P.reset(); setRound(); lethalSafe(P, 'right', [1350, 1650, 1400].slice(0, N));   // all inside 234 px but none under the shell (no direct hit)
    const blast = r1(H.wizard.dmg * 1.5);
    P.launch(P.projectile({ team: 'player', hero: 'wizard', x: 1500, y: GY - 5, vy: 400, extra: { ultBlast: blast, ultThrow: true } })); P.run(5);
    for (const u of P.units('right')) near(u.maxHp - u.hp, r1(blast * mult), 'N=' + N + ' round ' + round + ' blast ' + u.id);
    // wave: primary dx 20 (100%), splash dx 60 (75%) and dx 90 (50%)
    P.reset(); setRound(); lethalSafe(P, 'right', [1520, 1440, 1590].slice(0, N));
    P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20 })); P.run(5);
    const D = H.bride.dmg, R = P.units('right');
    near(R[0].maxHp - R[0].hp, r1(r1(D) * mult), 'N=' + N + ' round ' + round + ' wave primary');
    if (N > 1) near(R[1].maxHp - R[1].hp, r1(r1(D * 0.75) * mult), 'wave splash 75%');
    if (N > 2) near(R[2].maxHp - R[2].hp, r1(r1(D * 0.5) * mult), 'wave splash 50%');
    // swarm: far units take only the swarm
    if (N > 1) {
      P.reset(); setRound(); lethalSafe(P, 'right', [1520, 1100, 1900].slice(0, N));
      P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
      const S = P.units('right'); near(S[1].maxHp - S[1].hp, r1(r1(D * 1.3) * mult), 'N=' + N + ' round ' + round + ' swarm');
      if (N > 2) near(S[2].maxHp - S[2].hp, r1(r1(D * 1.3) * mult), 'swarm 2');
    }
    return mult;
  };
  const st = TUNE.ramp.start_round, pr = TUNE.ramp.per_round;
  assert.strictEqual(run(3, st - 1), 1); near(run(3, st), 1 + pr); near(run(3, st + 3), 1 + 4 * pr); near(run(2, st + 3), 1 + 4 * pr); near(run(2, st), 1 + pr);
  assert.strictEqual(run(1, st + 3), 1, 'N = 1: no ramp even after the start round');
  // the page announces the ramp once: the round change INTO start_round pushes the team.ramp toast, the one before does not
  for (const [from, want] of [[st - 2, false], [st - 1, true]]) {
    const P = mk({ team: 3 }); P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
    P.eval('roundNum = ' + from + '; floatTexts.length = 0'); P.clearWeather(); P.eval('resolveRound()');
    assert.strictEqual(Array.from(P.get('floatTexts')).some(f => f.text === 'team.ramp'), want, 'ramp toast when entering round ' + (from + 1));
  }
}, [['no ramp at all', [['const rampDmg = x => TEAM_N > 1 ? Math.round(x * TeamTuning.rampMultiplier(roundNum, TEAM_N) * 10) / 10 : x;', 'const rampDmg = x => x;']]],
    ['the blast is not ramped', [['const blastDmg = rampDmg(p.ultBlast);', 'const blastDmg = p.ultBlast;']]],
    ['the wave splash is not ramped', [['dw = rampDmg(dw);', 'dw = dw;']]],
    ['the swarm is not ramped', [['const swarm = rampDmg(Math.round(HERO_PROFILES.bride.dmg * 1.3 * 10) / 10);', 'const swarm = Math.round(HERO_PROFILES.bride.dmg * 1.3 * 10) / 10;']]],
    ['the direct hit is not ramped', [['dmgNow = rampDmg(dmgNow);', 'dmgNow = dmgNow;']]],
    ['the ramp also applies with one unit per team', [['const rampDmg = x => TEAM_N > 1 ? Math.round(x * TeamTuning.rampMultiplier(roundNum, TEAM_N) * 10) / 10 : x;', 'const rampDmg = x => Math.round(x * (1 + ' + TUNE.ramp.per_round + ' * Math.max(0, roundNum - ' + (TUNE.ramp.start_round - 1) + ')) * 10) / 10;']]]]);

// ---------------------------------------------------------------- (3) round cap
rule2('round cap: at N = 1 (cap 40), N = 2 (cap 24) and N = 3 (cap 28) the round after the cap ends the match for the team with the larger hp share, pushes the toast and returns before a new turn starts; below the cap nothing happens', mk => {
  const texts = P => Array.from(P.get('floatTexts')).map(f => f.text);
  for (const [N, cap] of [[1, TUNE.round_cap['1']], [2, TUNE.round_cap['2']], [3, TUNE.round_cap['3']]]) {
    // left ahead -> player wins
    let P = mk({ team: N }); P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
    P.units('right').forEach(u => { u.hp = u.maxHp / 2; });
    P.eval('roundNum = ' + cap + '; wind = 1.5; turn = "ai"; floatTexts.length = 0'); P.clearWeather();
    assert.strictEqual(P.eval('TeamTuning.capWinner(teams)'), 'left');
    P.eval('resolveRound()');
    assert.strictEqual(P.get('roundNum'), cap + 1); assert.strictEqual(P.get('gameOver'), 'player'); assert.strictEqual(P.get('turn'), 'over');
    assert.ok(texts(P).includes('team.roundCap'), 'toast pushed: ' + texts(P));
    assert.strictEqual(P.get('wind'), 1.5, 'returned before the new round (no new wind)'); assert.ok(!texts(P).includes('team.ramp'));
    // right ahead -> ai wins
    P = mk({ team: N }); P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
    P.units('left').forEach(u => { u.hp = u.maxHp / 4; });
    P.eval('roundNum = ' + cap + '; turn = "ai"'); P.clearWeather(); P.eval('resolveRound()');
    assert.strictEqual(P.get('gameOver'), 'ai'); assert.strictEqual(P.get('turn'), 'over');
    // equal share and equal living units -> the right side (rule text of shared/team_tuning.json)
    P = mk({ team: N }); P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
    P.eval('roundNum = ' + cap); P.clearWeather(); P.eval('resolveRound()'); assert.strictEqual(P.get('gameOver'), 'ai', 'tie -> right side');
    // one round before the cap: the match goes on
    P = mk({ team: N }); P.reset(); P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
    P.eval('roundNum = ' + (cap - 1) + '; wind = 1.5'); P.clearWeather(); P.eval('resolveRound()');
    assert.strictEqual(P.get('roundNum'), cap); assert.strictEqual(P.get('gameOver'), null); assert.strictEqual(P.get('turn'), 'player');
    // an already finished match is not decided again
    P = mk({ team: N }); P.reset(); P.eval('roundNum = ' + cap + '; gameOver = "player"'); P.clearWeather(); P.eval('resolveRound()'); assert.strictEqual(P.get('roundNum'), cap, 'resolveRound returns at once after game over');
  }
  const P1 = mk({ team: 1 }); P1.reset(); P1.place('left', [300]); P1.place('right', [1300]); P1.units('right')[0].hp = 1;
  P1.eval('roundNum = 39'); P1.clearWeather(); P1.eval('resolveRound()');
  assert.strictEqual(P1.get('gameOver'), null, 'N = 1: round 40 is still played'); assert.strictEqual(P1.get('turn'), 'player'); assert.ok(!texts(P1).includes('team.roundCap'));
}, [['the cap is ignored', [['roundNum > TeamTuning.roundCap(TEAM_N) && !gameOver', 'roundNum > 1000 && !gameOver']]],
    ['the left team always wins', [['gameOver = TeamTuning.capWinner(teams) === "left" ? "player" : "ai"; turn = "over";', 'gameOver = "player"; turn = "over";']]],
    ['the right team always wins', [['gameOver = TeamTuning.capWinner(teams) === "left" ? "player" : "ai"; turn = "over";', 'gameOver = "ai"; turn = "over";']]],
    ['the toast is missing', [['floatTexts.push({ x: CANVAS_W / 2, y: 200, text: T("team.roundCap"), color: "#ffd32a", alpha: 1.0 });', '']]],
    ['no early return: a new turn starts after the cap', [['text: T("team.roundCap"), color: "#ffd32a", alpha: 1.0 });\n        return;', 'text: T("team.roundCap"), color: "#ffd32a", alpha: 1.0 });']]],
    ['the duel cap is 50 instead of 40', [['if (roundNum > TeamTuning.roundCap(TEAM_N) && !gameOver)', 'if (roundNum > (TEAM_N > 1 ? TeamTuning.roundCap(TEAM_N) : 50) && !gameOver)']]]]);

// ---------------------------------------------------------------- (4) team-size selector
rule2('selector: pk_team_n in localStorage sets TEAM_N when ?team= is absent, ?team= wins, junk falls back to 1, the value is clamped to 3; a click writes storage and navigates to ?team=N (nothing on the current size)', mk => {
  assert.strictEqual(mk({ search: '', storage: { pk_team_n: '3' } }).get('TEAM_N'), 3);
  assert.strictEqual(mk({ search: '', storage: { pk_team_n: '2' } }).units('left').length, 2);
  assert.strictEqual(mk({ search: '?team=2', storage: { pk_team_n: '3' } }).get('TEAM_N'), 2, 'the URL flag wins');
  assert.strictEqual(mk({ search: '', storage: { pk_team_n: 'abc' } }).get('TEAM_N'), 1);
  assert.strictEqual(mk({ search: '', storage: { pk_team_n: '7' } }).get('TEAM_N'), 3);
  assert.strictEqual(mk({ search: '', storage: {} }).get('TEAM_N'), 1);
  assert.strictEqual(mk({ search: '', storageBlocked: true }).get('TEAM_N'), 1, 'blocked storage must not break the page');
  // the buttons: pressed state and click handler
  const P = mk({ search: '', storage: { pk_team_n: '3' } });
  assert.deepStrictEqual(P.teamButtons.map(b => b.attrs['aria-pressed']), ['false', 'false', 'true']);
  P.teamButtons[1].click();                                              // 2v2
  assert.strictEqual(P.store.get('pk_team_n'), '2', 'the choice is stored');
  const href = P.location.href; assert.ok(/[?&]team=2(&|$)/.test(href), 'navigates to ?team=2: ' + href);
  const Q = mk({ search: '?team=2', storage: {} }); Q.teamButtons[1].click();
  assert.strictEqual(Q.store.has('pk_team_n'), false, 'clicking the current size does nothing'); assert.ok(!/team=/.test(Q.location.href));
  const R = mk({ search: '', storage: {} }); R.teamButtons[2].click();
  assert.strictEqual(R.store.get('pk_team_n'), '3'); assert.ok(/team=3/.test(R.location.href));
  const B = mk({ search: '', storageBlocked: true }); B.teamButtons[1].click();
  assert.ok(/team=2/.test(B.location.href), 'storage blocked: the URL still carries the choice');
}, [['the URL flag no longer wins', [['.get("team"), 10) ||', '.get("team"), 10) && 0 ||']]],
    ['the stored size is not read', [['localStorage.getItem("pk_team_n")', 'localStorage.getItem("pk_team_x")']]],
    ['the size is not clamped to 3', [['Math.max(1, Math.min(3, parseInt(new URLSearchParams(location.search)', 'Math.max(1, Math.min(9, parseInt(new URLSearchParams(location.search)']]],
    ['a click does not write storage', [['localStorage.setItem("pk_team_n", String(n));', '']]],
    ['a click does not navigate', [['u.searchParams.set("team", String(n)); u.searchParams.delete("room"); location.href = u.toString();', 'u.searchParams.set("team", String(n)); u.searchParams.delete("room");']]],
    ['a click navigates to the wrong size', [['u.searchParams.set("team", String(n));', 'u.searchParams.set("team", String(n + 1));']]]]);

// ---------------------------------------------------------------- (5) double shot keeps its thrower
rule2('double shot: the second shell (queued 260 ms later) is thrown by the unit that fired, even after the team rotated; the rotated unit is not disarmed', mk => {
  const P = mk({ team: 3 });
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.eval('wind = 0; turn = "player"; matchStarted = true; currentHero = "skeleton"; selectedSkill = "double"; skillCharges.player.double = 1; isCharging = true; chargeStart = -1000; chargePower = 60;');
  P.eval('releaseAndThrow()');
  for (let i = 0; i < 40 && P.get('projectiles').length === 0; i++) P.eval('hitStop = 0; updatePhysics(0.1)');
  const first = Array.from(P.get('projectiles'));
  assert.strictEqual(first.length, 1, 'the first shell left the hand of left_0');
  assert.strictEqual(first[0].startX, 300 + 58, 'first shell leaves left_0');
  const second = P.timers.filter(t => t.ms === 260);
  assert.strictEqual(second.length, 1, 'a second shell is queued 260 ms later');
  P.eval('rotateTeam("left")'); assert.strictEqual(P.activeId('left'), 'left_1');   // the turn already moved on
  second[0].fn();
  const all = Array.from(P.get('projectiles')); assert.strictEqual(all.length, 2);
  assert.strictEqual(all[1].startX, 300 + 58, 'the second shell is thrown by left_0, not by the rotated left_1 (x 450)');
  assert.strictEqual(P.units('left')[0].armed, false); assert.strictEqual(P.units('left')[1].armed, true, 'the rotated unit keeps its weapon');
  assert.ok(Math.abs(all[1].vx / first[0].vx - 1.04) < 1e-9, 'second shell power x 1.04');
  // Max-power double shot: second shell must stay capped at MAX_POWER (115), matching mcp_stdio_server
  const Pcap = mk({ team: 1 });
  Pcap.place('left', [300]); Pcap.place('right', [1400]);
  Pcap.eval('wind = 0; turn = "player"; matchStarted = true; currentHero = "skeleton"; selectedSkill = "double"; skillCharges.player.double = 1; isCharging = true; chargeStart = -1000; chargePower = MAX_POWER;');
  Pcap.eval('releaseAndThrow()');
  for (let i = 0; i < 40 && Pcap.get('projectiles').length === 0; i++) Pcap.eval('hitStop = 0; updatePhysics(0.1)');
  const c1 = Array.from(Pcap.get('projectiles'));
  const t2 = Pcap.timers.filter(t => t.ms === 260);
  t2[0].fn();
  const cAll = Array.from(Pcap.get('projectiles'));
  assert.strictEqual(cAll.length, 2);
  assert.ok(Math.abs(cAll[1].vx - c1[0].vx) < 1e-9, 'second shell at MAX_POWER stays clamped to MAX_POWER');
}, [['the thrower argument is dropped from the queued shell', [['setTimeout(() => executeThrow(team, Math.min(MAX_POWER, power * 1.04), firedAngle, unit), 260);', 'setTimeout(() => executeThrow(team, Math.min(MAX_POWER, power * 1.04), firedAngle), 260);']]],
    ['executeThrow ignores the thrower argument', [['const u = thrower || (isPlayer ? player : ai);', 'const u = (isPlayer ? player : ai);']]]]);

// ================================================================ round 3: opener alternation (routeAfterTurn) and the Comeback cap
const route = (P, code) => { const n0 = P.timers.length; P.eval(code); return P.timers.slice(n0); };
rule2('opener: openerOfRound is fixed from the coin for the whole match, nobody attacks twice in a row (owner 2026-11-17; null = left always opens); routeAfterTurn / advanceAfterAttack send the turn to the other side or end the round; resolveRound starts the right side in its opener rounds; one unit per team keeps the old order', mk => {
  const P = mk({ team: 3 });
  P.eval('seats.left = "human"; seats.right = "ai"');
  const opener = r => P.eval('openerOfRound(' + r + ')');
  assert.strictEqual(P.get('firstOpener'), null);
  assert.deepStrictEqual([1, 2, 3, 4].map(opener), ['player', 'player', 'player', 'player'], 'no coin yet: the left side opens every round');
  P.eval('beginOpeningTurn("left")'); assert.strictEqual(P.get('firstOpener'), 'player');
  assert.deepStrictEqual([1, 2, 3, 4, 5, 6].map(opener), ['player', 'player', 'player', 'player', 'player', 'player']);
  P.eval('seats.right = "human"; beginOpeningTurn("right")'); assert.strictEqual(P.get('firstOpener'), 'ai');
  assert.deepStrictEqual([1, 2, 3, 4, 5, 6].map(opener), ['ai', 'ai', 'ai', 'ai', 'ai', 'ai']);
  // routing: the opener is followed by the other side, the second mover ends the round
  P.eval('seats.right = "ai"; firstOpener = "player"; roundNum = 1');
  let t = route(P, 'routeAfterTurn("player", 700)');
  assert.strictEqual(t.length, 1); assert.strictEqual(t[0].fn, P.get('triggerAITurn')); assert.strictEqual(t[0].ms, 700);
  t = route(P, 'routeAfterTurn("ai", 500)'); assert.strictEqual(t.length, 1); assert.strictEqual(t[0].fn, P.get('resolveRound')); assert.strictEqual(t[0].ms, 500);
  P.eval('roundNum = 2');                                              // the left side opens round 2 as well (fixed opener)
  t = route(P, 'routeAfterTurn("player", 400)'); assert.strictEqual(t[0].fn, P.get('triggerAITurn')); assert.strictEqual(t[0].ms, 400);
  P.eval('firstOpener = "ai"');                                        // coin: the right side opens every round
  t = route(P, 'routeAfterTurn("ai", 600)'); assert.strictEqual(t.length, 1); assert.strictEqual(t[0].fn, P.get('beginLeftTurnMidRound')); assert.strictEqual(t[0].ms, 600);
  t = route(P, 'routeAfterTurn("player", 400)'); assert.strictEqual(t[0].fn, P.get('resolveRound')); assert.strictEqual(t[0].ms, 400);
  P.eval('firstOpener = null');
  t = route(P, 'routeAfterTurn("ai", 300)'); assert.strictEqual(t[0].fn, P.get('resolveRound'), 'without a coin the left side opens round 2 too');
  // the real turn end: a landed shot goes through advanceAfterAttack
  P.reset(); P.eval('seats.right = "ai"; firstOpener = "ai"; roundNum = 1');
  t = route(P, 'advanceAfterAttack("player")'); assert.strictEqual(t[t.length - 1].fn, P.get('resolveRound'), 'right opened round 1: the left throw ends it'); assert.strictEqual(t[t.length - 1].ms, 1000);
  t = route(P, 'advanceAfterAttack("ai")'); assert.strictEqual(t[t.length - 1].fn, P.get('beginLeftTurnMidRound'), 'right opened: the left side follows'); assert.strictEqual(t[t.length - 1].ms, 800);
  // resolveRound starts the right side itself when it opens the next round
  let calls = 0; P.context.triggerAITurn = () => { calls++; };
  P.place('left', [300, 450, 600]); P.place('right', [1300, 1450, 1600]);
  P.reset(); P.eval('firstOpener = "ai"; roundNum = 2'); P.clearWeather(); P.eval('resolveRound()');       // -> round 3: the coin's right side opens again
  assert.strictEqual(P.get('roundNum'), 3); assert.strictEqual(calls, 1, 'the right side opens round 3'); assert.strictEqual(P.get('turn'), 'busy');
  calls = 0; P.reset(); P.eval('firstOpener = "ai"; roundNum = 1'); P.clearWeather(); P.eval('resolveRound()');   // -> round 2: still the right side
  assert.strictEqual(calls, 1, 'the right side opens round 2 too');
  calls = 0; P.reset(); P.eval('firstOpener = "player"; roundNum = 1'); P.clearWeather(); P.eval('resolveRound()');   // -> round 2: the left side
  assert.strictEqual(calls, 0); assert.strictEqual(P.get('turn'), 'player');
  // one unit per team: firstOpener is never read, the old order stays (player throw -> AI turn, AI throw -> resolveRound; resolveRound never starts the AI)
  const Q = mk({ team: 1 }); Q.eval('seats.left = "human"; seats.right = "ai"; firstOpener = "ai"; roundNum = 1');
  t = route(Q, 'advanceAfterAttack("player")'); assert.strictEqual(t[t.length - 1].fn, Q.get('triggerAITurn'), 'N = 1: the AI follows the player'); assert.strictEqual(t[t.length - 1].ms, 1000);
  t = route(Q, 'advanceAfterAttack("ai")'); assert.strictEqual(t[t.length - 1].fn, Q.get('resolveRound')); assert.strictEqual(t[t.length - 1].ms, 800);
  let q = 0; Q.context.triggerAITurn = () => { q++; }; Q.eval('roundNum = 2'); Q.clearWeather(); Q.eval('resolveRound()');
  assert.strictEqual(q, 0, 'N = 1: resolveRound never starts the AI'); assert.strictEqual(Q.get('turn'), 'player');
}, [['the opener alternates again', [['firstOpener === null ? "player" : firstOpener;', 'firstOpener === null ? "player" : ((r % 2 === 1) === (firstOpener === "player") ? "player" : "ai");']]],
    ['no coin means the right side opens', [['firstOpener === null ? "player"', 'firstOpener === null ? "ai"']]],
    ['the coin winner is recorded on the wrong side', [['firstOpener = side === "right" ? "ai" : "player";', 'firstOpener = side === "right" ? "player" : "ai";']]],
    ['routeAfterTurn routes to the wrong side', [['if (openerOfRound(roundNum) !== team) { setTimeout(resolveRound, ms); return; }', 'if (openerOfRound(roundNum) === team) { setTimeout(resolveRound, ms); return; }']]],
    ['resolveRound never starts the right side as opener', [['if (TEAM_N > 1 && openerOfRound(roundNum) === "ai") { turn = "busy"; triggerAITurn(); return; }', 'if (false) { turn = "busy"; triggerAITurn(); return; }']]],
    ['one unit per team also uses the alternating route', [['if (TEAM_N > 1) { routeAfterTurn(team, team === "player" ? 1000 : 800); return; }', 'if (true) { routeAfterTurn(team, team === "player" ? 1000 : 800); return; }']]]]);

rule2('comeback: a real hit takes underdog x (1 + pity), never more than 2.3 in total (Comeback.finalDamage); the wave and the swarm use the same capped numbers; the pity charge resets after a hit; none of it at N = 1', mk => {
  const hit = (N, ownHp, misses, hero) => {
    const P = mk({ team: N }); P.reset();
    P.place('left', [300, 450, 600].slice(0, N), ownHp); P.place('right', [1300, 1450, 1600].slice(0, N), 300);
    P.eval('pityMisses.player = ' + misses);
    P.launch(P.projectile({ team: 'player', hero: hero || 'skeleton', x: 1300, y: GY - 60 })); P.run(5);
    return P;
  };
  const dmg = P => { const u = P.units('right')[0]; return r1(u.maxHp - u.hp); };
  const SK = 24;                                                          // skeleton javelin (22 until 2026-11-17, 24 since the balanced role +7 percent of 2026-11-18); checked below against the page profile; the pins below are SK times the comeback factor
  assert.strictEqual(mk({ team: 3 }).get('HERO_PROFILES').skeleton.dmg, SK, 'fixture: skeleton dmg');
  near(dmg(hit(3, 100, 0, 'skeleton')), SK, 'equal shares, no misses: x1');
  near(dmg(hit(3, 10, 0)), SK * 2, 'own share 0.1: underdog x2');
  near(dmg(hit(3, 75, 0)), SK * 1.5, 'own share 0.75 vs 1: deficit 0.25 -> x1.5');
  near(dmg(hit(3, 100, 2)), SK * 1.8, 'two missed throws: pity x1.8');
  near(dmg(hit(3, 75, 1)), SK * 2.1, 'underdog x1.5 times pity x1.4 = x2.1 (below the cap)');
  near(dmg(hit(3, 10, 4)), SK * 2.3, 'x2 x 2.6 = 5.2 is capped at x2.3');
  near(dmg(hit(3, 10, 1)), SK * 2.3, 'x2 x 1.4 = 2.8 is capped at x2.3');
  near(dmg(hit(3, 100, 10)), SK * 2.3, 'pity alone: 2.6 is capped at x2.3');
  assert.strictEqual(hit(3, 10, 4).get('pityMisses').player, 0, 'a hit uses up the pity charge');
  near(dmg(hit(1, 10, 4)), SK, 'N = 1: no comeback at all');
  // the wave and the swarm of one projectile share the capped numbers
  const P = mk({ team: 3 }); P.reset(); const D = P.get('HERO_PROFILES').bride.dmg;
  P.place('left', [300, 450, 600], 10); P.place('right', [1520, 1100, 1900], 300); P.eval('pityMisses.player = 4');
  P.launch(P.projectile({ team: 'player', hero: 'bride', x: 1500, y: GY - 20, extra: { ultThrow: true, ultSwarm: true } })); P.run(5);
  const R = P.units('right');
  near(r1(R[1].maxHp - R[1].hp), r1(r1(D * 1.3) * 2.3), 'swarm on a far unit is capped at x2.3'); near(r1(R[2].maxHp - R[2].hp), r1(r1(D * 1.3) * 2.3));
  near(r1(R[0].maxHp - R[0].hp), r1(D * 2.3) + r1(r1(D * 1.3) * 2.3), 'primary: capped wave + capped swarm');
}, [{ label: 'the cap constant is 9', e: { files: { 'js/comeback.js': [['var MAX_TOTAL = 2.3;', 'var MAX_TOTAL = 9;']] } } },
    { label: 'finalDamage has no cap', e: { files: { 'js/comeback.js': [['Math.min(MAX_TOTAL, underdogMultiplier(ownShare, enemyShare) * (1 + pityBonus(missCount)))', 'underdogMultiplier(ownShare, enemyShare) * (1 + pityBonus(missCount))']] } } },
    { label: 'the page bypasses Comeback.finalDamage with an uncapped formula', e: { page: [['return Comeback.finalDamage(x, c.own, c.foe, c.misses); };', 'return Math.round(x * Comeback.underdogMultiplier(c.own, c.foe) * (1 + Comeback.pityBonus(c.misses)) * 10) / 10; };']] } },
    { label: 'the page ignores the comeback', e: { page: [['return Comeback.finalDamage(x, c.own, c.foe, c.misses); };', 'return x; };']] } },
    { label: 'comeback also at N = 1', e: { page: [['if (TEAM_N > 1) dmgNow = cbDmg(dmgNow, p);', 'dmgNow = cbDmg(dmgNow, p);']] } },
    { label: 'the swarm skips the comeback', e: { page: [['const swarmFinal = TEAM_N > 1 ? cbDmg(swarm, p) : swarm;', 'const swarmFinal = swarm;']] } }].map(m => [m.label, m.e]));

// ---------------------------------------------------------------- finish
const ms = Date.now() - t0;
console.log('test_page_team_exec: ' + passed + ' ok, ' + failed + ' failed (' + (ms / 1000).toFixed(2) + ' s)');
if (failed) {
  try {
    const dir = path.join(__dirname, '..', 'logs_local'); fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'test_page_team_exec.log'), results.filter(r => r.startsWith('FAIL')).join('\n') + '\n');
  } catch (e) { /* logging is best effort */ }
  process.exitCode = 1;
}
