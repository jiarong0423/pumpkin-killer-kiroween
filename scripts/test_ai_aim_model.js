#!/usr/bin/env node
'use strict';
// The computer's aim after the weakening of 2026-11-17 (owner: 'three items together' plus 'so it can see the formula'):
//  1. a random whole-number angle from 25 to 80 degrees on every shot, flat and lobbed;
//  2. power from the AI's OWN flight model (gravity and wind coefficient a few percent off, drawn once per match and per side), not from simulateLandingX or the game's wind constants;
//  3. a wind misread that grows with the wind;
//  4. a scale it learns only from where its own earlier shots landed.
// Pins the shape of the new code; the hit-rate bands are in scripts/test_page_ai_hit_rates.js.
const assert = require('assert');
const { loadPage } = require('./page_harness');

let passed = 0;
function check(name, fn) { try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { process.exitCode = 1; console.error('FAIL - ' + name + '\n       ' + String(e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n       ') : e)); } }
const sd = a => { const m = a.reduce((s, v) => s + v, 0) / a.length; return Math.sqrt(a.reduce((s, v) => s + (v - m) * (v - m), 0) / a.length); };

function page(level) {
  const P = loadPage({ team: 1, seed: 77 });
  P.reset(); P.clearWeather();
  P.eval('seats = { left: "ai", right: "ai", level: { left: ' + JSON.stringify(level) + ', right: ' + JSON.stringify(level) + ' } }; aiModelBy.left = aiModelBy.right = null; aiCals.left = aiCals.right = 1;');
  P.place('left', [400], null); P.place('right', [1500], null);
  return P;
}

check('the AI never reads the real flight: aiPlanShot, aiModelLandingX, normalAiAim and leftAiShot name neither simulateLandingX, estimatePowerForTarget, windAccelFor nor the game constants', () => {
  const P = page('normal');
  for (const fn of ['aiPlanShot', 'aiModelLandingX', 'normalAiAim', 'leftAiShot', 'aiModelFor', 'aiSeenWind', 'aiMuzzle']) {
    const src = P.eval(fn + '.toString()');
    for (const banned of ['simulateLandingX', 'estimatePowerForTarget', 'windAccelFor', 'WIND_TAIL', 'WIND_HEAD', 'GRAVITY', 'predictPath', 'relayFlightLanding']) assert.ok(!src.includes(banned), fn + ' mentions ' + banned);
  }
});

check('every shot has a whole-number angle between 25 and 80 degrees; flat (under 35) and steep (over 70) angles both occur', () => {
  const P = page('normal'), angles = [];
  for (let i = 0; i < 600; i++) angles.push(P.eval('leftAiShot()').angle);
  assert.ok(angles.every(a => Number.isInteger(a) && a >= 25 && a <= 80), 'range: ' + [Math.min(...angles), Math.max(...angles)]);
  assert.ok(angles.some(a => a < 35) && angles.some(a => a > 70), 'flat and lobbed both appear');
  const right = []; for (let i = 0; i < 300; i++) right.push(P.eval('normalAiAim({ enemy_position: 400, wind: 0 })').angle);
  assert.ok(right.every(a => Number.isInteger(a) && a >= 25 && a <= 80) && new Set(right).size > 30, 'the right seat uses the same rule');
});

check('the flight model is drawn once per match and per side, a few percent off, and a new match draws again', () => {
  const P = page('normal');
  const a = P.eval('aiModelFor("left")'), b = P.eval('aiModelFor("left")');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(a)), JSON.parse(JSON.stringify(b)), 'same model on the second call');
  const gs = [], ws = [];
  for (let i = 0; i < 300; i++) { P.eval('aiModelBy.left = null'); const m = P.eval('aiModelFor("left")'); gs.push(m.g); ws.push(m.w); }
  assert.ok(gs.every(g => Math.abs(g) <= 0.03 + 1e-9) && ws.every(w => Math.abs(w) <= 0.06 + 1e-9), 'normal level: gravity within 3 percent, wind coefficient within 6 percent');
  assert.ok(gs.some(g => g > 0.01) && gs.some(g => g < -0.01) && sd(gs) > 0.008, 'both signs, a real spread');
  P.eval('aiModelBy.left = {g: 0.02, w: 0.01}; aiCals.left = 1.2; resetGame()');
  assert.strictEqual(P.eval('aiModelBy.left'), null, 'resetGame clears the model');
  assert.strictEqual(P.eval('aiCals.left'), 1, 'and the learned scale');
});

check('the model errors follow the level (easy a little more, hard less)', () => {
  const spread = level => { const P = page(level), g = []; for (let i = 0; i < 400; i++) { P.eval('aiModelBy.left = null'); g.push(Math.abs(P.eval('aiModelFor("left")').g)); } return Math.max(...g); };
  const e = spread('easy'), n = spread('normal'), h = spread('hard');
  assert.ok(e > n && n > h, 'max |g| easy ' + e.toFixed(4) + ' > normal ' + n.toFixed(4) + ' > hard ' + h.toFixed(4));
});

check('the wind misread grows with the wind: no wind leaves only the fixed part, a strong wind a larger spread', () => {
  const P = page('normal'), err = w => { const out = []; for (let i = 0; i < 3000; i++) out.push(P.eval('aiSeenWind("left", ' + w + ')') - w); return out; };
  const s0 = sd(err(0)), s2 = sd(err(2)), s4 = sd(err(4));
  assert.ok(s0 < s2 && s2 < s4, 'spread at wind 0, 2, 4: ' + [s0, s2, s4].map(v => v.toFixed(3)));
  assert.ok(s4 > 1.6 * s0, 'a strong wind is misread clearly more than no wind (' + s4.toFixed(3) + ' vs ' + s0.toFixed(3) + ')');
});

check('the AI learns a scale from its own landings: a model that makes every shot too short is corrected towards more reach', () => {
  const P = page('hard');
  P.eval('aiModelBy.left = { g: -0.05, w: 0 }');   // believes gravity is 5 percent weaker than it is: it plans too little power, the real shots fall short
  const before = P.eval('aiCals.left');
  let moved = 0;
  for (let i = 0; i < 40 && moved < 3; i++) {
    P.reset(); P.clearWeather(); P.place('left', [400], null); P.place('right', [1500], null);
    P.eval('wallHp = 0');   // no fence: a flat shot would end on it and teach nothing
    const shot = P.eval('leftAiShot()');
    const x0 = P.eval('aiCals.left');
    P.eval('executeThrow("player", ' + shot.power + ', ' + shot.angle + ')');
    P.run(900, 0.01);
    if (P.eval('aiCals.left') !== x0) moved++;
  }
  assert.ok(moved >= 1, 'the scale moved after a ground landing');
  assert.ok(P.eval('aiCals.left') > before, 'scale ' + before + ' -> ' + P.eval('aiCals.left'));
});

check('the three levels exist and the multipliers are ordered easy > normal > hard with normal = 1', () => {
  const P = page('normal');
  const m = P.eval('AI_LEVEL_MULTIPLIERS');
  assert.ok(m.easy > m.normal && m.normal > m.hard && m.hard > 0, 'ordered easy > normal > hard (values 2.25 / 0.52 / 0.27 since MAX_POWER 115 on 2026-11-19)');
  assert.deepStrictEqual([m.easy, m.normal, m.hard], [2.25, 0.52, 0.27]);
});
console.log('test_ai_aim_model: ' + passed + ' checks passed');
