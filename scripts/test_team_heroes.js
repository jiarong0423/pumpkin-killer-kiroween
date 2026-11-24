#!/usr/bin/env node
'use strict';
// Team heroes (owner 2026-11-17: each unit of a team has its own hero, no hero twice in a team, the slots are filled automatically, a hero picked in the team is locked,
// the opponent team has distinct heroes too). Runs the REAL index.html script in the Node vm (scripts/page_harness.js); every rule also runs against a mutant that must fail.
const assert = require('assert');
const { loadPage } = require('./page_harness');
let passed = 0, failed = 0;
function rule(name, scenario, mutants) {
  const run = (label, fn) => { try { fn(); passed++; console.log('ok   - ' + label); } catch (e) { failed++; process.exitCode = 1; console.error('FAIL - ' + label + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n       ') : e)); } };
  run(name, () => scenario(loadPage({ team: 3 })));
  for (const [label, edits] of mutants) {
    run(name + ' [negative: ' + label + ' must be caught]', () => {
      const M = loadPage({ team: 3, mutate: edits });
      let caught = null; try { scenario(M); } catch (e) { caught = e; }
      assert.ok(caught, 'mutant survived: ' + label);
      assert.ok(caught instanceof assert.AssertionError, 'mutant died for the wrong reason: ' + caught);
    });
  }
}
const distinct = a => new Set(a).size === a.length;

rule('auto-fill: a 3-unit team starts with the picked hero and fills the other slots with different heroes in the fixed order; the picked hero stays slot 0', P => {
  P.eval('pickedHero = "bat"; teamPick = ["bat"]; fillTeamPick()');
  assert.deepStrictEqual(Array.from(P.get('teamPick')), ['bat', 'skeleton', 'wizard']);
  assert.strictEqual(P.get('pickedHero'), 'bat');
  P.eval('pickedHero = "hag"; teamPick = ["hag"]; fillTeamPick()');
  assert.deepStrictEqual(Array.from(P.get('teamPick')), ['hag', 'skeleton', 'wizard']);
}, [['the fill ignores the hero order and repeats the picked hero', [['ids.forEach(id => { if (out.length < teamSizeNow() && out.indexOf(id) < 0) out.push(id); });', 'ids.forEach(id => { if (out.length < teamSizeNow()) out.push(pickedHero); });']]]]);

rule('no hero twice: a list with a repeated hero is repaired to distinct heroes', P => {
  P.eval('pickedHero = "bat"; teamPick = ["bat", "bat", "wizard"]; fillTeamPick()');
  const t = Array.from(P.get('teamPick'));
  assert.ok(distinct(t) && t.length === 3 && t[0] === 'bat' && t.includes('wizard'), 'team ' + t);
}, [['the repair keeps repeated heroes', [['if (HERO_PROFILES[h] && out.indexOf(h) < 0) out.push(h);', 'if (HERO_PROFILES[h]) out.push(h);']]]]);

rule('lock: a hero already in another slot of the team cannot be picked for this slot; a free hero can', P => {
  P.eval('pickedHero = "skeleton"; teamPick = ["skeleton", "wizard", "bat"]; activeSlot = 1; buildStartScreen = function () {}');
  P.eval('selectPickedHero("bat")');   // slot 2 holds it: locked
  assert.deepStrictEqual(Array.from(P.get('teamPick')), ['skeleton', 'wizard', 'bat']);
  P.eval('selectPickedHero("hag")');
  assert.deepStrictEqual(Array.from(P.get('teamPick')), ['skeleton', 'hag', 'bat']);
  assert.strictEqual(P.eval('heroLockedByTeam("skeleton")'), true);
  assert.strictEqual(P.eval('heroLockedByTeam("hag")'), false, 'the hero of the slot being edited is not locked against itself');
}, [['no lock', [['if (heroLockedByTeam(heroId)) return;', '']]]]);

rule('slot 0 is the picked hero: picking for slot 0 changes pickedHero, picking for another slot does not', P => {
  P.eval('pickedHero = "skeleton"; teamPick = ["skeleton", "wizard", "bat"]; activeSlot = 0; buildStartScreen = function () {}; selectPickedHero("hag")');
  assert.strictEqual(P.get('pickedHero'), 'hag');
  P.eval('activeSlot = 2; selectPickedHero("knight")');
  assert.strictEqual(P.get('pickedHero'), 'hag');
  assert.deepStrictEqual(Array.from(P.get('teamPick')), ['hag', 'wizard', 'knight']);
}, [['every slot changes pickedHero', [['if (activeSlot === 0) pickedHero = heroId;', 'pickedHero = heroId;']]]]);

rule('opponent team: N distinct heroes, the first one is the drawn class, the daily match is deterministic', P => {
  for (let i = 0; i < 60; i++) { const l = Array.from(P.eval('drawRightHeroes(AI_CLASSES[' + (i % 8) + '])')); assert.ok(distinct(l) && l.length === 3 && l[0] === P.eval('AI_CLASSES[' + (i % 8) + ']'), 'opponent ' + l); }
  P.eval('dailyCode = 20261117');
  assert.deepStrictEqual(Array.from(P.eval('drawRightHeroes("hag")')), ['hag', 'skeleton', 'wizard']);
}, [['the shuffle may repeat the first hero', [['const rest = AI_CLASSES.filter(h => h !== first);', 'const rest = AI_CLASSES.slice();']]]]);

rule('units wear their own heroes: after startMatch-style assignment each left unit has its slot hero and its own hp; the active unit sets currentHero', P => {
  P.eval('leftHeroes = ["wizard", "bat", "knight"]; rightHeroes = ["hag", "reaper", "bride"]; unitsOf("left").forEach((u, i) => { u.profile = leftHeroes[i]; }); unitsOf("right").forEach((u, i) => { u.profile = rightHeroes[i]; }); applyClassStats()');
  const H = P.get('HERO_PROFILES');
  P.units('left').forEach((u, i) => { const h = H[['wizard', 'bat', 'knight'][i]]; assert.strictEqual(u.maxHp, P.eval('unitStartHp(HERO_PROFILES.' + ['wizard', 'bat', 'knight'][i] + ')'), 'hp of left unit ' + i); assert.ok(h); });
  P.units('right').forEach((u, i) => { assert.strictEqual(u.maxHp, P.eval('unitStartHp(HERO_PROFILES.' + ['hag', 'reaper', 'bride'][i] + ')'), 'hp of right unit ' + i); });
  P.setActive('left', 2);
  assert.strictEqual(P.get('currentHero'), 'knight');
  P.setActive('left', 1);
  assert.strictEqual(P.get('currentHero'), 'bat');
}, [['the acting hero does not follow the active unit', [['if (unit.profile) currentHero = unit.profile;', '']]],
    ['every unit gets the first hero hp', [['const hp0 = HERO_PROFILES[leftHeroes[i]] || pp; if (hp0)', 'const hp0 = pp; if (hp0)']]]]);

(function oneUnit() {
  try {
    const P = loadPage({ team: 1 });
    P.eval('pickedHero = "bat"; teamPick = ["bat"]; fillTeamPick()');
    assert.deepStrictEqual(Array.from(P.get('teamPick')), ['bat']);
    assert.strictEqual(P.eval('heroLockedByTeam("skeleton")'), false);
    assert.deepStrictEqual(Array.from(P.eval('drawRightHeroes("hag")')).length >= 1, true);
    assert.deepStrictEqual(Array.from(P.get('rightHeroes')), []);
    passed++; console.log('ok   - one unit per team: one slot, nothing locked, no hero lists');
  } catch (e) { failed++; process.exitCode = 1; console.error('FAIL - one unit per team\n       ' + e); }
})();
console.log('test_team_heroes: ' + passed + ' ok, ' + failed + ' failed');
