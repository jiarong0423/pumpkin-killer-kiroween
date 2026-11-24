/* Comeback pack for team matches (pure, no DOM): near-miss damage, underdog bonus, pity charge. One unit per team: callers must not use it.
   Constants: shared/comeback.json (copied here, pinned equal by scripts/test_comeback.js). Python twin: scripts/comeback_py.py. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.Comeback = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var NEAR_ENABLED = false, NEAR_REACH = 120, NEAR_SCALE = 0.9;   // mirror shared/comeback.json near_miss: OFF since 2026-11-18 (owner); reach 120 px is the dormant value
  var UNDERDOG_MAX = 1.0, UNDERDOG_FULL = 0.5;
  var PITY_PER_MISS = 0.4, PITY_CAP = 1.6;
  var MAX_TOTAL = 2.3;   // underdog x (1 + pity) never exceeds this (owner 2026-11-17: 'too extreme, 2.3 times is enough')

  function round1(x) { return Math.round(x * 10) / 10; }
  function hpShare(units) {
    var hp = 0, max = 0;
    (units || []).forEach(function (u) { max += u.maxHp; if (u.hp > 0) hp += u.hp; });
    return max > 0 ? hp / max : 0;
  }
  function nearMissDamage(baseDmg, e) {
    if (!(e > 0) || e > NEAR_REACH) return 0;
    return round1(baseDmg * NEAR_SCALE * (1 - e / NEAR_REACH));
  }
  function underdogMultiplier(ownShare, enemyShare) {
    var deficit = Math.max(0, enemyShare - ownShare);
    return 1 + Math.min(UNDERDOG_MAX, deficit / UNDERDOG_FULL);
  }
  function pityBonus(missCount) { return Math.min(PITY_CAP, PITY_PER_MISS * Math.max(0, missCount)); }
  // damage = base x weather x ramp x underdog x (1 + pity), rounded to 0.1 at the end. weatherAndRampBase = base x weather x ramp (already computed by the caller).
  function finalDamage(weatherAndRampBase, ownShare, enemyShare, missCount) {
    return round1(weatherAndRampBase * Math.min(MAX_TOTAL, underdogMultiplier(ownShare, enemyShare) * (1 + pityBonus(missCount))));
  }
  return { hpShare: hpShare, nearMissDamage: nearMissDamage, underdogMultiplier: underdogMultiplier, pityBonus: pityBonus, finalDamage: finalDamage,
    CONSTANTS: { NEAR_ENABLED: NEAR_ENABLED, NEAR_REACH: NEAR_REACH, NEAR_SCALE: NEAR_SCALE, UNDERDOG_MAX: UNDERDOG_MAX, UNDERDOG_FULL: UNDERDOG_FULL, PITY_PER_MISS: PITY_PER_MISS, PITY_CAP: PITY_CAP, MAX_TOTAL: MAX_TOTAL } };
});
