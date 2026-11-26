'use strict';
/*
 * Tests for js/audio.js. Node `assert` only, no network, no browser.
 * A fake AudioContext records what the module creates.
 * Run: node scripts/test_audio.js
 * Exit code 1 if any test fails. The last line is the summary.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const GameAudio = require(path.join(ROOT, 'js', 'audio.js'));
const EPS = 1e-9;

// ---------------------------------------------------------------------------
// fake Web Audio

function makeParam(ctx, initial) {
  const p = { value: initial === undefined ? 1 : initial };
  p.setValueAtTime = (v) => { p.value = v; return p; };
  p.linearRampToValueAtTime = (v, t) => { p.value = v; ctx.ramps.push({ value: v, time: t }); return p; };
  p.exponentialRampToValueAtTime = (v) => { p.value = v; return p; };
  p.setTargetAtTime = (v) => { p.value = v; return p; };
  p.cancelScheduledValues = () => p;
  return p;
}

function makeCtx(opts) {
  const o = opts || {};
  const ctx = {
    currentTime: 0, sampleRate: 8000, state: 'suspended', destination: { kind: 'destination' },
    resumeCalls: 0, sources: [], gains: [], ramps: []
  };
  const base = (kind) => ({ kind, connect: (x) => x, disconnect: () => {} });
  ctx.resume = () => { ctx.resumeCalls++; ctx.state = 'running'; return Promise.resolve(); };
  ctx.createGain = () => {
    const n = base('gain');
    n.gain = makeParam(ctx, 1);
    ctx.gains.push(n);
    return n;
  };
  ctx.createOscillator = () => {
    if (o.throwOn === 'osc') throw new Error('osc boom');
    const n = base('osc');
    n.type = 'sine';
    n.frequency = makeParam(ctx, 440);
    n.detune = makeParam(ctx, 0);
    n.started = [];
    n.stopped = [];
    n.start = (t) => { n.started.push(t); };
    n.stop = (t) => { n.stopped.push(t); };
    ctx.sources.push(n);
    return n;
  };
  ctx.createBufferSource = () => {
    const n = base('buffer');
    n.buffer = null;
    n.loop = false;
    n.playbackRate = makeParam(ctx, 1);
    n.started = [];
    n.stopped = [];
    n.start = (t) => { n.started.push(t); };
    n.stop = (t) => { n.stopped.push(t); };
    ctx.sources.push(n);
    return n;
  };
  ctx.createBiquadFilter = () => {
    const n = base('filter');
    n.type = 'lowpass';
    n.frequency = makeParam(ctx, 350);
    n.Q = makeParam(ctx, 1);
    return n;
  };
  ctx.createBuffer = (ch, len, rate) => {
    if (o.throwOn === 'buffer') throw new Error('buffer boom');
    return { duration: len / rate, length: len, getChannelData: () => new Float32Array(len) };
  };
  ctx.createDynamicsCompressor = () => {
    const n = base('compressor');
    n.threshold = makeParam(ctx, -24);
    n.ratio = makeParam(ctx, 12);
    n.attack = makeParam(ctx, 0.003);
    n.release = makeParam(ctx, 0.25);
    return n;
  };
  return ctx;
}

function seeded(seed) {
  let a = seed | 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function setup(extra) {
  const x = extra || {};
  const ctx = x.ctx || makeCtx();
  const logs = [];
  const audio = GameAudio.createAudio({
    ctx,
    loader: x.loader,
    random: x.random || seeded(7),
    eventMap: x.eventMap,
    log: (m) => logs.push(m)
  });
  return { audio, ctx, logs };
}

async function ready(extra) {
  const s = setup(extra);
  await s.audio.unlock();
  await s.audio.ready();
  return s;
}

// A map with n copies of ui_click: all synthesized, same priority, bands rotating.
// loop: true makes each voice last the full 10 s (a one-shot voice lasts as long as its recipe).
function customMap(n, mutate) {
  const base = JSON.parse(JSON.stringify(GameAudio.DEFAULT_EVENT_MAP));
  const events = {};
  for (let i = 0; i < n; i++) {
    events['e' + i] = Object.assign({}, base.events.ui_click, { file: null, duration: 10, loop: true, band: GameAudio.BANDS[i % 3] }, mutate ? mutate(i) : {});
  }
  base.events = events;
  return base;
}

function layerState(audio, name) {
  return audio.getState().layers.find((l) => l.name === name);
}

// ---------------------------------------------------------------------------
// test runner

const tests = [];
function test(name, fn) { tests.push({ name, fn }); }

const REQUIRED_EVENTS = [
  'ui_click', 'ui_hover', 'round_start', 'round_end', 'charge',
  'throw_spear', 'throw_shuriken', 'throw_cannon', 'throw_shield', 'throw_flame', 'throw_cross', 'throw_axe', 'throw_soundwave', 'coin_flip', 'throw_bomb', 'impact_flame', 'ult_skeleton', 'ult_skeleton_hit', 'ult_wizard', 'ult_wizard_hit', 'ult_bat', 'ult_bat_hit', 'ult_knight', 'ult_reaper', 'ult_reaper_hit', 'ult_bride', 'ult_bride_hit', 'ult_hunchback', 'ult_hunchback_hit', 'ult_hag', 'ult_hag_hit',
  'flight_spear', 'flight_shuriken', 'flight_cannon', 'flight_shield',
  'impact_unit', 'impact_unit_heavy', 'impact_fence', 'impact_fence_break', 'impact_ground', 'impact_ground_heavy',
  'shield_block', 'shield_place', 'dice_rattle', 'dice_result', 'move_step',
  'ko', 'poison_tick', 'ultimate_ready', 'low_hp_heartbeat', 'heal', 'item_pickup',
  'status_stun', 'status_slow', 'status_shock', 'status_frost',   // 2026-11-22: status cues
  'status_bleed', 'status_poison', 'status_burn', 'bleed_tick', 'burn_tick'   // 2026-11-23 (gap N9): synthesized cues for the three damage-over-time statuses and the two missing ticks
];

// ---------------------------------------------------------------------------
// tests

test('nothing plays before unlock; unlock resumes the context once', async () => {
  const { audio, ctx } = setup();
  assert.strictEqual(audio.play('ui_click'), null);
  assert.strictEqual(ctx.sources.length, 0);
  assert.strictEqual(audio.getState().unlocked, false);
  assert.strictEqual(await audio.unlock(), true);
  assert.strictEqual(await audio.unlock(), true);
  assert.strictEqual(ctx.resumeCalls, 1);
  const r = audio.play('ui_click');
  assert.ok(r && r.id > 0);
  assert.ok(ctx.sources.length > 0);
});

test('playMusic and volumes set before unlock are applied at unlock', async () => {
  const { audio, ctx } = setup();
  assert.strictEqual(audio.playMusic('title'), true);
  audio.setVolumes({ master: 0.5 });
  assert.strictEqual(ctx.sources.length, 0);
  await audio.unlock();
  assert.strictEqual(layerState(audio, 'bed').active, true);
  assert.ok(Math.abs(audio.getState().gains.master - 0.5) < EPS);
});

test('voice limit is never exceeded; equal priority replaces the oldest', async () => {
  const { audio, ctx } = await ready({ eventMap: customMap(20) });
  let max = 0;
  for (let i = 0; i < 100; i++) {
    ctx.currentTime += 0.2;
    const r = audio.play('e' + (i % 20));
    assert.ok(r, 'equal priority must be admitted');
    max = Math.max(max, audio.getState().voiceCount);
    assert.ok(audio.getState().voiceCount <= GameAudio.MAX_VOICES);
  }
  assert.strictEqual(max, GameAudio.MAX_VOICES);
});

test('voice limit with the real map and rapid mixed events', async () => {
  const { audio, ctx } = await ready();
  const names = audio.eventNames();
  let max = 0;
  for (let i = 0; i < 400; i++) {
    ctx.currentTime += 0.05;
    audio.play(names[i % names.length]);
    max = Math.max(max, audio.getState().voiceCount);
  }
  assert.ok(max <= GameAudio.MAX_VOICES, 'max voices ' + max);
  assert.ok(max > 3, 'test should actually load the mixer');
});

test('a lower-priority sound is dropped when all voices are busy with higher priority', async () => {
  const map = customMap(17, (i) => ({ priority: i < 16 ? 5 : 1 }));
  const { audio, ctx } = await ready({ eventMap: map });
  for (let i = 0; i < 16; i++) {
    ctx.currentTime += 0.2;
    assert.ok(audio.play('e' + i));
  }
  ctx.currentTime += 0.2;
  assert.strictEqual(audio.play('e16'), null);
  assert.strictEqual(audio.getState().voiceCount, 16);
});

test('band rule: at most 3 effects start in the same band within the window', async () => {
  const map = customMap(0);
  for (let i = 0; i < 5; i++) {
    map.events['e' + i] = Object.assign({}, GameAudio.DEFAULT_EVENT_MAP.events.ui_click, {
      file: null, duration: 5, band: 'high', priority: i === 4 ? 1 : 3
    });
  }
  const { audio } = await ready({ eventMap: map });
  assert.ok(audio.play('e0'));
  assert.ok(audio.play('e1'));
  assert.ok(audio.play('e2'));
  assert.ok(audio.play('e3'), 'equal priority replaces the oldest in the band');
  assert.strictEqual(audio.play('e4'), null, 'lower priority is dropped');
  const high = audio.getState().voices.filter((v) => v.band === 'high');
  assert.strictEqual(high.length, GameAudio.BAND_CAP);
});

test('mute silences everything and unmute restores', async () => {
  const { audio, ctx } = await ready();
  assert.ok(audio.play('ui_click'));
  audio.playMusic('battle_calm');
  assert.strictEqual(audio.mute(true), true);
  assert.strictEqual(audio.getState().muted, true);
  assert.strictEqual(audio.getState().gains.master, 0);
  const before = ctx.sources.length;
  assert.strictEqual(audio.play('throw_cannon'), null);
  assert.strictEqual(audio.play('ui_click'), null);
  assert.strictEqual(ctx.sources.length, before, 'no new sources while muted');
  audio.mute(false);
  assert.ok(Math.abs(audio.getState().gains.master - audio.getState().volumes.master) < EPS);
  ctx.currentTime += 1;
  assert.ok(audio.play('ui_click'));
});

test('volumes clamp to 0..1 and ignore junk', async () => {
  const { audio } = await ready();
  assert.deepStrictEqual(audio.setVolumes({ master: 2, music: -1, sfx: 0.5 }), { master: 1, music: 0, sfx: 0.5 });
  assert.deepStrictEqual(audio.setVolumes({ master: NaN, music: 'x', sfx: Infinity }), { master: 1, music: 0, sfx: 0.5 });
  assert.deepStrictEqual(audio.setVolumes(null), { master: 1, music: 0, sfx: 0.5 });
  const g = audio.getState().gains;
  assert.strictEqual(g.master, 1);
  assert.strictEqual(g.music, 0);
  assert.strictEqual(g.sfx, 0.5);
  audio.setVolumes({ music: 1, sfx: 1 });
  const g2 = audio.getState().gains;
  const db = 20 * Math.log10(g2.music / g2.sfx);
  assert.ok(Math.abs(db - -12) < 0.01, 'music is 12 dB under effects, got ' + db);
});

test('pitch variation stays within +/- 6 % for every event, at both ends of the random range', async () => {
  const lo = 1 - GameAudio.PITCH_LIMIT - EPS;
  const hi = 1 + GameAudio.PITCH_LIMIT + EPS;
  for (const rnd of [() => 0, () => 0.9999999, () => 0.5]) {
    const names = Object.keys(GameAudio.DEFAULT_EVENT_MAP.events);
    for (const name of names) {
      const { audio } = await ready({ random: rnd });
      const r = audio.play(name);
      assert.ok(r, name + ' should play');
      assert.ok(r.pitch >= lo && r.pitch <= hi, name + ' pitch ' + r.pitch);
    }
  }
});

test('a map that asks for more than +/- 6 % is clamped', async () => {
  const map = customMap(1, () => ({ pitch: [0.5, 2] }));
  const a = await ready({ eventMap: map, random: () => 0 });
  assert.ok(Math.abs(a.audio.play('e0').pitch - 0.94) < EPS);
  const b = await ready({ eventMap: map, random: () => 0.9999999 });
  assert.ok(Math.abs(b.audio.play('e0').pitch - 1.06) < 1e-6);
});

test('repeats differ: 200 plays give many distinct pitches, all in range', async () => {
  const { audio, ctx } = await ready();
  const seen = new Set();
  for (let i = 0; i < 200; i++) {
    ctx.currentTime += 0.2;
    const r = audio.play('impact_ground');
    assert.ok(r.pitch >= 0.94 - EPS && r.pitch <= 1.06 + EPS);
    seen.add(r.pitch);
  }
  assert.ok(seen.size > 100, 'distinct pitches: ' + seen.size);
});

test('same seed gives the same pitches', async () => {
  const run = async () => {
    const { audio, ctx } = await ready({ random: seeded(42) });
    const out = [];
    for (let i = 0; i < 20; i++) { ctx.currentTime += 0.2; out.push(audio.play('throw_spear').pitch); }
    return out;
  };
  assert.deepStrictEqual(await run(), await run());
});

test('ducking lowers the music gain for 400 ms then restores it', async () => {
  const { audio, ctx } = await ready();
  assert.strictEqual(audio.getState().duck, 1);
  audio.play('ui_click');
  assert.strictEqual(audio.getState().duck, 1, 'a small sound does not duck');
  assert.ok(audio.play('impact_unit_heavy'));
  const duckDb = 20 * Math.log10(GameAudio.DUCK_GAIN);
  assert.ok(Math.abs(duckDb - -6) < 0.05, 'duck is 6 dB');
  assert.ok(Math.abs(audio.getState().duck - GameAudio.DUCK_GAIN) < EPS);
  assert.ok(Math.abs(audio.getState().gains.duck - GameAudio.DUCK_GAIN) < EPS);
  ctx.currentTime += 0.3;
  audio.update(0.3);
  assert.ok(Math.abs(audio.getState().duck - GameAudio.DUCK_GAIN) < EPS, 'still held at 300 ms');
  audio.update(0.2);
  const mid = audio.getState().duck;
  assert.ok(mid > GameAudio.DUCK_GAIN && mid < 1, 'releasing after 400 ms: ' + mid);
  audio.update(1);
  assert.strictEqual(audio.getState().duck, 1);
  assert.strictEqual(audio.getState().gains.duck, 1);
});

test('a second big impact restarts the duck hold', async () => {
  const { audio, ctx } = await ready();
  audio.play('throw_cannon');
  audio.update(0.35);
  ctx.currentTime += 0.5;
  audio.play('ko');
  audio.update(0.3);
  assert.ok(Math.abs(audio.getState().duck - GameAudio.DUCK_GAIN) < EPS);
});

test('missing files fall back to synthesized sound (null, reject, throw, bad buffer)', async () => {
  const loaders = {
    null: () => Promise.resolve(null),
    reject: () => Promise.reject(new Error('404')),
    throws: () => { throw new Error('sync boom'); },
    badBuffer: () => Promise.resolve({ duration: NaN })
  };
  for (const key of Object.keys(loaders)) {
    const { audio, logs } = await ready({ loader: loaders[key] });
    const r = audio.play('shield_block');
    assert.ok(r, key);
    assert.strictEqual(r.synth, true, key);
    const missing = logs.filter((l) => l.indexOf('not loaded') >= 0);
    assert.strictEqual(missing.length, 1, key + ': one summary line, got ' + logs.length);
  }
});

test('with no loader every event still plays', async () => {
  for (const name of Object.keys(GameAudio.DEFAULT_EVENT_MAP.events)) {
    const { audio, ctx } = await ready();
    const r = audio.play(name);
    assert.ok(r && r.synth === true, name);
    assert.ok(ctx.sources.length > 0, name + ' created no sources');
  }
});

test('a loaded file is used, at the chosen pitch; other events still fall back', async () => {
  const file = GameAudio.DEFAULT_EVENT_MAP.events.shield_block.file;
  const loader = { load: (f) => Promise.resolve(f === file ? { duration: 1.2 } : null) };
  const { audio, ctx } = await ready({ loader });
  const r = audio.play('shield_block');
  assert.strictEqual(r.synth, false);
  const src = ctx.sources.filter((s) => s.kind === 'buffer' && s.buffer && s.buffer.duration === 1.2);
  assert.strictEqual(src.length, 1);
  assert.ok(Math.abs(src[0].playbackRate.value - r.pitch) < EPS);
  assert.strictEqual(src[0].started.length, 1);
  assert.strictEqual(audio.play('impact_unit').synth, true);
});

test('a file that throws during playback falls back to synthesis', async () => {
  const file = GameAudio.DEFAULT_EVENT_MAP.events.ui_click.file;
  const ctx = makeCtx();
  const orig = ctx.createBufferSource;
  let first = true;
  ctx.createBufferSource = () => {
    if (first) { first = false; throw new Error('decode boom'); }
    return orig();
  };
  const { audio } = await ready({ ctx, loader: (f) => Promise.resolve(f === file ? { duration: 0.2 } : null) });
  const r = audio.play('ui_click');
  assert.ok(r);
  assert.strictEqual(r.synth, true);
  assert.strictEqual(audio.getState().errors, 1);
});

test('unknown events and bad arguments never throw', async () => {
  const { audio, logs } = await ready();
  const bad = ['nope', undefined, null, 42, {}, [], '__proto__', 'toString', 'constructor', ''];
  for (const b of bad) assert.strictEqual(audio.play(b), null);
  assert.ok(audio.play('ui_click', null));
  assert.ok(audio.play('ui_click', 'junk'));
  audio.play('nope');
  audio.play('nope');
  assert.strictEqual(logs.filter((l) => l.indexOf('unknown event nope') >= 0).length, 1, 'logged once');
  assert.strictEqual(audio.playMusic('nope'), false);
  assert.strictEqual(audio.playMusic(undefined), false);
  audio.update(NaN);
  audio.update(-1);
  audio.update('x');
  audio.update();
  audio.setTension(NaN);
  audio.setTension('x');
  audio.setVolumes('x');
  assert.strictEqual(audio.stop('nope'), 0);
});

test('a failing context never throws out of the API and logs once', async () => {
  const { audio, logs } = await ready({ ctx: makeCtx({ throwOn: 'osc' }) });
  assert.strictEqual(audio.play('ui_click'), null);
  assert.strictEqual(audio.play('ui_click'), null);
  assert.strictEqual(audio.getState().voiceCount, 0);
  assert.ok(audio.getState().errors >= 2);
  assert.strictEqual(logs.filter((l) => l.indexOf('play ui_click') >= 0).length, 1);
});

test('if the noise buffer cannot be made, oscillator sounds still play', async () => {
  const { audio } = await ready({ ctx: makeCtx({ throwOn: 'buffer' }) });
  assert.ok(audio.play('ui_click'));
  assert.ok(audio.play('throw_cannon'));
});

test('no context at all: unlock resolves false, nothing throws', async () => {
  assert.ok(GameAudio.createAudio());   // no options at all
  const a = GameAudio.createAudio({ log: () => {} });
  assert.strictEqual(await a.unlock(), false);
  assert.strictEqual(a.play('ui_click'), null);
  assert.strictEqual(a.playMusic('title'), true);
  a.update(0.016);
  a.mute(true);
  a.setVolumes({ master: 0.2 });
  assert.strictEqual(a.getState().unlocked, false);
  const b = GameAudio.createAudio({ ctx: () => null, log: () => {} });
  assert.strictEqual(await b.unlock(), false);
});

test('a context factory is called at unlock, not before', async () => {
  let made = 0;
  const a = GameAudio.createAudio({ ctx: () => { made++; return makeCtx(); }, random: seeded(1), log: () => {} });
  assert.strictEqual(made, 0);
  await a.unlock();
  assert.strictEqual(made, 1);
  assert.ok(a.play('ui_click'));
});

test('loop events do not stack, can be updated and stopped', async () => {
  const { audio, ctx } = await ready();
  const a = audio.play('charge', { power: 0 });
  const b = audio.play('charge', { power: 1 });
  assert.strictEqual(a.id, b.id);
  assert.strictEqual(b.refreshed, true);
  assert.strictEqual(audio.getState().voiceCount, 1);
  assert.strictEqual(audio.stop('charge'), 1);
  assert.strictEqual(audio.getState().voiceCount, 0);
  audio.play('low_hp_heartbeat');
  ctx.currentTime = 13;
  audio.update(0.016);
  assert.strictEqual(audio.getState().voiceCount, 0, 'a forgotten loop ends by itself');
});

test('hover is rate limited by its cooldown', async () => {
  const { audio, ctx } = await ready();
  assert.ok(audio.play('ui_hover'));
  assert.strictEqual(audio.play('ui_hover'), null);
  ctx.currentTime += 0.07;
  assert.ok(audio.play('ui_hover'));
});

test('music moods switch layers; crossfade is 1.5 s; tension clamps', async () => {
  const { audio, ctx } = await ready();
  ctx.currentTime = 10;
  audio.playMusic('title');
  assert.strictEqual(layerState(audio, 'bed').active, true);
  assert.strictEqual(layerState(audio, 'rhythm').active, false);
  assert.ok(ctx.ramps.some((r) => Math.abs(r.time - 11.5) < EPS && r.value === 1), 'bed fades in over 1.5 s');
  audio.playMusic('battle_calm');
  assert.strictEqual(layerState(audio, 'rhythm').active, true);
  assert.strictEqual(layerState(audio, 'tension').active, false);
  assert.strictEqual(audio.setTension(2), 1);
  assert.strictEqual(audio.getState().tension, 1);
  assert.strictEqual(layerState(audio, 'tension').active, true);
  assert.ok(layerState(audio, 'tension').target > 0.8);
  assert.strictEqual(audio.setTension(-5), 0);
  assert.strictEqual(audio.setTension(NaN), 0);
  audio.playMusic('victory');
  assert.strictEqual(layerState(audio, 'victory').active, true);
  ctx.currentTime += 2;
  audio.update(0.016);
  assert.strictEqual(layerState(audio, 'rhythm').active, false);
  assert.strictEqual(layerState(audio, 'tension').active, false);
});

test('synthesized music runs for ten seconds without errors or runaway nodes', async () => {
  const { audio, ctx } = await ready();
  audio.playMusic('battle_tense');
  for (let i = 0; i < 600; i++) {
    ctx.currentTime += 1 / 60;
    audio.update(1 / 60);
  }
  assert.strictEqual(audio.getState().errors, 0);
  assert.ok(ctx.sources.length > 20, 'notes were scheduled');
  assert.ok(ctx.sources.length < 5000, 'sources: ' + ctx.sources.length);
  ctx.currentTime += 500;   // tab was asleep
  audio.update(0.016);
  assert.strictEqual(audio.getState().errors, 0);
});

test('a long track that finishes decoding after its mood started takes over from the stand-in', async () => {
  const bedFile = GameAudio.DEFAULT_EVENT_MAP.music.layers.bed.file;
  let finish;
  const { audio } = setup({ loader: (f) => (f === bedFile ? new Promise((r) => { finish = r; }) : Promise.resolve(null)) });
  await audio.unlock();
  audio.playMusic('title');
  assert.strictEqual(layerState(audio, 'bed').mode, 'synth');
  finish({ duration: 170 });
  await audio.ready();
  assert.strictEqual(layerState(audio, 'bed').mode, 'file');
  assert.strictEqual(audio.getState().errors, 0);
});

test('a loaded music file replaces the synthesized bed', async () => {
  const bedFile = GameAudio.DEFAULT_EVENT_MAP.music.layers.bed.file;
  const { audio, ctx } = await ready({ loader: (f) => Promise.resolve(f === bedFile ? { duration: 30 } : null) });
  audio.playMusic('title');
  assert.strictEqual(layerState(audio, 'bed').mode, 'file');
  const src = ctx.sources.filter((s) => s.kind === 'buffer' && s.buffer && s.buffer.duration === 30);
  assert.strictEqual(src.length, 1);
  assert.strictEqual(src[0].loop, true);
  audio.playMusic('battle_calm');
  assert.strictEqual(layerState(audio, 'rhythm').mode, 'synth');
});

test('event map file parses and every entry is valid', () => {
  const text = fs.readFileSync(path.join(ROOT, 'docs', 'audio_event_map.json'), 'utf8');
  const map = JSON.parse(text);
  assert.strictEqual(map.version, 1);
  const names = Object.keys(map.events);
  for (const req of REQUIRED_EVENTS) assert.ok(names.indexOf(req) >= 0, 'missing event ' + req);
  assert.strictEqual(names.length, REQUIRED_EVENTS.length, 'unexpected extra events');
  const sounds = new Set();
  const files = new Set();
  const sources = fs.readFileSync(path.join(ROOT, 'docs', 'audio_sources.md'), 'utf8');
  for (const name of names) {
    const e = map.events[name];
    const where = 'event ' + name;
    assert.ok(typeof e.sound === 'string' && /^[a-z0-9_]+$/.test(e.sound), where + ' sound id');
    assert.ok(!sounds.has(e.sound), where + ' sound id is unique');
    sounds.add(e.sound);
    assert.ok(e.file === null || (typeof e.file === 'string' && /^assets\/audio\/(sfx|music)\/[a-z0-9_]+\.ogg$/.test(e.file)), where + ' file');
    if (e.file) { assert.ok(!files.has(e.file), where + ' file is unique'); files.add(e.file); }
    assert.ok(typeof e.source === 'string' && e.source.length > 0, where + ' source');
    assert.ok((e.file === null) === (e.source === 'synth-only'), where + ': file null exactly when source is synth-only');
    if (e.source !== 'synth-only') assert.ok(sources.indexOf(e.source) >= 0, where + ' source key is documented in audio_sources.md');
    assert.ok(GameAudio.RECIPE_NAMES.indexOf(e.synth) >= 0, where + ' synth recipe exists: ' + e.synth);
    assert.ok(e.sparkle === null || GameAudio.RECIPE_NAMES.indexOf(e.sparkle) >= 0, where + ' sparkle');
    assert.ok(typeof e.volume === 'number' && e.volume > 0 && e.volume <= 1, where + ' volume');
    assert.ok(Array.isArray(e.pitch) && e.pitch.length === 2, where + ' pitch');
    assert.ok(e.pitch[0] <= e.pitch[1] && e.pitch[0] >= 0.94 && e.pitch[1] <= 1.06, where + ' pitch within +/- 6 %');
    assert.ok(Number.isInteger(e.priority) && e.priority >= 1 && e.priority <= 5, where + ' priority');
    assert.ok(GameAudio.BANDS.indexOf(e.band) >= 0, where + ' band');
    assert.ok(typeof e.duration === 'number' && e.duration > 0 && e.duration <= 60, where + ' duration');
    assert.strictEqual(typeof e.loop, 'boolean', where + ' loop');
    assert.strictEqual(typeof e.duck, 'boolean', where + ' duck');
    assert.ok(Number.isInteger(e.cooldownMs) && e.cooldownMs >= 0, where + ' cooldownMs');
  }
  const m = map.music;
  assert.ok(m.bpm >= 70 && m.bpm <= 90, 'tempo 70-90 BPM');
  assert.strictEqual(m.crossfadeSeconds, 1.5);
  assert.strictEqual(m.trimDb, -12);
  for (const layer of GameAudio.LAYER_NAMES) {
    const l = m.layers[layer];
    assert.ok(l, 'music layer ' + layer);
    assert.strictEqual(l.synth, 'music_' + layer);
    assert.ok(l.file === null || /^assets\/audio\/music\/[a-z0-9_]+\.(ogg|m4a)$/.test(l.file));
    assert.ok((l.file === null) === (l.source === 'synth-only'));
    if (l.source !== 'synth-only') assert.ok(sources.indexOf(l.source) >= 0, 'music source ' + l.source + ' documented');
  }
  for (const mood of ['title', 'battle_calm', 'battle_tense', 'victory', 'defeat']) {
    const md = m.moods[mood];
    assert.ok(md, 'mood ' + mood);
    for (const layer of GameAudio.LAYER_NAMES) {
      assert.ok(typeof md[layer] === 'number' && md[layer] >= 0 && md[layer] <= 1, mood + '.' + layer);
    }
    assert.ok(md.bed > 0, mood + ': the base bed always plays');
  }
});

test('the JSON file and the map embedded in js/audio.js are identical', () => {
  const map = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs', 'audio_event_map.json'), 'utf8'));
  assert.deepStrictEqual(map, GameAudio.DEFAULT_EVENT_MAP);
});

test('big impacts are exactly the events marked duck', () => {
  const ducking = Object.keys(GameAudio.DEFAULT_EVENT_MAP.events).filter((k) => GameAudio.DEFAULT_EVENT_MAP.events[k].duck).sort();
  assert.deepStrictEqual(ducking, ['impact_fence_break', 'impact_ground_heavy', 'impact_unit_heavy', 'ko', 'throw_bomb', 'throw_cannon']);
});

test('the module has no DOM, no Math.random, no Date', () => {
  const src = fs.readFileSync(path.join(ROOT, 'js', 'audio.js'), 'utf8').split('\n')
    .filter((l) => !/^\s*(\*|\/\/|\/\*)/.test(l)).join('\n');
  assert.ok(!/Math\.random|\bdocument\b|\bwindow\b|Date\.now|new Date/.test(src));
});

// ---------------------------------------------------------------------------

(async () => {
  let passed = 0;
  let failed = 0;
  for (const t of tests) {
    try {
      await t.fn();
      passed++;
      console.log('ok   ' + t.name);
    } catch (e) {
      failed++;
      console.log('FAIL ' + t.name + '\n     ' + (e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n     ') : e));
    }
  }
  console.log('test_audio: ' + passed + ' passed, ' + failed + ' failed');
  process.exit(failed ? 1 : 0);
})();
