/*
 * Ghost nun cross ultimate resolution.
 *
 * Pure deterministic combat data: callers provide both contact order and the
 * seeded random function used for the one electric-stun selection.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.NunUlt = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // PROVISIONAL: owner requested this starting value for later balance tuning.
  var NUN_ULT_HIT_MULT = 0.575;   // balance 2026-11-16 (arbitration): 0.5 to 0.575, two touches now total 27.6 with a 24 normal hit
  var MAX_TARGETS = 3;
  var MAX_HITS_PER_TARGET = 2;

  function isFiniteNumber(value) {
    return typeof value === 'number' && isFinite(value);
  }

  function isTargetId(value) {
    return (typeof value === 'string' && value !== '') || isFiniteNumber(value);
  }

  function roundTenth(value) {
    return Math.round(value * 10) / 10;
  }

  function emptyResult() {
    return { hits: [], stunned: null, total: 0 };
  }

  function randomIndex(rng, length) {
    var value = rng();
    var unit = isFiniteNumber(value) ? value : 0;
    if (unit < 0) unit = 0;
    if (unit >= 1) unit = 0.999999999;
    return Math.floor(unit * length);
  }

  // options = { normal, targets: [enemy id in contact order], rng: seeded fn }.
  // The cross remembers the first three distinct enemies it reaches, then
  // resolves no more than two contacts for each of those enemies.
  function resolve(options) {
    var input = options && typeof options === 'object' ? options : null;
    if (!input || !isFiniteNumber(input.normal) || input.normal <= 0 ||
        !Array.isArray(input.targets) || typeof input.rng !== 'function') {
      return emptyResult();
    }

    var allowed = [];
    var seen = Object.create(null);
    var i;
    for (i = 0; i < input.targets.length && allowed.length < MAX_TARGETS; i++) {
      var candidate = input.targets[i];
      var key = typeof candidate + ':' + String(candidate);
      if (isTargetId(candidate) && !seen[key]) {
        seen[key] = true;
        allowed.push(candidate);
      }
    }
    if (allowed.length === 0) return emptyResult();

    var allowedKeys = Object.create(null);
    var counts = Object.create(null);
    for (i = 0; i < allowed.length; i++) {
      var allowedKey = typeof allowed[i] + ':' + String(allowed[i]);
      allowedKeys[allowedKey] = true;
      counts[allowedKey] = 0;
    }

    var damage = roundTenth(input.normal * NUN_ULT_HIT_MULT);
    var hits = [];
    var touched = [];
    for (i = 0; i < input.targets.length; i++) {
      var target = input.targets[i];
      var targetKey = typeof target + ':' + String(target);
      if (!isTargetId(target) || !allowedKeys[targetKey] || counts[targetKey] >= MAX_HITS_PER_TARGET) {
        continue;
      }
      counts[targetKey]++;
      hits.push({ target: target, damage: damage });
      if (counts[targetKey] === 1) touched.push(target);
    }
    if (hits.length === 0) return emptyResult();

    return {
      hits: hits,
      stunned: touched[randomIndex(input.rng, touched.length)],
      total: roundTenth(damage * hits.length)
    };
  }

  return {
    NUN_ULT_HIT_MULT: NUN_ULT_HIT_MULT,
    MAX_TARGETS: MAX_TARGETS,
    MAX_HITS_PER_TARGET: MAX_HITS_PER_TARGET,
    resolve: resolve
  };
});
