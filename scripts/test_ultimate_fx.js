'use strict';
/* Tests for js/ultimate_fx.js. Node assert only. Run: node scripts/test_ultimate_fx.js */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const UltimateFx = require(path.join(__dirname, '..', 'js', 'ultimate_fx.js'));
const source = fs.readFileSync(path.join(__dirname, '..', 'js', 'ultimate_fx.js'), 'utf8');
const particleSource = fs.readFileSync(path.join(__dirname, '..', 'js', 'particles.js'), 'utf8');
const presetNames = new Set(Array.from(particleSource.matchAll(/PRESETS\.([A-Za-z0-9_]+)\s*=/g), match => match[1]));
const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

function inputFor(extra) {
  return Object.assign({
    startX: 300, startY: 600, landingX: 1500, landingY: 860,
    flightTime: 1.2, dirX: 1, normalDamage: 23,
    targets: [{ x: 1300, y: 700 }, { x: 1500, y: 760 }, { x: 1700, y: 820 }]
  }, extra || {});
}
function allTimelines(input) {
  return [
    UltimateFx.batShurikenRain(input), UltimateFx.skeletonTripleJavelin(input),
    UltimateFx.wizardPumpkinBlast(input), UltimateFx.brideSoulDirge(input),
    UltimateFx.hunchbackTowerToll(input), UltimateFx.hunchbackBoomerang(input), UltimateFx.nunCrossDart(input),
    UltimateFx.necroGhostfireTrio(input)
  ];
}
function assertTimeline(events) {
  assert.ok(Array.isArray(events) && events.length > 0);
  for (const event of events) {
    assert.ok(Number.isFinite(event.t) && event.t >= 0);
    assert.ok(Number.isFinite(event.x) && event.x >= 0 && event.x <= UltimateFx.CANVAS_WIDTH);
    assert.ok(Number.isFinite(event.y) && event.y >= 0 && event.y <= UltimateFx.CANVAS_HEIGHT);
    assert.ok(presetNames.has(event.preset), 'missing preset: ' + event.preset);
  }
  for (let index = 1; index < events.length; index++) {
    assert.ok(events[index - 1].t <= events[index].t,
      'timeline event ' + index + ' is out of time order: ' + events[index - 1].t + ' then ' + events[index].t);
  }
}

test('named timelines emit valid events with existing particle presets', () => {
  for (const timeline of allTimelines(inputFor())) assertTimeline(timeline);
  assert.strictEqual(UltimateFx.batShurikenRain(inputFor()).filter(event => event.preset === 'weapon_trail_dart').length, 5);
  assert.strictEqual(UltimateFx.skeletonTripleJavelin(inputFor()).filter(event => event.preset === 'weapon_trail_spear').length, 3);
});

test('short flights keep every direct timeline in nondecreasing time order', () => {
  const input = inputFor({
    flightTime: 0.05,
    hits: [
      { phase: 'outbound', target: 'agent-a', x: 1300, y: 700, t: 0.05 },
      { phase: 'return', target: 'agent-a', x: 1300, y: 700, t: 0.25 }
    ]
  });
  for (const timeline of allTimelines(input)) assertTimeline(timeline);
});

test('the reaper flame alias is exactly the retained ghost-fire timeline', () => {
  const input = inputFor({ normalDamage: 23, hits: [false, 'agent-b', true] });
  const fromAlias = UltimateFx.timeline('reaper_flame_trio', input);
  const retained = UltimateFx.timeline('necro_ghostfire_trio', input);
  assert.deepStrictEqual(fromAlias, retained);
  assert.strictEqual(UltimateFx.timeline('reaper_triple_slash', input).length, 0);
  assert.strictEqual(typeof UltimateFx.reaperTripleSlash, 'undefined');
  assert.strictEqual(/scythe_slash_fx|weapon_trail_skull|reaperTripleSlash/.test(source), false);
});

test('the necromancer volley uses the owner multipliers and rounds each flame to 0.1', () => {
  assert.deepStrictEqual(UltimateFx.NECRO_VOLLEY_MULT, [1.1, 1.3, 1.5]);
  assert.strictEqual(UltimateFx.NECRO_VOLLEY_SCALE, 0.5);   // provisional total-attack scale (owner 2026-11-15)
  assert.deepStrictEqual(UltimateFx.necroVolleyDamage(23), [12.7, 15, 17.3]);
  assert.deepStrictEqual(UltimateFx.necroVolleyDamage(28), [15.4, 18.2, 21]);
  assert.deepStrictEqual(UltimateFx.necroVolleyDamage(19.5), [10.7, 12.7, 14.6]);
  assert.deepStrictEqual(UltimateFx.necroVolleyDamage(0), [0, 0, 0]);
  for (const bad of [undefined, null, NaN, Infinity, -1, '23', {}]) {
    assert.deepStrictEqual(UltimateFx.necroVolleyDamage(bad), [0, 0, 0]);
  }
  assert.strictEqual(UltimateFx.damageFor('reaper', 23), 12.7);
  assert.strictEqual(UltimateFx.resolveDamage('reaper', 23, { effects: false }), 12.7);
});

