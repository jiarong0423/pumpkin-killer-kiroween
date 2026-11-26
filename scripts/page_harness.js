'use strict';
// Browser-free harness for the REAL inline script of index.html.
// It loads js/*.js (the page's <script src> list, in page order) and the page's own inline script into one Node vm context
// with permissive DOM stubs, so the real top-level functions (rotateTeam, updatePhysics, stepDice, resolveRound ...) can be
// driven and the real state (units, projectiles, gameOver ...) read back. No file is written, no network is touched.
//
//   const { loadPage } = require('./page_harness');
//   const P = loadPage({ team: 3 });                 // ?team=3 -> three units per side
//   P.eval('rotateTeam("left")'); P.get('activeIndex');
//   const M = loadPage({ team: 3, mutate: [[from, to]] });   // mutation: `from` must occur exactly once in the inline script
//
// Page-script top-level let/const live in the context's global lexical scope, so P.eval() (a later vm script in the
// same context) can read AND assign them. No export hook in index.html is needed.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const HTML = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');

// Everything touched by the page that has no meaning without a browser answers with a callable, iterable, number-coercible stub.
function makeStub(store) {
  const cache = store || Object.create(null);
  const target = function () {};
  return new Proxy(target, {
    get(t, k) {
      if (k === Symbol.toPrimitive) return () => 0;
      if (k === 'then') return undefined;
      if (k === Symbol.iterator) return function* () {};
      if (k === 'length') return 0;
      if (k === 'toString' || k === 'valueOf') return () => '';
      if (typeof k === 'symbol') return undefined;
      if (!(k in cache)) cache[k] = makeStub();
      return cache[k];
    },
    set(t, k, v) { cache[k] = v; return true; },
    has() { return true; },
    apply() { return makeStub(); },
    construct() { return makeStub(); }
  });
}

function pageScript(mutations) {
  const open = HTML.indexOf('<script>\n    // ====');
  if (open < 0) throw new Error('page_harness: inline script start marker not found');
  const bodyStart = open + '<script>'.length;
  const close = HTML.indexOf('\n  </script>', bodyStart);
  if (close < 0) throw new Error('page_harness: inline script end marker not found');
  let src = HTML.slice(bodyStart, close);
  for (const [from, to] of (mutations || [])) {
    const n = src.split(from).length - 1;
    if (n !== 1) { const e = new Error('page_harness: MUTATION_NOT_FOUND (' + n + ' matches): ' + from.slice(0, 80)); e.mutationNotFound = true; throw e; }
    src = src.replace(from, () => to);
  }
  return src;
}

