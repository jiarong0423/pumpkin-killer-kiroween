/*
 * Pumpkin Killer - headless balance simulator.
 *
 * Plays full 1 v 1 matches with the same physics as index.html and a seeded bot, and counts who wins.
 * DOM-free and deterministic: every random draw comes from one seeded generator (no Math.random, no Date).
 * Works in Node (module.exports + a command line) and in the browser (global `SimBalance`).
 * Spec: .kiro/specs/balance-sim. Bands: docs/class_stats_judgement.md section 8.
 *
 * Command line (Node):
 *   node scripts/sim_balance.js --matches 200 --seed 7
 *   options: --table recommended|provisional  --agent-level easy|normal|hard  --aim-error 9  --max-rounds 60  --classes skeleton,bat  --shield-rule current|A  --json
 *   prints the win-rate matrix and exits with 1 if a band is violated.
 *
 * Same as index.html (read only; a test checks the constants against the file):
 *   fixed step 1/60 s, gravity 980, wind acceleration 56 (tailwind) / 84 (headwind) px/s^2 per wind unit, launch speed power x 13.8,
 *   ground y 860, fence x 960 / width 130 / height 250 (15 damage per hit, 100 HP), hit box |dx| <= 70 px and a 190 px body,
 *   wind rerolled every round in [-4, 4] with one decimal, one throw per unit per turn, the left side acts first.
 * Different or left out, on purpose:
 *   - no sky shield, no airdrops, no heal, no skills; moving is only the forward die when the target is out of reach.
 *   - only the cat's ultimate (the 5-shuriken volley) is played. The other classes' pips are counted but never spent.
 *   - the bot receives a noisy reading of the public target position and HUD wind, using the normal-level knobs
 *     copied from scripts/agent_levels.py. It never receives exact state or a hidden aiming value.
 */
