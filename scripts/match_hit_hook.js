'use strict';
// The recorder that scripts/trace_match_hits.js and scripts/trace_ult_down.js install inside the page vm (wraps updatePhysics; see trace_match_hits.js header).
module.exports = `(function () {
  window.__rec = []; window.__mid = 0; window.__tick = 0; window.__wallMode = 'natural'; window.__wallAt = 0;
  var orig = updatePhysics;
  updatePhysics = function (dt) {
    window.__tick++; if (window.__wallMode === 'down' || (window.__wallMode === 'mid' && window.__tick >= window.__wallAt)) wallHp = 0;
    if (typeof hitStop === 'number' && hitStop > 0) return orig.apply(this, arguments);   // index.html returns early during hit-stop without stepping projectiles or hitCool
    var ps = projectiles.slice(), pos = ps.map(function (p) { return [p.x, p.y]; });
    var us = allUnits().map(function (u) { return { u: u, hp: u.hp, x: u.x, y: u.y, side: sideOfUnit(u) }; });
    var dt0 = arguments[0] || 0, cool0 = ps.map(function (p) { return (p.hitCool - dt0) > 0 ? 1 : 0; }),   /* the page lowers hitCool by dt BEFORE the contact test of the same step */ pier0 = ps.map(function (p) { return us.map(function (e) { return (p.pierced && p.pierced.has && p.pierced.has(e.u)) ? 1 : 0; }); });
    var w0 = wallHp, b0 = (shields.player.charges || 0) + (shields.ai.charges || 0) + (knightPts.length || 0) + (aiKnightPts.length || 0);
    var r = orig.apply(this, arguments);
    var w1 = wallHp, b1 = (shields.player.charges || 0) + (shields.ai.charges || 0) + (knightPts.length || 0) + (aiKnightPts.length || 0);
    for (var k = 0; k < ps.length; k++) {
      var p = ps[k]; if (p.delay > 0) continue;
      var shooterSide = p.team === "player" ? "left" : "right";
      for (var j = 0; j < us.length; j++) {
        var e = us[j]; if (e.side === shooterSide || e.hp <= 0) continue;
        var dx = p.x - e.x, dy = p.y - e.y, damaged = e.u.hp < e.hp;
        if ((Math.abs(dx) < 260 && dy > -320 && dy < 70) || damaged) {
          window.__rec.push({ tick: window.__tick, c: window.__mid, dir: shooterSide === "left" ? "L2R" : "R2L", hero: p.weapon, weapon: p.weapon, ang: p.throwId || 0, pw: k, wind: 0, step: window.__rec.length, hitR: projHitRadius(p), i: j, prof: e.u.profile || (e.side === "left" ? currentHero : ai.profile), side: e.side, px: p.x, py: p.y, ux: e.x, uy: e.y, hp0: e.hp, hp1: e.u.hp, cool: cool0[k], pierced: pier0[k][j], ult: p.ultThrow ? 1 : 0, ret: p.returning ? 1 : 0, area: (p.weapon === "proj_soundwave" || p.ultBlast || p.ultSwarm) ? 1 : 0, w0: w0, w1: w1, blocked: (b1 !== b0 || w1 !== w0) ? 1 : 0 });
        }
      }
    }
    return r;
  };
})();`;
