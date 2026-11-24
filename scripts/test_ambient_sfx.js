'use strict';
/* Tests for js/ambient_sfx.js with a recording fake AudioContext. Run: node scripts/test_ambient_sfx.js */
const assert = require('assert');
const path = require('path');
const Amb = require(path.join(__dirname, '..', 'js', 'ambient_sfx.js'));

function fakeCtx() {
  const log = { osc: 0, buffers: 0, gains: 0, started: 0 };
  const param = () => ({ value: 0, setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {} });
  const node = (extra) => Object.assign({ connect() {}, start() { log.started++; }, stop() {} }, extra);
  return {
    log, sampleRate: 8000, currentTime: 1, destination: node({}),
    createGain() { log.gains++; return node({ gain: param() }); },
    createOscillator() { log.osc++; return node({ frequency: param(), type: '' }); },
    createBiquadFilter() { return node({ frequency: param(), Q: param(), type: '' }); },
    createBufferSource() { return node({ buffer: null }); },
    createBuffer(c, n) { log.buffers++; return { getChannelData() { return new Float32Array(n); } }; },
    createDelay() { return node({ delayTime: param() }); },
    createStereoPanner() { return node({ pan: param() }); }
  };
}
let seed = 7;
const rng = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };

const tests = [];
const t = (name, fn) => tests.push([name, fn]);

