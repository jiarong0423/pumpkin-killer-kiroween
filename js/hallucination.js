/*
 * One-turn hallucination status for the Necromancer's soulfire volley.
 *
 * This module mutates only the supplied unit record. The internal marker is
 * numeric so the public projection can expose only a boolean.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.Hallucination = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function isUnit(unit) {
    return unit !== null && typeof unit === 'object' && !Array.isArray(unit);
  }

  function has(unit) {
    return isUnit(unit) && unit.hallucination === 1;
  }

  function apply(unit) {
    if (!isUnit(unit) || has(unit)) return { applied: false };
    unit.hallucination = 1;
    return { applied: true };
  }

  function clear(unit) {
    if (!isUnit(unit)) return { cleared: false };
    var wasSet = has(unit);
    delete unit.hallucination;
    return { cleared: wasSet };
  }

  function startOfTurn(unit) {
    if (!has(unit)) return { skip: false };
    clear(unit);
    return { skip: true };
  }

  function publicState(unit) {
    return { hallucination: has(unit) };
  }

  return {
    apply: apply,
    clear: clear,
    onKO: clear,
    startOfTurn: startOfTurn,
    publicState: publicState
  };
});
