/*
 * Pumpkin Killer - shield knight A/B/C ultimate.
 *
 * Pure, deterministic state machine for the knight's hidden shield points.
 * Callers own presentation and pass a monotonic `time` to answer()/getReveal();
 * this module never reads a clock. Point locations never appear in publicView().
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.KnightUlt = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var MAX_POINTS = 3;
  var REQUIRED_PIPS = 3;
  var MAX_USES = 2;
  var POINT_HALF_WIDTH = 70; // Provisional until the owner sets the knight tolerance.
  var REVEAL_SECONDS = 1.4;  // Provisional owner-visible block reveal duration.
  var REASONS = {
    NOT_READY: 'ultimate_not_ready',
    WRONG_PHASE: 'wrong_phase',
    NOT_DEFENDING: 'not_defending',
    DEAD: 'unit_dead',
    NO_LEFT: 'no_ultimates_left',
    ALREADY_PLACING: 'already_placing',
    NOT_PLACING: 'not_placing',
    NO_PATHS: 'no_remembered_paths',
    BAD_PATH: 'bad_path',
    BAD_POINT: 'bad_point',
    NO_PENDING_POINT: 'no_pending_point',
    NO_POINTS: 'no_points_placed',
    NOT_LOCKED: 'not_locked',
    BAD_ATTACK: 'bad_attack',
    NOT_FIRST_PROJECTILE: 'not_first_projectile',
    DUPLICATE_THROW: 'duplicate_throw',
    KNOCKED_OUT: 'unit_knocked_out'
  };

  function finite(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function validId(v) {
    return finite(v) || (typeof v === 'string' && v !== '');
  }

  function pointAt(raw) {
    if (Array.isArray(raw) && raw.length >= 2 && finite(raw[0]) && finite(raw[1])) {
      return { x: raw[0], y: raw[1] };
    }
    if (raw && typeof raw === 'object' && finite(raw.x) && finite(raw.y)) {
      return { x: raw.x, y: raw.y };
    }
    return null;
  }

  function normalPath(raw) {
    if (!Array.isArray(raw) || raw.length < 2) return null;
    var out = [];
    for (var i = 0; i < raw.length; i++) {
      var p = pointAt(raw[i]);
      if (!p) return null;
      out.push(p);
    }
    return out;
  }

  // `s` is a normalized distance along the remembered path, not an x coordinate.
  // That keeps a placement valid for vertical or curved paths as well as flat ones.
  function pointOnPath(path, s) {
    if (!finite(s) || s < 0 || s > 1) return null;
    var lengths = [];
    var total = 0;
    for (var i = 1; i < path.length; i++) {
      var dx = path[i].x - path[i - 1].x;
      var dy = path[i].y - path[i - 1].y;
      var length = Math.sqrt(dx * dx + dy * dy);
      lengths.push(length);
      total += length;
    }
    if (total === 0) return copyPoint(path[0]);
    var wanted = total * s;
    var covered = 0;
    for (var j = 1; j < path.length; j++) {
      var segment = lengths[j - 1];
      if (wanted <= covered + segment || j === path.length - 1) {
        var ratio = segment === 0 ? 0 : (wanted - covered) / segment;
        var a = path[j - 1];
        var b = path[j];
        return { x: a.x + (b.x - a.x) * ratio, y: a.y + (b.y - a.y) * ratio };
      }
      covered += segment;
    }
    return null;
  }

  // A point is selected from a recorded flight path, so its zone is horizontal:
  // the projectile is blocked if any part of its first path overlaps that x interval.
  function crossesZone(path, x, halfWidth) {
    var left = x - halfWidth;
    var right = x + halfWidth;
    for (var i = 1; i < path.length; i++) {
      var low = Math.min(path[i - 1].x, path[i].x);
      var high = Math.max(path[i - 1].x, path[i].x);
      if (high >= left && low <= right) return true;
    }
    return false;
  }

  function copyPoint(point) {
    return point ? { x: point.x, y: point.y } : null;
  }

  function createKnightUlt(options) {
    var cfg = options && typeof options === 'object' ? options : {};
    var halfWidth = finite(cfg.pointHalfWidth) && cfg.pointHalfWidth >= 0 ? cfg.pointHalfWidth : POINT_HALF_WIDTH;
    var maxUses = finite(cfg.maxUses) && cfg.maxUses >= 1 ? Math.floor(cfg.maxUses) : MAX_USES;
    var pips = finite(cfg.pips) && cfg.pips >= 0 ? Math.min(REQUIRED_PIPS, Math.floor(cfg.pips)) : 0;
    var knightId = validId(cfg.knightId) ? cfg.knightId : null;
    var teamIds = Object.create(null);
    if (Array.isArray(cfg.teamIds)) {
      for (var teamIndex = 0; teamIndex < cfg.teamIds.length; teamIndex++) {
        if (validId(cfg.teamIds[teamIndex])) teamIds[typeof cfg.teamIds[teamIndex] + ':' + String(cfg.teamIds[teamIndex])] = true;
      }
    }
    if (knightId !== null) teamIds[typeof knightId + ':' + String(knightId)] = true;
    function isTeammate(id) {
      return validId(id) && teamIds[typeof id + ':' + String(id)] === true;
    }
    var mode = 'idle';
    var uses = 0;
    var paths = [];
    var points = [];
    var pending = null;
    var answered = 0;
    var seenThrows = Object.create(null);
    var reveal = null;

    function status() {
      return {
        state: mode,
        pips: pips,
        uses: uses,
        pointsPlaced: points.length,
        attacksAnswered: answered
      };
    }

    function publicView() {
      return { ult_points_left: mode === 'locked' ? points.length : 0 };
    }

    function setPips(value) {
      if (!finite(value) || value < 0) return { ok: false, reason: REASONS.NOT_READY };
      pips = Math.min(REQUIRED_PIPS, Math.floor(value));
      return { ok: true, reason: null, pips: pips };
    }

    // ctx = { ownTurn: true, defendMode: true, dead: false, rememberedPaths: [[{x, y}, ...], ...] }
    function begin(ctx) {
      if (!ctx || typeof ctx !== 'object') return { ok: false, reason: REASONS.WRONG_PHASE };
      if (ctx.dead === true) return { ok: false, reason: REASONS.DEAD };
      if (ctx.ownTurn !== true) return { ok: false, reason: REASONS.WRONG_PHASE };
      if (ctx.defendMode !== true) return { ok: false, reason: REASONS.NOT_DEFENDING };
      if (uses >= maxUses) return { ok: false, reason: REASONS.NO_LEFT };
      if (pips < REQUIRED_PIPS) return { ok: false, reason: REASONS.NOT_READY };
      if (mode === 'placing') return { ok: false, reason: REASONS.ALREADY_PLACING };
      if (mode === 'locked') return { ok: false, reason: REASONS.NOT_LOCKED };
      if (!Array.isArray(ctx.rememberedPaths) || ctx.rememberedPaths.length === 0) {
        return { ok: false, reason: REASONS.NO_PATHS };
      }
      paths = [];
      for (var i = 0; i < ctx.rememberedPaths.length && paths.length < 4; i++) {
        var path = normalPath(ctx.rememberedPaths[i]);
        if (path) paths.push(path);
      }
      if (paths.length === 0) return { ok: false, reason: REASONS.NO_PATHS };
      mode = 'placing';
      points = [];
      pending = null;
      answered = 0;
      seenThrows = Object.create(null);
      reveal = null;
      return { ok: true, reason: null };
    }

    // `s` is normalized along the selected remembered path. Earlier placements do
    // not constrain it, so A, B, and C may be placed back and forth or coincide.
    function place(pathId, s) {
      if (mode !== 'placing') return { ok: false, reason: REASONS.NOT_PLACING };
      if (!Number.isInteger(pathId) || pathId < 0 || pathId >= paths.length) {
        return { ok: false, reason: REASONS.BAD_PATH };
      }
      var selected = pointOnPath(paths[pathId], s);
      if (!selected) return { ok: false, reason: REASONS.BAD_POINT };
      pending = selected;
      return { ok: true, reason: null, pointsPlaced: points.length };
    }

    function spendAndLock() {
      pips = 0;
      uses++;
      mode = 'locked';
      pending = null;
      paths = [];
      return { ok: true, reason: null, spent: true, uses: uses, pointsPlaced: points.length };
    }

    // Commits the selected point. The third committed point spends the ultimate.
    function lock() {
      if (mode !== 'placing') return { ok: false, reason: REASONS.NOT_PLACING };
      if (!pending) return { ok: false, reason: REASONS.NO_PENDING_POINT };
      points.push(pending);
      pending = null;
      if (points.length >= MAX_POINTS) return spendAndLock();
      return { ok: true, reason: null, spent: false, pointsPlaced: points.length };
    }

    // A turn ending early keeps committed points. A plan with no committed point costs nothing.
    function endTurn() {
      if (mode !== 'placing') return { ok: false, reason: REASONS.NOT_PLACING };
      pending = null;
      if (points.length === 0) {
        mode = 'idle';
        paths = [];
        return { ok: true, reason: null, spent: false, pointsPlaced: 0 };
      }
      return spendAndLock();
    }

    function cancel() {
      if (mode !== 'placing') return { ok: false, reason: REASONS.NOT_PLACING };
      mode = 'idle';
      points = [];
      pending = null;
      paths = [];
      return { ok: true, reason: null };
    }

    // attack = { projectilePath, targetId, throwId?, projectileIndex?, time? }.
    // projectilePath and targetId are the required public attack facts. throwId is
    // optional bookkeeping for callers that identify repeat notifications.
    function answer(attack) {
      if (mode !== 'locked') return { ok: false, reason: REASONS.NOT_LOCKED, blocked: false };
      if (!attack || typeof attack !== 'object' || !validId(attack.targetId)) {
        return { ok: false, reason: REASONS.BAD_ATTACK, blocked: false };
      }
      if (attack.projectileIndex !== undefined && attack.projectileIndex !== 0) {
        return { ok: true, reason: REASONS.NOT_FIRST_PROJECTILE, blocked: false };
      }
      var key = validId(attack.throwId) ? typeof attack.throwId + ':' + String(attack.throwId) : null;
      if (key && seenThrows[key]) return { ok: true, reason: REASONS.DUPLICATE_THROW, blocked: false };
      var path = normalPath(attack.projectilePath);
      if (!path) return { ok: false, reason: REASONS.BAD_ATTACK, blocked: false };
      // Other teams' attacks do not consume a prediction or an attack slot.
      if (!isTeammate(attack.targetId)) {
        return { ok: true, reason: null, blocked: false, reveal: null, reveal_seconds: 0, ult_points_left: publicView().ult_points_left };
      }
      if (key) seenThrows[key] = true;
      answered++;
      var point = points.length ? points[0] : null;
      var blocked = point && crossesZone(path, point.x, halfWidth);
      var shown = null;
      if (blocked) {
        points.shift();
        var at = finite(attack.time) ? attack.time : 0;
        reveal = { point: copyPoint(point), until: at + REVEAL_SECONDS };
        shown = copyPoint(point);
      }
      // A point plan covers at most the next three relevant enemy attacks, whether
      // they cross its zone or not.
      if (answered >= MAX_POINTS || points.length === 0) {
        points = [];
        mode = 'spent';
      }
      return {
        ok: true,
        reason: null,
        blocked: !!blocked,
        reveal: shown,
        reveal_seconds: blocked ? REVEAL_SECONDS : 0,
        ult_points_left: publicView().ult_points_left
      };
    }

    function getReveal(time) {
      if (!reveal || !finite(time) || time > reveal.until) return null;
      return { position: copyPoint(reveal.point), until: reveal.until };
    }

    function registerKO() {
      pips = 0;
      points = [];
      pending = null;
      paths = [];
      reveal = null;
      mode = 'spent';
      return { ok: true, reason: null };
    }

    return {
      setPips: setPips,
      begin: begin,
      place: place,
      lock: lock,
      endTurn: endTurn,
      cancel: cancel,
      answer: answer,
      getReveal: getReveal,
      registerKO: registerKO,
      publicView: publicView,
      getStatus: status,
      pointHalfWidth: halfWidth,
      maxUses: maxUses
    };
  }

  return {
    createKnightUlt: createKnightUlt,
    MAX_POINTS: MAX_POINTS,
    REQUIRED_PIPS: REQUIRED_PIPS,
    MAX_USES: MAX_USES,
    POINT_HALF_WIDTH: POINT_HALF_WIDTH,
    REVEAL_SECONDS: REVEAL_SECONDS,
    REASONS: REASONS
  };
});
