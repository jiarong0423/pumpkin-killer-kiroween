#!/usr/bin/env node
'use strict';
// SANDBOX AUDIT, DATA ONLY, NO RENDERING (binary-mask rule: the page's own hit rule runs). Full computer-vs-computer page matches (1v1, 2v2, 3v3 in turn, every hero, easy/normal/hard, ULTIMATES ON: plainOnly false) in the Node vm; every sound event the page
// asks for (snd(...) and the sfx.* helpers), every hit report by weapon and kind (hero / ground / wall / shield ...), and two ghost-signal checks per physics step: HIT_SOUND_NO_DAMAGE (a hit sound played in a step in which nobody lost hp) and DAMAGE_NO_HIT_SOUND
// (somebody lost hp in a step without any hit sound). Chunks: --from N --matches M writes <out> (one JSON per chunk, atomic rename); --report a.json b.json ... merges chunks, adds the static wiring check against docs/audio_event_map.json and prints the table.
//   node scripts/audit_page_events.js --from 0 --matches 100 --out logs_local/audit/chunk_0.json     |     node scripts/audit_page_events.js --report logs_local/audit/chunk_*.json
const fs = require('fs'), path = require('path'), vm = require('vm');
const argv = process.argv.slice(2), opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : d; };
const ROOT = path.join(__dirname, '..');
if (argv.includes('--report')) { { const rest = argv.slice(argv.indexOf('--report') + 1), cut = rest.findIndex(a => a.startsWith('--')); report(cut < 0 ? rest : rest.slice(0, cut)); } process.exit(0); }
const { loadPage } = require('./page_harness'); const D = require('./page_match_driver');
const FROM = +opt('from', 0), N = +opt('matches', 10), OUT = opt('out', 'logs_local/audit/chunk.json'), SEEDBASE = +opt('seed-base', 71000);
const HEROES = ['skeleton', 'wizard', 'bat', 'knight', 'bride', 'hunchback', 'reaper', 'hag'], TIERS = ['easy', 'normal', 'hard'];
const HOOK = `(function () {
  window.__ev = {}; window.__col = {}; window.__anom = { hitSoundNoDamage: 0, damageNoHitSound: 0, steps: 0, ex: [] }; var log = []; var ev = window.__ev;
  function note(n) { ev[n] = (ev[n] || 0) + 1; log.push(n); }
  function isHit(n) { return n === 'ko' || /^impact_unit/.test(n) || n === 'impact_flame' || /^ult_.*_hit$/.test(n) || /^sfx\\.hit:(ko|impact_unit|impact_unit_heavy)/.test(n); }   // sounds that mean 'a unit was hurt' (the fence and ground impacts do not)
  var os = snd, lastStack = ''; snd = function (n) { note(n); return os.apply(this, arguments); };
  Object.keys(sfx).forEach(function (k) { if (typeof sfx[k] === 'function') { var o = sfx[k]; sfx[k] = function (a) { note('sfx.' + k + (typeof a === 'string' ? ':' + a : '')); if (a === 'ko') lastStack = String(new Error().stack).split('\\n').slice(2, 6).map(function (l) { return l.trim().replace(/\\(.*\\)/, ''); }).join(' < '); return o.apply(this, arguments); }; } });
  var ohr = pushHitReport; pushHitReport = function (p, t) { var key = (p.weapon || '?') + '|' + t; window.__col[key] = (window.__col[key] || 0) + 1; return ohr.apply(this, arguments); };
  var up = updatePhysics;
  updatePhysics = function (dt) {
    if (typeof hitStop === 'number' && hitStop > 0) return up.apply(this, arguments);
    var n0 = log.length, snap = function () { return allUnits().map(function (u) { return u.hp; }); }, hp0 = snap(), w0 = wallHp, pj = projectiles.map(function (p) { return p.weapon + (p.returning ? '(return)' : '') + (p.ultBoom ? '(boom)' : '') + (p.ultThrow ? '(ult)' : '') + (p.bounceN > 0 ? '(bounce)' : ''); }).join('+');   // per unit, so that a heal of another unit in the same step cannot hide a hit
    var r = up.apply(this, arguments); var fired = log.slice(n0), hp1 = snap(), a = window.__anom; a.steps++;
    var hitSnd = fired.some(isHit), dmg = hp1.some(function (h, i) { return h < hp0[i] - 1e-9; });
    if (hitSnd && !dmg) { a.hitSoundNoDamage++; if (a.ex.length < 6) a.ex.push('HIT_SOUND_NO_DAMAGE ' + fired.filter(isHit).join(',') + ' wall ' + w0 + '->' + wallHp + ' projectiles ' + pj + ' hp ' + hp0.map(function (h) { return Math.round(h); }).join('/') + ' stack ' + lastStack); }
    if (dmg && !hitSnd) { a.damageNoHitSound++; if (a.ex.length < 6) a.ex.push('DAMAGE_NO_HIT_SOUND hp ' + hp0.map(function (h) { return Math.round(h); }).join('/') + '->' + hp1.map(function (h) { return Math.round(h); }).join('/') + ' sounds ' + fired.join(',')); }
    return r;
  };
})();`;
let peakRss = 0;
const agg = { matches: 0, errors: 0, bySize: {}, ev: {}, col: {}, anom: { hitSoundNoDamage: 0, damageNoHitSound: 0, steps: 0, ex: [] }, winners: {}, throws: 0 };
for (let i = FROM; i < FROM + N; i++) {
  const size = [1, 2, 3][i % 3], hero = HEROES[(i * 3 + size) % 8], heroRight = HEROES[(i * 5 + 3) % 8], tier = TIERS[Math.floor(i / 3) % 3], seed = SEEDBASE + i;
  const P = loadPage({ team: size, seed }); vm.runInContext(D.source, P.context, { filename: 'page_match_driver.js' }); vm.runInContext(HOOK, P.context);
  let rec; try { rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify({ hero, heroRight, size, seed, tierLeft: tier, tierRight: tier, plainOnly: false }) + ')', P.context))); } catch (e) { agg.errors++; continue; }
  peakRss = Math.max(peakRss, process.memoryUsage().rss);
  agg.errors += rec.errors.length; agg.matches++; agg.throws += rec.throws || 0; agg.bySize[size] = (agg.bySize[size] || 0) + 1; agg.winners[rec.winner] = (agg.winners[rec.winner] || 0) + 1;
  const g = k => JSON.parse(JSON.stringify(vm.runInContext(k, P.context)));
  for (const [k, v] of Object.entries(g('window.__ev'))) agg.ev[k] = (agg.ev[k] || 0) + v;
  for (const [k, v] of Object.entries(g('window.__col'))) agg.col[k] = (agg.col[k] || 0) + v;
  const a = g('window.__anom'); agg.anom.hitSoundNoDamage += a.hitSoundNoDamage; agg.anom.damageNoHitSound += a.damageNoHitSound; agg.anom.steps += a.steps; a.ex.forEach(x => { if (agg.anom.ex.length < 12) agg.anom.ex.push('m' + i + ' size ' + size + ' ' + x); });
}
fs.mkdirSync(path.dirname(OUT), { recursive: true }); fs.writeFileSync(OUT + '.tmp', JSON.stringify(agg)); fs.renameSync(OUT + '.tmp', OUT);
console.log(JSON.stringify({ peakRssMB: Math.round(peakRss / 1048576), from: FROM, matches: agg.matches, errors: agg.errors, throws: agg.throws, steps: agg.anom.steps, hitSoundNoDamage: agg.anom.hitSoundNoDamage, damageNoHitSound: agg.anom.damageNoHitSound, out: OUT }));
function report(files) {
  const t = { matches: 0, errors: 0, bySize: {}, ev: {}, col: {}, anom: { hitSoundNoDamage: 0, damageNoHitSound: 0, steps: 0, ex: [] }, winners: {}, throws: 0 };
  for (const f of files) { const a = JSON.parse(fs.readFileSync(f, 'utf8')); t.matches += a.matches; t.errors += a.errors; t.throws += a.throws;
    for (const k of ['bySize', 'ev', 'col', 'winners']) for (const [x, v] of Object.entries(a[k])) t[k][x] = (t[k][x] || 0) + v;
    for (const k of ['hitSoundNoDamage', 'damageNoHitSound', 'steps']) t.anom[k] += a.anom[k]; a.anom.ex.forEach(x => { if (t.anom.ex.length < 12) t.anom.ex.push(x); }); }
  const map = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/audio_event_map.json'), 'utf8')), events = Object.keys(map.events || map);
  const src = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8') + fs.readdirSync(path.join(ROOT, 'js')).filter(f => f.endsWith('.js') && f !== 'audio.js').map(f => fs.readFileSync(path.join(ROOT, 'js', f), 'utf8')).join('\n');   // the event map itself (js/audio.js) is not a reference
  const fired = e => (t.ev[e] || 0) + Object.keys(t.ev).filter(k => k === 'sfx.' + e || k.startsWith('sfx.' + e + ':')).reduce((s, k) => s + t.ev[k], 0);
  const referenced = e => new RegExp('["\'`]' + e + '["\'`]').test(src);
  const rows = events.map(e => ({ event: e, fired: fired(e), referenced: referenced(e) }));
  const neverFired = rows.filter(r => !r.fired), unreferenced = rows.filter(r => !r.referenced);
  console.log(JSON.stringify({ matches: t.matches, errors: t.errors, throws: t.throws, bySize: t.bySize, physicsSteps: t.anom.steps, HIT_SOUND_NO_DAMAGE: t.anom.hitSoundNoDamage, DAMAGE_NO_HIT_SOUND: t.anom.damageNoHitSound, winners: t.winners }, null, 1));
  console.log('events in the audio map: ' + events.length + '; fired at least once: ' + rows.filter(r => r.fired).length + '; never fired in these matches: ' + neverFired.map(r => r.event + (r.referenced ? '' : ' (NOT referenced in code)')).join(', '));
  console.log('referenced nowhere in the page code: ' + (unreferenced.map(r => r.event).join(', ') || 'none'));
  console.log('hit reports (weapon|kind): ' + Object.entries(t.col).sort().map(([k, v]) => k + '=' + v).join('  '));
  console.log('examples: ' + (t.anom.ex.join(' || ') || 'none'));
  fs.writeFileSync(opt('write', 'logs_local/audit/merged.json'), JSON.stringify({ totals: t, events: rows }, null, 1));
}
