/*
 * Pumpkin Killer ultimate effect timelines.
 *
 * This module produces deterministic data for the page to play. It owns no
 * canvas state and leaves combat resolution to index.html.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.UltimateFx = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var CANVAS_WIDTH = 1920;
  var CANVAS_HEIGHT = 1080;
  var ULT_MULT = 1.5;
  // Owner decision 2026-11-16: the bride's normal sound wave deals 25 damage.
  var BRIDE_NORMAL_DAMAGE = 28;
  var BRIDE_BAT_SWARM_MULT = 1.3;
  var BRIDE_PRECISE_HIT_RADIUS = 55;   // playtest 2026-11-16 (3 arbiters): 40 px was too strict, one miss wasted the whole ultimate
  // Owner decision 2026-11-16: the hunchback's giant axe deals 21 damage.
  var HUNCHBACK_NORMAL_DAMAGE = 21;
  var HUNCHBACK_BOOMERANG_RETURN_DAMAGE = 31.5;
  // The reaper id is the owner-facing Necromancer. Its ultimate deliberately
  // exceeds the generic 1.5x split: the owner specified an escalating volley.
  var REAPER_FLAME_NORMAL_DAMAGE = 21;
  var NECRO_VOLLEY_MULT = [1.1, 1.3, 1.5];
  // PROVISIONAL (owner 2026-11-15: lower the total attack now, tune the balance later): one scale on the whole volley keeps the 1.1 : 1.3 : 1.5 ratio.
  var NECRO_VOLLEY_SCALE = 0.5;

  function isFiniteNumber(value) {
    return typeof value === 'number' && isFinite(value);
  }

  function clamp(value, low, high) {
    return value < low ? low : value > high ? high : value;
  }

  function coordinate(value, fallback, maximum) {
    return isFiniteNumber(value) ? clamp(value, 0, maximum) : fallback;
  }

  function normalDamage(value) {
    return isFiniteNumber(value) && value > 0 ? value : 0;
  }

  function roundTenth(value) {
    return Math.round(value * 10) / 10;
  }

  function strikeDamage(normal, strikes) {
    var count = isFiniteNumber(strikes) && strikes >= 1 ? Math.floor(strikes) : 1;
    return roundTenth(normalDamage(normal) * ULT_MULT / count);
  }

  function blastDamage(normal) {
    return roundTenth(normalDamage(normal) * ULT_MULT);
  }

  function necroVolleyDamage(normal) {
    var base = normalDamage(normal);
    return NECRO_VOLLEY_MULT.map(function (multiplier) {
      return roundTenth(base * multiplier * NECRO_VOLLEY_SCALE);
    });
  }

  function damageFor(hero, normal) {
    if (hero === 'bat') return strikeDamage(normal, 5);
    if (hero === 'skeleton') return strikeDamage(normal, 3);
    // Callers that need the full volley use necroVolleyDamage(). This retains a
    // useful single-hit answer for generic presentation callers.
    if (hero === 'reaper') return necroVolleyDamage(normal)[0];
    if (hero === 'wizard' || hero === 'bride' || hero === 'hunchback') return blastDamage(normal);
    return 0;
  }

  function resolveDamage(hero, normal, options) {
    // Effects are presentation data only; reduced motion cannot change combat.
    return damageFor(hero, normal);
  }

  function inputValues(input) {
    var source = input && typeof input === 'object' ? input : {};
    var startX = coordinate(source.startX, CANVAS_WIDTH / 2, CANVAS_WIDTH);
    var startY = coordinate(source.startY, CANVAS_HEIGHT / 2, CANVAS_HEIGHT);
    return {
      startX: startX,
      startY: startY,
      landingX: coordinate(source.landingX, startX, CANVAS_WIDTH),
      landingY: coordinate(source.landingY, startY, CANVAS_HEIGHT),
      flightTime: isFiniteNumber(source.flightTime) ? clamp(source.flightTime, 0.05, 10) : 0.65,
      dirX: source.dirX < 0 ? -1 : 1,
      normal: normalDamage(source.normalDamage)
    };
  }

  function targetsFor(input, values) {
    var source = input && typeof input === 'object' ? input : {};
    var rawTargets = Array.isArray(source.targets) && source.targets.length > 0 ? source.targets : [{}];
    var targets = [];
    for (var i = 0; i < rawTargets.length; i++) {
      var target = rawTargets[i] && typeof rawTargets[i] === 'object' ? rawTargets[i] : {};
      targets.push({
        x: coordinate(target.x, values.landingX, CANVAS_WIDTH),
        y: coordinate(target.y, values.landingY, CANVAS_HEIGHT)
      });
    }
    return targets;
  }

  function heroNormal(values, fallback) {
    return values.normal > 0 ? values.normal : fallback;
  }

  function event(t, preset, x, y, anchor, extra) {
    return Object.assign({
      t: t,
      preset: preset,
      x: clamp(x, 0, CANVAS_WIDTH),
      y: clamp(y, 0, CANVAS_HEIGHT),
      anchor: anchor
    }, extra || {});
  }

  // Input-driven effects can schedule an offset after a short flight. Keep the
  // declarative stream chronological, preserving construction order for ties.
  function ordered(events) {
    return events.map(function (item, index) {
      return { item: item, index: index };
    }).sort(function (a, b) {
      return a.item.t - b.item.t || a.index - b.index;
    }).map(function (entry) {
      return entry.item;
    });
  }

  function batShurikenRain(input) {
    var values = inputValues(input);
    var damage = damageFor('bat', values.normal);
    var angles = [-8, -4, 0, 4, 8];
    var events = [event(0, 'weapon_charge_aura', values.startX, values.startY, 'muzzle')];
    for (var i = 0; i < angles.length; i++) {
      events.push(event(0, 'weapon_trail_dart', values.startX, values.startY, 'muzzle', {
        index: i,
        angle: angles[i],
        damage: damage,
        dirX: values.dirX
      }));
    }
    for (var j = 0; j < angles.length; j++) {
      events.push(event(values.flightTime, 'hit_sparks', values.landingX, values.landingY, 'impact', {
        index: j,
        dirX: values.dirX
      }));
      events.push(event(values.flightTime, 'damage_number', values.landingX, values.landingY, 'impact', {
        index: j,
        amount: damage,
        dirX: values.dirX
      }));
    }
    return ordered(events);
  }

  function skeletonTripleJavelin(input) {
    var values = inputValues(input);
    var damage = damageFor('skeleton', values.normal);
    var scales = [0.95, 1, 1.05];
    var events = [
      event(0, 'weapon_charge_aura', values.startX, values.startY, 'muzzle'),
      event(0, 'face_glow_skeleton', values.startX, values.startY, 'unit')
    ];
    for (var i = 0; i < scales.length; i++) {
      events.push(event(0, 'weapon_trail_spear', values.startX, values.startY, 'muzzle', {
        index: i,
        velocityScale: scales[i],
        damage: damage,
        dirX: values.dirX
      }));
    }
    for (var j = 0; j < scales.length; j++) {
      events.push(event(values.flightTime * 0.65, 'ghost_spear_fall', values.landingX, values.landingY, 'flight', {
        index: j,
        dirX: values.dirX
      }));
      events.push(event(values.flightTime, 'sprite_ghostfire', values.landingX, values.landingY, 'impact', { index: j }));
      events.push(event(values.flightTime, 'impact_burst', values.landingX, values.landingY, 'impact', {
        index: j,
        dirX: values.dirX
      }));
    }
    return ordered(events);
  }

  function wizardPumpkinBlast(input) {
    var values = inputValues(input);
    var events = [
      event(0, 'muzzle_flash', values.startX, values.startY, 'muzzle', { dirX: values.dirX, scale: 1.3 }),
      event(0, 'smoke_puff', values.startX, values.startY, 'muzzle', { dirX: values.dirX, scale: 1.2 }),
      event(values.flightTime * 0.5, 'weapon_trail_cannon', values.landingX, values.landingY, 'flight', { dirX: values.dirX }),
      event(values.flightTime, 'impact_burst', values.landingX, values.landingY, 'impact', { dirX: values.dirX, scale: 3 }),
      event(values.flightTime, 'shock_ring', values.landingX, values.landingY, 'ground'),
      event(values.flightTime, 'landing_ring_dust', values.landingX, values.landingY, 'ground'),
      event(values.flightTime, 'sprite_stardust', values.landingX, clamp(values.landingY - 60, 0, CANVAS_HEIGHT), 'impact', { scale: 2.5 })
    ];
    for (var i = -6; i <= 6; i++) {
      events.push(event(values.flightTime, 'sprite_fire_tongue', values.landingX + i * 36, values.landingY - 30, 'ground', {
        index: i + 6,
        damage: blastDamage(values.normal),
        scale: 1.45
      }));
    }
    return ordered(events);
  }

  function brideSoulDirge(input) {
    var values = inputValues(input);
    var targets = targetsFor(input, values);
    var damage = damageFor('bride', heroNormal(values, BRIDE_NORMAL_DAMAGE));
    var events = [event(0, 'weapon_charge_aura', values.startX, values.startY, 'muzzle', { dirX: values.dirX })];
    for (var i = 0; i < targets.length; i++) {
      var target = targets[i];
      var time = values.flightTime + i * 0.1;
      events.push(event(time, 'soundwave_rings', target.x, target.y, 'impact', {
        index: i,
        dirX: values.dirX
      }));
      events.push(event(time, 'weapon_trail_wave', target.x, target.y, 'impact', {
        index: i,
        damage: damage,
        dirX: values.dirX,
        travelling: true
      }));
      events.push(event(time, 'hit_sparks', target.x, target.y, 'impact', {
        index: i,
        damage: damage,
        dirX: values.dirX
      }));
    }
    return ordered(events);
  }

  function brideBatSwarm(input) {
    var values = inputValues(input);
    var source = input && typeof input === 'object' ? input : {};
    // The page measures this horizontal distance using SoundWave before it
    // requests the timeline. A hit exactly 40 px away does not trigger bats.
    if (!isFiniteNumber(source.hitDistance) || Math.abs(source.hitDistance) >= BRIDE_PRECISE_HIT_RADIUS) {
      return [];
    }
    var normal = heroNormal(values, BRIDE_NORMAL_DAMAGE);
    var swarmDamage = roundTenth(normal * Math.min(BRIDE_BAT_SWARM_MULT, ULT_MULT));
    var rawEnemies = Array.isArray(source.enemies) ? source.enemies : [];
    var enemies = [];
    var seenIds = Object.create(null);
    for (var i = 0; i < rawEnemies.length; i++) {
      var enemy = rawEnemies[i];
      if (!enemy || typeof enemy !== 'object') continue;
      var key = enemy.id === undefined ? 'index:' + i : typeof enemy.id + ':' + String(enemy.id);
      if (seenIds[key]) continue;
      seenIds[key] = true;
      enemies.push({
        id: enemy.id,
        x: coordinate(enemy.x, values.landingX, CANVAS_WIDTH),
        y: coordinate(enemy.y, values.landingY, CANVAS_HEIGHT)
      });
    }
    var events = [event(values.flightTime, 'soundwave_rings', values.landingX, values.landingY, 'impact', {
      phase: 'precise_hit',
      damage: normal,
      blockable: true,
      dirX: values.dirX
    })];
    for (var j = 0; j < enemies.length; j++) {
      var target = enemies[j];
      events.push(event(values.flightTime + 0.01, 'bat_swarm', target.x, target.y, 'unit', {
        phase: 'swarm_hit',
        index: j,
        target: target.id,
        damage: swarmDamage,
        blockable: false,
        dirX: values.dirX
      }));
    }
    return ordered(events);
  }

  // Retained for compatibility while the main line replaces its page wiring.
  function hunchbackTowerToll(input) {
    var values = inputValues(input);
    var targets = targetsFor(input, values);
    var damage = damageFor('hunchback', heroNormal(values, HUNCHBACK_NORMAL_DAMAGE));
    var time = values.flightTime;
    var events = [
      event(time * 0.5, 'weapon_trail_bell', values.landingX, values.landingY, 'flight', { dirX: values.dirX }),
      event(time, 'bell_toll_rings', values.landingX, values.landingY, 'ground', { dirX: values.dirX }),
      event(time, 'bounce_ring', values.landingX, values.landingY, 'ground', { directions: [-1, 1], travelling: true }),
      event(time, 'impact_wave', values.landingX, values.landingY, 'impact', { bellShockwave: true, dirX: values.dirX }),
      event(time, 'landing_ring_dust', values.landingX, values.landingY, 'ground', { knockbackDust: true, dirX: values.dirX })
    ];
    for (var i = 0; i < targets.length; i++) {
      events.push(event(time, 'damage_number', targets[i].x, targets[i].y, 'unit', {
        index: i,
        amount: damage,
        damage: damage,
        dirX: values.dirX
      }));
    }
    return ordered(events);
  }

  // Presentation consumes the ordered data returned by Boomerang.resolve().
  // The return speed belongs to that pure rule module, not this timeline.
  function hunchbackBoomerang(input) {
    var values = inputValues(input);
    var source = input && typeof input === 'object' ? input : {};
    var rawHits = Array.isArray(source.hits) ? source.hits : [];
    var outbound = [];
    var returned = null;
    for (var i = 0; i < rawHits.length; i++) {
      var hit = rawHits[i];
      if (!hit || typeof hit !== 'object') continue;
      var x = coordinate(hit.x, values.landingX, CANVAS_WIDTH);
      var y = coordinate(hit.y, values.landingY, CANVAS_HEIGHT);
      var time = isFiniteNumber(hit.t) && hit.t >= 0 ? hit.t : values.flightTime;
      if (hit.phase === 'outbound') {
        outbound.push({ target: hit.target, x: x, y: y, t: time });
      } else if (hit.phase === 'return' && !returned) {
        returned = { target: hit.target, x: x, y: y, t: time };
      }
    }
    var turnTime = values.flightTime;
    for (var j = 0; j < outbound.length; j++) turnTime = Math.max(turnTime, outbound[j].t);
    var events = [event(0, 'axe_spin_trail', values.startX, values.startY, 'muzzle', {
      phase: 'outbound_spin', dirX: values.dirX
    })];
    for (var k = 0; k < outbound.length; k++) {
      var pierce = outbound[k];
      events.push(event(pierce.t, 'hit_sparks', pierce.x, pierce.y, 'unit', {
        phase: 'pierce_hit', index: k, target: pierce.target, damage: HUNCHBACK_NORMAL_DAMAGE,
        blockable: false, dirX: values.dirX
      }));
    }
    events.push(event(turnTime, 'axe_spin_trail', values.landingX, values.landingY, 'far_end', {
      phase: 'turn', dirX: values.dirX
    }));
    if (outbound.length > 0 && returned) {
      events.push(event(turnTime, 'boomerang_return', values.landingX, values.landingY, 'far_end', {
        phase: 'return', dirX: -values.dirX
      }));
      events.push(event(returned.t, 'hit_sparks', returned.x, returned.y, 'unit', {
        phase: 'return_hit', target: returned.target, damage: HUNCHBACK_BOOMERANG_RETURN_DAMAGE,
        blockable: false, dirX: -values.dirX
      }));
    }
    return ordered(events);
  }

  function firstHit(hits) {
    if (!Array.isArray(hits)) return null;
    for (var i = 0; i < hits.length; i++) {
      var hit = hits[i];
      if (hit === true || (hit !== false && hit !== null && hit !== undefined)) {
        return { index: i, target: hit === true ? undefined : hit };
      }
    }
    return null;
  }

  function necroGhostfireTrio(input) {
    var values = inputValues(input);
    var damages = necroVolleyDamage(heroNormal(values, REAPER_FLAME_NORMAL_DAMAGE));
    var handX = values.startX + values.dirX * 42;
    var impactTime = values.flightTime;
    var events = [event(0, 'weapon_charge_aura', handX, values.startY, 'front_hand', {
      phase: 'finger_point', dirX: values.dirX
    })];
    for (var i = 0; i < damages.length; i++) {
      events.push(event(i * 0.15, 'sprite_ghostfire', handX, values.startY, 'front_hand', {
        index: i,
        damage: damages[i],
        phase: 'flame_launch',
        dirX: values.dirX
      }));
    }
    for (var j = 0; j < damages.length; j++) {
      events.push(event(impactTime, 'hit_sparks', values.landingX, values.landingY, 'impact', {
        index: j,
        damage: damages[j],
        phase: 'hit',
        dirX: values.dirX
      }));
    }
    var hit = firstHit(input && input.hits);
    if (hit) {
      events.push(event(impactTime, 'sprite_rune_circle', values.landingX, values.landingY, 'impact', {
        index: hit.index,
        target: hit.target,
        phase: 'hallucination_mark',
        dirX: values.dirX
      }));
    }
    events.push(event(0.35, 'ko_wisps', values.startX, values.startY, 'caster', {
      phase: 'fires_vanish', dirX: values.dirX
    }));
    return ordered(events);
  }

  function nunStunnedTarget(input, values) {
    var source = input && typeof input === 'object' ? input : {};
    var wanted = source.stunnedTarget !== undefined ? source.stunnedTarget : source.stunned;
    if (isFiniteNumber(source.stunnedIndex) && Array.isArray(source.targets)) {
      var indexed = source.targets[Math.floor(source.stunnedIndex)];
      if (indexed && typeof indexed === 'object') {
        return {
          x: coordinate(indexed.x, values.landingX, CANVAS_WIDTH),
          y: coordinate(indexed.y, values.landingY, CANVAS_HEIGHT),
          target: indexed.id
        };
      }
    }
    if (wanted && typeof wanted === 'object') {
      return {
        x: coordinate(wanted.x, values.landingX, CANVAS_WIDTH),
        y: coordinate(wanted.y, values.landingY, CANVAS_HEIGHT),
        target: wanted.id
      };
    }
    if (Array.isArray(source.targets)) {
      for (var i = 0; i < source.targets.length; i++) {
        var candidate = source.targets[i];
        if (candidate && typeof candidate === 'object' && candidate.id === wanted) {
          return {
            x: coordinate(candidate.x, values.landingX, CANVAS_WIDTH),
            y: coordinate(candidate.y, values.landingY, CANVAS_HEIGHT),
            target: candidate.id
          };
        }
      }
    }
    return { x: values.landingX, y: values.landingY, target: wanted };
  }

  // Presentation only. Combat calls NunUlt.resolve() first and passes the
  // selected target as `stunnedTarget` (or `stunned`) into this timeline.
  function nunCrossDart(input) {
    var values = inputValues(input);
    var stunned = nunStunnedTarget(input, values);
    return ordered([
      event(0, 'cross_spin_trail', values.startX, values.startY, 'muzzle', {
        phase: 'cross_launch', dirX: values.dirX
      }),
      event(values.flightTime, 'hit_sparks', values.landingX, values.landingY, 'impact', {
        phase: 'quiet_landing', dirX: values.dirX
      }),
      event(values.flightTime + 0.01, 'spark_electric', stunned.x, stunned.y, 'unit', {
        phase: 'electric_stun', target: stunned.target, dirX: values.dirX
      })
    ]);
  }

  function timeline(id, input) {
    if (id === 'bat_shuriken_rain') return batShurikenRain(input);
    if (id === 'skeleton_triple_javelin') return skeletonTripleJavelin(input);
    if (id === 'wizard_pumpkin_blast') return wizardPumpkinBlast(input);
    if (id === 'bride_soul_dirge') return brideSoulDirge(input);
    if (id === 'bride_bat_swarm') return brideBatSwarm(input);
    if (id === 'hunchback_tower_toll') return hunchbackTowerToll(input);
    if (id === 'hunchback_boomerang') return hunchbackBoomerang(input);
    if (id === 'nun_cross_dart') return nunCrossDart(input);
    if (id === 'necro_ghostfire_trio' || id === 'reaper_flame_trio') return necroGhostfireTrio(input);
    return [];
  }

  return {
    CANVAS_WIDTH: CANVAS_WIDTH,
    CANVAS_HEIGHT: CANVAS_HEIGHT,
    ULT_MULT: ULT_MULT,
    BRIDE_NORMAL_DAMAGE: BRIDE_NORMAL_DAMAGE,
    BRIDE_BAT_SWARM_MULT: BRIDE_BAT_SWARM_MULT,
    BRIDE_PRECISE_HIT_RADIUS: BRIDE_PRECISE_HIT_RADIUS,
    HUNCHBACK_NORMAL_DAMAGE: HUNCHBACK_NORMAL_DAMAGE,
    HUNCHBACK_BOOMERANG_RETURN_DAMAGE: HUNCHBACK_BOOMERANG_RETURN_DAMAGE,
    REAPER_FLAME_NORMAL_DAMAGE: REAPER_FLAME_NORMAL_DAMAGE,
    NECRO_VOLLEY_MULT: NECRO_VOLLEY_MULT.slice(),
    NECRO_VOLLEY_SCALE: NECRO_VOLLEY_SCALE,
    strikeDamage: strikeDamage,
    blastDamage: blastDamage,
    necroVolleyDamage: necroVolleyDamage,
    damageFor: damageFor,
    resolveDamage: resolveDamage,
    batShurikenRain: batShurikenRain,
    skeletonTripleJavelin: skeletonTripleJavelin,
    wizardPumpkinBlast: wizardPumpkinBlast,
    brideSoulDirge: brideSoulDirge,
    brideBatSwarm: brideBatSwarm,
    hunchbackTowerToll: hunchbackTowerToll,
    hunchbackBoomerang: hunchbackBoomerang,
    nunCrossDart: nunCrossDart,
    necroGhostfireTrio: necroGhostfireTrio,
    timeline: timeline
  };
});
