/*
 * Ghost bride sound-wave targeting and damage.
 *
 * Pure deterministic rules. The page applies poison after this module selects
 * the target; this module does not own status effects or canvas state.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.SoundWave = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var HIT_HALF_WIDTH = 105;
  // The owner chose the 100% / 75% / 50% steps (2026-11-10) and on 2026-11-18 asked for the falloff to be counted in grid cells:
  // one cell is 35 px, so the three steps are the first, second and third cell (35 / 70 / 105 px). Before, the edges were the
  // INVENTED 40 / 75 / 105 px.
  var CELL = 35;
  var BANDS = [
    { maxDistance: CELL, multiplier: 1 },
    { maxDistance: 2 * CELL, multiplier: 0.75 },
    { maxDistance: HIT_HALF_WIDTH, multiplier: 0.5 }
  ];

  function isFiniteNumber(value) {
    return typeof value === 'number' && isFinite(value);
  }

  function isId(value) {
    return (typeof value === 'string' && value !== '') || isFiniteNumber(value);
  }

  function compareIds(left, right) {
    if (typeof left === 'number' && typeof right === 'number') return left - right;
    return String(left) < String(right) ? -1 : String(left) > String(right) ? 1 : 0;
  }

  function damageAt(distancePx, normalDamage) {
    if (!isFiniteNumber(distancePx) || !isFiniteNumber(normalDamage) || normalDamage <= 0) return 0;
    var distance = Math.abs(distancePx);
    for (var i = 0; i < BANDS.length; i++) {
      if (distance <= BANDS[i].maxDistance) return normalDamage * BANDS[i].multiplier;
    }
    return 0;
  }

  // Finds the living unit closest to the landing point. Equal distances use
  // the smaller id so every caller resolves the same target.
  function pickTarget(units, landingX) {
    if (!Array.isArray(units) || !isFiniteNumber(landingX)) return null;
    var selected = null;
    var selectedDistance = Infinity;
    for (var i = 0; i < units.length; i++) {
      var unit = units[i];
      if (!unit || typeof unit !== 'object' || unit.alive !== true ||
          !isId(unit.id) || !isFiniteNumber(unit.x)) continue;
      var distance = Math.abs(unit.x - landingX);
      if (distance > HIT_HALF_WIDTH) continue;
      if (distance < selectedDistance ||
          (distance === selectedDistance && selected && compareIds(unit.id, selected.id) < 0)) {
        selected = unit;
        selectedDistance = distance;
      }
    }
    return selected;
  }

  return {
    HIT_HALF_WIDTH: HIT_HALF_WIDTH,
    CELL: CELL,
    BANDS: BANDS.map(function (band) {
      return { maxDistance: band.maxDistance, multiplier: band.multiplier };
    }),
    damageAt: damageAt,
    pickTarget: pickTarget
  };
});