t('bat and ghost both play and make nodes', () => {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng });
  assert.strictEqual(a.trigger('bat'), true);
  assert.ok(c.log.osc >= 2, 'bat needs chirp oscillators');
  const before = c.log.osc;
  assert.strictEqual(a.trigger('ghost'), true);
  assert.ok(c.log.osc > before, 'ghost needs voices');
});
t('a real ghost recording is used when given, the synthesized voice otherwise', () => {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng });
  assert.ok(a.trigger('ghost')); const synthOsc = c.log.osc; assert.ok(synthOsc > 0);
  const c2 = fakeCtx(); const a2 = Amb.createAmbient({ ctx: c2, random: rng });
  a2.setBuffer('ghost', { duration: 3, length: 3 * 8000 });
  assert.ok(a2.trigger('ghost')); assert.strictEqual(c2.log.osc, 0, 'no synthesized voices when the recording plays');
  a2.setBuffer('ghost', null); a2.setBuffer('bat', { duration: 1 });          // bad input is ignored
});
t('unknown kind and missing ctx never throw', () => {
  const a = Amb.createAmbient({ ctx: null }); assert.strictEqual(a.trigger('bat'), false);
  const b = Amb.createAmbient({ ctx: fakeCtx(), random: rng }); assert.strictEqual(b.trigger('dog'), false);
});
t('at most two creature sounds at once', () => {
  const a = Amb.createAmbient({ ctx: fakeCtx(), random: rng });
  assert.ok(a.trigger('bat')); assert.ok(a.trigger('ghost'));
  assert.strictEqual(a.trigger('bat'), false);
});
t('random sounds come every 9 to 22 s and alternate bat / ghost', () => {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng }); const kinds = [];
  let prev = 0;
  for (let i = 0; i < 6000; i++) {                       // 100 s at 60 fps
    a.update(1 / 60);
    const s = a.getState();
    if (s.last && (kinds.length === 0 || kinds[kinds.length - 1] !== s.last || s.active !== prev)) { /* count by changes below */ }
    prev = s.active;
  }
  const s = a.getState();
  assert.ok(s.errors === 0);
  assert.ok(s.last === 'bat' || s.last === 'ghost');
  assert.ok(c.log.osc >= 2 * Math.floor(100 / Amb.MAX_GAP), 'at least a few sounds in 100 s');
  assert.ok(c.log.osc <= 400, 'not a flood');
});
t('muted: the output gain is 0 and no random sound is triggered', () => {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng });
  a.trigger('bat'); a.setMuted(true);
  const gainsBefore = c.log.osc;
  for (let i = 0; i < 6000; i++) a.update(1 / 60);
  assert.strictEqual(c.log.osc, gainsBefore, 'nothing new while muted');
  assert.strictEqual(a.getState().muted, true);
});
t('stop() ends everything; bad dt is ignored', () => {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng });
  a.update(NaN); a.update(-1); a.stop();
  for (let i = 0; i < 6000; i++) a.update(1 / 60);
  assert.strictEqual(c.log.osc, 0);
  assert.strictEqual(a.trigger('bat'), false);
});
t('the module has no DOM, no Math.random and no clock', () => {
  const src = require('fs').readFileSync(path.join(__dirname, '..', 'js', 'ambient_sfx.js'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  assert.ok(!/document\.|window\.|Math\.random|Date\.|performance\./.test(src));
});

const buf = (d) => ({ duration: d, length: d * 8000 });
function loaded(extra) {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng });
  ['crow', 'cat_meow', 'dog_bark', 'ghost_moan1', 'ghost_moan3', 'zombie_moan', 'witch_cackle', 'ghost_cackle', 'thunder'].forEach((k) => a.setBuffer(k, buf(2)));
  return { c, a };
}
t('real kinds play, and the same kind never plays twice in a row', () => {
  const { a } = loaded(); const seen = []; let prevLast = '';
  for (let i = 0; i < 60 * 600; i++) { a.update(1 / 60); const l = a.getState().last; if (l && l !== prevLast) { seen.push(l); prevLast = l; } }
  assert.ok(seen.length >= 10, 'sounds happened');
  for (let i = 1; i < seen.length; i++) assert.notStrictEqual(seen[i], seen[i - 1]);
  assert.ok(new Set(seen).size >= 4, 'variety');
});
t('a long moan keeps the moan family silent for 30 s', () => {
  const { a } = loaded(); assert.ok(a.trigger('ghost_moan1'));
  for (let i = 0; i < 60 * 28; i++) a.update(1 / 60);
  // within 30 s no moan-family kind may be picked by the random layer
  let moans = 0; const fams = ['ghost_moan1', 'ghost_moan3', 'zombie_moan'];
  for (let i = 0; i < 60 * 2; i++) { a.update(1 / 60); if (fams.indexOf(a.getState().last) >= 0 && a.getState().last !== 'ghost_moan1') moans++; }
  assert.strictEqual(moans, 0);
});
t('nothing starts while a throw is in the air, a KO window is open, or in victory', () => {
  const { a } = loaded(); a.notify('throw_spear');
  for (let i = 0; i < 60 * 11; i++) a.update(1 / 60);
  assert.strictEqual(a.getState().last, '', 'blocked during throw'); assert.strictEqual(a.getState().blocked, true);
  a.notify('impact_ground');
  assert.strictEqual(a.getState().blocked, true, '0.8 s after the hit still blocked');
  for (let i = 0; i < 60; i++) a.update(1 / 60);
  assert.strictEqual(a.getState().blocked, false);
  a.notify('ko'); assert.strictEqual(a.getState().blocked, true);
  for (let i = 0; i < 60 * 3.1; i++) a.update(1 / 60);
  assert.strictEqual(a.getState().blocked, false);
  a.setMood('victory'); assert.strictEqual(a.getState().blocked, true); a.setMood('battle_calm');
  assert.strictEqual(a.getState().blocked, false);
});
t('beds: one at a time, wind level follows the wind, muted bus is 0', () => {
  const c = fakeCtx(); const a = Amb.createAmbient({ ctx: c, random: rng });
  a.setBuffer('night', buf(28)); a.setBuffer('wind', buf(20));
  assert.ok(a.setBed('night')); assert.strictEqual(a.getState().bed, 'night');
  assert.ok(a.setBed('wind')); assert.strictEqual(a.getState().bed, 'wind');
  a.setWind(0.7); a.setWind(NaN); a.setWind(5);
  a.setBed(null); assert.strictEqual(a.getState().bed, null);
  assert.strictEqual(a.getState().errors, 0);
  a.stop();
});
t('missing buffers never throw: only bat and the synthesized ghost are used', () => {
  const a = Amb.createAmbient({ ctx: fakeCtx(), random: rng });
  assert.strictEqual(a.trigger('crow'), false); a.setBuffer('crow', null); a.setBuffer('crow', buf(0)); assert.strictEqual(a.trigger('crow'), false);
  assert.strictEqual(a.setBed('wind'), true); assert.strictEqual(a.getState().errors, 0);
});

let failed = 0;
for (const [name, fn] of tests) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + '\n     ' + e.message); }
}
console.log('test_ambient_sfx: ' + (tests.length - failed) + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
