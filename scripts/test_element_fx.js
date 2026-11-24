'use strict';
/* Deterministic contract tests for js/element_fx.js. */
const assert = require('assert');
const path = require('path');
const ElementFx = require(path.join(__dirname, '..', 'js', 'element_fx.js'));
const Particles = require(path.join(__dirname, '..', 'js', 'particles.js'));

const HEROES = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];
const PRESETS = new Set(Particles.PRESET_NAMES);
const HEX = /^#[0-9a-f]{6}$/i;

function hue(hex) {
  const rgb = [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16) / 255);
  const max = Math.max(...rgb), min = Math.min(...rgb), delta = max - min;
  if (delta === 0) return null;
  let h = max === rgb[0] ? ((rgb[1] - rgb[2]) / delta) % 6
    : max === rgb[1] ? (rgb[2] - rgb[0]) / delta + 2
      : (rgb[0] - rgb[1]) / delta + 4;
  return (h * 60 + 360) % 360;
}

function entriesFor(element) {
  return [element.trailPreset].concat(element.launchPresets, element.impactPresets);
}

function scales(entries) {
  return entries.map((entry) => entry.scale);
}

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

test('every hero has one known element and a distinct trail', () => {
  const trails = new Set();
  for (const hero of HEROES) {
    const element = ElementFx.forHero(hero);
    assert.notStrictEqual(element.id, 'unknown', hero + ' has no element');
    assert.ok(!trails.has(element.trailPreset), hero + ' reuses trail ' + element.trailPreset);
    trails.add(element.trailPreset);
  }
  assert.strictEqual(trails.size, HEROES.length);
});

test('every named preset exists in particles.js', () => {
  for (const element of ElementFx.ELEMENTS) {
    for (const preset of entriesFor(element)) {
      assert.ok(PRESETS.has(preset), element.id + ' names missing preset ' + preset);
    }
  }
});

test('nun colours are warm and never blue-violet', () => {
  const nun = ElementFx.forHero('hag');
  for (const colour of nun.colours) {
    assert.ok(HEX.test(colour), 'invalid nun colour ' + colour);
    const h = hue(colour);
    assert.ok(h === null || h < 200 || h > 300, 'blue-violet nun hue ' + h + ' in ' + colour);
  }
});

test('trail, launch, and impact are deterministic with bounded scales', () => {
  for (const hero of HEROES.concat(['unknown-hero'])) {
    const first = { trail: ElementFx.trail(hero, false), heavy: ElementFx.trail(hero, true), launch: ElementFx.launch(hero), impact: ElementFx.impact(hero, 'hero') };
    const second = { trail: ElementFx.trail(hero, false), heavy: ElementFx.trail(hero, true), launch: ElementFx.launch(hero), impact: ElementFx.impact(hero, 'hero') };
    assert.deepStrictEqual(first, second, hero + ' is not deterministic');
    assert.ok(first.trail.scale >= 0.1 && first.trail.scale <= 4);
    assert.ok(first.heavy.scale >= 0.1 && first.heavy.scale <= 4);
    for (const scale of scales(first.launch).concat(scales(first.impact))) {
      assert.ok(Number.isFinite(scale) && scale >= 0.1 && scale <= 4, hero + ' has unbounded scale');
    }
    for (const entry of first.launch.concat(first.impact)) {
      assert.ok(entry.dirX === -1 || entry.dirX === 1, hero + ' has unsafe direction');
      assert.ok(PRESETS.has(entry.preset), hero + ' returns unknown preset');
    }
  }
});

test('unknown heroes use a safe neutral fallback', () => {
  const fallback = ElementFx.forHero(null);
  assert.strictEqual(fallback.id, 'unknown');
  assert.deepStrictEqual(ElementFx.launch(null), []);
  assert.deepStrictEqual(ElementFx.impact(null, 'hero'), []);
  assert.deepStrictEqual(ElementFx.trail(null, false), { preset: 'weapon_enchant_stardust', scale: 1 });
});

let failed = 0;
for (const current of tests) {
  try {
    current.fn();
    console.log('ok   ' + current.name);
  } catch (error) {
    failed++;
    console.log('FAIL ' + current.name);
    console.log('     ' + (error && error.stack ? error.stack.split('\n').slice(0, 4).join('\n     ') : error));
  }
}
console.log('\n' + (tests.length - failed) + '/' + tests.length + ' tests passed');
process.exit(failed ? 1 : 0);
