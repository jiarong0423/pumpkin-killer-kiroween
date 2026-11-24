/*
 * Portable deterministic match values. Keep this integer-only hash identical
 * to scripts/determinism_py.py so a replay has one answer on every device.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.Determinism = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var UINT32_MAX = 4294967295;
  var START_STEP = 36;
  var LEFT_START = 252;
  var RIGHT_START = 1296;
  var START_CHOICES = 11;
  var DOMAIN = {
    wind: 0x51f15e1d,
    startX: 0x5a17a7e1,
    moveDie: 0x6d0d0001,
    supplyDrop: 0x51a0d00d,
    bounceCount: 0xb00ce001,
    nunStunPick: 0x57a70001,
    sideDraw: 0x51de0001
  };

  function uint32(value, name) {
    if (typeof value !== 'number' || !isFinite(value) || Math.floor(value) !== value || value < 0 || value > UINT32_MAX) {
      throw new RangeError(name + ' must be a uint32 integer');
    }
    return value >>> 0;
  }

  function sideValue(side) {
    var value = uint32(side, 'side');
    if (value !== 0 && value !== 1) throw new RangeError('side must be 0 or 1');
    return value;
  }

  function positiveValue(value, name) {
    var result = uint32(value, name);
    if (result < 1) throw new RangeError(name + ' must be at least 1');
    return result;
  }

  function mix32(value) {
    value = Math.imul(value ^ (value >>> 16), 0x85ebca6b) >>> 0;
    value = Math.imul(value ^ (value >>> 13), 0xc2b2ae35) >>> 0;
    return (value ^ (value >>> 16)) >>> 0;
  }

  function hash(seed, domain, first, second) {
    var value = mix32((uint32(seed, 'seed') + 0x9e3779b9) >>> 0);
    value = mix32((value ^ (domain >>> 0)) >>> 0);
    value = mix32((value ^ uint32(first, 'hash input')) >>> 0);
    return mix32((value ^ uint32(second, 'hash input')) >>> 0);
  }

  function wind(seed, round) {
    var seedValue = uint32(seed, 'seed');
    var roundValue = positiveValue(round, 'round');
    var tenths = roundValue === 1 ? (seedValue % 81) - 40 : (hash(seedValue, DOMAIN.wind, roundValue, 0) % 81) - 40;
    return tenths / 10;
  }

  function startX(seed, side, slot) {
    var sideNumber = sideValue(side);
    var slotValue = uint32(slot, 'slot');
    var start = sideNumber === 0 ? LEFT_START : RIGHT_START;
    return start + (hash(seed, DOMAIN.startX, sideNumber, slotValue) % START_CHOICES) * START_STEP;
  }

  function moveDie(seed, round, side) {
    return 1 + (hash(seed, DOMAIN.moveDie, positiveValue(round, 'round'), sideValue(side)) % 6);
  }

  function supplyDrop(seed, round) {
    var value = hash(seed, DOMAIN.supplyDrop, positiveValue(round, 'round'), 0);
    return { side: value & 1, item: (value >>> 1) & 1, offset: -120 + ((value >>> 2) % 241) };
  }

  function bounceCount(seed, round, throwId) {
    return 1 + (hash(seed, DOMAIN.bounceCount, positiveValue(round, 'round'), uint32(throwId, 'throwId')) % 6);
  }

  function nunStunPick(seed, round, throwId, n) {
    return hash(seed, DOMAIN.nunStunPick, positiveValue(round, 'round'), uint32(throwId, 'throwId')) % positiveValue(n, 'n');
  }

  function sideDraw(seed) {
    return hash(seed, DOMAIN.sideDraw, 0, 0) & 1;
  }

  function coinToss(seed) {
    return hash(seed, 7001, 0, 0) & 1;
  }

  return {
    wind: wind,
    startX: startX,
    moveDie: moveDie,
    supplyDrop: supplyDrop,
    bounceCount: bounceCount,
    nunStunPick: nunStunPick,
    sideDraw: sideDraw,
    coinToss: coinToss
  };
});
