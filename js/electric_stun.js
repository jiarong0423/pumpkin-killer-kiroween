/*
 * One-turn electric stun for the ghost nun's cross skill and ultimate.
 *
 * It uses the page's existing seven-second shortened-turn rule. The marker is
 * private state; callers may expose only the boolean projection.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.ElectricStun = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var STUN_SECONDS = 7;

  function isUnit(unit) {
    return unit !== null && typeof unit === 'object' && !Array.isArray(unit);
  }

  function has(unit) {
    return isUnit(unit) && unit.electricStun === 1;
  }

  function apply(unit) {
    if (!isUnit(unit) || has(unit)) return { applied: false };
    unit.electricStun = 1;
    return { applied: true };
  }

  function clear(unit) {
    if (!isUnit(unit)) return { cleared: false };
    var wasSet = has(unit);
    delete unit.electricStun;
    return { cleared: wasSet };
  }

  // A head-crit-style stun shortens the next turn rather than forfeiting it.
  function startOfTurn(unit) {
    if (!has(unit)) return { skip: false, timer: null };
    clear(unit);
    return { skip: false, timer: STUN_SECONDS };
  }

  function publicState(unit) {
    return { electricStun: has(unit) };
  }

  return {
    STUN_SECONDS: STUN_SECONDS,
    apply: apply,
    clear: clear,
    onKO: clear,
    startOfTurn: startOfTurn,
    publicState: publicState
  };
});
