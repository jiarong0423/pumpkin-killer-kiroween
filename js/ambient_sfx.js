/*
 * Pumpkin Killer - ambient creature sounds: bat chirps with wing flutter, and ghost wails, made in code with Web Audio.
 * They are sprinkled in now and then (owner request 2026-11-09: "bats and ghosts, occasionally interspersed").
 *
 * UMD module: Node (module.exports) or the browser global `AmbientSfx`. No DOM, no Math.random, no clock:
 * the AudioContext, the random source and the destination node are injected, time comes from update(dt), so tests need no browser.
 *
 *   var amb = AmbientSfx.createAmbient({ ctx: audioCtx, random: Math.random, destination: audioCtx.destination });
 *   amb.update(dt);                 // once per frame
 *   amb.trigger('ghost');           // or 'bat', for a scripted moment (e.g. a KO)
 *   amb.setMuted(true); amb.setVolume(0.8);
 *
 * Every statement about how it sounds is unverified: the author cannot listen.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.AmbientSfx = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var MIN_GAP = 9;        // seconds between two random creature sounds (shortest)
  var MAX_GAP = 22;       // and longest
  var MAX_ACTIVE = 2;     // never more than two creature sounds at once
  var BASE_GAIN = 0.5;    // overall level of this layer (the music is much louder)

  // Real-recording kinds (docs/sound_mapping.md, section 2b). `buffer` kinds play only once a decoded buffer was given with setBuffer.
  // family gap = seconds before any sound of the same family may play again; long = counts against MAX_LONG.
  var KINDS = {
    crow:          { weight: 4, minGap: 25, volume: 0.45, pan: [[-0.9, 0.9]], pitch: [0.95, 1.05], family: 'animal',  long: false },
    cat_meow:      { weight: 1, minGap: 60, volume: 0.35, pan: [[-0.9, -0.5], [0.5, 0.9]], pitch: [0.97, 1.03], family: 'animal', long: false },
    dog_bark:      { weight: 1, minGap: 60, volume: 0.4,  pan: [[-0.9, -0.5], [0.5, 0.9]], pitch: [0.97, 1.03], family: 'animal', long: false },
    ghost_real:    { weight: 2, minGap: 30, volume: 0.8,  pan: [[-0.6, 0.6]], pitch: [0.97, 1.03], family: 'moan',    long: true, echo: true },
    ghost_moan1:   { weight: 2, minGap: 30, volume: 0.7,  pan: [[-0.6, 0.6]], pitch: [0.97, 1.03], family: 'moan',    long: true, echo: true },
    ghost_moan3:   { weight: 1, minGap: 40, volume: 0.7,  pan: [[-0.6, 0.6]], pitch: [0.97, 1.03], family: 'moan',    long: true, echo: true },
    zombie_moan:   { weight: 1, minGap: 60, volume: 0.4,  pan: [[-0.7, 0.7]], pitch: [0.97, 1.03], family: 'moan',    long: true },
    witch_cackle:  { weight: 2, minGap: 45, volume: 0.5,  pan: [[-0.8, 0.8]], pitch: [0.95, 1.05], family: 'voice',   long: false },
    ghost_cackle:  { weight: 1, minGap: 45, volume: 0.5,  pan: [[-0.8, 0.8]], pitch: [0.97, 1.03], family: 'voice',   long: true, echo: true },
    thunder:       { weight: 1, minGap: 90, volume: 0.5,  pan: [[-0.3, 0.3]], pitch: [0.94, 1.06], family: 'weather', long: true }
  };
  var FAMILY_GAP = { moan: 30, animal: 12, voice: 45, weather: 90 };
  var MAX_LONG = 1;
  var BED_GAIN = { night: 0.08, windMin: 0.04, windMax: 0.14 };
  var THROW_EVENTS = { throw_spear: 1, throw_shuriken: 1, throw_cannon: 1, throw_shield: 1 };
  var IMPACT_EVENTS = { impact_unit: 1, impact_unit_heavy: 1, impact_fence: 1, impact_fence_break: 1, impact_ground: 1, impact_ground_heavy: 1, shield_block: 1 };
  var HEAVY_EVENTS = { throw_cannon: 1, impact_unit_heavy: 1, impact_fence_break: 1, impact_ground_heavy: 1, ko: 1 };

  function createAmbient(cfg) {
    cfg = cfg || {};
    var ctx = cfg.ctx;
    var rnd = typeof cfg.random === 'function' ? cfg.random : function () { return 0.5; };
    var out = null;
    var muted = false;
    var volume = 0.8;
    var running = true;
    var timer = 0;
    var active = [];       // end times (in update seconds) of sounds that are still playing
    var clock = 0;
    var lastKind = '';
    var errors = 0;
    var buffers = {};      // optional real recordings by kind ('ghost'); the synthesized voice is the fallback
    var kindBuf = {};      // real recordings of the KINDS table
    var kindLast = {};     // clock time each kind last started
    var familyLast = {};   // clock time each family last started
    var recent = [];       // last kinds played, newest last
    var playing = [];      // { end, long, gain } sounds still playing
    var blockedUntil = 0;  // clock time until which nothing starts (KO, round bell, after a hit)
    var throwOpen = -1;    // clock time a throw started, -1 when none is in the air
    var heavyAt = -100;
    var mood = '';
    var beds = { buf: { night: null, wind: null }, cur: null, src: {}, gain: {}, wind: 0, out: null };

    function range(a, b) { return a + rnd() * (b - a); }
    function nextGap() { return range(MIN_GAP, MAX_GAP); }
    timer = nextGap();

    function ensureOut() {
      if (out || !ctx) return out;
      out = ctx.createGain();
      out.connect(cfg.destination || ctx.destination);
      applyLevel();
      return out;
    }
    function applyLevel() {
      if (out && out.gain) out.gain.value = muted ? 0 : BASE_GAIN * volume;
      if (beds.out && beds.out.gain) beds.out.gain.value = muted ? 0 : volume;
    }

    function noiseBuffer(seconds) {
      var n = Math.max(1, Math.floor(ctx.sampleRate * seconds));
      var b = ctx.createBuffer(1, n, ctx.sampleRate);
      var d = b.getChannelData(0);
      for (var i = 0; i < n; i++) d[i] = rnd() * 2 - 1;
      return b;
    }

    // Bat (owner: "it sounds like a bird"): not melodic chirps. A train of very short, dry echolocation clicks that speeds up
    // (the "feeding buzz"), a thin squeak, and leathery wing flaps made of low filtered noise. No sweeping pitch glides.
    function bat() {
      var t0 = ctx.currentTime + 0.02;
      var pan = range(-0.8, 0.8);
      var panner = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
      var bus = ctx.createGain();
      if (panner) { panner.pan.value = pan; bus.connect(panner); panner.connect(out); } else { bus.connect(out); }
      // clicks: 6 to 10 tiny bursts, the gap shrinks from about 90 ms to 25 ms
      var clicks = 6 + Math.floor(rnd() * 5);
      var t = t0;
      var gap = range(0.07, 0.11);
      for (var i = 0; i < clicks; i++) {
        var o = ctx.createOscillator();
        var g = ctx.createGain();
        var f0 = range(4200, 5600);
        o.type = 'square';
        o.frequency.setValueAtTime(f0, t);
        o.frequency.exponentialRampToValueAtTime(f0 * 0.42, t + 0.012);   // a very steep, very short drop: a click, not a song
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.16, t + 0.002);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.016);
        o.connect(g); g.connect(bus);
        o.start(t); o.stop(t + 0.03);
        t += gap;
        gap = Math.max(0.025, gap * range(0.72, 0.86));
      }
      // one thin, dry squeak at the end (a short saw through a narrow band, no glide)
      var sq = ctx.createOscillator(); var sg = ctx.createGain(); var sf = ctx.createBiquadFilter();
      sq.type = 'sawtooth'; sq.frequency.value = range(2600, 3300);
      sf.type = 'bandpass'; sf.frequency.value = 3000; sf.Q.value = 6;
      sg.gain.setValueAtTime(0.0001, t + 0.03);
      sg.gain.exponentialRampToValueAtTime(0.09, t + 0.045);
      sg.gain.exponentialRampToValueAtTime(0.0001, t + 0.11);
      sq.connect(sf); sf.connect(sg); sg.connect(bus);
      sq.start(t + 0.03); sq.stop(t + 0.13);
      // leathery wing flaps: low band-passed noise, 4 to 6 flaps about 90 ms apart
      var src = ctx.createBufferSource();
      src.buffer = noiseBuffer(0.7);
      var lp = ctx.createBiquadFilter();
      lp.type = 'bandpass'; lp.frequency.value = range(260, 420); lp.Q.value = 0.8;
      var fg = ctx.createGain();
      fg.gain.setValueAtTime(0.0001, t0);
      var flaps = 4 + Math.floor(rnd() * 3);
      for (var k = 0; k < flaps; k++) {
        var tk = t0 + 0.05 + k * 0.095;
        fg.gain.linearRampToValueAtTime(0.28 * (1 - k / (flaps + 2)), tk + 0.02);
        fg.gain.linearRampToValueAtTime(0.02, tk + 0.07);
      }
      fg.gain.linearRampToValueAtTime(0.0001, t0 + 0.7);
      src.connect(lp); lp.connect(fg); fg.connect(bus);
      src.start(t0); src.stop(t0 + 0.72);
      return (t - t0) + 0.8;
    }

    // Ghost: a breathy, vowel-like wail that rises and falls, two detuned voices with slow vibrato, an airy noise layer and a long echo.
    function ghostReal() {
      // a real recording (chosen by the owner) through a short fade and the same long echo
      var b = buffers.ghost;
      var t0 = ctx.currentTime + 0.03;
      var src = ctx.createBufferSource();
      src.buffer = b;
      var g = ctx.createGain();
      var dur = Math.min(b.duration, 4);
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.9, t0 + 0.15);
      g.gain.setValueAtTime(0.9, t0 + Math.max(0.2, dur - 0.5));
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      var delay = ctx.createDelay(1);
      delay.delayTime.value = 0.31;
      var fb = ctx.createGain(); fb.gain.value = 0.35;
      var wet = ctx.createGain(); wet.gain.value = 0.4;
      src.connect(g); g.connect(out);
      g.connect(delay); delay.connect(fb); fb.connect(delay); delay.connect(wet); wet.connect(out);
      src.start(t0); src.stop(t0 + dur + 0.05);
      return dur + 1.2;
    }

    function ghost() {
      if (buffers.ghost && buffers.ghost.duration > 0) return ghostReal();
      var t0 = ctx.currentTime + 0.03;
      var dur = range(1.7, 2.6);
      var base = range(190, 280);
      var bus = ctx.createGain();
      var formant = ctx.createBiquadFilter();
      formant.type = 'bandpass'; formant.frequency.setValueAtTime(520, t0); formant.frequency.linearRampToValueAtTime(880, t0 + dur * 0.5); formant.frequency.linearRampToValueAtTime(600, t0 + dur); formant.Q.value = 4;
      var low = ctx.createBiquadFilter();
      low.type = 'lowpass'; low.frequency.value = 2400;
      bus.gain.setValueAtTime(0.0001, t0);
      bus.gain.exponentialRampToValueAtTime(0.5, t0 + dur * 0.35);
      bus.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      formant.connect(low);
      low.connect(bus);
      [1, 1.007].forEach(function (det, idx) {
        var o = ctx.createOscillator();
        o.type = idx ? 'triangle' : 'sawtooth';
        o.frequency.setValueAtTime(base * det, t0);
        o.frequency.linearRampToValueAtTime(base * 1.5 * det, t0 + dur * 0.5);
        o.frequency.linearRampToValueAtTime(base * 1.12 * det, t0 + dur);
        var lfo = ctx.createOscillator(); var lg = ctx.createGain();
        lfo.frequency.value = range(4.6, 5.6); lg.gain.value = base * 0.018;
        lfo.connect(lg); lg.connect(o.frequency);
        var vg = ctx.createGain(); vg.gain.value = idx ? 0.35 : 0.22;
        o.connect(vg); vg.connect(formant);
        o.start(t0); o.stop(t0 + dur + 0.05);
        lfo.start(t0); lfo.stop(t0 + dur + 0.05);
      });
      var air = ctx.createBufferSource();
      air.buffer = noiseBuffer(dur);
      var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 2500;
      var ag = ctx.createGain(); ag.gain.value = 0.05;
      air.connect(hp); hp.connect(ag); ag.connect(bus);
      air.start(t0); air.stop(t0 + dur + 0.05);
      // echo
      var delay = ctx.createDelay(1);
      delay.delayTime.value = 0.27;
      var fb = ctx.createGain(); fb.gain.value = 0.42;
      delay.connect(fb); fb.connect(delay);
      var wet = ctx.createGain(); wet.gain.value = 0.5;
      bus.connect(out);
      bus.connect(delay); delay.connect(wet); wet.connect(out);
      return dur + 1.6;
    }

    function range2(r) { var seg = r[Math.floor(rnd() * r.length)]; return range(seg[0], seg[1]); }

    // One real recording through a short fade, a random pan, and (for voices) the same long echo as the ghost.
    function playFile(kind) {
      var spec = KINDS[kind]; var b = kindBuf[kind];
      var t0 = ctx.currentTime + 0.03;
      var src = ctx.createBufferSource();
      src.buffer = b;
      var rate = range(spec.pitch[0], spec.pitch[1]);
      if (src.playbackRate) src.playbackRate.value = rate;
      var dur = Math.min(b.duration / rate, 4.2);
      var g = ctx.createGain();
      var peak = spec.volume;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(peak, t0 + Math.min(0.12, dur / 3));
      g.gain.setValueAtTime(peak, t0 + Math.max(0.15, dur - 0.45));
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      var panner = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
      src.connect(g);
      if (panner) { panner.pan.value = range2(spec.pan); g.connect(panner); panner.connect(out); } else { g.connect(out); }
      if (spec.echo) {
        var delay = ctx.createDelay(1); delay.delayTime.value = 0.31;
        var fb = ctx.createGain(); fb.gain.value = 0.35;
        var wet = ctx.createGain(); wet.gain.value = 0.4;
        g.connect(delay); delay.connect(fb); fb.connect(delay); delay.connect(wet); wet.connect(out);
      }
      src.start(t0); src.stop(t0 + dur + 0.05);
      playing.push({ end: clock + dur + (spec.echo ? 1.2 : 0.1), long: spec.long, gain: g, fadeFrom: dur });
      return dur + (spec.echo ? 1.2 : 0.1);
    }

    function isBlocked() {
      if (clock < blockedUntil) return true;
      if (throwOpen >= 0 && clock - throwOpen < 12) return true;   // a throw is in the air (safety: expires after 12 s)
      if (mood === 'victory' || mood === 'defeat') return true;
      return false;
    }
    function longCount() { var n = 0; playing.forEach(function (p) { if (p.long && p.end > clock) n++; }); return n; }

    // The kinds that may start right now, with their weights (rules 2 to 5, 9 of the mapping table).
    function candidates() {
      var list = [];
      function ok(name, spec) {
        if (name === lastKind) return false;
        if (recent.slice(-2).indexOf(name) >= 0) return false;
        if (kindLast[name] !== undefined && clock - kindLast[name] < spec.minGap) return false;
        if (familyLast[spec.family] !== undefined && clock - familyLast[spec.family] < FAMILY_GAP[spec.family]) return false;
        if (spec.long && longCount() >= MAX_LONG) return false;
        if (name === 'thunder' && clock - heavyAt < 6) return false;
        return true;
      }
      Object.keys(KINDS).forEach(function (k) {
        if (kindBuf[k] && ok(k, KINDS[k])) list.push({ kind: k, weight: KINDS[k].weight });
      });
      var hasMoan = ['ghost_real', 'ghost_moan1', 'ghost_moan3'].some(function (k) { return !!kindBuf[k]; });
      if (!hasMoan && ok('ghost', { minGap: 0, family: 'moan', long: true })) list.push({ kind: 'ghost', weight: 2 });
      if (ok('bat', { minGap: 12, family: 'animal', long: false })) list.push({ kind: 'bat', weight: 4 });
      return list;
    }

    function trigger(kind) {
      try {
        if (!ctx || !running) return false;
        var real = KINDS[kind] && kindBuf[kind];
        if (!real && kind !== 'bat' && kind !== 'ghost') return false;
        if (active.length >= MAX_ACTIVE) return false;
        ensureOut();
        if (!out) return false;
        var len = real ? playFile(kind) : (kind === 'bat' ? bat() : ghost());
        active.push(clock + len);
        lastKind = kind;
        kindLast[kind] = clock;
        var fam = real ? KINDS[kind].family : (kind === 'bat' ? 'animal' : 'moan');
        familyLast[fam] = clock;
        recent.push(kind); if (recent.length > 4) recent.shift();
        if (!real) playing.push({ end: clock + len, long: kind === 'ghost', gain: null });
        return true;
      } catch (e) {
        errors++;
        return false;
      }
    }

    function pick() {
      var list = candidates();
      if (!list.length) return null;
      var total = 0; list.forEach(function (c) { total += c.weight; });
      var r = rnd() * total;
      for (var i = 0; i < list.length; i++) { r -= list[i].weight; if (r <= 0) return list[i].kind; }
      return list[list.length - 1].kind;
    }

    // Tell the layer what the game just did, so it keeps quiet around throws, KOs and bells (mapping table, rules 6 to 10).
    function notify(eventName) {
      if (THROW_EVENTS[eventName]) { throwOpen = clock; fadeLong(); }
      else if (IMPACT_EVENTS[eventName]) { if (throwOpen >= 0) { throwOpen = -1; blockedUntil = Math.max(blockedUntil, clock + 0.8); } }
      else if (eventName === 'ko') { blockedUntil = Math.max(blockedUntil, clock + 3); fadeLong(); }
      else if (eventName === 'round_start' || eventName === 'round_end') { blockedUntil = Math.max(blockedUntil, clock + 3); }
      if (HEAVY_EVENTS[eventName]) heavyAt = clock;
    }
    function fadeLong() {
      if (!ctx) return;
      var now = ctx.currentTime;
      playing.forEach(function (p) {
        if (p.gain && p.end > clock && p.long && p.gain.gain.cancelScheduledValues) {
          try { p.gain.gain.cancelScheduledValues(now); p.gain.gain.setValueAtTime(p.gain.gain.value || 0.3, now); p.gain.gain.linearRampToValueAtTime(0.0001, now + 0.25); } catch (e) { errors++; }
        }
      });
    }

    // ---- beds: one continuous loop at a time, crossfaded over 2 s, on their own bus
    function ensureBedBus() {
      if (beds.out || !ctx) return beds.out;
      beds.out = ctx.createGain();
      beds.out.connect(cfg.destination || ctx.destination);
      applyLevel();
      return beds.out;
    }
    function bedTarget(name) {
      if (name === 'night') return BED_GAIN.night;
      return BED_GAIN.windMin + (BED_GAIN.windMax - BED_GAIN.windMin) * beds.wind;
    }
    function setBed(name) {      // 'night', 'wind' or null
      try {
        if (!ctx || !running) return false;
        if (name !== 'night' && name !== 'wind') name = null;
        if (name === beds.cur) return true;
        ensureBedBus();
        var now = ctx.currentTime;
        ['night', 'wind'].forEach(function (k) {
          if (k === name) {
            if (!beds.buf[k]) return;
            if (!beds.src[k]) {
              var s = ctx.createBufferSource(); s.buffer = beds.buf[k]; s.loop = true;
              var g = ctx.createGain(); g.gain.setValueAtTime(0.0001, now);
              s.connect(g); g.connect(beds.out); s.start(now);
              beds.src[k] = s; beds.gain[k] = g;
            }
            beds.gain[k].gain.linearRampToValueAtTime(bedTarget(k), now + 2);
          } else if (beds.src[k]) {
            var old = beds.src[k]; var og = beds.gain[k];
            og.gain.linearRampToValueAtTime(0.0001, now + 2);
            try { old.stop(now + 2.1); } catch (e) { errors++; }
            beds.src[k] = null; beds.gain[k] = null;
          }
        });
        beds.cur = name;
        return true;
      } catch (e) { errors++; return false; }
    }
    function setWind(v) {        // 0..1, public wind divided by the maximum wind
      beds.wind = typeof v === 'number' && isFinite(v) ? Math.min(1, Math.abs(v)) : 0;
      if (beds.cur === 'wind' && beds.gain.wind && ctx) {
        try { beds.gain.wind.gain.linearRampToValueAtTime(bedTarget('wind'), ctx.currentTime + 1); } catch (e) { errors++; }
      }
    }

    function update(dt) {
      if (!(dt > 0) || !running) return;
      clock += dt;
      active = active.filter(function (e) { return e > clock; });
      playing = playing.filter(function (p) { return p.end > clock; });
      if (throwOpen >= 0 && clock - throwOpen >= 12) throwOpen = -1;
      timer -= dt;
      if (timer <= 0) {
        if (muted || isBlocked()) { timer = muted ? nextGap() : 1; return; }
        var kind = pick();
        if (kind) { timer = nextGap(); trigger(kind); } else { timer = 1; }
      }
    }

    return {
      trigger: trigger,
      update: update,
      notify: notify,
      setMood: function (m) { mood = typeof m === 'string' ? m : ''; },
      setBed: setBed,
      setWind: setWind,
      setMuted: function (b) { muted = !!b; applyLevel(); },
      setVolume: function (v) { if (typeof v === 'number' && v >= 0) volume = Math.min(1, v); applyLevel(); },
      setBuffer: function (kind, buf) {
        if (!(buf && buf.duration > 0)) return;
        if (kind === 'ghost') { buffers.ghost = buf; kindBuf.ghost_real = buf; }
        else if (kind === 'night' || kind === 'wind') { beds.buf[kind] = buf; }
        else if (KINDS[kind]) { kindBuf[kind] = buf; }
      },
      stop: function () { running = false; setBedOffSafe(); },
      getState: function () { return { muted: muted, volume: volume, active: active.length, nextIn: timer, errors: errors, last: lastKind, bed: beds.cur, blocked: isBlocked() }; }
    };
    function setBedOffSafe() { try { ['night', 'wind'].forEach(function (k) { if (beds.src[k]) { beds.src[k].stop(); beds.src[k] = null; } }); beds.cur = null; } catch (e) { errors++; } }
  }

  return { createAmbient: createAmbient, MIN_GAP: MIN_GAP, MAX_GAP: MAX_GAP, MAX_ACTIVE: MAX_ACTIVE };
});
