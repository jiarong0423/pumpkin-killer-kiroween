#!/usr/bin/env node
'use strict';
// Why does the HARD computer stop at about 0.385 direct hits per throw whatever its noise knobs are (owner 2026-11-19: "find the hard-level ceiling")?
// Full one-unit page matches (plain throws, both seats at the level), every throw recorded at the moment it leaves (side, angle, power, distance to the enemy, fence hp) and at the moment its projectile is gone
// (did the enemy lose hp, did the fence take it, where did it end). Output: per side, outcome shares and the hit rate by angle band.
//   node scripts/diagnose_ai_ceiling.js [--level hard] [--per-hero 12] [--seed-base 31000]
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');
const argv = process.argv.slice(2), opt = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : d; };
const level = opt('level', 'hard'), perHero = +opt('per-hero', 12), seedBase = +opt('seed-base', 31000), angleMin = opt('angle-min', null);   // --angle-min 25 plays the diagnosed level with the old minimum launch angle: reproduces the capped numbers of commit 23a02165 (0.384, fence 33 / 38 percent)
const ACUR = 'AI_ANGLE_MIN_BY_LEVEL = Object.freeze({ easy: 25, normal: 25, hard: 42 });', ATO = 'AI_ANGLE_MIN_BY_LEVEL = Object.freeze({ easy: ' + (level === 'easy' ? angleMin : 25) + ', normal: ' + (level === 'normal' ? angleMin : 25) + ', hard: ' + (level === 'hard' ? angleMin : 42) + ' });';
const HOOK = `(function () {
  window.__thr = []; var open = null, lastX = 0, lastY = 0;
  var oe = executeThrow;
  executeThrow = function (shooter, power, ang, thrower) {
    var r = oe.apply(this, arguments);
    var t = projectiles.length ? projectiles[projectiles.length - 1] : null;
    if (t && !open) { var side = shooter === 'player' ? 'left' : 'right', en = unitsOf(side === 'left' ? 'right' : 'left').filter(function (u) { return u.hp > 0; })[0], me = unitOf(side);
      open = { side: side, power: power, ang: ang === undefined ? null : ang, pAng: Math.round(Math.atan2(-t.vy, Math.abs(t.vx)) * 180 / Math.PI), dist: en ? Math.abs(en.x - me.x) : null, wall0: wallHp, hp0: en ? en.hp : 0, en: en }; }
    return r; };
  var up = updatePhysics;
  updatePhysics = function (dt) {
    var ps = projectiles.slice(); ps.forEach(function (p) { lastX = p.x; lastY = p.y; });
    var r = up.apply(this, arguments);
    if (open && projectiles.length === 0) { open.hit = open.en && open.en.hp < open.hp0 ? 1 : 0; open.wallHit = wallHp < open.wall0 ? 1 : 0; open.endX = lastX; open.enX = open.en ? open.en.x : null; window.__thr.push(open); open = null; }
    return r; };
})();`;
const rows = [];
D.HEROES.forEach((hero, hi) => { for (let k = 0; k < perHero; k++) {
  const seed = seedBase + 1000 * ['easy', 'normal', 'hard'].indexOf(level) + 100 * hi + k;
  const P = loadPage(angleMin === null ? { team: 1, seed } : { team: 1, seed, mutate: [[ACUR, ATO]] }); vm.runInContext(D.source, P.context, { filename: 'page_match_driver.js' }); vm.runInContext(HOOK, P.context);
  vm.runInContext('runPageMatch(' + JSON.stringify({ hero, size: 1, seed, tierLeft: level, tierRight: level, plainOnly: true }) + ')', P.context);
  Array.from(vm.runInContext('window.__thr', P.context)).forEach(t => rows.push({ side: t.side, ang: t.pAng, power: t.power, dist: t.dist, wallHit: t.wallHit, hit: t.hit, err: t.enX == null ? null : t.endX - t.enX }));
} });
const out = {};
for (const side of ['left', 'right']) {
  const r = rows.filter(x => x.side === side), n = r.length, hit = r.filter(x => x.hit).length, wall = r.filter(x => x.wallHit).length;
  const miss = r.filter(x => !x.hit && !x.wallHit && x.err != null), errs = miss.map(x => Math.abs(x.err)).sort((a, b) => a - b);
  const q = f => errs.length ? Math.round(errs[Math.floor(f * (errs.length - 1))]) : null;
  const bands = {}; for (const b of [[0, 30], [30, 40], [40, 50], [50, 60], [60, 70], [70, 90]]) { const s = r.filter(x => x.ang >= b[0] && x.ang < b[1]); if (s.length) bands[b[0] + '-' + b[1]] = { throws: s.length, hitRate: Math.round(s.filter(x => x.hit).length / s.length * 1000) / 1000, fenceShare: Math.round(s.filter(x => x.wallHit).length / s.length * 1000) / 1000 }; }
  out[side] = { throws: n, hitRate: Math.round(hit / n * 1000) / 1000, fenceShare: Math.round(wall / n * 1000) / 1000, missMedianAbsErrPx: q(0.5), missP90AbsErrPx: q(0.9), byAngle: bands };
}
console.log(JSON.stringify({ level, matches: D.HEROES.length * perHero, totalThrows: rows.length, rate: Math.round(rows.filter(x => x.hit).length / rows.length * 1000) / 1000, perSide: out }, null, 1));
