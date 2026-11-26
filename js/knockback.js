/*
 * Pumpkin Killer knockback rule.
 *
 * Pure deterministic position adjustment for a direct, surviving unit hit.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.Knockback = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var ZONES = {
    left: { min: 110, max: 640 },
    right: { min: 1280, max: 1810 }
  };

  function isFiniteNumber(value) {
    return typeof value === 'number' && isFinite(value);
  }

  function zoneBounds(zone) {
    if (typeof zone === 'string' && ZONES[zone]) return ZONES[zone];
    if (zone && isFiniteNumber(zone.min) && isFiniteNumber(zone.max) && zone.min <= zone.max) {
      return zone;
    }
    return null;
  }

  function clamp(value, low, high) {
    return value < low ? low : value > high ? high : value;
  }

  // A direct hit on a living unit is the only contact that can move it.
  function eligible(hit) {
    return !!hit && hit.fatal === false && hit.hitKind === 'unit';
  }

  function apply(victimX, throwerX, px, zone) {
    var bounds = zoneBounds(zone);
    if (!bounds || !isFiniteNumber(victimX) || !isFiniteNumber(throwerX) ||
        !isFiniteNumber(px) || px < 0) {
      return victimX;
    }
    var direction = victimX < throwerX ? -1 : 1;
    return clamp(victimX + direction * px, bounds.min, bounds.max);
  }

  // A push stops `gap` px short of the first living teammate in its way: never past it, never backwards
  // (twin of clamp_knockback in scripts/mcp_game_server.py).
  var MATE_GAP = 120;
  function clearOfMates(start, wanted, mates) {
    if (wanted === start || !mates) return wanted;
    var direction = wanted > start ? 1 : -1;
    for (var i = 0; i < mates.length; i++) {
      if ((mates[i] - start) * direction > 0) {
        var limit = mates[i] - direction * MATE_GAP;
        wanted = direction > 0 ? Math.min(wanted, limit) : Math.max(wanted, limit);
      }
    }
    return direction > 0 ? Math.max(wanted, start) : Math.min(wanted, start);
  }

  return {
    ZONES: ZONES,
    eligible: eligible,
    apply: apply,
    clearOfMates: clearOfMates
  };
});
