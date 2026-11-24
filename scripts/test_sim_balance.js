'use strict';
/*
 * Tests for scripts/sim_balance.js (the headless balance simulator). Spec: .kiro/specs/balance-sim/requirements.md.
 * Node `assert` only. index.html and shared/constants.json are read, never written.
 * Run: node scripts/test_sim_balance.js        Exit code 1 if any check fails.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const CS = require(path.join(__dirname, '..', 'js', 'class_stats.js'));
const Ultimate = require(path.join(__dirname, '..', 'js', 'ultimate.js'));
const Sim = require(path.join(__dirname, 'sim_balance.js'));

const KEYS = CS.CLASS_KEYS;
const I = Sim.internals;
const C = Sim.CONSTANTS;
const INDEX_HTML = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SHARED = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'constants.json'), 'utf8'));

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }
const near = (a, b, tol, label) => assert.ok(Math.abs(a - b) <= tol, (label || '') + ' got ' + a + ', want ' + b + ' +-' + tol);

// ---------------------------------------------------------------------------
// the physics is the physics of index.html

test('constants equal index.html and shared/constants.json', () => {
  assert.ok(/const GROUND_Y = 860;/.test(INDEX_HTML));
  assert.ok(/const FENCE_X = 960;/.test(INDEX_HTML));
  assert.ok(/const FENCE_W = 238;/.test(INDEX_HTML));
  assert.ok(/const FENCE_H = 282;/.test(INDEX_HTML));
  assert.ok(/const GRAVITY = 980\.0;/.test(INDEX_HTML));
  assert.ok(/const WIND_TAIL = 56, WIND_HEAD = 84;/.test(INDEX_HTML));
  assert.ok(/const v0 = power \* 13\.8;/.test(INDEX_HTML));
  assert.ok(/const DICE_STEP_PX = 36;/.test(INDEX_HTML));
  assert.ok(/p\.vx \+= windAccelFor\(effWind\(\), /.test(INDEX_HTML));   // the storm adds to the wind magnitude through effWind() (2026-11-15)
  assert.ok(/p\.vy \+= GRAVITY \* dt;/.test(INDEX_HTML));
  assert.ok(/Math\.abs\(p\.x - opp\.x\) <= \(p\.weapon === "proj_soundwave" \? WAVE_HALF_WIDTH : \(oppReaper \? 57 : 70\) \+ hitR\) && p\.y >= opp\.y - \(p\.weapon === "proj_soundwave" \? 40 : \(oppReaper \? 165 : 190\) \+ hitR\) && p\.y <= opp\.y \+ \(p\.weapon === "proj_soundwave" \? 0 : hitR\)/.test(INDEX_HTML), 'hit box (default 70 x 190; the necromancer, id reaper, is slimmer: 50 x 165, owner 2026-11-15; the sound wave of the bride is 105 px wide)');
  assert.ok(/wallHp = Math\.max\(0, wallHp - WALL_HIT_DMG\);/.test(INDEX_HTML) && /const WALL_HIT_DMG = 8;/.test(INDEX_HTML), 'fence damage');
  assert.ok(/let wallHp = 100;/.test(INDEX_HTML), 'fence HP');
  assert.ok(/\(Math\.random\(\) - 0\.5\) \* 8\.0\)\.toFixed\(1\)/.test(INDEX_HTML), 'wind reroll');
  assert.ok(/const lo = d\.owner === "player" \? 110 : 1280, hi = d\.owner === "player" \? 640 : 1810;/.test(INDEX_HTML), 'move range');
  assert.ok(/const newPlayerX = Determinism\.startX\(matchSeed, 0, 0\);/.test(INDEX_HTML) && /const newAiX = Determinism\.startX\(matchSeed, 1, 0\);/.test(INDEX_HTML));
  // the knight's bounce numbers
  assert.ok(/p\.vx = Math\.max\(-400, Math\.min\(400, \(opp\.x - p\.x\) \/ 0\.62\)\); p\.vy = -330;/.test(INDEX_HTML), 'hop back');
  assert.ok(/T\("toast\.shieldStuck"\)/.test(INDEX_HTML) && /盾插進地板，不能再彈了/.test(require('fs').readFileSync(require('path').join(__dirname, '..', 'assets', 'i18n', 'zh-TW.json'), 'utf8')), 'the shield ends on the ground (text now lives in the i18n dictionary, 2026-11-15)');
  assert.ok(/p\.vx = -p\.vx \* 0\.3; p\.vy = -Math\.abs\(p\.vy\) \* 0\.3 - 90;/.test(INDEX_HTML), 'fence bounce');
  assert.ok(/p\.hitCool = 0\.3;/.test(INDEX_HTML));
  assert.ok(/const WIZARD_MUZZLE = \{ fwd: 70, up: 118 \};/.test(INDEX_HTML));
  assert.strictEqual(C.GROUND_Y, SHARED.GROUND_Y);
  assert.strictEqual(C.GRAVITY, SHARED.GRAVITY);
  assert.strictEqual(C.V0_PER_POWER, SHARED.V0_PER_POWER);
  assert.strictEqual(C.FENCE_X, SHARED.FENCE_X);
  assert.strictEqual(C.FENCE_W, SHARED.FENCE_W);
  assert.strictEqual(C.FENCE_H, SHARED.FENCE_H);
  assert.strictEqual(C.WIND_MAX, SHARED.WIND_MAX);
  assert.strictEqual(C.ANGLE_DEFAULT, SHARED.THROW_ANGLE_DEFAULT);
  assert.strictEqual(C.DT, 1 / 60);
  assert.strictEqual(C.WIND_TAIL, 56);
  assert.strictEqual(C.WIND_HEAD, 84);
  assert.deepStrictEqual(I.MOVE_RANGE, { a: [110, 640], b: [1280, 1810] });
  assert.deepStrictEqual(I.START_RANGE, { a: [220, 620], b: [1280, 1680] });
});

test('launch point per class equals index.html (hand offsets)', () => {
  assert.strictEqual(CS.CLASSES.wizard.launch.fwd, 70);
  assert.strictEqual(CS.CLASSES.wizard.launch.up, 118);
  assert.strictEqual(CS.CLASSES.knight.launch.fwd, 51);
  assert.strictEqual(CS.CLASSES.knight.launch.up, 73);
  for (const k of ['skeleton', 'bat']) assert.deepStrictEqual(CS.CLASSES[k].launch, { fwd: 58, up: 110 });
  assert.ok(/const fwd = isWizard \? WIZARD_MUZZLE\.fwd : \(isShield \? 51 : 58\);/.test(INDEX_HTML));
  assert.ok(/const startY = u\.y - \(isWizard \? WIZARD_MUZZLE\.up : \(isShield \? 73 : 110\)\);/.test(INDEX_HTML));
});

test('simulateLandingX: close to the closed-form parabola without wind, mirrored for the right side, wind moves it the right way', () => {
  const sk = CS.CLASSES.skeleton;
  const left = I.makeUnit(sk, 'a', 300);
  const right = I.makeUnit(sk, 'b', 1600);
  const g = 980;
  const v = 65 * 13.8;
  const rad = 54 * Math.PI / 180;
  const vy = v * Math.sin(rad);
  const tFlight = (vy + Math.sqrt(vy * vy + 2 * g * 110)) / g;
  const analytic = 300 + 58 + v * Math.cos(rad) * tFlight;
  const got = Sim.simulateLandingX(sk, left, 65, 54, 0);
  assert.ok(Math.abs(got - analytic) / (analytic - 358) < 0.02, 'landing ' + got + ' vs closed form ' + analytic);
  const mirrored = Sim.simulateLandingX(sk, right, 65, 54, 0);
  near(1600 - mirrored, got - 300, 1e-6, 'mirror');
  // a positive wind blows toward +x: it pushes the left side's shot farther and the right side's shot shorter
  const l0 = Sim.simulateLandingX(sk, left, 65, 54, 0);
  assert.ok(Sim.simulateLandingX(sk, left, 65, 54, 4) > l0 + 200);
  assert.ok(Sim.simulateLandingX(sk, left, 65, 54, -4) < l0 - 300);
  near(Sim.simulateLandingX(sk, right, 65, 54, -4) - 1600, -(Sim.simulateLandingX(sk, left, 65, 54, 4) - 300), 1e-6, 'mirror under wind');
  // the tailwind shift is about 0.5 * 56 * 4 * t^2 and the headwind shift 0.5 * 84 * 4 * t^2 (client acceleration model, owner 2026-11-16: a clear difference)
  near(Sim.simulateLandingX(sk, left, 65, 54, 4) - l0, 0.5 * 56 * 4 * tFlight * tFlight, 0.06 * 0.5 * 56 * 4 * tFlight * tFlight, 'tailwind shift');
  near(l0 - Sim.simulateLandingX(sk, left, 65, 54, -4), 0.5 * 84 * 4 * tFlight * tFlight, 0.08 * 0.5 * 84 * 4 * tFlight * tFlight, 'headwind shift');
  assert.ok((l0 - Sim.simulateLandingX(sk, left, 65, 54, -4)) > 1.3 * (Sim.simulateLandingX(sk, left, 65, 54, 4) - l0), 'headwind holds back clearly more than tailwind carries');
  const bride = CS.CLASSES.bride;
  // The synchronized bride launch uses the same fixed-step scale as the page.
  near(Sim.simulateLandingX(bride, I.makeUnit(bride, 'a', 300), 65, 54, 0), got, 1e-6, 'bride page-scale range');
});

test('solvePower lands on the target (to one step of flight), and says so when full power is not enough', () => {
  const rand = Sim.mulberry32(5);
  for (const k of KEYS) {
    const cls = CS.CLASSES[k];
    for (let n = 0; n < 40; n++) {
      const unit = I.makeUnit(cls, rand() < 0.5 ? 'a' : 'b', 0);
      unit.x = unit.side === 'a' ? 220 + rand() * 400 : 1280 + rand() * 400;
      const target = unit.side === 'a' ? 1280 + rand() * 400 : 220 + rand() * 400;
      const wind = Math.round((rand() - 0.5) * 80) / 10;
      const r = Sim.solvePower(cls, unit, target, 54, wind);
      assert.ok(r.power >= 10 && r.power <= 115 + 1e-9);
      if (r.reachable) {
        // the ground contact is found on a 1/60 s step, so the landing x moves in jumps of up to |vx| / 60 (about 20 px)
        near(Sim.simulateLandingX(cls, unit, r.power, 54, wind), target, 22, k + ' lands');
      } else near(r.power, 115, 1e-9);
    }
  }
  const hunch = CS.CLASSES.hunchback;
  const far = I.makeUnit(hunch, 'a', 220);
  assert.strictEqual(Sim.solvePower(hunch, far, 1680, 54, -4).reachable, false, 'the slow bell cannot cross the field into a headwind');
  assert.strictEqual(Sim.solvePower(CS.CLASSES.skeleton, I.makeUnit(CS.CLASSES.skeleton, 'a', 500), 1280, 54, 0).reachable, true);
});

// ---------------------------------------------------------------------------
// the rules, one at a time, with projectiles placed by hand

function scene(aKey, bKey, table) {
  const t = table || CS.CLASSES;
  const a = I.makeUnit(t[aKey], 'a', 400);
  const b = I.makeUnit(t[bKey], 'b', 1500);
  const m = {
    rand: Sim.mulberry32(1), wind: 0, wallHp: 100, round: 1, throwId: 1, over: false, winnerSide: null, angle: 54,
    aimError: 0, shieldRule: 'current', ultimates: 'bat', ledger: Ultimate.createLedger({ sides: ['a', 'b'] })
  };
  return { m, a, b };
}
function rec() { return { throwId: 1, dealt: 0, hit: false, fence: false, ult: false }; }
// a projectile of thrower at (x, y), standing still; it falls under gravity only
function drop(s, thrower, x, y, dmg) {
  const p = I.makeProjectile(s.m, thrower, thrower.cls, 50, 54, dmg === undefined ? thrower.cls.dmg : dmg, false);
  p.x = x; p.y = y; p.vx = 0; p.vy = 0;
  return p;
}
function play(s, thrower, foe, projectiles) {
  const r = rec();
  I.resolveThrow(s.m, thrower, foe, projectiles, r);
  return r;
}

test('a point weapon deals its damage once, adds one pip, and a miss on the ground deals nothing', () => {
  const s = scene('wizard', 'skeleton');
  const r = play(s, s.a, s.b, [drop(s, s.a, s.b.x + 30, 760)]);
  assert.strictEqual(s.b.hp, 150 - 36);   // wizard dmg 36 since 2026-11-18 (glass cannon +10 percent; 33 on 2026-11-17, 30 before)
  assert.strictEqual(r.dealt, 36);
  assert.strictEqual(s.m.ledger.getState('a').ult_pips, 1);
  const s2 = scene('wizard', 'skeleton');
  const r2 = play(s2, s2.a, s2.b, [drop(s2, s2.a, s2.b.x + 71, 760)]);   // just outside the 70 px half width
  assert.strictEqual(s2.b.hp, 150);
  assert.strictEqual(r2.hit, false);
  assert.strictEqual(s2.m.ledger.getState('a').ult_pips, 0);
  const s3 = scene('wizard', 'skeleton');
  play(s3, s3.a, s3.b, [drop(s3, s3.a, s3.b.x, 600)]);   // above the 190 px body, falls to the ground at the unit's x? it passes through the body
  assert.ok(s3.b.hp < 150, 'a shot falling straight through the body hits it');
});

test('the fence takes 8 per hit, blocks the shot, and stops blocking at 0 HP', () => {
  const s = scene('wizard', 'skeleton');
  const r = play(s, s.a, s.b, [drop(s, s.a, 960, 700)]);
  assert.strictEqual(s.m.wallHp, 92);
  assert.strictEqual(r.fence, true);
  assert.strictEqual(s.b.hp, 150);
  s.m.wallHp = 6;
  play(s, s.a, s.b, [drop(s, s.a, 960, 700)]);
  assert.strictEqual(s.m.wallHp, 0);
  const r2 = play(s, s.a, s.b, [drop(s, s.a, 960, 700)]);
  assert.strictEqual(s.m.wallHp, 0, 'a broken fence stays at 0');
  assert.strictEqual(r2.fence, false, 'and no longer blocks');
  const s2 = scene('wizard', 'skeleton');
  const over = drop(s2, s2.a, 900, 440);   // crosses the (now 238 px wide) fence well above its top (y = 578 since the collision equals the drawn gate, 2026-11-18; it was 610) and keeps going
  over.vx = 500;
  play(s2, s2.a, s2.b, [over]);
  assert.strictEqual(s2.m.wallHp, 100, 'a shot that flies over the top does not touch the fence');
  const s3 = scene('wizard', 'skeleton');
  const under = drop(s3, s3.a, 900, 608);  // same speed, 30 px below the new top (578): blocked
  under.vx = 500;
  play(s3, s3.a, s3.b, [under]);
  assert.strictEqual(s3.m.wallHp, 92);
});

test('frost curse: a surviving victim gets weak for 2 throws at the class cut; a kill does not', () => {
  for (const [table, cut] of [[CS.CLASSES, 0.15], [CS.PROVISIONAL, 0.3]]) {
    const s = scene('skeleton', 'wizard', table);
    play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
    assert.strictEqual(s.b.weak, 2);
    assert.strictEqual(s.b.weakCut, cut);
    assert.strictEqual(s.b.hp, table.wizard.hp - table.skeleton.dmg);
  }
  const k = scene('skeleton', 'wizard');
  k.b.hp = 10;
  play(k, k.a, k.b, [drop(k, k.a, k.b.x, 760)]);
  assert.strictEqual(k.b.hp, 0);
  assert.strictEqual(k.b.weak, 0, 'a dead unit is not cursed');
  assert.strictEqual(k.m.over, true);
  assert.strictEqual(k.m.winnerSide, 'a');
  const other = scene('wizard', 'skeleton');
  play(other, other.a, other.b, [drop(other, other.a, other.b.x, 760)]);
  assert.strictEqual(other.b.weak, 0, 'only the javelin curses');
});

test('reaper flame applies normal damage and refreshes a non-lethal burn for three round starts', () => {
  const s = scene('reaper', 'wizard');
  s.m.stats = { a: { damage: 0, burnDamage: 0 }, b: { damage: 0, burnDamage: 0 } };
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.hp, 124 - 22);   // wizard hp 124 since 2026-11-17 (was 113); reaper dmg 22 since 2026-11-18 (balanced role +7 percent; 21 since the evening of 2026-11-17)
  assert.strictEqual(s.b.burn, 3);
  assert.strictEqual(s.b.burnDamage, 2);
  assert.strictEqual(s.b.burnOwner, 'a');
  I.tickBurns(s.m, { a: s.a, b: s.b });
  assert.strictEqual(s.b.hp, 100);   // 124 - 22 - 2
  assert.strictEqual(s.b.burn, 2);
  assert.strictEqual(s.m.stats.a.burnDamage, 2);
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.burn, 3, 'a later flame refreshes instead of stacking');
  s.b.hp = 1;
  I.tickBurns(s.m, { a: s.a, b: s.b });
  assert.strictEqual(s.b.hp, 1, 'burn alone cannot finish a unit');
  assert.strictEqual(Object.prototype.hasOwnProperty.call(s.a.cls.special, 'execute'), false);
});

test('wizard and bride poison refreshes for two round starts and cannot finish a unit', () => {
  const s = scene('wizard', 'skeleton');
  s.m.stats = { a: { damage: 0, burnDamage: 0 }, b: { damage: 0, burnDamage: 0 } };
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.hp, 114);   // 150 - the wizard's 36 since 2026-11-18 (33 on 2026-11-17, 30 before)
  assert.strictEqual(s.b.poison, 2);
  I.tickPoisons(s.m, { a: s.a, b: s.b });
  assert.strictEqual(s.b.hp, 112);   // 114 - 2
  assert.strictEqual(s.b.poison, 1);
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.poison, 2, 'a later hit refreshes instead of stacking');
  s.b.hp = 1;
  I.tickPoisons(s.m, { a: s.a, b: s.b });
  assert.strictEqual(s.b.hp, 1, 'poison alone cannot finish a unit');
  assert.strictEqual(s.m.winnerSide, null);
});

test('poison, bleed, and burn never reduce a living unit below 1 HP', () => {
  const statusCases = [
    ['poison', 'wizard', 'skeleton', 'applyPoison', 'tickPoisons'],
    ['bleed', 'skeleton', 'wizard', 'applyBleed', 'tickBleeds'],
    ['burn', 'reaper', 'wizard', 'applyBurn', 'tickBurns']
  ];
  for (const [name, attacker, defender, apply, tick] of statusCases) {
    const s = scene(attacker, defender);
    s.m.stats = { a: { damage: 0 }, b: { damage: 0 } };
    const status = s.a.cls.special[name];
    I[apply](s.b, status, 'a');
    s.b.hp = 1;
    I[tick](s.m, { a: s.a, b: s.b });
    assert.strictEqual(s.b.hp, 1, name + ' must leave one HP');
    assert.strictEqual(s.b[name], status.turns - 1, name + ' consumes its round-start tick');
    assert.strictEqual(s.m.over, false, name + ' must not end the match');
  }
});

test('hunchback knockback: 50 px away from the thrower, kept inside the move range, none on a kill', () => {
  const s = scene('hunchback', 'wizard');
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.x, 1550);
  s.b.x = 1790;
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.x, 1810, 'clamped at the edge of the move range (1810 since 2026-11-17)');
  const back = scene('wizard', 'hunchback');
  back.a.x = 300;
  back.b.x = 1500;
  play(back, back.b, back.a, [drop(back, back.b, back.a.x, 760)]);   // the hunchback on the right throws left
  assert.strictEqual(back.a.x, 250, 'pushed away: toward -x');
  const killed = scene('hunchback', 'wizard');
  killed.b.hp = 5;
  play(killed, killed.a, killed.b, [drop(killed, killed.a, killed.b.x, 760)]);
  assert.strictEqual(killed.b.x, 1500);
  const prov = scene('hunchback', 'wizard', CS.PROVISIONAL);
  play(prov, prov.a, prov.b, [drop(prov, prov.a, prov.b.x, 760)]);
  assert.strictEqual(prov.b.x, 1600, 'provisional knockback is 100 px');
});

test('bride wave: 100% to 35 px, 75% to 70 px, 50% to 105 px (cells of 35 px, owner 2026-11-18), then nothing; one target', () => {
  const dmgAt = (dx) => {
    const s = scene('bride', 'knight');
    const r = play(s, s.a, s.b, [drop(s, s.a, s.b.x + dx, 760)]);
    return { dealt: r.dealt, hp: s.b.hp };
  };
  assert.strictEqual(dmgAt(0).dealt, 40);   // bride dmg 40 since 2026-11-18 (glass cannon +10 percent; 36 on the evening of 2026-11-17): 100, 75 and 50 percent
  assert.strictEqual(dmgAt(35).dealt, 40);
  assert.strictEqual(dmgAt(35.1).dealt, 30);
  assert.strictEqual(dmgAt(70).dealt, 30);
  assert.strictEqual(dmgAt(70.1).dealt, 20);
  assert.strictEqual(dmgAt(105).dealt, 20);
  assert.strictEqual(dmgAt(-105).dealt, 20);
  assert.strictEqual(dmgAt(106).dealt, 0, 'outside the wave');
  assert.strictEqual(dmgAt(80).dealt, dmgAt(90).dealt, 'outer band stays at 50%');
});

test('provisional bouquet: bursts on landing, 12 to a unit within 90 px, nothing farther', () => {
  const near90 = scene('bride', 'knight', CS.PROVISIONAL);
  play(near90, near90.a, near90.b, [drop(near90, near90.a, near90.b.x + 85, 850)]);   // lands on the ground 85 px away
  assert.strictEqual(near90.b.hp, 120 - 12);
  const far = scene('bride', 'knight', CS.PROVISIONAL);
  play(far, far.a, far.b, [drop(far, far.a, far.b.x + 95, 850)]);
  assert.strictEqual(far.b.hp, 120);
  const direct = scene('bride', 'knight', CS.PROVISIONAL);
  play(direct, direct.a, direct.b, [drop(direct, direct.a, direct.b.x + 10, 760)]);
  assert.strictEqual(direct.b.hp, 120 - 12, 'a direct hit bursts once');
});

test('bride wave, rule choice: measured at the first touch of the tall body box the falloff almost always bites; at body-centre height it does not', () => {
  const hitWith = (rule) => {
    const s = scene('bride', 'knight');
    s.m.waveRule = rule;
    const p = drop(s, s.a, s.b.x - 100, 680);   // enters the top-left corner of the box, falling at an angle
    p.vx = 200;
    p.vy = 300;
    return play(s, s.a, s.b, [p]).dealt;
  };
  const first = hitWith('first_contact');
  const centre = hitWith('centre');
  console.log('     wave damage for the same shot: first touch ' + first.toFixed(1) + ', body centre ' + centre.toFixed(1));
  assert.ok(first > 0 && centre > first, 'centre ' + centre + ' vs first contact ' + first);
  near(first, CS.waveDamage(CS.CLASSES.bride, -100), 2.5, 'first contact is measured near the edge');
});

test('knight rule A: the ground skip happens once, then the shield ends', () => {
  const s = scene('knight', 'bat');
  s.m.shieldRule = 'A';
  const p = drop(s, s.a, 1200, 858, 30);
  p.rule = 'A'; p.die = 3; p.total = 30; p.freeSkips = 1;
  p.vy = 400;   // falling, and about to touch the ground on the next step
  const pending = [];
  const r = rec();
  assert.strictEqual(I.stepProjectile(s.m, p, s.a, s.b, r, pending, 0), false, 'first ground contact: it skips');
  assert.strictEqual(p.freeSkips, 0);
  assert.ok(p.vy < 0, 'and goes up again');
  let steps = 0;
  while (!I.stepProjectile(s.m, p, s.a, s.b, r, pending, 0) && steps < 2000) steps++;
  assert.ok(steps < 2000, 'the second ground contact ends it');
  assert.strictEqual(r.dealt, 0);
});

test('knight, current rule: every collision counts; damage is an even share per unit contact and never above the total', () => {
  const totals = new Set();
  for (let die = 1; die <= 6; die++) {
    const s = scene('knight', 'wizard');
    const p = drop(s, s.a, s.b.x, 760, 30);
    p.die = die; p.bouncesLeft = die; p.bounceDmg = Math.round(30 / die * 10) / 10;
    const r = play(s, s.a, s.b, [p]);
    const share = Math.round(30 / die * 10) / 10;
    assert.ok(r.dealt >= share - 1e-9 && r.dealt <= 30 + 1e-9, 'die ' + die + ' dealt ' + r.dealt);
    near(r.dealt / share, Math.round(r.dealt / share), 1e-6, 'a whole number of shares');
    totals.add(r.dealt);
    assert.strictEqual(s.m.ledger.getState('a').ult_pips, 1, 'one throw, one pip');
  }
  const one = scene('knight', 'wizard');
  const p1 = drop(one, one.a, one.b.x, 760, 30);
  p1.die = 1; p1.bouncesLeft = 1; p1.bounceDmg = 30;
  assert.strictEqual(play(one, one.a, one.b, [p1]).dealt, 30, 'die 1: the whole 30 in one contact');
  // the ground and the fence also use up collisions and deal nothing
  const g = scene('knight', 'wizard');
  const pg = drop(g, g.a, 1200, 850, 30);
  pg.die = 4; pg.bouncesLeft = 4; pg.bounceDmg = 7.5;
  assert.strictEqual(play(g, g.a, g.b, [pg]).dealt, 0);
});

test('knight, rule A: the die only sets the number of ticks; the total is always 30; ground skip once; the fence ends it', () => {
  for (let die = 1; die <= 6; die++) {
    const s = scene('knight', 'bat');
    s.m.shieldRule = 'A';
    const p = drop(s, s.a, s.b.x, 760, 30);
    p.rule = 'A'; p.die = die; p.total = 30; p.freeSkips = 1;
    const r = play(s, s.a, s.b, [p]);
    near(r.dealt, 30, 1e-9, 'die ' + die);
    near(s.b.hp, 147 - 30, 1e-9, 'hp after die ' + die);   // bat hp 147 since 2026-11-17 (was 143)
    assert.strictEqual(s.m.ledger.getState('a').ult_pips, 1);
  }
  assert.deepStrictEqual(Sim.splitEven(30, 4), [7.5, 7.5, 7.5, 7.5]);
  assert.deepStrictEqual(Sim.splitEven(30, 6), [5, 5, 5, 5, 5, 5]);
  const sp = Sim.splitEven(22, 3);
  near(sp.reduce((x, y) => x + y, 0), 22, 1e-9, 'parts add up');
  const kill = scene('knight', 'bat');
  kill.m.shieldRule = 'A';
  kill.b.hp = 8;
  const pk = drop(kill, kill.a, kill.b.x, 760, 30);
  pk.rule = 'A'; pk.die = 4; pk.total = 30; pk.freeSkips = 1;
  const rk = play(kill, kill.a, kill.b, [pk]);
  assert.strictEqual(kill.b.hp, 0);
  assert.strictEqual(rk.dealt, 8, 'only the HP that was left');
  assert.strictEqual(kill.m.over, true);
  // fence: ends the shield (no rebound)
  const f = scene('knight', 'bat');
  f.m.shieldRule = 'A';
  const pf = drop(f, f.a, 960, 700, 30);
  pf.rule = 'A'; pf.die = 6; pf.total = 30; pf.freeSkips = 1;
  const rf = play(f, f.a, f.b, [pf]);
  assert.strictEqual(rf.dealt, 0);
  assert.strictEqual(f.m.wallHp, 92, 'exactly one fence hit');
});

test('cat volley: five shuriken share 1.5 x the normal damage, one throw gives one pip', () => {
  const s = scene('bat', 'skeleton');
  const share = Ultimate.splitDamage(26, 5);
  assert.strictEqual(share, 7.8);
  const ps = [0, 1, 2, 3, 4].map((i) => drop(s, s.a, s.b.x + (i - 2) * 20, 760, share));
  const r = play(s, s.a, s.b, ps);
  near(r.dealt, 39, 1e-9, 'all five on one unit: 1.5 x 26');
  assert.strictEqual(s.m.ledger.getState('a').ult_pips, 1);
  const half = scene('bat', 'skeleton');
  const ps2 = [0, 1, 2, 3, 4].map((i) => drop(half, half.a, i < 2 ? half.b.x : half.b.x + 300, 760, share));
  near(play(half, half.a, half.b, ps2).dealt, 15.6, 1e-9, 'two of five');
});

test('knockout ends the match at once and drops the loser pips', () => {
  const s = scene('wizard', 'skeleton');
  s.m.ledger.registerHit('b', 90);
  s.b.hp = 20;
  play(s, s.a, s.b, [drop(s, s.a, s.b.x, 760), drop(s, s.a, s.b.x, 760)]);
  assert.strictEqual(s.b.hp, 0);
  assert.strictEqual(s.m.over, true);
  assert.strictEqual(s.m.winnerSide, 'a');
  assert.strictEqual(s.m.ledger.getState('b').ult_pips, 0, 'a KO loses the pips');
});

// ---------------------------------------------------------------------------
// whole matches

function allFinite(v, where) {
  if (typeof v === 'number') assert.ok(Number.isFinite(v), where + ' = ' + v);
  else if (Array.isArray(v)) v.forEach((x, i) => allFinite(x, where + '[' + i + ']'));
  else if (v && typeof v === 'object') Object.keys(v).forEach((k) => allFinite(v[k], where + '.' + k));
}

test('a fixed seed gives the same match, another seed another match; no Math.random and no Date', () => {
  const run = (seed) => JSON.stringify(Sim.simulateMatch({ a: 'skeleton', b: 'knight', seed }));
  assert.strictEqual(run(7), run(7));
  assert.notStrictEqual(run(7), run(8));
  const pairs = JSON.stringify(Sim.runPairings({ classes: KEYS, matchesPerPairing: 4, seed: 11 }));
  assert.strictEqual(pairs, JSON.stringify(Sim.runPairings({ classes: KEYS, matchesPerPairing: 4, seed: 11 })));
  assert.notStrictEqual(pairs, JSON.stringify(Sim.runPairings({ classes: KEYS, matchesPerPairing: 4, seed: 12 })));
  const rnd = Math.random;
  const DateOrig = global.Date;
  Math.random = () => { throw new Error('Math.random used'); };
  global.Date = function () { throw new Error('Date used'); };
  try {
    Sim.simulateMatch({ a: 'bat', b: 'bride', seed: 3 });
    Sim.simulateMatch({ a: 'knight', b: 'hunchback', seed: 3, shieldRule: 'A' });
    Sim.runPairings({ classes: ['skeleton', 'reaper'], matchesPerPairing: 3, seed: 1 });
  } finally {
    Math.random = rnd;
    global.Date = DateOrig;
  }
});

test('no NaN anywhere, HP stays in range, the winner has HP left, the loser has none', () => {
  let ko = 0;
  for (const table of [CS.CLASSES, CS.PROVISIONAL]) {
    for (const a of KEYS) {
      for (const b of KEYS) {
        for (let seed = 1; seed <= 4; seed++) {
          const r = Sim.simulateMatch({ a, b, seed: seed * 101 + KEYS.indexOf(a) * 7 + KEYS.indexOf(b), table });
          allFinite(r, a + ' vs ' + b);
          assert.ok(r.hp.a >= 0 && r.hp.a <= table[a].hp && r.hp.b >= 0 && r.hp.b <= table[b].hp);
          assert.ok(r.rounds >= 1 && r.rounds <= 60);
          if (r.endedBy === 'ko') {
            ko++;
            const loser = r.winner === 'a' ? 'b' : 'a';
            assert.strictEqual(r.hp[loser], 0);
            assert.ok(r.hp[r.winner] > 0);
            assert.ok(r.hitsToKill >= 1);
          }
        }
      }
    }
  }
  assert.ok(ko > 200, 'most matches end by a knockout, got ' + ko);
});

test('the match always ends: knockout or timeout, never an endless loop; damage adds up to the HP lost', () => {
  const rand = Sim.mulberry32(77);
  for (let n = 0; n < 150; n++) {
    const a = KEYS[Math.floor(rand() * KEYS.length)];
    const b = KEYS[Math.floor(rand() * KEYS.length)];
    const maxRounds = [1, 2, 3, 60][Math.floor(rand() * 4)];
    const aimError = [0, 9, 40, 400][Math.floor(rand() * 4)];
    const rule = rand() < 0.5 ? 'A' : 'current';
    const r = Sim.simulateMatch({ a, b, seed: Math.floor(rand() * 1e9), maxRounds, aimError, shieldRule: rule });
    assert.ok(r.endedBy === 'ko' || r.endedBy === 'timeout');
    assert.ok(r.rounds <= maxRounds, 'rounds ' + r.rounds + ' > ' + maxRounds);
    if (r.endedBy === 'timeout') assert.strictEqual(r.rounds, maxRounds);
    // accounting: what a dealt is what b lost, and the other way round (no healing in the simulator)
    near(r.stats.a.damage, CS.CLASSES[b].hp - r.hp.b, 1e-6, 'damage a -> b');
    near(r.stats.b.damage, CS.CLASSES[a].hp - r.hp.a, 1e-6, 'damage b -> a');
    // Status ticks never knock out a unit. The left side acts first, and the
    // right side follows unless it was defeated by the left-side throw.
    assert.ok(r.stats.a.throws === r.rounds || r.stats.a.throws === r.rounds - 1);
    assert.ok(r.stats.b.throws === r.rounds || r.stats.b.throws === r.rounds - 1);
    assert.ok(Math.abs(r.stats.a.throws - r.stats.b.throws) <= 1,
      'turn counts differ by more than the first-mover or poison-start knockout');
    if (r.endedBy === 'timeout') {
      assert.strictEqual(r.stats.a.throws, r.rounds);
      assert.strictEqual(r.stats.b.throws, r.rounds);
    }
  }
  const t = Sim.simulateMatch({ a: 'skeleton', b: 'skeleton', seed: 1, maxRounds: 1, aimError: 400 });
  assert.strictEqual(t.endedBy, 'timeout');
  assert.strictEqual(t.rounds, 1);
  assert.throws(() => Sim.simulateMatch({ a: 'nobody', b: 'bat' }), /two class keys/);
  assert.throws(() => Sim.simulateMatch({ a: 'bat', b: '__proto__' }), /two class keys/);
  assert.throws(() => Sim.simulateMatch(), /two class keys/);
});

test('the bot uses public-information normal-level errors: zero-error control hits most, normal and wide errors hit less', () => {
  const rate = (options) => {
    let throws = 0;
    let hits = 0;
    for (let seed = 1; seed <= 60; seed++) {
      const r = Sim.simulateMatch(Object.assign({ a: 'wizard', b: 'wizard', seed, maxRounds: 8 }, options));
      throws += r.stats.a.throws + r.stats.b.throws;
      hits += r.stats.a.hitThrows + r.stats.b.hitThrows;
    }
    return hits / throws;
  };
  const exact = rate({ perceptionTargetPx: 0, perceptionWind: 0, aimError: 0 });
  const normal = rate({ agentLevel: 'normal' });
  const wide = rate({ agentLevel: 'normal', aimError: 30 });
  const sample = Sim.simulateMatch({ a: 'wizard', b: 'wizard', seed: 1 });
  console.log('     hit rate by public bot error (wizard mirror): exact -> ' + exact.toFixed(2) + ', normal -> ' + normal.toFixed(2) + ', wide -> ' + wide.toFixed(2));
  assert.deepStrictEqual(sample.publicPerception, { targetPx: 80, wind: 0.8, aimPowerError: 6 });
  assert.ok(exact > normal && normal > wide, 'hit rate should fall with public-information error');
  assert.ok(exact > 0.7, 'a noiseless control hits most throws, got ' + exact);
  assert.ok(normal > 0.2 && normal < 0.7, 'the normal public bot should have a bounded non-exact hit rate, got ' + normal);
});

test('the cat uses its volley at most twice per match, never for the other side, and never with ultimates off', () => {
  let used = 0;
  for (let seed = 1; seed <= 80; seed++) {
    const r = Sim.simulateMatch({ a: 'bat', b: 'knight', seed, aimError: 5 });
    assert.ok(r.stats.a.ultUsed <= 2 && r.stats.b.ultUsed === 0);
    assert.ok(r.ledger.a.ultimates_used === r.stats.a.ultUsed);
    used += r.stats.a.ultUsed;
    const none = Sim.simulateMatch({ a: 'bat', b: 'knight', seed, aimError: 5, ultimates: 'none' });
    assert.strictEqual(none.stats.a.ultUsed, 0);
  }
  assert.ok(used > 0, 'the volley was never used in 80 matches');
});

// ---------------------------------------------------------------------------
// pairings

test('runPairings: win rates add up to 1 across the diagonal, rounds are symmetric, class averages match the matrix', () => {
  const n = 10;
  const res = Sim.runPairings({ classes: KEYS, matchesPerPairing: n, seed: 21 });
  assert.strictEqual(res.totalMatches, (KEYS.length * (KEYS.length + 1) / 2) * n);
  for (let i = 0; i < KEYS.length; i++) {
    assert.strictEqual(res.winRates[i][i], 0.5);
    for (let j = 0; j < KEYS.length; j++) {
      near(res.winRates[i][j] + res.winRates[j][i], 1, 1e-12, 'rates ' + i + ',' + j);
      assert.strictEqual(res.avgRounds[i][j], res.avgRounds[j][i]);
      assert.ok(res.winRates[i][j] >= 0 && res.winRates[i][j] <= 1);
      if (i !== j) {
        near(res.wins[i][j] + res.wins[j][i], n, 1e-12, 'wins ' + i + ',' + j);
        near(res.winRates[i][j] * n, res.wins[i][j], 1e-9);
      }
    }
  }
  KEYS.forEach((k, i) => {
    let sum = 0;
    for (let j = 0; j < KEYS.length; j++) if (j !== i) sum += res.winRates[i][j];
    near(res.classAverage[k], sum / (KEYS.length - 1), 1e-12, 'average of ' + k);
  });
  // totals: the class averages of all classes add up to class-count x 50%
  near(KEYS.reduce((s, k) => s + res.classAverage[k], 0), KEYS.length / 2, 1e-9, 'sum of averages');
  allFinite(res, 'pairings');
  assert.ok(res.avgRoundsOverall > 2 && res.avgRoundsOverall < 40);
  for (const k of KEYS) {
    assert.ok(res.hitsToKill[k] === null || res.hitsToKill[k] >= 1);
    assert.ok(res.throwStats[k].throws > 0);
  }
  assert.strictEqual(res.pass, res.violations.length === 0);
});

test('runPairings: the sides alternate, so a pairing is not decided by who moves first', () => {
  const res = Sim.runPairings({ classes: ['wizard', 'wizard'], matchesPerPairing: 6, seed: 4 });
  assert.strictEqual(res.classes.length, 2);
  const one = Sim.runPairings({ classes: ['skeleton'], matchesPerPairing: 6, seed: 4 });
  assert.strictEqual(one.totalMatches, 6);
  assert.deepStrictEqual(one.violations, [], 'a single class has no pairing to violate');
  assert.strictEqual(one.pass, true);
});

test('runPairings: a lopsided table is reported as a violation, and pass is false', () => {
  const t = CS.cloneTable(CS.CLASSES);
  t.reaper.hp = 2000;     // cannot be beaten
  const res = Sim.runPairings({ classes: ['skeleton', 'wizard', 'reaper'], matchesPerPairing: 10, seed: 3, table: t, maxRounds: 25 });
  assert.strictEqual(res.pass, false);
  assert.ok(res.violations.some((v) => v.kind === 'pairing' && (v.a === 'reaper' || v.b === 'reaper')));
  assert.ok(res.violations.some((v) => v.kind === 'class_average'));
  const text = Sim.formatReport(res, 'test');
  assert.ok(/BANDS: \d+ violation/.test(text));
  assert.ok(text.includes('reaper') && text.includes('skeleton'));
});

test('command line: prints the matrix; exit code 0 inside the bands, 1 outside, 2 for bad options', () => {
  const run = (args) => spawnSync(process.execPath, [path.join(__dirname, 'sim_balance.js')].concat(args), { encoding: 'utf8' });
  const lopsided = run(['--matches', '8', '--seed', '3', '--classes', 'skeleton,bride', '--table', 'provisional']);
  assert.ok(/Win rate of the ROW class/.test(lopsided.stdout), lopsided.stderr);
  assert.ok(/skeleton/.test(lopsided.stdout) && /bride/.test(lopsided.stdout));
  assert.strictEqual(lopsided.status, 1, 'the 12-damage bride must break the band against the skeleton');
  assert.ok(/BANDS: \d+ violation/.test(lopsided.stdout));
  const mirror = run(['--matches', '4', '--seed', '3', '--classes', 'wizard']);
  assert.strictEqual(mirror.status, 0);
  assert.ok(/BANDS: pass/.test(mirror.stdout));
  const bad = run(['--nope']);
  assert.strictEqual(bad.status, 2);
  const centre = run(['--matches', '2', '--seed', '1', '--classes', 'bride', '--wave-rule', 'centre']);
  assert.ok(/wave rule centre/.test(centre.stdout), centre.stderr);
  const json = run(['--matches', '3', '--seed', '1', '--classes', 'bat,reaper', '--json']);
  const parsed = JSON.parse(json.stdout);
  assert.deepStrictEqual(parsed.classes, ['bat', 'reaper']);
  assert.strictEqual(parsed.totalMatches, 9);
  const storm = run(['--matches', '2', '--seed', '1', '--classes', 'wizard', '--weather', 'storm', '--json']);
  assert.strictEqual(JSON.parse(storm.stdout).weather, 'storm');
  const adjusted = run(['--matches', '2', '--seed', '1', '--classes', 'wizard', '--weather', 'snow', '--adjust', 'wizard:dmg:0.9', '--json']);
  assert.strictEqual(JSON.parse(adjusted.stdout).weather, 'snow');
  assert.strictEqual(run(['--adjust', 'wizard:dmg:0.8']).status, 2);
});

test('hits to kill from play are near the hand table (30 matches per pairing, seeded)', () => {
  // A small version of the real check, fast enough for every run. Seeded, so the same numbers every time.
  const res = Sim.runPairings({ classes: KEYS, matchesPerPairing: 30, seed: 7 });
  const m = CS.matrix();
  const lines = [];
  KEYS.forEach((k, i) => {
    const hand = m[i].reduce((a, b) => a + b, 0) / KEYS.length;
    lines.push(k + ': play ' + (res.hitsToKill[k] === null ? '-' : res.hitsToKill[k].toFixed(2)) + ' vs table ' + hand.toFixed(2));
    assert.ok(res.hitsToKill[k] !== null);
    // The knight's hop was fixed on 2026-11-16 (it lands on the unit's centre, so the whole total is dealt); the hand table still models the old drift,
    // so the knight gets a wider band until Kiro task 170 rebuilds the table (docs/kiro_task_170_balance_model.md).
    const band = k === 'knight' ? 2.8 : 1.6;   // every HP x1.5 on 2026-11-16: crits, ultimates and burn make play shorter than the hand table by more
    assert.ok(Math.abs(res.hitsToKill[k] - hand) < band, k + ' hits to kill in play ' + res.hitsToKill[k] + ' vs table ' + hand);
  });
  console.log('     hits to kill, simulated winners vs hand table: ' + lines.join('; '));
});

// ---------------------------------------------------------------------------

let failed = 0;
for (const t of tests) {
  try {
    t.fn();
    console.log('ok   - ' + t.name);
  } catch (err) {
    failed++;
    console.log('FAIL - ' + t.name + '\n       ' + (err && err.stack ? err.stack.split('\n').slice(0, 5).join('\n       ') : err));
  }
}
if (failed > 0) {
  console.log('test_sim_balance: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_sim_balance: all ' + tests.length + ' tests passed');
