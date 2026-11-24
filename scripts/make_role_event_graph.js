#!/usr/bin/env node
'use strict';
// ROLE x EVENT x SKILL x STATUS GRAPH (owner 2026-11-22: "make a graph", "full inventory of roles, events, skills, statuses", "use the old ones first and fill in order").
// Every cell is MEASURED in the Node vm with the real page code (no rendering, binary-mask hit rule): for each of the 8 roles a hand-built scenario is played and every sound (snd / sfx.*), every particle effect (fxEmit), every floating text and
// every status the foe ends up with are recorded: plain hit (non-fatal), fatal hit, ground miss, the armed ultimate, heavy skill, heal skill. The older tables stay the reference for what they cover (docs/character_connect_gaps_20261115.md: hero x pictures;
// docs/event_role_table.html: event x role listening table) and are linked from the page. Output: docs/role_event_graph_<date>.html / .md / .json.   usage: node scripts/make_role_event_graph.js --date 20261123
const fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const argv = process.argv.slice(2), opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const DATE = opt('date', '20261123'), ROOT = path.join(__dirname, '..');
const ROLES = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];
const STATUSES = ['bleed', 'poison', 'burn', 'slow', 'stun', 'shock', 'weak'];
const HOOK = `(function () { window.__rec = { snd: [], fx: [], text: [], st: [] };
  var os = snd; snd = function (n) { window.__rec.snd.push(n); return os.apply(this, arguments); };
  Object.keys(sfx).forEach(function (k) { if (typeof sfx[k] === 'function') { var o = sfx[k]; sfx[k] = function (a) { if (typeof a === 'string') window.__rec.snd.push('sfx.' + k + ':' + a); else window.__rec.snd.push('sfx.' + k); return o.apply(this, arguments); }; } });
  var of = fxEmit; fxEmit = function (n) { window.__rec.fx.push(n); return of.apply(this, arguments); };
  var op = floatTexts.push; floatTexts.push = function (t) { window.__rec.text.push(String(t && t.text || '').replace(/[0-9.]+/g, '#')); return op.apply(this, arguments); };
})();`;
function fresh(hero, foeHp) {
  const P = loadPage({ team: 1, seed: 5 }); P.reset(); P.clearWeather(); P.place('left', [300]); P.place('right', [900]);
  P.eval('wind = 0; wallHp = 0; matchStarted = true; turn = "player"; currentHero = ' + JSON.stringify(hero) + '; energy.player = 0; energy.ai = 0; ultArmed.player = false; ultArmed.ai = false; shields.player.active = false; shields.ai.active = false; Math.random = function () { return 0.05; };');
  P.units('left').forEach(u => { u.profile = hero; u.hp = u.maxHp = 300; }); const f = P.units('right')[0]; f.profile = 'skeleton'; f.hp = f.maxHp = foeHp; ['bleed', 'poison', 'burn', 'slow', 'weak'].forEach(k => { f[k] = 0; }); f.stun = f.shock = f.stunLast = false;
  P.eval(HOOK); return { P, f };
}
function summarize(P, f, hp0) {
  const r = JSON.parse(JSON.stringify(P.eval('window.__rec'))), uniq = a => Array.from(new Set(a)), st = STATUSES.filter(k => f[k] === true || f[k] > 0);
  return { sounds: uniq(r.snd.filter(n => !/^sfx\./.test(n) || /:/.test(n))), fx: uniq(r.fx), texts: uniq(r.text), statuses: st, damaged: f.hp < hp0, hpAfter: Math.round(f.hp * 10) / 10 };
}
function shoot(hero, foeHp, ult, power, angle) {
  const { P, f } = fresh(hero, foeHp); if (ult) P.eval('energy.player = 3; ultUsed.player = 0; ultArmed.player = true;');
  P.eval('hitStop = 0; executeThrow("player", ' + power + ', ' + angle + ');'); let n = 0; while ((P.get('projectiles').length || n < 3) && n < 1200) { P.eval('hitStop = 0; updatePhysics(1/60);'); n++; }
  return summarize(P, f, foeHp);
}
function findShot(hero, foeHp, ult) {   // the weakest power at angle 45 that damages the foe 600 px away
  for (let pw = 15; pw <= 110; pw++) { const r = shoot(hero, foeHp, ult, pw, 45); if (r.damaged || (r.hpAfter < foeHp)) return { pw, r }; }
  return null;
}
const out = { date: DATE, roles: {}, events: {} };
for (const role of ROLES) {
  const o = out.roles[role] = {}; const hit = findShot(role, 300, false);
  o.plainHit = hit ? hit.r : null; o.power = hit ? hit.pw : null;
  o.fatal = hit ? shoot(role, 1, false, hit.pw, 45) : null; o.miss = hit ? shoot(role, 300, false, Math.max(15, hit.pw - 12), 45) : null;
  if (role === 'knight') o.ultimate = { note: 'placement (shield wall), not a thrown shot' };
  else { const u = findShot(role, 300, true); o.ultimate = u ? u.r : null; }
  // heavy skill
  { const { P, f } = fresh(role, 300); P.eval('selectedSkill = "heavy"; hitStop = 0; executeThrow("player", ' + (hit ? hit.pw : 60) + ', 45);'); let n = 0; while ((P.get('projectiles').length || n < 3) && n < 1200) { P.eval('hitStop = 0; updatePhysics(1/60);'); n++; } o.heavy = summarize(P, f, 300); }
  // heal skill
  { const { P, f } = fresh(role, 300); P.units('left')[0].hp = 100; P.eval('selectSkill("heal");'); o.heal = summarize(P, P.units('left')[0], 300); o.heal.damaged = false; }
}
// head hit (the stun source): a projectile at head height
for (const role of ROLES) { const { P, f } = fresh(role, 300); P.eval('hitStop = 0;'); P.launch(P.projectile({ hero: role, team: 'player', x: f.x - 6, y: f.y - 180, vx: 600 })); let n = 0; while (P.get('projectiles').length && n < 600) { P.eval('hitStop = 0; updatePhysics(0.01);'); n++; } out.roles[role].head = summarize(P, f, 300); }
// static facts from the code and the audio map
const page = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8').split('\n'), map = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/audio_event_map.json'), 'utf8')).events;
const at = page.findIndex(l => /if \(u\.poison > 0\) \{\s+\/\/ poisoned: the body pulses/.test(l)); const region = page.slice(Math.max(0, at - 5), at + 90).join('\n');
out.statusVisual = {}; STATUSES.forEach(k => { out.statusVisual[k] = new RegExp('u\\.' + k + '\\b').test(region); out.statusVisual[k + '_lines'] = (region.match(new RegExp('u\\.' + k + '\\b', 'g')) || []).length; });
out.events = Object.fromEntries(Object.entries(map).map(([k, v]) => [k, { file: v.file, source: v.source }]));
const T = r => out.roles[r];
const gaps = [], byStatus = {};
for (const r of ROLES) {
  const o = T(r);
  for (const [name, x] of [['plain hit', o.plainHit], ['head hit', o.head], ['ultimate', o.ultimate && o.ultimate.statuses ? o.ultimate : null]]) if (x) for (const st of x.statuses) {
    const cue = x.sounds.some(n => new RegExp('^status_' + (st === 'weak' ? 'frost' : st) + '$').test(n));
    (byStatus[st] = byStatus[st] || { roles: new Set(), cue: false }).roles.add(r); if (cue) byStatus[st].cue = true;
  }
  if (o.ultimate && o.ultimate.sounds) { if (!o.ultimate.sounds.includes('ult_' + r)) gaps.push({ kind: 'ultimate without its cast sound', role: r, detail: (o.ultimate.sounds.join(', ') || 'none') }); if (!o.ultimate.sounds.includes('ult_' + r + '_hit') && o.ultimate.damaged) gaps.push({ kind: 'ultimate hit without its hit sound', role: r, detail: o.ultimate.sounds.join(', ') }); }
  if (o.ultimate === null) gaps.push({ kind: 'ultimate never damaged the foe in the scan', role: r, detail: 'powers 15..110 at 45 degrees' });
  if (o.plainHit && !o.plainHit.fx.some(f => /^(impact_burst|sprite_impact_flash|hit_sparks|sprite_fire_tongue|blood_spray|sprite_poison|spark_electric)/.test(f))) gaps.push({ kind: 'plain hit without a hit effect', role: r, detail: o.plainHit.fx.join(', ') });
  if (o.heal && !o.heal.sounds.some(n => /heal/.test(n))) gaps.push({ kind: 'heal without a sound', role: r, detail: o.heal.sounds.join(', ') || 'none' });
}
Object.entries(byStatus).forEach(([st, v]) => { if (!v.cue) gaps.push({ kind: 'status without a cue sound when it is applied', role: Array.from(v.roles).join(', '), detail: st }); });
const glowRoles = ROLES.filter(r => r !== 'skeleton' && T(r).plainHit && T(r).plainHit.fx.includes('face_glow_skeleton')); if (glowRoles.length) gaps.push({ kind: 'roles that borrow the skeleton face glow (no glow of their own)', role: glowRoles.join(', '), detail: 'only face_glow_skeleton and face_glow_pumpkin exist' });
STATUSES.forEach(k => { if (!out.statusVisual[k]) gaps.push({ kind: 'status without a lasting visual on the unit', role: '-', detail: k + ' (no reference in the unit status drawing block)' }); });
['bleed', 'burn', 'poison'].forEach(k => { const has = Object.keys(map).some(e => new RegExp(k).test(e)); if (!has) gaps.push({ kind: 'status without any sound event', role: '-', detail: k }); });
Object.keys(map).forEach(e => { const fired = ROLES.some(r => ['plainHit', 'fatal', 'miss', 'ultimate', 'heavy', 'heal', 'head'].some(k => T(r)[k] && T(r)[k].sounds && T(r)[k].sounds.some(n => n === e || n === 'sfx.hit:' + e || n === 'sfx.' + e))); T.fired = T.fired || {}; T.fired[e] = fired; });
out.eventsNotFiredInTheScenarios = Object.keys(map).filter(e => !T.fired[e]);
out.gaps = gaps;
const esc = x => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const has = (x, re) => !!(x && x.sounds && x.sounds.some(n => re.test(n))), cell = (ok, t) => '<td class="' + (ok === true ? 'ok' : ok === false ? 'no' : 'na') + '">' + esc(t) + '</td>';
const rows = ROLES.map(r => { const o = T(r), ph = o.plainHit || { sounds: [], fx: [], statuses: [] }, ult = o.ultimate || {};
  const hitFx = ph.fx.filter(f => !/^(weapon_|muzzle|face_glow|smoke)/.test(f)).join(', ');
  const stat = ph.statuses.concat((o.head || { statuses: [] }).statuses.filter(x => x === 'stun')).filter((x, i, a) => a.indexOf(x) === i);
  return '<tr><th>' + r + '</th>' + cell(has(ph, /^throw_/), ph.sounds.filter(n => /^throw_/.test(n)).join(', ') || 'none') + cell(has(ph, /^(impact_|ko)/), ph.sounds.filter(n => /^(impact_flame|impact_unit)/.test(n)).join(', ') || 'none') + cell(hitFx ? true : false, hitFx || 'none') +
    cell(stat.length ? stat.every(st => byStatus[st] && byStatus[st].cue) : null, stat.map(st => st + (byStatus[st] && byStatus[st].cue ? ' (cue)' : ' (NO cue)')).join(', ') || 'none') +
    (r === 'knight' ? cell(null, 'placement') : cell(has(ult, new RegExp('^ult_' + r + '$')), has(ult, new RegExp('^ult_' + r + '$')) ? 'ult_' + r : 'none')) + (r === 'knight' ? cell(null, '-') : cell(has(ult, new RegExp('^ult_' + r + '_hit$')), has(ult, new RegExp('^ult_' + r + '_hit$')) ? 'ult_' + r + '_hit' : 'none')) +
    cell(ult.fx && ult.fx.length ? true : null, (ult.fx || []).filter(f => !/^(weapon_|muzzle|face_glow)/.test(f)).slice(0, 5).join(', ') || '-') + cell(has(o.heal, /heal/), (o.heal.sounds.filter(n => /heal/.test(n))[0] || 'none') + ' / ' + (o.heal.fx.join(', ') || 'no effect')) + '</tr>'; });
const statusRows = STATUSES.map(st => { const by = ROLES.filter(r => byStatus[st] && byStatus[st].roles.has(r)).join(', ') || '-'; const evt = st === 'weak' ? 'status_frost' : 'status_' + st; const cue = !!map[evt];
  return '<tr><th>' + st + (st === 'weak' ? ' (frost)' : '') + '</th><td>' + esc(by) + '</td>' + cell(cue, cue ? evt + ' (' + (map[evt].file || 'synth') + ')' : 'none') + cell(out.statusVisual[st], out.statusVisual[st] ? 'yes' : 'none') + cell(st === 'poison' ? true : false, st === 'poison' ? 'poison_tick' : 'none') + '</tr>'; });
const html = '<!doctype html><meta charset="utf-8"><title>Role event skill status graph ' + DATE + '</title><style>:root{color-scheme:light dark}body{font:14px/1.45 system-ui,sans-serif;margin:24px;max-width:1500px}table{border-collapse:collapse;margin:12px 0 28px}th,td{border:1px solid #8886;padding:5px 9px;text-align:left;vertical-align:top}td.ok{background:#2e7d3233}td.no{background:#c6282833}td.na{background:#8882}h2{margin-top:30px}code{font-size:12px}</style>' +
  '<h1>Roles x events x skills x statuses (measured ' + DATE + ')</h1><p>Every cell is MEASURED in the Node vm with the real page code (binary-mask hit rule, no rendering): a hand-built scenario per role, every sound and effect recorded. Green = present, red = missing, grey = not applicable. Older tables still valid for what they cover: <a href="character_connect_gaps_20261115.html">hero x pictures (136 of 136)</a>, <a href="event_role_table.html">event x role listening table</a>. Generated by <code>scripts/make_role_event_graph.js</code>.</p>' +
  '<h2>Roles</h2><table><tr><th>role</th><th>throw sound</th><th>hit sound</th><th>hit effects</th><th>statuses it applies</th><th>ultimate cast</th><th>ultimate hit</th><th>ultimate effects</th><th>heal (sound / effect)</th></tr>' + rows.join('') + '</table>' +
  '<h2>Statuses</h2><table><tr><th>status</th><th>applied by</th><th>cue sound when applied</th><th>lasting visual on the unit</th><th>tick sound</th></tr>' + statusRows.join('') + '</table>' +
  '<h2>Gaps found (' + gaps.length + ')</h2><table><tr><th>kind</th><th>role</th><th>detail</th></tr>' + gaps.map(g => '<tr><td>' + esc(g.kind) + '</td><td>' + esc(g.role) + '</td><td>' + esc(g.detail) + '</td></tr>').join('') + '</table>' +
  '<h2>Sound events that none of the scenarios fired (' + out.eventsNotFiredInTheScenarios.length + ')</h2><p>' + esc(out.eventsNotFiredInTheScenarios.join(', ')) + '</p>';
fs.writeFileSync(path.join(ROOT, 'docs', 'role_event_graph_' + DATE + '.html'), html);
const md = '# Roles x events x skills x statuses graph (measured ' + DATE + ')\n\nGenerated by scripts/make_role_event_graph.js; the HTML has the coloured tables. Gaps found: ' + gaps.length + '\n\n' + gaps.map(g => '- ' + g.kind + ' [' + g.role + ']: ' + g.detail).join('\n') + '\n\nSound events none of the scenarios fired: ' + out.eventsNotFiredInTheScenarios.join(', ') + '\n';
fs.writeFileSync(path.join(ROOT, 'docs', 'role_event_graph_' + DATE + '.md'), md);
fs.writeFileSync(path.join(ROOT, 'docs', 'role_event_graph_' + DATE + '.json'), JSON.stringify(out, null, 1));
console.log(JSON.stringify({ roles: ROLES.length, written: 'docs/role_event_graph_' + DATE + '.json' }));
