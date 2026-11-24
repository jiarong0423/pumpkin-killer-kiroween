/*
 * Pumpkin Killer - the ultimate ledger.
 *
 * Counts the pips that make an ultimate available, decides WHEN it may be armed,
 * and spends it. DOM-free and deterministic: no Math.random, no Date, no timers.
 * Works in Node (module.exports) and in the browser (global `Ultimate`).
 * Rules: docs/ultimate_rules.md and docs/owner_feedback_log.md (the log wins).
 * Spec: .kiro/specs/ultimate-ledger.
 *
 * Rules in one place
 *  - A hit that damages a unit adds ONE pip per throw. The same throwId never counts twice.
 *  - Pips cap at maxPips (3). Each side counts its own. At most maxUses (2) ultimates per side per match.
 *    Once a side has used them all its pips stop counting.
 *  - Arming is allowed only on the side's own turn, never on a defend turn, never when dead, never with
 *    fewer than maxPips pips, and at most once per side per round. There is no round-1 lockout and no
 *    "not two rounds in a row" lockout. cooldownRounds (default 0) is the one published lever to add one.
 *  - Arming can be cancelled for free.
 *  - consume() spends the ultimate at release even if the throw misses: pips go to 0, uses go up by 1.
 *    The ultimate throw itself gives 0 pips (pass its throwId so later hits of the same throw are ignored).
 *  - A KO'd unit loses its pips and its arming. The used count does not change.
 *
 * Every function takes plain data and returns plain objects. A bad argument never throws; it returns
 * { ok: false, reason } and changes nothing.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.Ultimate = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Published constants (names as in docs/ultimate_rules.md section 2g).
  var ULT_PIPS = 3;
  var ULT_MAX_PER_MATCH = 2;
  var ULT_PER_ROUND = 1;
  var ULT_COOLDOWN_ROUNDS = 0;
  var ULT_MULT = 1.5;   // total follow-up damage of an ultimate = ULT_MULT x the class's normal attack

  // Rejection reasons. The first six are the names the MCP tools use (docs/ultimate_rules.md 2g).
  var REASONS = {
    NOT_READY: 'ultimate_not_ready',
    NO_LEFT: 'no_ultimates_left',
    USED_THIS_ROUND: 'ultimate_used_this_round',
    DEAD: 'unit_dead',
    WRONG_PHASE: 'wrong_phase',
    WITH_DEFEND: 'ultimate_with_defend',
    COOLDOWN: 'ultimate_cooldown',
    ALREADY_ARMED: 'already_armed',
    NOT_ARMED: 'not_armed',
    UNKNOWN_SIDE: 'unknown_side',
    BAD_CONTEXT: 'bad_context',
    BAD_ROUND: 'bad_round',
    BAD_THROW_ID: 'bad_throw_id',
    DUPLICATE_THROW: 'duplicate_throw',
    PIPS_FULL: 'pips_full'
  };

  function isFiniteNumber(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function posInt(v, def) {
    return isFiniteNumber(v) && v >= 0 ? Math.floor(v) : def;
  }

  function validThrowId(id) {
    return (isFiniteNumber(id)) || (typeof id === 'string' && id !== '');
  }

  // Total ultimate damage per unit is ULT_MULT x normal, shared over the strikes, each rounded to 0.1
  // (the same rounding index.html uses for the shuriken volley and the knight's collisions).
  function splitDamage(normal, strikes) {
    var n = isFiniteNumber(normal) && normal > 0 ? normal : 0;
    var k = isFiniteNumber(strikes) && strikes >= 1 ? Math.floor(strikes) : 1;
    return Math.round(n * ULT_MULT / k * 10) / 10;
  }

  // options: { maxPips: 3, maxUses: 2, cooldownRounds: 0, sides: ['player', 'ai'] }
  function createLedger(options) {
    var cfg = options && typeof options === 'object' ? options : {};
    var maxPips = isFiniteNumber(cfg.maxPips) && cfg.maxPips >= 1 ? Math.floor(cfg.maxPips) : ULT_PIPS;
    var maxUses = isFiniteNumber(cfg.maxUses) && cfg.maxUses >= 1 ? Math.floor(cfg.maxUses) : ULT_MAX_PER_MATCH;
    var cooldown = posInt(cfg.cooldownRounds, ULT_COOLDOWN_ROUNDS);
    var sideNames = Array.isArray(cfg.sides) && cfg.sides.length > 0 ?
      cfg.sides.filter(function (s) { return typeof s === 'string' && s !== ''; }) : [];
    if (sideNames.length === 0) {
      sideNames = ['player', 'ai'];
    }

    var sides = Object.create(null);
    var seenRound = null;   // last round number given to canArm / arm / consume / getState

    function fresh() {
      return { pips: 0, uses: 0, armed: false, lastUseRound: null, counted: Object.create(null) };
    }

    function reset() {
      sides = Object.create(null);
      for (var i = 0; i < sideNames.length; i++) {
        sides[sideNames[i]] = fresh();
      }
      seenRound = null;
    }

    function get(side) {
      return typeof side === 'string' && sides[side] ? sides[side] : null;
    }

    function note(round) {
      if (isFiniteNumber(round)) {
        seenRound = round;
      }
    }

    // A hit that damaged a unit of the OTHER side. Returns { counted, pips, reason }.
    function registerHit(side, throwId) {
      var s = get(side);
      if (!s) {
        return { counted: false, pips: 0, reason: REASONS.UNKNOWN_SIDE };
      }
      if (!validThrowId(throwId)) {
        return { counted: false, pips: s.pips, reason: REASONS.BAD_THROW_ID };
      }
      var key = typeof throwId + ':' + String(throwId);
      if (s.counted[key]) {
        return { counted: false, pips: s.pips, reason: REASONS.DUPLICATE_THROW };
      }
      s.counted[key] = true;   // remembered even when no pip is added, so a later hit of the same throw cannot add one
      if (s.uses >= maxUses) {
        return { counted: false, pips: s.pips, reason: REASONS.NO_LEFT };
      }
      if (s.pips >= maxPips) {
        return { counted: false, pips: s.pips, reason: REASONS.PIPS_FULL };
      }
      s.pips++;
      return { counted: true, pips: s.pips, reason: null };
    }

    // ctx = { turn, side, round, defendTurn, dead }. Returns { ok, reason }.
    function canArm(side, ctx) {
      var s = get(side);
      if (!s) {
        return { ok: false, reason: REASONS.UNKNOWN_SIDE };
      }
      if (!ctx || typeof ctx !== 'object') {
        return { ok: false, reason: REASONS.BAD_CONTEXT };
      }
      if (!isFiniteNumber(ctx.round)) {
        return { ok: false, reason: REASONS.BAD_ROUND };
      }
      note(ctx.round);
      if (ctx.turn !== side || (ctx.side !== undefined && ctx.side !== side)) {
        return { ok: false, reason: REASONS.WRONG_PHASE };
      }
      if (ctx.dead === true) {
        return { ok: false, reason: REASONS.DEAD };
      }
      if (ctx.defendTurn === true) {
        return { ok: false, reason: REASONS.WITH_DEFEND };
      }
      if (s.armed) {
        return { ok: false, reason: REASONS.ALREADY_ARMED };
      }
      if (s.uses >= maxUses) {
        return { ok: false, reason: REASONS.NO_LEFT };
      }
      if (s.lastUseRound !== null && s.lastUseRound === ctx.round) {
        return { ok: false, reason: REASONS.USED_THIS_ROUND };
      }
      if (cooldown > 0 && s.lastUseRound !== null && ctx.round - s.lastUseRound <= cooldown) {
        return { ok: false, reason: REASONS.COOLDOWN };
      }
      if (s.pips < maxPips) {
        return { ok: false, reason: REASONS.NOT_READY };
      }
      return { ok: true, reason: null };
    }

    function arm(side, ctx) {
      var res = canArm(side, ctx);
      if (res.ok) {
        get(side).armed = true;
      }
      return res;
    }

    // Free: pips and used count stay as they are.
    function cancel(side) {
      var s = get(side);
      if (!s) {
        return { ok: false, wasArmed: false, reason: REASONS.UNKNOWN_SIDE };
      }
      var was = s.armed;
      s.armed = false;
      return { ok: true, wasArmed: was, reason: null };
    }

    // Spend the armed ultimate at release, hit or miss. throwId (optional) is the ultimate throw's id: hits of that throw give no pip.
    function consume(side, round, throwId) {
      var s = get(side);
      if (!s) {
        return { ok: false, reason: REASONS.UNKNOWN_SIDE };
      }
      if (!isFiniteNumber(round)) {
        return { ok: false, reason: REASONS.BAD_ROUND };
      }
      if (!s.armed) {
        return { ok: false, reason: REASONS.NOT_ARMED };
      }
      note(round);
      s.armed = false;
      s.pips = 0;
      s.uses++;
      s.lastUseRound = round;
      if (validThrowId(throwId)) {
        s.counted[typeof throwId + ':' + String(throwId)] = true;
      }
      return { ok: true, reason: null, uses: s.uses, remaining: Math.max(0, maxUses - s.uses) };
    }

    // The unit of this side was knocked out: pips and arming are lost, the used count is not spent.
    function registerKO(side) {
      var s = get(side);
      if (!s) {
        return { ok: false, reason: REASONS.UNKNOWN_SIDE };
      }
      s.pips = 0;
      s.armed = false;
      return { ok: true, reason: null };
    }

    // Public state (field names from docs/ultimate_rules.md 2g). round is optional and defaults to the last round seen.
    function getState(side, round) {
      var s = get(side);
      if (!s) {
        return null;
      }
      var r = isFiniteNumber(round) ? round : seenRound;
      return {
        ult_pips: s.pips,
        ult_ready: s.pips >= maxPips && s.uses < maxUses,
        ult_armed: s.armed,
        ultimates_remaining: Math.max(0, maxUses - s.uses),
        ultimates_used: s.uses,
        ult_used_this_round: r !== null && s.lastUseRound !== null && s.lastUseRound === r
      };
    }

    reset();

    return {
      registerHit: registerHit,
      canArm: canArm,
      arm: arm,
      cancel: cancel,
      consume: consume,
      registerKO: registerKO,
      getState: getState,
      reset: reset,
      maxPips: maxPips,
      maxUses: maxUses,
      cooldownRounds: cooldown,
      sides: sideNames.slice()
    };
  }

  return {
    createLedger: createLedger,
    splitDamage: splitDamage,
    REASONS: REASONS,
    ULT_PIPS: ULT_PIPS,
    ULT_MAX_PER_MATCH: ULT_MAX_PER_MATCH,
    ULT_PER_ROUND: ULT_PER_ROUND,
    ULT_COOLDOWN_ROUNDS: ULT_COOLDOWN_ROUNDS,
    ULT_MULT: ULT_MULT
  };
});