test('the necromancer timeline has ordered point, launches, impacts, first-hit mark, and final fire removal', () => {
  const fires = UltimateFx.timeline('reaper_flame_trio', inputFor({ hits: [false, 'agent-b', 'agent-c'] }));
  assert.deepStrictEqual(fires.map(event => event.phase), [
    'finger_point', 'flame_launch', 'flame_launch', 'flame_launch', 'fires_vanish',
    'hit', 'hit', 'hit', 'hallucination_mark'
  ]);
  const launches = fires.filter(event => event.phase === 'flame_launch');
  assert.deepStrictEqual(launches.map(event => event.t), [0, 0.15, 0.3]);
  assert.deepStrictEqual(launches.map(event => event.damage), [12.7, 15, 17.3]);
  assert.deepStrictEqual(launches.map(event => event.index), [0, 1, 2]);
  const hits = fires.filter(event => event.phase === 'hit');
  assert.deepStrictEqual(hits.map(event => event.t), [1.2, 1.2, 1.2]);
  assert.deepStrictEqual(hits.map(event => event.damage), [12.7, 15, 17.3]);
  const mark = fires.find(event => event.phase === 'hallucination_mark');
  assert.strictEqual(mark.t, 1.2);
  assert.strictEqual(mark.index, 1);
  assert.strictEqual(mark.target, 'agent-b');
  const vanish = fires.find(event => event.phase === 'fires_vanish');
  assert.strictEqual(vanish.t, 0.35);
  assert.strictEqual(vanish.x, 300);
  assert.strictEqual(vanish.y, 600);
  assertTimeline(fires);
});

test('the hallucination mark appears only for the first declared enemy hit', () => {
  for (const hits of [undefined, [], [false, null, undefined], [false, false, false]]) {
    assert.strictEqual(UltimateFx.timeline('reaper_flame_trio', inputFor({ hits }))
      .filter(event => event.phase === 'hallucination_mark').length, 0);
  }
  const marked = UltimateFx.timeline('reaper_flame_trio', inputFor({ hits: [true, 'later-target'] }))
    .filter(event => event.phase === 'hallucination_mark');
  assert.strictEqual(marked.length, 1);
  assert.strictEqual(marked[0].index, 0);
  assert.strictEqual(marked[0].target, undefined);
});

test('the hunchback boomerang timeline spins, pierces every declared hit, and returns once to its first target', () => {
  const events = UltimateFx.timeline('hunchback_boomerang', inputFor({
    normalDamage: 99,
    hits: [
      { phase: 'outbound', target: 'agent-a', x: 1300, y: 700, t: 0.6 },
      { phase: 'outbound', target: 'agent-b', x: 1500, y: 760, t: 0.9 },
      { phase: 'return', target: 'agent-a', x: 1300, y: 700, t: 1.6 }
    ]
  }));
  assert.strictEqual(UltimateFx.HUNCHBACK_NORMAL_DAMAGE, 21);
  assert.strictEqual(UltimateFx.HUNCHBACK_BOOMERANG_RETURN_DAMAGE, 31.5);
  assert.deepStrictEqual(events.map(event => event.phase), [
    'outbound_spin', 'pierce_hit', 'pierce_hit', 'turn', 'return', 'return_hit'
  ]);
  assert.deepStrictEqual(events.filter(event => event.phase === 'pierce_hit').map(event => event.damage), [21, 21]);
  const returnHit = events.find(event => event.phase === 'return_hit');
  assert.strictEqual(returnHit.target, 'agent-a');
  assert.strictEqual(returnHit.damage, 31.5);
  assert.ok(returnHit.damage <= UltimateFx.HUNCHBACK_NORMAL_DAMAGE * UltimateFx.ULT_MULT);
  assert.ok(events.filter(event => event.phase === 'pierce_hit').every(event => event.blockable === false));
  assert.ok(returnHit.blockable === false);
  assert.deepStrictEqual(events.map(event => event.preset), [
    'axe_spin_trail', 'hit_sparks', 'hit_sparks', 'axe_spin_trail', 'boomerang_return', 'hit_sparks'
  ]);
  assertTimeline(events);
});


test('the ghost nun timeline launches a spinning cross, lands quietly, then sparks its selected target', () => {
  const input = inputFor({
    flightTime: 0.8,
    targets: [{ id: 'agent-a', x: 1300, y: 700 }, { id: 'agent-b', x: 1700, y: 820 }],
    stunnedTarget: 'agent-b'
  });
  const events = UltimateFx.timeline('nun_cross_dart', input);
  assert.deepStrictEqual(events.map(event => event.phase), ['cross_launch', 'quiet_landing', 'electric_stun']);
  assert.deepStrictEqual(events.map(event => event.preset), ['cross_spin_trail', 'hit_sparks', 'spark_electric']);
  assert.deepStrictEqual(events.map(event => event.t), [0, 0.8, 0.81]);
  assert.strictEqual(events[2].target, 'agent-b');
  assert.strictEqual(events[2].x, 1700);
  assert.strictEqual(events[2].y, 820);
  assert.strictEqual(events.some(event => /soundwave|impact_wave|weapon_trail_wave/.test(event.preset)), false);
  assertTimeline(events);
});

