/*
 * Pumpkin Killer - class table and balance calculator.
 *
 * The eight playable classes mirrored from shared/heroes.json, plus a retained
 * historical provisional table and a hand model for hits to kill, expected
 * damage per throw, and the matchup matrix.
 * DOM-free and deterministic: no Math.random, no Date. Works in Node (module.exports) and in the browser
 * (global `ClassStats`). Spec: .kiro/specs/class-stats.
 *
 * Every figure here is a hand model or a table value. Nothing in this file has been played; scripts/sim_balance.js
 * is the check that does play it.
 *
 * Conventions
 *  - dmg  = what one hit does at full strength (the knight's dmg is the TOTAL over its die-decided collisions).
 *  - dTyp = the typical damage of one hit that the hits-to-kill table uses (judgement section 5). It differs from dmg
 *           for the bride (average over her falloff) and for the knight (hand estimate of what the bounces really deal).
 *  - speedScale multiplies the launch speed (power x 13.8). gravityScale and windScale multiply gravity and the wind
 *    acceleration for that class's projectile. All three are 1 unless noted.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.ClassStats = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var CLASS_KEYS = ['skeleton', 'wizard', 'bat', 'knight', 'bride', 'hunchback', 'reaper', 'hag'];

  // docs/class_stats_judgement.md section 8 and the task brief.
  var BAND = {
    rowMeanMin: 4.0,                   // 2026-11-28 owner: global attack x1.2 for faster match pace (wizard row mean 4.00, bride 4.88, others 5.00..7.13)
    typicalMin: 4, typicalMax: 9,      // hits to kill: typical band after 2026-11-28 global attack x1.2
    hardMin: 3, hardMax: 10,           // never below 3, never above 10
    typicalShareMin: 0.8,              // at least this share of the 64 cells must be inside the typical band
    winMin: 0.40, winMax: 0.60,        // one pairing
    classAvgMin: 0.45, classAvgMax: 0.55,
    roundsMin: 6, roundsMax: 12        // average match length (informational)
  };

  var ULT_MULT = 1.5;                  // docs/owner_feedback_log.md: each unit hit by an ultimate takes 1.5 x the normal attack

  // Knight, current rules of index.html: share of the total damage that lands, per die value 1..6, hand-worked in
  // docs/class_stats_judgement.md section 3 for a total of 30. direct = the first contact is the unit,
  // ground = the first contact is the ground and the shield skips into the unit.
  var KNIGHT_REF_TOTAL = 30;
  var KNIGHT_CURRENT = {
    direct: [30, 24.1, 20.5, 17.6, 15.4, 13.7],
    ground: [0, 15, 12, 9.8, 7.8, 6.8]
  };
  // What the 65-round playtest measured, converted (judgement section 4): the lower end of the knight's range.
  var KNIGHT_MEASURED = { ai: 4.8, bot: 10.1 };
  var KNIGHT_SKIP_SUCCESS = 0.4;       // rule A of docs/playtest_fixes.md (free ground skip), chance that the skip reaches the unit

  // Aim models (judgement section 2). A = half width of the landing spread in px, uniform around the target.
  // fenceFactor: the part of the throws that survives the fence and the wind (measured/model 0.85 to 0.93, judgement 0.88).
  var AIM = {
    ai: { A: 210, fenceFactor: 1.0, knightGround: 1 / 3 },
    bot: { A: 100, fenceFactor: 0.88, knightGround: 0.15 }
  };

  // Typical full-power range is the no-wind ground landing point measured from the unit:
  // launch.fwd + V cos(54°) * (V sin(54°) + sqrt((V sin(54°))² + 2 * 980 * launch.up)) / (980 * gravityScale),
  // where V = 100 * 13.8 * speedScale. This is the continuous form of sim_balance.js's fixed-step flight model.
  var TYPICAL_RANGE_POWER = 100;
  var TYPICAL_RANGE_ANGLE = 54 * Math.PI / 180;
  var TYPICAL_RANGE_GRAVITY = 980;

  function typicalRange(speedScale, gravityScale, launch) {
    var l = launch || { fwd: 58, up: 110 };
    var v = TYPICAL_RANGE_POWER * 13.8 * speedScale;
    var vy = v * Math.sin(TYPICAL_RANGE_ANGLE);
    var flight = (vy + Math.sqrt(vy * vy + 2 * TYPICAL_RANGE_GRAVITY * l.up)) /
      (TYPICAL_RANGE_GRAVITY * gravityScale);
    return l.fwd + v * Math.cos(TYPICAL_RANGE_ANGLE) * flight;
  }

  // Task 53 supplies the working flame profile; task 133 applies the owner decision that this is the existing `reaper` id.
  var REAPER_FLAME_CONSTANTS = {
    HP: 143,
    DAMAGE: 26,   // 2026-11-28 owner: global attack x1.2 (was 22)
    TYPICAL_DAMAGE: 26,
    HIT_HALF_WIDTH: 57,
    SPEED_SCALE: 1,
    GRAVITY_SCALE: 1,
    WIND_SCALE: 1,
    LAUNCH_FORWARD: 58,
    LAUNCH_UP: 110,
    BURN_DAMAGE: 2,
    BURN_TURNS: 3,
    ULTIMATE_FLAMES: 3
  };

  function reaperFlameProfile(source) {
    var r = REAPER_FLAME_CONSTANTS;
    var launch = { fwd: r.LAUNCH_FORWARD, up: r.LAUNCH_UP };
    return {
      key: 'reaper', name: '死靈法師', weapon: 'proj_flame', source: source,
      hp: r.HP, attack: r.DAMAGE, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(r.SPEED_SCALE, r.GRAVITY_SCALE, launch),
      dmg: r.DAMAGE, dTyp: r.TYPICAL_DAMAGE, hitHalfWidth: r.HIT_HALF_WIDTH,
      speedScale: r.SPEED_SCALE, gravityScale: r.GRAVITY_SCALE, windScale: r.WIND_SCALE,
      launch: launch,
      special: {
        burn: { damage: r.BURN_DAMAGE, turns: r.BURN_TURNS, nonLethal: true },
        soulflameVolley: { count: r.ULTIMATE_FLAMES }
      },
      ultKind: 'soulfire_volley', ultStrikes: 3
    };
  }

  function clone(o) {
    return JSON.parse(JSON.stringify(o));
  }

  function freeze(o) {
    Object.keys(o).forEach(function (k) {
      if (o[k] && typeof o[k] === 'object') {
        freeze(o[k]);
      }
    });
    return Object.freeze(o);
  }

  // ---------------------------------------------------------------------
  // The recommended table (docs/class_stats_judgement.md sections 1 and 6)

  var CLASSES = {
    skeleton: {
      key: 'skeleton', name: '骷髏長矛兵', weapon: 'proj_spear',
      hp: 150, attack: 29, defense: 0,
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 29, dTyp: 29, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { frost: { cut: 0.15, throws: 2 }, bleed: { damage: 2, turns: 2, nonLethal: true } },
      ultKind: 'ghost_spears', ultStrikes: 3
    },
    wizard: {
      key: 'wizard', name: '南瓜巫師', weapon: 'cannonball',
      hp: 124, attack: 43, defense: 0,
      range: typicalRange(1, 1, { fwd: 70, up: 118 }),
      dmg: 43, dTyp: 43, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 70, up: 118 },
      special: { poison: { damage: 2, turns: 2 } },
      ultKind: 'chain_blast', ultStrikes: 1
    },
    bat: {
      key: 'bat', name: '蝙蝠刺客', weapon: 'proj_shuriken',
      hp: 147, attack: 35, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 35, dTyp: 35, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { volley: { count: 5, spreadDeg: [-8, -4, 0, 4, 8], speedJitter: [0.95, 1.05] } },   // the volley is the ultimate
      ultKind: 'shuriken_scatter', ultStrikes: 5
    },
    knight: {
      key: 'knight', name: '南瓜重裝盾衛', weapon: 'proj_shield',
      hp: 198, attack: 25, defense: 0,
      range: typicalRange(1, 1, { fwd: 51, up: 73 }),
      dmg: 25, dTyp: 25, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 51, up: 73 },
      special: { bounce: { dieMin: 1, dieMax: 6, total: 25 } },
      ultKind: 'shield_chain', ultStrikes: 6
    },
    bride: {
      key: 'bride', name: '鬼娃新娘', weapon: 'proj_soundwave',
      hp: 149, attack: 48, defense: 0,
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 48, dTyp: 36, hitHalfWidth: 105,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { wave: { bands: [
        { maxDistance: 35, multiplier: 1 },
        { maxDistance: 70, multiplier: 0.75 },
        { maxDistance: 105, multiplier: 0.5 }
      ] }, poison: { damage: 2, turns: 2 } },
      ultKind: 'piercing_wail', ultStrikes: 1
    },
    hunchback: {
      key: 'hunchback', name: '鐘樓怪人', weapon: 'proj_axe',
      hp: 157, attack: 23, defense: 0,
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 23, dTyp: 23, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { knockback: { px: 50 }, bleed: { damage: 2, turns: 2, nonLethal: true } },
      ultKind: 'tower_toll', ultStrikes: 1
    },
    reaper: reaperFlameProfile('shared/heroes.json'),
    hag: {
      key: 'hag', name: '幽靈修女', weapon: 'proj_cross',
      hp: 158, attack: 29, defense: 0,
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 29, dTyp: 29, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: {},
      ultKind: 'cross_dart', ultStrikes: 1
    }
  };

  // ---------------------------------------------------------------------
  // The provisional table: what index.html holds today (HERO_PROFILES: hp, dmg, the frost curse of 30%, the
  // single shuriken of 20). The bride, hunchback and reaper are not in index.html yet; their numbers are the
  // INVENTED ones of docs/converge_characters.md with HP 100 (docs/review_reconcile.md C1).
  // scripts/test_class_stats.js reads index.html and fails if the four real classes drift from this table.

  var PROVISIONAL = {
    skeleton: {
      key: 'skeleton', name: '骷髏長矛兵', weapon: 'proj_spear', source: 'index.html HERO_PROFILES',
      hp: 100, attack: 24, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 24, dTyp: 24, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { frost: { cut: 0.3, throws: 2 } },
      ultKind: 'ghost_spears', ultStrikes: 3
    },
    wizard: {
      key: 'wizard', name: '南瓜巫師', weapon: 'cannonball', source: 'index.html HERO_PROFILES',
      hp: 85, attack: 28, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(1, 1, { fwd: 70, up: 118 }),
      dmg: 28, dTyp: 28, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 70, up: 118 },
      special: {},
      ultKind: 'chain_blast', ultStrikes: 1
    },
    bat: {
      key: 'bat', name: '蝙蝠刺客', weapon: 'proj_shuriken', source: 'index.html HERO_PROFILES',
      hp: 90, attack: 20, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 20, dTyp: 20, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { volley: { count: 5, spreadDeg: [-8, -4, 0, 4, 8], speedJitter: [0.95, 1.05] } },
      ultKind: 'shuriken_scatter', ultStrikes: 5
    },
    knight: {
      key: 'knight', name: '南瓜重裝盾衛', weapon: 'proj_shield', source: 'index.html HERO_PROFILES',
      hp: 120, attack: 30, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(1, 1, { fwd: 51, up: 73 }),
      dmg: 30, dTyp: 20, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 51, up: 73 },
      special: { bounce: { dieMin: 1, dieMax: 6, total: 30 } },
      ultKind: 'shield_chain', ultStrikes: 6
    },
    bride: {
      key: 'bride', name: '鬼娃新娘', weapon: 'proj_bouquet', source: 'docs/converge_characters.md (INVENTED), HP from docs/review_reconcile.md C1',
      hp: 100, attack: 12, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 12, dTyp: 12, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: { splash: { radius: 90 } },          // the bouquet bursts where it lands: 12 to every unit within 90 px
      ultKind: 'piercing_wail', ultStrikes: 1
    },
    hunchback: {
      key: 'hunchback', name: '鐘樓怪人', weapon: 'proj_bell', source: 'docs/converge_characters.md (INVENTED), HP from docs/review_reconcile.md C1',
      hp: 100, attack: 22, defense: 0, // PROVISIONAL: owner has not selected damage reduction.
      range: typicalRange(0.85, 1, { fwd: 58, up: 110 }),
      dmg: 22, dTyp: 22, hitHalfWidth: 70,
      speedScale: 0.85, gravityScale: 1, windScale: 0.6,
      launch: { fwd: 58, up: 110 },
      special: { knockback: { px: 100 } },
      ultKind: 'tower_toll', ultStrikes: 1
    },
    reaper: reaperFlameProfile('docs/kiro_53_recommendations.md working flame values'),
    hag: {
      key: 'hag', name: '幽靈修女', weapon: 'proj_cross', source: 'index.html HERO_PROFILES / shared/heroes.json',
      hp: 105, attack: 24, defense: 0,
      range: typicalRange(1, 1, { fwd: 58, up: 110 }),
      dmg: 24, dTyp: 24, hitHalfWidth: 70,
      speedScale: 1, gravityScale: 1, windScale: 1,
      launch: { fwd: 58, up: 110 },
      special: {},
      ultKind: 'cross_dart', ultStrikes: 1
    }
  };

  freeze(CLASSES);
  freeze(PROVISIONAL);

  // What index.html holds NOW (after the owner accepted Kiro's recommendations on 2026-11-09): the cat-bat at 26, the frost curse at 15 percent.
  // PROVISIONAL stays as the OLD values the judgement and its tests were written against.
  var CURRENT = JSON.parse(JSON.stringify(PROVISIONAL));
  CURRENT.bat.dmg = 22; CURRENT.bat.dTyp = 22; CURRENT.bat.attack = 22;
  CURRENT.wizard.dmg = 24; CURRENT.wizard.dTyp = 24; CURRENT.wizard.attack = 24;
  CURRENT.skeleton.special.frost.cut = 0.15;
  freeze(CURRENT);

  // ---------------------------------------------------------------------
  // lookup

  function tableOf(opts) {
    var t = opts && typeof opts === 'object' && opts.table ? opts.table : CLASSES;
    return t;
  }

  function classOf(key, table) {
    var t = table || CLASSES;
    if (typeof key !== 'string' || !Object.prototype.hasOwnProperty.call(t, key)) {
      throw new Error('Unknown class: ' + String(key));
    }
    return t[key];
  }

  // The public four-stat view deliberately omits balance-model implementation fields.
  function statsOf(key, table) {
    var c = classOf(key, table);
    return { hp: c.hp, defense: c.defense, range: c.range, attack: c.attack };
  }

  // ---------------------------------------------------------------------
  // hits to kill

  // Smallest n with n x damage >= hp. A tiny tolerance keeps 90 / 30 at exactly 3.
  function ceilDiv(hp, damage) {
    return Math.max(1, Math.ceil(hp / damage - 1e-9));
  }

  // opts: { table, damage: 'typical' (default, dTyp) | 'nominal' (attack) }.
  function hitsToKill(attackerKey, defenderKey, opts) {
    var table = tableOf(opts);
    var a = classOf(attackerKey, table);
    var d = classOf(defenderKey, table);
    var nominal = opts && opts.damage === 'nominal';
    var damage = nominal ? a.attack : a.dTyp;
    return ceilDiv(d.hp, damage * (1 - d.defense));
  }

  function keysOf(opts, table) {
    var keys = opts && Array.isArray(opts.keys) ? opts.keys.slice() : CLASS_KEYS.slice();
    keys.forEach(function (key) { classOf(key, table); });
    return keys;
  }

  // Square table: row = attacker, column = defender. `opts.keys` limits it for legacy hand-model comparisons.
  function matrix(opts) {
    var table = tableOf(opts);
    var keys = keysOf(opts, table);
    return keys.map(function (a) {
      return keys.map(function (d) {
        return hitsToKill(a, d, opts);
      });
    });
  }

  function matrixStats(m) {
    var all = [];
    var rowMeans = [];
    m.forEach(function (row) {
      var sum = 0;
      row.forEach(function (v) {
        all.push(v);
        sum += v;
      });
      rowMeans.push(sum / row.length);
    });
    var inBand = all.filter(function (v) { return v >= BAND.typicalMin && v <= BAND.typicalMax; }).length;
    return {
      min: Math.min.apply(null, all),
      max: Math.max.apply(null, all),
      mean: all.reduce(function (s, v) { return s + v; }, 0) / all.length,
      inTypicalBand: inBand,
      cells: all.length,
      rowMeans: rowMeans
    };
  }

  // Violations of the band: a list of { kind, attacker, defender, hits, message }. Empty list = inside the band.
  //   below_min / above_max  a cell under 3 or over 8 (hard)
  //   row_mean               a class whose average hits to kill, as attacker, leaves 4 to 6
  //   typical_share          fewer than 80% of the cells are inside 4 to 6
  function validate(opts) {
    var table = tableOf(opts);
    var keys = keysOf(opts, table);
    var m = matrix(opts);
    var out = [];
    m.forEach(function (row, i) {
      row.forEach(function (hits, j) {
        if (hits < BAND.hardMin) {
          out.push({ kind: 'below_min', attacker: keys[i], defender: keys[j], hits: hits,
            message: keys[i] + ' kills ' + keys[j] + ' in ' + hits + ' hits, under ' + BAND.hardMin });
        } else if (hits > BAND.hardMax) {
          out.push({ kind: 'above_max', attacker: keys[i], defender: keys[j], hits: hits,
            message: keys[i] + ' needs ' + hits + ' hits to kill ' + keys[j] + ', over ' + BAND.hardMax });
        }
      });
    });
    var st = matrixStats(m);
    st.rowMeans.forEach(function (mean, i) {
      if (mean < BAND.rowMeanMin || mean > BAND.typicalMax) {
        out.push({ kind: 'row_mean', attacker: keys[i], defender: null, hits: mean,
          message: keys[i] + ' averages ' + mean.toFixed(2) + ' hits to kill, outside ' + BAND.typicalMin + ' to ' + BAND.typicalMax });
        }
      });
    if (st.inTypicalBand / st.cells < BAND.typicalShareMin) {
      out.push({ kind: 'typical_share', attacker: null, defender: null, hits: st.inTypicalBand,
        message: st.inTypicalBand + ' of ' + st.cells + ' cells are in ' + BAND.typicalMin + ' to ' + BAND.typicalMax });
    }
    return out;
  }

  // ---------------------------------------------------------------------
  // expected damage

  // Damage of the bride's stepped sound wave at horizontal distance e (px).
  // These bands mirror SoundWave.BANDS, which the page uses for combat.
  function waveDamage(c, e) {
    var w = c.special && c.special.wave;
    var bands = w && Array.isArray(w.bands) ? w.bands : [];
    var x = Math.abs(e);
    for (var i = 0; i < bands.length; i++) {
      if (x <= bands[i].maxDistance) return c.dmg * bands[i].multiplier;
    }
    return 0;
  }

  // Mean wave damage given that it hit, with the landing error uniform in +-A (A in px). Midpoint rule, 0.5 px steps.
  function waveMeanDamage(c, A) {
    var top = Math.min(A, c.hitHalfWidth);
    var steps = Math.max(1, Math.round(top / 0.5));
    var sum = 0;
    for (var i = 0; i < steps; i++) {
      sum += waveDamage(c, (i + 0.5) * top / steps);
    }
    return sum / steps;
  }

  function aimModel(assumptions) {
    var a = assumptions && typeof assumptions === 'object' ? assumptions : {};
    var base = a.aim === 'ai' ? AIM.ai : AIM.bot;
    return {
      name: a.aim === 'ai' ? 'ai' : 'bot',
      A: typeof a.A === 'number' && isFinite(a.A) && a.A > 0 ? a.A : base.A,
      fenceFactor: typeof a.fenceFactor === 'number' && isFinite(a.fenceFactor) && a.fenceFactor > 0 ? a.fenceFactor : base.fenceFactor,
      knightGround: typeof a.knightGround === 'number' && isFinite(a.knightGround) ? a.knightGround : base.knightGround
    };
  }

  // Expected damage of the knight's throw. The die (1 to 6, even odds) and the ground-skip rule are both inside.
  //   rule 'current' (index.html today): judgement section 3 tables, scaled by total / 30.
  //     basis 'hand' = the hand model, 'measured' = the playtest figure, 'mid' (default) = their mean.
  //   rule 'A' (docs/playtest_fixes.md Fix 1): a unit contact always deals the full total (the die only sets the
  //     number of ticks), a ground contact skips once and then reaches the unit with chance 0.4.
  function knightDetail(c, m, assumptions) {
    var total = c.special && c.special.bounce ? c.special.bounce.total : c.dmg;
    var scale = total / KNIGHT_REF_TOTAL;
    var P = Math.min(1, c.hitHalfWidth / m.A);
    var rule = assumptions && assumptions.shieldRule === 'A' ? 'A' : 'current';
    var out = { rule: rule, P: P, pGround: m.knightGround, byDie: [] };
    var i;
    if (rule === 'A') {
      for (i = 0; i < 6; i++) {
        out.byDie.push({ die: i + 1, direct: total, ground: total * KNIGHT_SKIP_SUCCESS, ticks: i + 1 });
      }
      out.perThrow = total * (P + m.knightGround * KNIGHT_SKIP_SUCCESS);
      return out;
    }
    var directSum = 0;
    var groundSum = 0;
    for (i = 0; i < 6; i++) {
      var dd = KNIGHT_CURRENT.direct[i] * scale;
      var gg = KNIGHT_CURRENT.ground[i] * scale;
      out.byDie.push({ die: i + 1, direct: dd, ground: gg, ticks: i + 1 });
      directSum += dd;
      groundSum += gg;
    }
    var hand = P * (directSum / 6) + m.knightGround * (groundSum / 6);
    var measured = (m.name === 'ai' ? KNIGHT_MEASURED.ai : KNIGHT_MEASURED.bot) * scale;
    var basis = assumptions && (assumptions.knightBasis === 'hand' || assumptions.knightBasis === 'measured') ? assumptions.knightBasis : 'mid';
    out.hand = hand;
    out.measured = measured;
    out.basis = basis;
    out.perThrow = basis === 'hand' ? hand : basis === 'measured' ? measured : (hand + measured) / 2;
    return out;
  }

  // Everything behind expectedDamage, for tests and the report. assumptions:
  //   aim 'bot' (default, landing spread +-100 px) | 'ai' (+-210 px); A overrides the spread; fenceFactor overrides 0.88 / 1;
  //   table (class table, default CLASSES); shieldRule 'current' | 'A'; knightBasis 'hand' | 'measured' | 'mid'.
  function expectedDamageDetail(attackerKey, assumptions) {
    var table = tableOf(assumptions);
    var c = classOf(attackerKey, table);
    var m = aimModel(assumptions);
    var sp = c.special || {};
    var detail = { aim: m.name, A: m.A, fenceFactor: m.fenceFactor, hitProbability: 0, damageWhenHit: c.dmg, multiplier: 1, perThrow: 0 };
    if (sp.bounce) {
      var k = knightDetail(c, m, assumptions);
      detail.hitProbability = k.P;
      detail.knight = k;
      detail.damageWhenHit = k.perThrow / Math.max(k.P, 1e-9);
      detail.perThrow = k.perThrow;
      return detail;
    }
    var reach = sp.wave ? c.hitHalfWidth : (sp.splash ? Math.max(sp.splash.radius, c.hitHalfWidth) : c.hitHalfWidth);
    var P = Math.min(1, reach / m.A);
    var dmgWhenHit = sp.wave ? waveMeanDamage(c, m.A) : c.dmg;
    var mult = 1;
    if (sp.frost) {
      // A cursed victim deals less for `throws` throws. Share of the opponent's throws that are cursed = 1 - (1 - p)^2
      // with p the raw hit chance (judgement section 2).
      var coverage = 1 - Math.pow(1 - P, sp.frost.throws);
      mult = 1 / (1 - sp.frost.cut * coverage);
    }
    detail.hitProbability = P;
    detail.damageWhenHit = dmgWhenHit;
    detail.multiplier = mult;
    detail.perThrow = P * dmgWhenHit * m.fenceFactor * mult;
    return detail;
  }

  // Expected damage of one throw against one standing target, in HP.
  function expectedDamage(attackerKey, assumptions) {
    return expectedDamageDetail(attackerKey, assumptions).perThrow;
  }

  // Power = HP x expected damage. Two classes with equal power win equally often (judgement section 2).
  function power(key, assumptions) {
    var c = classOf(key, tableOf(assumptions));
    return c.hp * expectedDamage(key, assumptions);
  }

  // { key: { hp, edt, power, vsMean } } plus the mean power. vsMean = power / mean - 1.
  function powerTable(assumptions) {
    var table = tableOf(assumptions);
    var keys = CLASS_KEYS.filter(function (k) { return Object.prototype.hasOwnProperty.call(table, k); });
    var rows = {};
    var sum = 0;
    keys.forEach(function (k) {
      var edt = expectedDamage(k, assumptions);
      rows[k] = { hp: table[k].hp, edt: edt, power: table[k].hp * edt, vsMean: 0 };
      sum += rows[k].power;
    });
    var mean = sum / keys.length;
    keys.forEach(function (k) {
      rows[k].vsMean = rows[k].power / mean - 1;
    });
    return { rows: rows, mean: mean };
  }

  // ---------------------------------------------------------------------
  // ultimate numbers (docs/ultimate_mapping.md): each unit hit takes 1.5 x the normal attack

  function ultimatePerUnit(key, table) {
    var c = classOf(key, table);
    return Math.round(c.dmg * ULT_MULT * 10) / 10;
  }

  // Most one ultimate does to ONE unit: the trigger hit (a normal hit) plus the 1.5 x follow-up.
  // The bat's scatter has no trigger hit (docs/ultimate_mapping.md row 3), so it is only the 1.5 x.
  function ultimateOneTarget(key, table) {
    var c = classOf(key, table);
    var per = ultimatePerUnit(key, table);
    if (c.special && (c.special.volley || c.special.soulflameVolley)) {
      return per;
    }
    return Math.round((c.dmg + per) * 10) / 10;
  }

  // Pairs where one ultimate on a full-HP unit already kills it: [{ attacker, defender, total, hp }].
  function oneShotRisks(table) {
    var t = table || CLASSES;
    var out = [];
    CLASS_KEYS.forEach(function (a) {
      var total = ultimateOneTarget(a, t);
      CLASS_KEYS.forEach(function (d) {
        if (total >= t[d].hp) {
          out.push({ attacker: a, defender: d, total: total, hp: t[d].hp });
        }
      });
    });
    return out;
  }

  // ---------------------------------------------------------------------
  // comparison of two tables

  var FIELDS = ['hp', 'attack', 'defense', 'range', 'dmg', 'dTyp', 'hitHalfWidth', 'speedScale', 'gravityScale', 'windScale'];

  // What changed from `base` to `next`: field values, special blocks and the hits-to-kill cells.
  function compareTables(base, next) {
    var fields = [];
    var cells = [];
    CLASS_KEYS.forEach(function (k) {
      var a = base[k];
      var b = next[k];
      FIELDS.forEach(function (f) {
        if (a[f] !== b[f]) {
          fields.push({ cls: k, field: f, from: a[f], to: b[f] });
        }
      });
      if (JSON.stringify(a.special) !== JSON.stringify(b.special)) {
        fields.push({ cls: k, field: 'special', from: clone(a.special), to: clone(b.special) });
      }
    });
    var ma = matrix({ table: base });
    var mb = matrix({ table: next });
    CLASS_KEYS.forEach(function (att, i) {
      CLASS_KEYS.forEach(function (def, j) {
        if (ma[i][j] !== mb[i][j]) {
          cells.push({ attacker: att, defender: def, from: ma[i][j], to: mb[i][j] });
        }
      });
    });
    return { fields: fields, cells: cells };
  }

  // Plain-text 7 x 7 table, for the CLI and for reports.
  function formatMatrix(m) {
    var pad = function (s, n) { s = String(s); while (s.length < n) { s += ' '; } return s; };
    var lines = [pad('attacker \\ target', 18) + CLASS_KEYS.map(function (k) { return pad(k, 10); }).join('')];
    m.forEach(function (row, i) {
      lines.push(pad(CLASS_KEYS[i], 18) + row.map(function (v) { return pad(v, 10); }).join(''));
    });
    return lines.join('\n');
  }

  return {
    CLASS_KEYS: CLASS_KEYS,
    CLASSES: CLASSES,
    RECOMMENDED: CLASSES,
    PROVISIONAL: PROVISIONAL,
    CURRENT: CURRENT,
    BAND: BAND,
    AIM: AIM,
    ULT_MULT: ULT_MULT,
    KNIGHT_CURRENT: KNIGHT_CURRENT,
    REAPER_FLAME_CONSTANTS: freeze(clone(REAPER_FLAME_CONSTANTS)),
    statsOf: statsOf,
    typicalRange: typicalRange,
    hitsToKill: hitsToKill,
    expectedDamage: expectedDamage,
    expectedDamageDetail: expectedDamageDetail,
    power: power,
    powerTable: powerTable,
    matrix: matrix,
    matrixStats: matrixStats,
    validate: validate,
    waveDamage: waveDamage,
    waveMeanDamage: waveMeanDamage,
    ultimatePerUnit: ultimatePerUnit,
    ultimateOneTarget: ultimateOneTarget,
    oneShotRisks: oneShotRisks,
    compareTables: compareTables,
    cloneTable: clone,
    formatMatrix: formatMatrix
  };
});
