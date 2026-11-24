/* Shared landing-result classification. Browser global: HitReport; Node: module.exports. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.HitReport = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var DICE_STEP_PX = 36;
  var WAVE_BANDS = [{ max: 35, band: '100' }, { max: 70, band: '75' }, { max: 105, band: '50' }];   // cells of 35 px (owner 2026-11-18): twin of js/sound_wave.js BANDS

  function finite(value, fallback) {
    return typeof value === 'number' && isFinite(value) ? value : fallback;
  }

  function waveBand(distance) {
    var d = Math.abs(finite(distance, Infinity));
    for (var i = 0; i < WAVE_BANDS.length; i++) if (d <= WAVE_BANDS[i].max) return WAVE_BANDS[i].band;
    return 'out';
  }

  function classify(landingX, targetX, hitType, weapon) {
    var landing = finite(landingX, 0);
    var target = finite(targetX, landing);
    var distance = Math.abs(landing - target);
    if (weapon === 'proj_soundwave') {
      var band = waveBand(distance);
      return { kind: 'wave', key: 'hitReport.wave' + band, params: { band: band }, distance: distance, steps: Math.round(distance / DICE_STEP_PX) };
    }
    if (hitType === 'hero') return { kind: 'hit', key: 'hitReport.hit', params: {}, distance: distance, steps: 0 };
    if (hitType === 'wall' || hitType === 'central_wall') return { kind: 'blocked', key: 'hitReport.fence', params: {}, distance: distance, steps: 0 };
    if (hitType === 'shield_blocked' || hitType === 'ultblock' || hitType === 'ultimate_blocked') return { kind: 'blocked', key: 'hitReport.shield', params: {}, distance: distance, steps: 0 };
    return { kind: 'miss', key: landing < target ? 'hitReport.short' : 'hitReport.long', params: { steps: Math.round(distance / DICE_STEP_PX) }, distance: distance, steps: Math.round(distance / DICE_STEP_PX) };
  }

  return { DICE_STEP_PX: DICE_STEP_PX, WAVE_BANDS: WAVE_BANDS, waveBand: waveBand, classify: classify };
});