test('the new mapped effects extend their matching timelines without changing damage', () => {
  const input = inputFor();
  assert.strictEqual(UltimateFx.skeletonTripleJavelin(input).filter(event => event.preset === 'ghost_spear_fall').length, 3);
  assert.strictEqual(UltimateFx.wizardPumpkinBlast(input).filter(event => event.preset === 'shock_ring').length, 1);
  assert.strictEqual(UltimateFx.brideSoulDirge(input).filter(event => event.preset === 'soundwave_rings').length, input.targets.length);
  assert.strictEqual(UltimateFx.hunchbackTowerToll(input).filter(event => event.preset === 'bell_toll_rings').length, 1);
  assert.deepStrictEqual(UltimateFx.brideSoulDirge(input).filter(event => event.preset === 'weapon_trail_wave').map(event => event.damage),
    Array(input.targets.length).fill(UltimateFx.damageFor('bride', input.normalDamage)));
});

test('the bride bat swarm follows an inside-55 precise hit and reaches every supplied enemy once', () => {
  const enemies = [
    { id: 'agent-a', x: 1300, y: 700 },
    { id: 'agent-b', x: 1500, y: 760 },
    { id: 'agent-c', x: 1700, y: 820 }
  ];
  const events = UltimateFx.timeline('bride_bat_swarm', inputFor({
    normalDamage: 28, hitDistance: 54.9, enemies
  }));
  const precise = events.filter(event => event.phase === 'precise_hit');
  const swarm = events.filter(event => event.phase === 'swarm_hit');
  assert.strictEqual(UltimateFx.BRIDE_NORMAL_DAMAGE, 28);
  assert.strictEqual(UltimateFx.BRIDE_BAT_SWARM_MULT, 1.3);
  assert.strictEqual(UltimateFx.BRIDE_PRECISE_HIT_RADIUS, 55);
  assert.strictEqual(precise.length, 1);
  assert.strictEqual(precise[0].damage, 28);
  assert.strictEqual(swarm.length, enemies.length);
  assert.deepStrictEqual(swarm.map(event => event.target), enemies.map(enemy => enemy.id));
  assert.ok(swarm.every(event => event.damage === 36.4 && event.blockable === false));
  assert.ok(swarm.every(event => event.damage <= 28 * UltimateFx.ULT_MULT));
  assert.ok(swarm.every(event => event.preset === 'bat_swarm'));
  assertTimeline(events);
});

test('the bride swarm rejects an edge or missed precise hit and keeps each duplicate enemy to one event', () => {
  const noEdgeHit = UltimateFx.brideBatSwarm(inputFor({ hitDistance: 55, enemies: [{ id: 'a' }] }));
  assert.deepStrictEqual(noEdgeHit, []);
  const noMissedHit = UltimateFx.brideBatSwarm(inputFor({ hitDistance: 55.1, enemies: [{ id: 'a' }] }));
  assert.deepStrictEqual(noMissedHit, []);
  const duplicate = UltimateFx.brideBatSwarm(inputFor({
    hitDistance: 0,
    enemies: [{ id: 'a' }, { id: 'a' }, { id: 'b' }]
  }));
  assert.deepStrictEqual(duplicate.filter(event => event.phase === 'swarm_hit').map(event => event.target), ['a', 'b']);
});

test('the nun timeline is deterministic with bounded inputs', () => {
  const input = inputFor({
    startX: -1, startY: Infinity, landingX: 3000, landingY: -20, flightTime: 100,
    targets: [{ id: 'agent-a', x: -4, y: 9999 }], stunned: 'agent-a'
  });
  const once = UltimateFx.nunCrossDart(input);
  assert.deepStrictEqual(UltimateFx.timeline('nun_cross_dart', input), once);
  assertTimeline(once);
});

test('timelines are deterministic and do not access ambient entropy or time', () => {
  assert.strictEqual(/Math\.random/.test(source), false);
  assert.strictEqual(/\bDate\b/.test(source), false);
  const input = inputFor();
  const before = JSON.stringify(allTimelines(input));
  const random = Math.random;
  const DateOriginal = global.Date;
  Math.random = () => { throw new Error('ambient entropy used'); };
  global.Date = function () { throw new Error('wall clock used'); };
  try {
    assert.strictEqual(JSON.stringify(allTimelines(input)), before);
  } finally {
    Math.random = random;
    global.Date = DateOriginal;
  }
});

let failed = 0;
for (const current of tests) {
  try {
    current.fn();
    console.log('ok   - ' + current.name);
  } catch (error) {
    failed++;
    console.log('FAIL - ' + current.name + '\n       ' + (error && error.stack ? error.stack.split('\n').slice(0, 4).join('\n       ') : error));
  }
}
if (failed > 0) {
  console.log('test_ultimate_fx: ' + failed + ' of ' + tests.length + ' tests FAILED');
  process.exit(1);
}
console.log('test_ultimate_fx: all ' + tests.length + ' tests passed');