function loadPage(opts) {
  opts = opts || {};
  const team = opts.team == null ? 1 : opts.team;   // opts.search overrides ?team=; opts.storage seeds localStorage (e.g. {pk_team_n:'3'}); opts.storageBlocked makes storage throw
  const timers = [];
  const store = new Map(Object.entries(opts.storage || {}));
  const teamButtons = [1, 2, 3].map(n => { const b = { dataset: { n: String(n) }, attrs: {}, handlers: {}, setAttribute(k, v) { b.attrs[k] = v; }, addEventListener(ev, fn) { b.handlers[ev] = fn; }, click() { if (b.handlers.click) b.handlers.click(); } }; return b; });   // the start screen's #team-size buttons
  const elements = Object.create(null);
  const getEl = id => elements[id] || (elements[id] = makeStub());
  const documentStub = makeStub();
  documentStub.getElementById = id => getEl(String(id));
  documentStub.createElement = () => makeStub();
  documentStub.querySelector = () => makeStub();
  documentStub.querySelectorAll = sel => (sel === '#team-size button' ? teamButtons : []);
  documentStub.addEventListener = () => {};
  documentStub.fonts = { load: () => Promise.reject(new Error('no fonts')) };
  documentStub.fullscreenElement = null;
  const canvasStub = getEl('gameCanvas');
  canvasStub.getContext = () => { const c = makeStub(); c.measureText = () => ({ width: 10 }); return c; };
  canvasStub.getBoundingClientRect = () => ({ left: 0, top: 0, width: 1920, height: 1080 });
  canvasStub.width = 1920; canvasStub.height = 1080;

  // Deterministic Math.random (mulberry32): the page rolls dice, shock, lifesteal and weather from it; a test must not flake.
  const SM = {}; Object.getOwnPropertyNames(Math).forEach(k => { SM[k] = Math[k]; });
  let seed = (opts.seed == null ? 20261117 : opts.seed) >>> 0;
  SM.random = () => { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const sandbox = {
    console: { log() {}, warn() {}, error() {}, info() {}, debug() {} },
    Math: SM, JSON, Date, Object, Array, Set, Map, WeakMap, WeakSet, Promise, Symbol, Error, TypeError, RangeError,
    parseInt, parseFloat, isNaN, isFinite, Number, String, Boolean, RegExp, Uint8Array, Uint32Array, Float64Array, Int32Array, ArrayBuffer, DataView, Proxy, Reflect, BigInt,
    encodeURIComponent, decodeURIComponent,
    URLSearchParams, URL, structuredClone, TextEncoder, TextDecoder,
    document: documentStub,
    location: { search: opts.search != null ? opts.search : (team > 1 ? '?team=' + team : ''), protocol: 'file:', hostname: '', host: '', href: 'file:///index.html', pathname: '/index.html', hash: '', origin: 'null' },
    navigator: { userAgent: 'node-harness', language: 'en', languages: ['en'], maxTouchPoints: 0, clipboard: makeStub(), serviceWorker: undefined },
    screen: { width: 1920, height: 1080, orientation: undefined },
    performance: { now: () => 0 },
    localStorage: { getItem: k => { if (opts.storageBlocked) throw new Error('storage blocked'); return store.has(k) ? store.get(k) : null; }, setItem: (k, v) => { if (opts.storageBlocked) throw new Error('storage blocked'); store.set(k, String(v)); }, removeItem: k => { store.delete(k); }, clear: () => store.clear() },
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    Audio: function () { return makeStub(); },
    Image: function () { return makeStub(); },
    AudioContext: undefined, webkitAudioContext: undefined,
    fetch: () => new Promise(() => {}),                     // never settles: I18N.loadDictionaries().then(init) never runs
    requestAnimationFrame: () => 0, cancelAnimationFrame: () => {},
    setTimeout: (fn, ms) => { timers.push({ fn, ms }); return timers.length; }, clearTimeout: () => {},
    setInterval: () => 0, clearInterval: () => {},
    matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
    addEventListener: () => {}, removeEventListener: () => {},
    innerWidth: 1920, innerHeight: 1080, devicePixelRatio: 1,
    visualViewport: undefined,
    getComputedStyle: () => makeStub(),
    WebSocket: function () { return makeStub(); },
    XMLHttpRequest: function () { return makeStub(); },
    CustomEvent: function () { return makeStub(); }, Event: function () { return makeStub(); },
    ResizeObserver: function () { return { observe() {}, disconnect() {} }; },
    IntersectionObserver: function () { return { observe() {}, disconnect() {} }; },
    crypto: { getRandomValues: a => a, randomUUID: () => '00000000-0000-4000-8000-000000000000', subtle: makeStub() },
    atob: s => Buffer.from(s, 'base64').toString('binary'), btoa: s => Buffer.from(s, 'binary').toString('base64')
  };
  sandbox.window = sandbox; sandbox.self = sandbox; sandbox.globalThis = sandbox;
  const context = vm.createContext(sandbox);

  // js/*.js exactly as the page's <script src> tags load them (relay-config.js is a deploy config, not game code).
  const srcs = [...HTML.matchAll(/<script src="(js\/[^"]+)"><\/script>/g)].map(m => m[1]);
  for (const s of srcs) {
    let code = fs.readFileSync(path.join(ROOT, s), 'utf8');
    for (const [from, to] of ((opts.mutateFiles || {})[s] || [])) {   // opts.mutateFiles = { 'js/comeback.js': [[from, to]] }: mutants of a module
      if (code.split(from).length - 1 !== 1) { const e = new Error('page_harness: MUTATION_NOT_FOUND in ' + s + ': ' + from.slice(0, 80)); e.mutationNotFound = true; throw e; }
      code = code.replace(from, () => to);
    }
    vm.runInContext(code, context, { filename: s });
  }
  // opts.bigHitOff: every throw passes the rare-big-hit rule, so tests of other damage rules see the uncapped numbers (scripts/test_big_hit.py covers the cap).
  if (opts.bigHitOff) vm.runInContext('Determinism = Object.assign({}, Determinism, { bigHitPass: function () { return true; } });', context);
  // The page script itself, optionally mutated (negative checks).
  const src = pageScript(opts.mutate);
  vm.runInContext(src, context, { filename: 'index.html#inline' });

  const P = {
    context, timers, store, teamButtons, location: sandbox.location, scriptLength: src.length, loadedScripts: srcs,
    eval: code => vm.runInContext(code, context),
    get: name => vm.runInContext(name, context),
    // ---- state helpers (all operate on the real page objects) ----
    units: side => Array.from(P.eval('unitsOf(' + JSON.stringify(side) + ')')),   // host-realm array of the REAL unit objects
    groundY: () => P.get('GROUND_Y'),
    // Put a team on given x positions with full hp (the page only spaces units at match start; clones all start on the same x).
    place(side, xs, hp) {
      const units = P.units(side);
      units.forEach((u, i) => { const x = xs[i] == null ? xs[xs.length - 1] : xs[i]; u.x = x; u.targetX = x; u.y = P.groundY(); u.hp = hp == null ? u.maxHp : hp; u.maxHp = Math.max(u.maxHp, u.hp); u.poison = 0; u.bleed = 0; u.burn = 0; u.stun = false; });
      return units;
    },
    setActive(side, i) { P.eval('setActiveUnit(' + JSON.stringify(side) + ', unitsOf(' + JSON.stringify(side) + ')[' + i + '])'); },
    activeId: side => P.eval('unitOf(' + JSON.stringify(side) + ')').id,
    // A projectile shaped exactly like the one executeThrow pushes (fields trail, recordedPath, flightDir, startX, dmg, wLen, wThick, weapon, team ...), built from the real HERO_PROFILES.
    projectile(o) {
      const prof = P.get('HERO_PROFILES')[o.hero];
      const flightDir = o.team === 'player' ? 1 : -1;
      const seq = P.eval('++throwSeq');
      return Object.assign({
        team: o.team, flightDir, aiAim: null, startX: o.x, weapon: prof.weapon, wLen: prof.wLen, wThick: prof.wThick, isHeavy: false,
        dmg: prof.dmg, x: o.x, y: o.y, vx: o.vx || 0, vy: o.vy || 0, trail: [], recordedPath: [{ x: o.x, y: o.y }], throwId: seq
      }, o.extra || {});
    },
    launch(p) { P.get('projectiles').push(p); return p; },
    // Run the REAL physics step until the projectile list is empty (or the step cap is hit). hitStop is cleared each step so an impact freeze never swallows a step.
    run(maxSteps, dt) {
      let n = 0;
      for (; n < (maxSteps || 400); n++) {
        if (P.get('projectiles').length === 0) break;
        P.eval('hitStop = 0');
        P.eval('updatePhysics(' + (dt || 0.01) + ')');
      }
      return n;
    },
    hp: side => P.units(side).map(u => u.hp),
    // Pin the weather to clear (the page draws rain/snow/fog from the match seed; attackMult and moveMult would change every expected number).
    clearWeather() { P.eval('weatherCache = { round: roundNum, scene: pickedScene, seed: matchSeed, w: WEATHER_CLEAR }'); },
    reset() {   // clean slate between scenarios inside one page instance
      P.eval('projectiles.length = 0; gameOver = null; hitStop = 0; turn = "player"; wallHp = 100; wind = 0; diceRoll = null; lastActedRight = null; setActiveUnit("left", teams.left[0]); setActiveUnit("right", teams.right[0]);');
      P.eval('allUnits().forEach(u => { u.stun = u.stunNow = u.stunLast = false; u.poison = 0; u.bleed = 0; u.burn = 0; u.shock = false; u.slow = 0; u.weak = 0; u.animState = "idle"; u.animProgress = 0; u.onRelease = null; })');
      P.eval('shields.player.active = false; shields.ai.active = false; floatTexts.length = 0; roundNum = 1');
      P.clearWeather();
    }
  };
  P.clearWeather();
  return P;
}

module.exports = { loadPage, makeStub, pageScript, HTML, ROOT };