(function (root, factory) {
  'use strict';
  var deps;
  if (typeof module === 'object' && module && module.exports && typeof require === 'function') {
    deps = { ClassStats: require('../js/class_stats.js'), Ultimate: require('../js/ultimate.js'), Weather: require('../js/weather.js') };
  } else {
    deps = { ClassStats: root.ClassStats, Ultimate: root.Ultimate, Weather: root.Weather };
  }
  var api = factory(deps.ClassStats, deps.Ultimate, deps.Weather);
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.SimBalance = api;
  }
})(typeof self !== 'undefined' ? self : this, function (ClassStats, Ultimate, Weather) {
  'use strict';

  // ---- constants copied from index.html (scripts/test_sim_balance.js compares them with the file)
  var DT = 1 / 60;
  var GRAVITY = 980;
  var V0_PER_POWER = 13.8;
  var WIND_TAIL = 56;    // wind blowing the way the shot travels (owner 2026-11-16)
  var WIND_HEAD = 84;    // wind against the shot
  function windAccelFor(wind, dirX) { return wind * (wind * dirX > 0 ? WIND_TAIL : WIND_HEAD); }
  function effectiveWind(wind, weather) {
    var bonus = weather && isFiniteNumber(weather.windBonus) ? weather.windBonus : 0;
    return wind === 0 ? 0 : wind + (wind < 0 ? -bonus : bonus);
  }
  function weatherOf(id) {
    var key = typeof id === 'string' ? id : 'clear';
    var source = Weather && Weather.WEATHER ? Weather.WEATHER : {
      clear: { attackMult: 1, moveMult: 1, windBonus: 0 }
    };
    if (!Object.prototype.hasOwnProperty.call(source, key)) {
      key = 'clear';
    }
    var base = source[key];
    return { id: key, attackMult: base.attackMult, moveMult: base.moveMult, windBonus: base.windBonus };
  }
  var WIND_MAX = 4;
  var GROUND_Y = 860;
  var FENCE_X = 960;
  var FENCE_W = 238;   // the collision equals the drawn gate (2026-11-18); shared/constants.json is the source and test_sim_balance.js pins it
  var FENCE_H = 282;
  var WALL_HP = 100;
  var WALL_DMG = 8;   // owner 2026-11-10: the wall is sturdier (was 15); must equal WALL_HIT_DMG in index.html
  var BODY_H = 190;
  var DICE_STEP_PX = 36;
  var MOVE_RANGE = { a: [110, 640], b: [1280, 1810] };   // index.html: forward limits 640 / 1280 since 2026-11-18 (were 680 / 1240), retreat limits 110 / 1810; aligned here 2026-11-19 (arbitration)
  var START_RANGE = { a: [220, 620], b: [1280, 1680] };   // randomizePositions()
  var ANGLE_DEFAULT = 54;
  // Copied from scripts/agent_levels.py LEVELS. The simulator is JavaScript, so it cannot import that Python map.
  // These are perception errors on public HUD information, not access to exact internal state.
  var PUBLIC_AGENT_LEVELS = {
    easy: { perceptionTargetPx: 180, perceptionWind: 1.8, aimPowerError: 13 },
    normal: { perceptionTargetPx: 80, perceptionWind: 0.8, aimPowerError: 6 },
    hard: { perceptionTargetPx: 20, perceptionWind: 0.2, aimPowerError: 3 }
  };
  var DEFAULT_AGENT_LEVEL = 'normal';
  var POWER_MIN = 30;
  var POWER_MAX = 115;   // MAX_POWER of index.html since owner H15 2026-11-19 (it was 100)
  var MAX_STEPS = 2400;           // 40 s of flight at most per throw
  var RULE_A_TICK = 0.12;         // docs/playtest_fixes.md Fix 1: follow-up hits of the shield, 0.12 s apart
  var KNIGHT_HOP_COOL = 0.3;      // index.html: hitCool after a hop

  // ---------------------------------------------------------------------
  // helpers

  function isFiniteNumber(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function clamp(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
  }

  function mulberry32(seed) {
    var a = seed | 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function seedToInt(seed) {
    return isFiniteNumber(seed) ? Math.floor(seed) | 0 : 1;
  }

  // One independent seed per (base seed, pairing, match number).
  function mixSeed(seed, i, j, m) {
    var h = Math.imul(seedToInt(seed), 2654435761);
    h ^= Math.imul(i + 1, 40503);
    h ^= Math.imul(j + 1, 9973);
    h ^= Math.imul(m + 1, 69069);
    h = Math.imul(h ^ (h >>> 15), 2246822519);
    return (h ^ (h >>> 13)) | 0;
  }

  function rollWind(rand) {
    return Math.round((rand() - 0.5) * 2 * WIND_MAX * 10) / 10;   // uniform in [-4, 4], one decimal (index.html: toFixed(1))
  }

  function sideOther(s) {
    return s === 'a' ? 'b' : 'a';
  }

  function kindOf(cls) {
    var sp = cls.special || {};
    return sp.bounce ? 'shield' : sp.wave ? 'wave' : sp.splash ? 'splash' : 'point';
  }

  // ---------------------------------------------------------------------
  // the integrator, as in index.html updatePhysics / simulateLandingX (class multipliers added)

  function launchState(cls, unit, power, angleDeg) {
    var rad = angleDeg * Math.PI / 180;
    var v0 = power * V0_PER_POWER * cls.speedScale;
    var launch = cls.launch || { fwd: 58, up: 110 };
    return {
      x: unit.x + unit.dir * launch.fwd,
      y: GROUND_Y - launch.up,
      vx: v0 * Math.cos(rad) * unit.dir,
      vy: -v0 * Math.sin(rad)
    };
  }

  // Ground landing x of a throw with no obstacle (the bot's aiming model, same steps as the projectile).
  function simulateLandingX(cls, unit, power, angleDeg, wind, weather) {
    var s = launchState(cls, unit, power, angleDeg);
    var appliedWind = effectiveWind(wind, weather);
    var x = s.x;
    var y = s.y;
    var vx = s.vx;
    var vy = s.vy;
    var shotDir = s.vx >= 0 ? 1 : -1;
    for (var i = 0; i < 1500; i++) {
      vx += windAccelFor(appliedWind, shotDir) * cls.windScale * DT;
      vy += GRAVITY * cls.gravityScale * DT;
      x += vx * DT;
      y += vy * DT;
      if (y >= GROUND_Y && vy > 0) {
        break;
      }
    }
    return x;
  }

  // Power that lands the throw on the target x. reachable false = even full power falls short.
  function solvePower(cls, unit, targetX, angleDeg, wind, weather) {
    var start = unit.x + unit.dir * (cls.launch || { fwd: 58 }).fwd;
    var need = (targetX - start) * unit.dir;
    var reach = function (p) { return (simulateLandingX(cls, unit, p, angleDeg, wind, weather) - start) * unit.dir; };
    if (reach(POWER_MAX) < need) {
      return { power: POWER_MAX, reachable: false };
    }
    var lo = 10;
    var hi = POWER_MAX;
    for (var i = 0; i < 30; i++) {
      var mid = (lo + hi) / 2;
      if (reach(mid) < need) {
        lo = mid;
      } else {
        hi = mid;
      }
    }
    return { power: (lo + hi) / 2, reachable: true };
  }

  // ---------------------------------------------------------------------
  // projectiles

  // drawn size of each projectile (wLen, wThick), equal to HERO_PROFILES in index.html and PROJECTILE_SIZE in scripts/mcp_game_server.py (scripts/test_hit_radius.py checks the engine against the page)
  var PROJ_SIZE = { proj_spear: [210, 33], cannonball: [40, 40], proj_shuriken: [58, 58], proj_flame: [150, 55], proj_cross: [118, 82], proj_soundwave: [170, 170], proj_axe: [130, 130], proj_shield: [62, 92] };
  function projRadius(weapon) { var z = PROJ_SIZE[weapon]; return (!z || weapon === 'proj_soundwave') ? 0 : Math.max(0, Math.sqrt(z[0] * z[1]) / 2 - 20); }
  function makeProjectile(m, unit, cls, power, angleDeg, dmg, extra) {
    var s = launchState(cls, unit, power, angleDeg);
    var kind = kindOf(cls);
    var p = {
      side: unit.side, kind: kind, x: s.x, y: s.y, vx: s.vx, vy: s.vy, dmg: dmg,
      factor: cls.dmg > 0 ? dmg / cls.dmg : 1,    // the frost cut (and the volley share) as a factor on the class damage
      half: cls.hitHalfWidth, rad: projRadius(cls.weapon), throwId: m.throwId, hitCool: 0, rule: m.shieldRule, extra: !!extra
    };
    if (kind === 'shield') {
      var bounce = cls.special.bounce;
      var die = bounce.dieMin + Math.floor(m.rand() * (bounce.dieMax - bounce.dieMin + 1));
      p.die = die;
      p.total = dmg;
      if (m.shieldRule === 'A') {
        p.freeSkips = 1;
      } else {
        p.bouncesLeft = die;
        p.bounceDmg = Math.round(dmg / die * 10) / 10;
      }
    }
    return p;
  }

  // Splits `total` into n parts of one decimal that add up to total exactly (the last one takes the remainder).
  function splitEven(total, n) {
    var parts = [];
    var sum = 0;
    for (var i = 0; i < n - 1; i++) {
      var v = Math.round(total / n * 10) / 10;
      parts.push(v);
      sum += v;
    }
    parts.push(Math.round((total - sum) * 10) / 10);
    return parts;
  }

  function knock(foe, px, dir) {
    var r = MOVE_RANGE[foe.side];
    foe.x = clamp(foe.x + dir * px, r[0], r[1]);
  }

  function applyStatus(foe, name, status, throwerSide) {
    // The page retains the longer remaining duration, so repeated hits refresh rather than stack ticks.
    foe[name] = Math.max(foe[name] || 0, status.turns);
    foe[name + 'Damage'] = status.damage;
    foe[name + 'Owner'] = throwerSide;
  }

  function applyBurn(foe, burn, throwerSide) {
    applyStatus(foe, 'burn', burn, throwerSide);
  }

  function applyBleed(foe, bleed, throwerSide) {
    applyStatus(foe, 'bleed', bleed, throwerSide);
  }

  function applyPoison(foe, poison, throwerSide) {
    applyStatus(foe, 'poison', poison, throwerSide);
  }

  function tickStatus(m, units, name) {
    ['a', 'b'].forEach(function (side) {
      var unit = units[side];
      if (!(unit[name] > 0) || unit.hp <= 0 || !m.stats) {
        return;
      }
      // Page ticks use Math.min(DMG, hp - 1), including a zero-damage final tick at 1 HP.
      var dealt = Math.min(unit[name + 'Damage'], Math.max(0, unit.hp - 1));
      unit.hp -= dealt;
      unit[name]--;
      var source = unit[name + 'Owner'];
      if (source && m.stats[source]) {
        m.stats[source].damage += dealt;
        m.stats[source][name + 'Damage'] = (m.stats[source][name + 'Damage'] || 0) + dealt;
      }
    });
  }

  function tickPoisons(m, units) { tickStatus(m, units, 'poison'); }
  function tickBleeds(m, units) { tickStatus(m, units, 'bleed'); }
  function tickBurns(m, units) { tickStatus(m, units, 'burn'); }

  // Damage lands on foe. Returns the damage that was really dealt.
  function applyHit(m, thrower, foe, amount, rec) {
    var sp = thrower.cls.special || {};
    amount = Weather.applyAttack(m.weather, amount);
    if (!(amount > 0) || foe.hp <= 0) {
      return 0;
    }
    var dealt = Math.min(amount, foe.hp);
    foe.hp = Math.max(0, foe.hp - amount);
    if (foe.hp < 1e-9) {
      foe.hp = 0;
    }
    rec.dealt += dealt;
    rec.hit = true;
    m.ledger.registerHit(thrower.side, rec.throwId);
    if (foe.hp > 0) {
      if (sp.frost) {
        foe.weak = sp.frost.throws;
        foe.weakCut = sp.frost.cut;
      }
      if (sp.knockback) {
        knock(foe, sp.knockback.px, thrower.dir);
      }
      if (sp.burn) {
        applyBurn(foe, sp.burn, thrower.side);
      }
      if (sp.bleed) {
        applyBleed(foe, sp.bleed, thrower.side);
      }
      if (sp.poison) {
        applyPoison(foe, sp.poison, thrower.side);
      }
    }
    if (foe.hp <= 0) {
      m.ledger.registerKO(foe.side);
      m.over = true;
      m.winnerSide = thrower.side;
    }
    return dealt;
  }

  // One physics step of one projectile. Returns true when the projectile is finished.
  // The order of the checks is the one of index.html: fence, unit, ground.
  function stepProjectile(m, p, thrower, foe, rec, pending, time) {
    var cls = thrower.cls;
    if (!p.shotDir) p.shotDir = p.vx >= 0 ? 1 : -1;
    p.vx += windAccelFor(effectiveWind(m.wind, m.weather), p.shotDir) * cls.windScale * DT;
    p.vy += GRAVITY * cls.gravityScale * DT;
    p.x += p.vx * DT;
    p.y += p.vy * DT;
    if (p.hitCool > 0) {
      p.hitCool -= DT;
    }
    var current = p.kind === 'shield' && p.rule !== 'A';
    var hit = false;
    var done = false;

    // 1. the fence
    if (m.wallHp > 0 && p.x >= FENCE_X - FENCE_W / 2 && p.x <= FENCE_X + FENCE_W / 2 && p.y >= GROUND_Y - FENCE_H) {
      hit = true;
      done = true;
      m.wallHp = Math.max(0, m.wallHp - WALL_DMG);
      rec.fence = true;
      if (current && p.bouncesLeft > 1) {      // current rule: a bounce off the fence uses up one collision
        p.bouncesLeft--;
        hit = false;
        done = false;
        p.x = p.x < FENCE_X ? FENCE_X - FENCE_W / 2 - 6 : FENCE_X + FENCE_W / 2 + 6;
        p.vx = -p.vx * 0.3;
        p.vy = -Math.abs(p.vy) * 0.3 - 90;
      }
    }

    // 2. the unit
    // the page's rule (index.html, opponent collision): the TARGET's box (70 x 190, the necromancer 57 x 165; the bride's wave 105 and 40 px high), widened by the radius of the drawn projectile
    var tHalf = p.kind === 'wave' ? p.half : (foe.cls.key === 'reaper' ? 57 : 70);
    var tTop = p.kind === 'wave' ? BODY_H : (foe.cls.key === 'reaper' ? 165 : BODY_H);   // the wave keeps its own rule below (waveRule), measured inside the 190 px body box
    if (!hit && !(p.hitCool > 0) && Math.abs(p.x - foe.x) <= tHalf + p.rad && p.y >= GROUND_Y - tTop - p.rad && p.y <= GROUND_Y + (p.kind === 'wave' ? 0 : p.rad)) {
      hit = true;
      done = true;
      if (p.kind === 'wave') {
        if (m.waveRule === 'centre' && p.y < GROUND_Y - BODY_H / 2) {
          hit = false;     // 'centre': keep flying inside the box and measure the distance at body-centre height instead of at the edge
          done = false;
        } else {
          applyHit(m, thrower, foe, ClassStats.waveDamage(cls, p.x - foe.x) * p.factor, rec);
        }
      } else if (p.kind === 'shield' && p.rule === 'A') {
        var parts = splitEven(p.total, p.die);   // first tick now, the rest on the same unit 0.12 s apart
        applyHit(m, thrower, foe, parts[0], rec);
        for (var k = 1; k < parts.length; k++) {
          pending.push({ at: time + k * RULE_A_TICK, amount: parts[k] });
        }
      } else if (p.kind === 'shield') {
        applyHit(m, thrower, foe, p.bounceDmg, rec);
        if (p.bouncesLeft > 1 && foe.hp > 0) {   // a short hop that drops back on the same unit
          p.bouncesLeft--;
          hit = false;
          done = false;
          p.hitCool = KNIGHT_HOP_COOL;
          p.vx = Math.max(-400, Math.min(400, (foe.x - p.x) / 0.62));   // hops onto the unit's centre (same rule as index.html since 2026-11-16)
          p.vy = -330;
        }
      } else if (p.kind === 'splash') {
        if (Math.abs(p.x - foe.x) <= cls.special.splash.radius) {
          applyHit(m, thrower, foe, p.dmg, rec);
        }
      } else {
        applyHit(m, thrower, foe, p.dmg, rec);
      }
    }

    // 3. the ground
    if (!hit && p.y >= GROUND_Y) {
      hit = true;
      done = true;
      if (p.kind === 'splash' && Math.abs(p.x - foe.x) <= cls.special.splash.radius) {
        applyHit(m, thrower, foe, p.dmg, rec);
      } else if (current && p.kind === 'shield') {   // owner 2026-11-09: the shield sticks in the floor and cannot bounce any more (it ends)
        // nothing: hit and done stay true
      } else if (p.kind === 'shield' && p.rule === 'A' && p.freeSkips > 0) {   // rule A: the first ground contact is a free skip
        p.freeSkips--;
        hit = false;
        done = false;
        p.y = GROUND_Y - 2;
        p.vy = -Math.abs(p.vy) * 0.55;
        p.vx *= 0.75;
      }
    }
    return done;
  }

  // Plays one throw to the end: every projectile and every timed follow-up hit.
  function resolveThrow(m, thrower, foe, projectiles, rec) {
    var pending = [];
    var time = 0;
    for (var step = 0; step < MAX_STEPS; step++) {
      if (projectiles.length === 0 && pending.length === 0) {
        break;
      }
      time += DT;
      var k;
      for (k = pending.length - 1; k >= 0; k--) {
        if (pending[k].at <= time + 1e-9) {
          var due = pending.splice(k, 1)[0];
          applyHit(m, thrower, foe, due.amount, rec);
          if (m.over) {
            break;
          }
        }
      }
      for (k = projectiles.length - 1; k >= 0 && !m.over; k--) {
        if (stepProjectile(m, projectiles[k], thrower, foe, rec, pending, time)) {
          projectiles.splice(k, 1);
        }
      }
      if (m.over) {
        projectiles.length = 0;
        pending.length = 0;
      }
    }
  }

  // ---------------------------------------------------------------------
  // the bot and the match

  function makeUnit(cls, side, x) {
    return {
      cls: cls, side: side, dir: side === 'a' ? 1 : -1, x: x, hp: cls.hp, maxHp: cls.hp,
      weak: 0, weakCut: 0, held: 0,
      burn: 0, burnDamage: 0, burnOwner: null,
      bleed: 0, bleedDamage: 0, bleedOwner: null,
      poison: 0, poisonDamage: 0, poisonOwner: null
    };
  }

  function publicObservation(m, foe) {
    // Source: scripts/agent_levels.py LevelAgent.choose_power, normal difficulty defaults.
    return {
      targetX: foe.x + (m.rand() * 2 - 1) * m.perceptionTargetPx,
      wind: effectiveWind(m.wind, m.weather) + (m.rand() * 2 - 1) * m.perceptionWind
    };
  }

  // The bot uses the cat's ultimate when it is ready and (the enemy can be finished with it, or it has held it for 3 turns).
  // docs/ultimate_rules.md 2h, rules 1 and 4 (rule 3 "dialled in" needs a landing record and is left out).
  function wantsVolley(m, me, foe) {
    var sp = me.cls.special || {};
    if (m.ultimates !== 'bat' || !sp.volley) {
      return false;
    }
    var st = m.ledger.getState(me.side, m.round);
    if (!st.ult_ready) {
      return false;
    }
    var ctx = { turn: me.side, side: me.side, round: m.round, defendTurn: false, dead: me.hp <= 0 };
    if (!m.ledger.canArm(me.side, ctx).ok) {
      return false;
    }
    var weakFactor = me.weak > 0 ? 1 - me.weakCut : 1;
    var finish = foe.hp <= Ultimate.ULT_MULT * me.cls.dmg * weakFactor + 1e-9;
    var deadline = me.held >= 3;
    me.held++;
    if (finish || deadline) {
      return m.ledger.arm(me.side, ctx).ok;
    }
    return false;
  }

  function takeTurn(m, me, foe) {
    var cls = me.cls;
    var rec = { throwId: 0, dealt: 0, hit: false, fence: false, ult: false };
    var stat = m.stats[me.side];

    // The bot may only aim from a noisy observation of public target position and the HUD wind.
    var observation = publicObservation(m, foe);
    var aim = solvePower(cls, me, observation.targetX, m.angle, observation.wind);
    if (!aim.reachable) {                       // out of reach: roll the move die once, forward
      var range = MOVE_RANGE[me.side];
      var die = 1 + Math.floor(m.rand() * 6);
      var distance = Weather.applyMove(m.weather, die * DICE_STEP_PX);
      var nx = clamp(me.x + me.dir * distance, range[0], range[1]);
      if (nx !== me.x) {
        me.x = nx;
        stat.moves++;
        aim = solvePower(cls, me, observation.targetX, m.angle, observation.wind);
      }
    }
    var power = aim.power + (m.rand() * 2 - 1) * m.aimError;
    power = clamp(power, POWER_MIN, POWER_MAX);

    var volley = wantsVolley(m, me, foe);
    m.throwId++;
    rec.throwId = m.throwId;
    var factor = me.weak > 0 ? 1 - me.weakCut : 1;
    var dmg = cls.dmg * factor;
    if (me.weak > 0) {
      me.weak--;
    }
    var projectiles = [];
    if (volley) {
      // the volley replaces the throw: 5 shuriken, each 1.5 x normal / 5, fan -8 -4 0 +4 +8, the extra four with a speed jitter
      rec.ult = true;
      stat.ultUsed++;
      m.ledger.consume(me.side, m.round, rec.throwId);   // spent at release, hit or miss; this throw gives no pip
      var share = Ultimate.splitDamage(dmg, cls.special.volley.count);
      var base = makeProjectile(m, me, cls, power, m.angle, share, false);
      projectiles.push(base);
      cls.special.volley.spreadDeg.forEach(function (deg) {
        if (deg === 0) {
          return;
        }
        var r = deg * Math.PI / 180;
        var sc = cls.special.volley.speedJitter[0] + m.rand() * (cls.special.volley.speedJitter[1] - cls.special.volley.speedJitter[0]);
        var c = Math.cos(r);
        var s = Math.sin(r);
        var q = makeProjectile(m, me, cls, power, m.angle, share, true);
        q.vx = (base.vx * c - base.vy * s) * sc;
        q.vy = (base.vx * s + base.vy * c) * sc;
        projectiles.push(q);
      });
    } else {
      projectiles.push(makeProjectile(m, me, cls, power, m.angle, dmg, false));
    }

    resolveThrow(m, me, foe, projectiles, rec);

    stat.throws++;
    if (rec.hit) {
      stat.hitThrows++;
    }
    if (rec.fence) {
      stat.fenceThrows++;
    }
    stat.damage += rec.dealt;
  }

  function newStats() {
    return { throws: 0, hitThrows: 0, fenceThrows: 0, damage: 0, burnDamage: 0, bleedDamage: 0, poisonDamage: 0, moves: 0, ultUsed: 0 };
  }

  // options: { a, b, seed, maxRounds, aimError, angle, table, shieldRule, ultimates }
  //   a, b        class keys; a stands on the left and acts first
  //   aimError    the bot's power error, uniform +-aimError power units (1 unit is about 20 px of landing distance)
  //   table       class table, default ClassStats.CLASSES (pass ClassStats.PROVISIONAL for index.html today)
  //   shieldRule  'current' (index.html: every collision counts, hop back onto the unit) or 'A' (docs/playtest_fixes.md Fix 1)
  //   waveRule    'first_contact' (default, docs/class_stats_judgement.md 6a: the wave distance is measured where the wave
  //               first touches the 190 px tall body box) or 'centre' (measured at body-centre height, a proposal)
  //   ultimates   'bat' (default: the cat's volley is played) or 'none'
  function simulateMatch(options) {
    var o = options && typeof options === 'object' ? options : {};
    var table = o.table || ClassStats.CLASSES;
    if (typeof o.a !== 'string' || !Object.prototype.hasOwnProperty.call(table, o.a) ||
        typeof o.b !== 'string' || !Object.prototype.hasOwnProperty.call(table, o.b)) {
      throw new Error('simulateMatch needs two class keys of the table: ' + String(o.a) + ', ' + String(o.b));
    }
    var rand = mulberry32(seedToInt(o.seed));
    var agentLevel = Object.prototype.hasOwnProperty.call(PUBLIC_AGENT_LEVELS, o.agentLevel) ? o.agentLevel : DEFAULT_AGENT_LEVEL;
    var level = PUBLIC_AGENT_LEVELS[agentLevel];
    var maxRounds = isFiniteNumber(o.maxRounds) && o.maxRounds >= 1 ? Math.floor(o.maxRounds) : 60;
    var m = {
      rand: rand,
      weather: weatherOf(o.weather),
      wind: 0,
      wallHp: WALL_HP,
      round: 1,
      throwId: 0,
      over: false,
      winnerSide: null,
      angle: isFiniteNumber(o.angle) ? clamp(o.angle, 25, 80) : ANGLE_DEFAULT,
      agentLevel: agentLevel,
      perceptionTargetPx: isFiniteNumber(o.perceptionTargetPx) && o.perceptionTargetPx >= 0 ? o.perceptionTargetPx : level.perceptionTargetPx,
      perceptionWind: isFiniteNumber(o.perceptionWind) && o.perceptionWind >= 0 ? o.perceptionWind : level.perceptionWind,
      aimError: isFiniteNumber(o.aimError) && o.aimError >= 0 ? o.aimError : level.aimPowerError,
      shieldRule: o.shieldRule === 'A' ? 'A' : 'current',
      waveRule: o.waveRule === 'centre' ? 'centre' : 'first_contact',
      ultimates: o.ultimates === 'none' ? 'none' : 'bat',
      ledger: Ultimate.createLedger({ maxPips: 3, maxUses: 2, sides: ['a', 'b'] }),
      stats: { a: newStats(), b: newStats() }
    };
    var a = makeUnit(table[o.a], 'a', Math.round(START_RANGE.a[0] + rand() * (START_RANGE.a[1] - START_RANGE.a[0])));
    var b = makeUnit(table[o.b], 'b', Math.round(START_RANGE.b[0] + rand() * (START_RANGE.b[1] - START_RANGE.b[0])));
    var units = { a: a, b: b };

    var rounds = 0;
    for (m.round = 1; m.round <= maxRounds && !m.over; m.round++) {
      m.wind = rollWind(rand);
      rounds = m.round;
      tickPoisons(m, units);
      tickBleeds(m, units);
      tickBurns(m, units);
      var order = ['a', 'b'];
      for (var i = 0; i < order.length && !m.over; i++) {
        var me = units[order[i]];
        takeTurn(m, me, units[sideOther(order[i])]);
      }
    }

    var winner = m.winnerSide;
    var endedBy = 'ko';
    if (!m.over) {
      endedBy = 'timeout';
      var fa = a.hp / a.maxHp;
      var fb = b.hp / b.maxHp;
      winner = fa > fb + 1e-9 ? 'a' : fb > fa + 1e-9 ? 'b' : null;
    }
    return {
      a: o.a,
      b: o.b,
      seed: seedToInt(o.seed),
      weather: m.weather.id,
      agentLevel: agentLevel,
      publicPerception: { targetPx: m.perceptionTargetPx, wind: m.perceptionWind, aimPowerError: m.aimError },
      winner: winner,
      winnerClass: winner ? units[winner].cls.key : null,
      endedBy: endedBy,
      rounds: rounds,
      hp: { a: a.hp, b: b.hp },
      wallHp: m.wallHp,
      hitsToKill: endedBy === 'ko' ? m.stats[winner].hitThrows : null,
      stats: m.stats,
      ledger: { a: m.ledger.getState('a'), b: m.ledger.getState('b') }
    };
  }

  // ---------------------------------------------------------------------
  // pairings

  // options: { classes, matchesPerPairing, seed, table, aimError, maxRounds, shieldRule, ultimates, angle }
  // Every unordered pair (and every class against itself) plays matchesPerPairing matches; the sides alternate
  // match by match, so the first-mover advantage cancels for two different classes.
  function runPairings(options) {
    var o = options && typeof options === 'object' ? options : {};
    var table = o.table || ClassStats.CLASSES;
    var classes = Array.isArray(o.classes) && o.classes.length > 0 ? o.classes.slice() : ClassStats.CLASS_KEYS.slice();
    var n = isFiniteNumber(o.matchesPerPairing) && o.matchesPerPairing >= 1 ? Math.floor(o.matchesPerPairing) : 200;
    var seed = seedToInt(o.seed);
    var k = classes.length;
    var band = ClassStats.BAND;

    var winRates = [];
    var avgRounds = [];
    var wins = [];
    var i;
    var j;
    for (i = 0; i < k; i++) {
      winRates.push([]);
      avgRounds.push([]);
      wins.push([]);
      for (j = 0; j < k; j++) {
        winRates[i].push(0.5);
        avgRounds[i].push(0);
        wins[i].push(0);
      }
    }
    var htkSum = {};
    var htkN = {};
    var dmgSum = {};
    var dmgN = {};
    var firstMover = {};
    var timeouts = 0;
    var totalMatches = 0;
    var roundsSum = 0;
    var throwStats = {};
    classes.forEach(function (c) {
      htkSum[c] = 0; htkN[c] = 0; dmgSum[c] = 0; dmgN[c] = 0; firstMover[c] = 0;
      throwStats[c] = { throws: 0, hitThrows: 0, fenceThrows: 0, damage: 0, burnDamage: 0, bleedDamage: 0, poisonDamage: 0, moves: 0, ultUsed: 0 };
    });

    for (i = 0; i < k; i++) {
      for (j = i; j < k; j++) {
        var winsI = 0;
        var pairRounds = 0;
        var leftWins = 0;
        for (var mi = 0; mi < n; mi++) {
          var iLeft = i === j || mi % 2 === 0;
          var res = simulateMatch({
            a: iLeft ? classes[i] : classes[j],
            b: iLeft ? classes[j] : classes[i],
            seed: mixSeed(seed, i, j, mi),
            table: table, weather: o.weather, aimError: o.aimError, agentLevel: o.agentLevel, perceptionTargetPx: o.perceptionTargetPx,
            perceptionWind: o.perceptionWind, maxRounds: o.maxRounds, shieldRule: o.shieldRule, waveRule: o.waveRule,
            ultimates: o.ultimates, angle: o.angle
          });
          totalMatches++;
          roundsSum += res.rounds;
          pairRounds += res.rounds;
          if (res.endedBy === 'timeout') {
            timeouts++;
          }
          if (res.winner === 'a') {
            leftWins++;
          }
          if (i !== j) {
            if (res.winner === null) {
              winsI += 0.5;
            } else if ((res.winner === 'a') === iLeft) {
              winsI += 1;
            }
          }
          if (res.winnerClass && res.hitsToKill !== null) {
            htkSum[res.winnerClass] += res.hitsToKill;
            htkN[res.winnerClass]++;
          }
          ['a', 'b'].forEach(function (s) {
            var st = res.stats[s];
            var cls = s === 'a' ? res.a : res.b;
            var ts = throwStats[cls];
            ts.throws += st.throws;
            ts.hitThrows += st.hitThrows;
            ts.fenceThrows += st.fenceThrows;
            ts.damage += st.damage;
            ts.burnDamage += st.burnDamage;
            ts.bleedDamage += st.bleedDamage;
            ts.poisonDamage += st.poisonDamage;
            ts.moves += st.moves;
            ts.ultUsed += st.ultUsed;
            if (st.hitThrows > 0) {
              dmgSum[cls] += st.damage / st.hitThrows;
              dmgN[cls]++;
            }
          });
        }
        avgRounds[i][j] = avgRounds[j][i] = pairRounds / n;
        if (i === j) {
          firstMover[classes[i]] = leftWins / n;
        } else {
          wins[i][j] = winsI;
          wins[j][i] = n - winsI;
          winRates[i][j] = winsI / n;
          winRates[j][i] = 1 - winsI / n;
        }
      }
    }

    var classAverage = {};
    var hitsToKill = {};
    var damagePerHitThrow = {};
    var damagePerThrow = {};
    var hitRate = {};
    classes.forEach(function (c, ci) {
      var sum = 0;
      for (var cj = 0; cj < k; cj++) {
        if (cj !== ci) {
          sum += winRates[ci][cj];
        }
      }
      classAverage[c] = k > 1 ? sum / (k - 1) : 0.5;
      hitsToKill[c] = htkN[c] > 0 ? htkSum[c] / htkN[c] : null;
      damagePerHitThrow[c] = dmgN[c] > 0 ? dmgSum[c] / dmgN[c] : null;
      damagePerThrow[c] = throwStats[c].throws > 0 ? throwStats[c].damage / throwStats[c].throws : null;
      hitRate[c] = throwStats[c].throws > 0 ? throwStats[c].hitThrows / throwStats[c].throws : null;
    });

    var violations = [];
    for (i = 0; i < k; i++) {
      for (j = i + 1; j < k; j++) {
        var r = winRates[i][j];
        if (r < band.winMin - 1e-9 || r > band.winMax + 1e-9) {
          violations.push({ kind: 'pairing', a: classes[i], b: classes[j], rate: r,
            message: classes[i] + ' vs ' + classes[j] + ': ' + (r * 100).toFixed(1) + '% for ' + classes[i] + ' (band 40 to 60)' });
        }
      }
    }
    classes.forEach(function (c) {
      var v = classAverage[c];
      if (k > 2 && (v < band.classAvgMin - 1e-9 || v > band.classAvgMax + 1e-9)) {
        violations.push({ kind: 'class_average', a: c, b: null, rate: v,
          message: c + ' averages ' + (v * 100).toFixed(1) + '% against the others (band 45 to 55)' });
      }
    });
    var avgOverall = totalMatches > 0 ? roundsSum / totalMatches : 0;

    return {
      classes: classes,
      matchesPerPairing: n,
      seed: seed,
      weather: weatherOf(o.weather).id,
      totalMatches: totalMatches,
      winRates: winRates,
      wins: wins,
      avgRounds: avgRounds,
      avgRoundsOverall: avgOverall,
      hitsToKill: hitsToKill,
      damagePerHitThrow: damagePerHitThrow,
      damagePerThrow: damagePerThrow,
      hitRate: hitRate,
      throwStats: throwStats,
      classAverage: classAverage,
      firstMoverWinRate: firstMover,
      timeouts: timeouts,
      violations: violations,
      pass: violations.length === 0,
      lengthOk: avgOverall >= band.roundsMin && avgOverall <= band.roundsMax
    };
  }

  // ---------------------------------------------------------------------
  // text output

  function pad(s, n) {
    s = String(s);
    while (s.length < n) {
      s += ' ';
    }
    return s;
  }

  function formatReport(result, label) {
    var cs = result.classes;
    var lines = [];
    lines.push('Balance simulation' + (label ? ' (' + label + ')' : '') + ': ' + result.matchesPerPairing + ' matches per pairing, ' +
      result.totalMatches + ' matches, seed ' + result.seed + ', weather ' + result.weather);
    lines.push('');
    lines.push('Win rate of the ROW class against the COLUMN class (%, a draw counts half):');
    lines.push(pad('', 11) + cs.map(function (c) { return pad(c, 11); }).join(''));
    cs.forEach(function (c, i) {
      lines.push(pad(c, 11) + cs.map(function (d, j) { return pad(i === j ? '-' : (result.winRates[i][j] * 100).toFixed(1), 11); }).join(''));
    });
    lines.push('');
    lines.push('Average match length in rounds (one round = both sides throw once):');
    lines.push(pad('', 11) + cs.map(function (c) { return pad(c, 11); }).join(''));
    cs.forEach(function (c, i) {
      lines.push(pad(c, 11) + cs.map(function (d, j) { return pad(result.avgRounds[i][j].toFixed(1), 11); }).join(''));
    });
    lines.push('overall ' + result.avgRoundsOverall.toFixed(2) + ' rounds (band 8 to 14: ' + (result.lengthOk ? 'inside' : 'outside') + '), timeouts ' + result.timeouts);
    lines.push('');
    lines.push(pad('class', 11) + pad('avg win %', 11) + pad('hits to kill', 14) + pad('dmg/throw', 12) + pad('hit rate %', 12) +
      pad('status dmg', 12) + pad('fence %', 9) + pad('moves/throw', 13) + pad('ults/match', 12) + 'first-mover win % (mirror)');
    cs.forEach(function (c) {
      var ts = result.throwStats[c];
      var per = function (x) { return ts.throws > 0 ? x / ts.throws : 0; };
      lines.push(pad(c, 11) + pad((result.classAverage[c] * 100).toFixed(1), 11) +
        pad(result.hitsToKill[c] === null ? '-' : result.hitsToKill[c].toFixed(2), 14) +
        pad(result.damagePerThrow[c] === null ? '-' : result.damagePerThrow[c].toFixed(1), 12) +
        pad((per(ts.hitThrows) * 100).toFixed(1), 12) +
        pad((ts.burnDamage + ts.bleedDamage + ts.poisonDamage).toFixed(1), 12) + pad((per(ts.fenceThrows) * 100).toFixed(1), 9) +
        pad(per(ts.moves).toFixed(2), 13) + pad((ts.ultUsed / Math.max(1, result.totalMatches * 2 / cs.length)).toFixed(2), 12) +
        (result.firstMoverWinRate[c] * 100).toFixed(1));
    });
    lines.push('');
    if (result.violations.length === 0) {
      lines.push('BANDS: pass (every pairing 40 to 60, every class average 45 to 55)');
    } else {
      lines.push('BANDS: ' + result.violations.length + ' violation(s)');
      result.violations.forEach(function (v) { lines.push('  - ' + v.message); });
    }
    return lines.join('\n');
  }

  return {
    simulateMatch: simulateMatch,
    runPairings: runPairings,
    simulateLandingX: simulateLandingX,
    solvePower: solvePower,
    formatReport: formatReport,
    mixSeed: mixSeed,
    mulberry32: mulberry32,
    rollWind: rollWind,
    splitEven: splitEven,
    internals: {   // exposed for scripts/test_sim_balance.js, not part of the API
      makeUnit: makeUnit, makeProjectile: makeProjectile, stepProjectile: stepProjectile, resolveThrow: resolveThrow,
      applyHit: applyHit, applyBurn: applyBurn, applyBleed: applyBleed, applyPoison: applyPoison,
      tickBurns: tickBurns, tickBleeds: tickBleeds, tickPoisons: tickPoisons, launchState: launchState, kindOf: kindOf,
      publicObservation: publicObservation, MOVE_RANGE: MOVE_RANGE, START_RANGE: START_RANGE
    },
    CONSTANTS: {
      DT: DT, GRAVITY: GRAVITY, V0_PER_POWER: V0_PER_POWER, WIND_TAIL: WIND_TAIL, WIND_HEAD: WIND_HEAD, WIND_MAX: WIND_MAX, GROUND_Y: GROUND_Y,
      FENCE_X: FENCE_X, FENCE_W: FENCE_W, FENCE_H: FENCE_H, WALL_HP: WALL_HP, WALL_DMG: WALL_DMG, BODY_H: BODY_H,
      DICE_STEP_PX: DICE_STEP_PX, ANGLE_DEFAULT: ANGLE_DEFAULT, POWER_MIN: POWER_MIN, POWER_MAX: POWER_MAX,
      PUBLIC_AGENT_LEVELS: PUBLIC_AGENT_LEVELS, DEFAULT_AGENT_LEVEL: DEFAULT_AGENT_LEVEL
    }
  };
});

// ---------------------------------------------------------------------------
// command line (Node only)

if (typeof require === 'function' && typeof module === 'object' && module && require.main === module) {
  (function main() {
    var Sim = module.exports;
    var CS = require('../js/class_stats.js');
    var Weather = require('../js/weather.js');
    var argv = process.argv.slice(2);
    var opt = { matches: 200, seed: 7, table: 'recommended', json: false };
    var num = function (v, name) {
      var x = Number(v);
      if (!isFinite(x)) {
        console.error('bad value for ' + name + ': ' + v);
        process.exit(2);
      }
      return x;
    };
    for (var i = 0; i < argv.length; i++) {
      var a = argv[i];
      var next = function () { i++; return argv[i]; };
      if (a === '--matches') opt.matches = num(next(), a);
      else if (a === '--seed') opt.seed = num(next(), a);
      else if (a === '--table') opt.table = next();
      else if (a === '--aim-error') opt.aimError = num(next(), a);
      else if (a === '--agent-level') opt.agentLevel = next();
      else if (a === '--max-rounds') opt.maxRounds = num(next(), a);
      else if (a === '--classes') opt.classes = String(next()).split(',');
      else if (a === '--shield-rule') opt.shieldRule = next();
      else if (a === '--wave-rule') opt.waveRule = next();
      else if (a === '--weather') opt.weather = next();
      else if (a === '--adjust') opt.adjust = next();
      else if (a === '--json') opt.json = true;
      else {
        console.error('unknown option ' + a + '\nusage: node scripts/sim_balance.js --matches 200 --seed 7 [--table recommended|provisional] [--weather clear|rain|snow|storm|fog] [--adjust hero:hp|dmg:0.9..1.1] [--aim-error 9] [--max-rounds 60] [--classes a,b] [--shield-rule current|A] [--json]');
        process.exit(2);
      }
    }
    if (opt.table !== 'recommended' && opt.table !== 'provisional') {
      console.error('--table must be recommended or provisional');
      process.exit(2);
    }
    if (opt.agentLevel !== undefined && !Object.prototype.hasOwnProperty.call(Sim.CONSTANTS.PUBLIC_AGENT_LEVELS, opt.agentLevel)) {
      console.error('--agent-level must be easy, normal, or hard');
      process.exit(2);
    }
    if (opt.weather !== undefined && !Object.prototype.hasOwnProperty.call(Weather.WEATHER, opt.weather)) {
      console.error('--weather must be clear, rain, snow, storm, or fog');
      process.exit(2);
    }
    var table = opt.table === 'provisional' ? CS.PROVISIONAL : CS.CLASSES;
    if (opt.adjust !== undefined) {
      var adjustment = /^([a-z]+):(hp|dmg):([0-9]+(?:\.[0-9]+)?)$/.exec(opt.adjust);
      if (!adjustment || !Object.prototype.hasOwnProperty.call(table, adjustment[1]) || Number(adjustment[3]) < 0.9 || Number(adjustment[3]) > 1.1) {
        console.error('--adjust must be <hero>:hp|dmg:<multiplier from 0.9 to 1.1>');
        process.exit(2);
      }
      table = CS.cloneTable(table);
      var key = adjustment[1];
      var multiplier = Number(adjustment[3]);
      table[key][adjustment[2]] = Math.round(table[key][adjustment[2]] * multiplier * 10) / 10;
      if (adjustment[2] === 'dmg') {
        table[key].attack = table[key].dmg;
        table[key].dTyp = Math.round(table[key].dTyp * multiplier * 10) / 10;
      }
    }
    var result = Sim.runPairings({
      classes: opt.classes, matchesPerPairing: opt.matches, seed: opt.seed,
      table: table,
      weather: opt.weather, aimError: opt.aimError, agentLevel: opt.agentLevel, maxRounds: opt.maxRounds, shieldRule: opt.shieldRule, waveRule: opt.waveRule
    });
    if (opt.json) {
      console.log(JSON.stringify(result));
    } else {
      console.log(Sim.formatReport(result, opt.table + ' values, public ' + (opt.agentLevel || Sim.CONSTANTS.DEFAULT_AGENT_LEVEL) +
        ' agent, aim error ' + (opt.aimError === undefined ? Sim.CONSTANTS.PUBLIC_AGENT_LEVELS[opt.agentLevel || Sim.CONSTANTS.DEFAULT_AGENT_LEVEL].aimPowerError : opt.aimError) +
        ', shield rule ' + (opt.shieldRule === 'A' ? 'A' : 'current') + ', wave rule ' + (opt.waveRule === 'centre' ? 'centre' : 'first_contact')));
    }
    process.exitCode = result.pass ? 0 : 1;
  })();
}
