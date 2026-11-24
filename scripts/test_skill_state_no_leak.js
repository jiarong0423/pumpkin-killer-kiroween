#!/usr/bin/env node
'use strict';
// Ledger 2026-11-22, owner: "I did not choose an item effect and it chose for me", "I attacked normally and it threw a bomb". The human and both computers share ONE `selectedSkill`; a computer that used heavy / double left it set and the human's next
// NORMAL throw became a heavy pumpkin bomb (and used the human's charge). This pins (1) both computer throw paths put the selection back (the double after its SECOND shell), (2) the helper resets state AND button, (3) the behaviour: heavy left over -> a normal human
// throw is a bomb (the bug), after clearSkillSelection() it is a plain shot.
const assert = require('assert'), fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
assert.match(html, /function clearSkillSelection\(\) \{[\s\S]{0,420}selectedSkill = "normal";[\s\S]{0,300}skill-normal/, 'helper resets the state and the highlighted button');
assert.match(html, /executeThrow\("ai", Math\.min\(MAX_POWER, aim\.power \* 1\.04\), aim\.angle, aiShooter\); clearSkillSelection\(\); \}, 260\); else clearSkillSelection\(\);/, 'right computer: clear after the second shell, or at once');
assert.match(html, /executeThrow\("player", Math\.min\(MAX_POWER, shot\.power \* 1\.04\), shot\.angle, leftShooter\); clearSkillSelection\(\); \}, 260\); else clearSkillSelection\(\);/, 'left computer: same');
function humanNormalThrow(skillLeftOver, clear) {
  const P = loadPage({ team: 1, seed: 5 }); P.reset(); P.clearWeather(); P.place('left', [300]); P.place('right', [1400]);
  P.eval('wind = 0; wallHp = 0; matchStarted = true; currentHero = "skeleton"; Math.random = function () { return 0.05; };');
  P.eval('selectedSkill = ' + JSON.stringify(skillLeftOver) + ';'); if (clear) P.eval('clearSkillSelection();');
  P.eval('turn = "player"; hitStop = 0; executeThrow("player", 60, 45);');
  const p = P.get('projectiles')[0]; return { weapon: p.weapon, heavy: !!p.isHeavy, skill: P.eval('selectedSkill') };
}
const leaked = humanNormalThrow('heavy', false), fixed = humanNormalThrow('heavy', true), plain = humanNormalThrow('normal', false);
assert.ok(leaked.heavy && leaked.weapon === 'proj_pumpkin', 'the test would catch the leak: a leftover heavy makes a bomb');
assert.ok(!fixed.heavy && fixed.weapon === 'proj_spear' && fixed.skill === 'normal', 'after clearSkillSelection the same throw is a plain spear');
assert.ok(!plain.heavy && plain.weapon === 'proj_spear', 'control: a plain throw is a spear');
console.log('test_skill_state_no_leak: ok (leftover heavy -> ' + leaked.weapon + ', cleared -> ' + fixed.weapon + ')');
