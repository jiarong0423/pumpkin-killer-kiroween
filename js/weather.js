/*
 * Deterministic round weather. The rules layer may expose this result directly
 * because weather is public match state.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.Weather = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var ROUNDS_PER_WEATHER = 2;
  var WEATHER = {
    clear: { attackMult: 1, moveMult: 1, windBonus: 0, label: 'Clear' },
    rain: { attackMult: 0.9, moveMult: 1, windBonus: 0, label: 'Rain' },
    snow: { attackMult: 1, moveMult: 0.5, windBonus: 0, label: 'Snow' },
    storm: { attackMult: 0.9, moveMult: 1, windBonus: 1.5, label: 'Storm' },
    fog: { attackMult: 1, moveMult: 1, windBonus: 0, label: 'Fog' }
  };

  // Each row totals 100. Rain and snow remain possible on every map; the
  // repeated draw comes from seed + round block, never from a device clock.
  var WEIGHTS = {
    graveyard: { clear: 42, rain: 20, snow: 8, storm: 5, fog: 25 },
    church: { clear: 24, rain: 32, snow: 6, storm: 18, fog: 20 },
    school: { clear: 37, rain: 27, snow: 7, storm: 4, fog: 25 },
    bell_tower: { clear: 34, rain: 8, snow: 24, storm: 27, fog: 7 },
    pumpkin_field: { clear: 50, rain: 8, snow: 17, storm: 4, fog: 21 },
    default: { clear: 40, rain: 20, snow: 12, storm: 8, fog: 20 }
  };
  var IDS = ['clear', 'rain', 'snow', 'storm', 'fog'];

  function isNum(value) {
    return typeof value === 'number' && isFinite(value);
  }

  function toInt(value, fallback) {
    return isNum(value) ? Math.floor(value) : fallback;
  }

  function safeSeed(value) {
    return toInt(value, 0) | 0;
  }

  function safeRound(value) {
    return Math.max(1, toInt(value, 1));
  }

  function sceneKey(value) {
    if (typeof value !== 'string') return 'default';
    var key = value.toLowerCase().replace(/[\s-]+/g, '_');
    return Object.prototype.hasOwnProperty.call(WEIGHTS, key) ? key : 'default';
  }

  // A small integer permutation, deliberately easy to reproduce in every
  // rules adapter. Across consecutive seeds it visits every hundredth exactly
  // once, which makes the weight distribution measurable without a clock.
  function sample(seed, block) {
    var point = (safeSeed(seed) * 97 + block * 37) % 100;
    return (point < 0 ? point + 100 : point) / 100;
  }

  function idFor(seed, block, weights) {
    // Round after scaling to avoid a binary fraction such as 0.58 becoming
    // 57.99999999999999 at a weight boundary.
    var point = Math.floor(sample(seed, block) * 100 + 1e-8);
    var total = 0;
    for (var i = 0; i < IDS.length; i++) {
      total += weights[IDS[i]];
      if (point < total) return IDS[i];
    }
    return 'clear';
  }

  function copyWeather(id, startsRound, endsRound) {
    var effect = WEATHER[id] || WEATHER.clear;
    return {
      id: id,
      startsRound: startsRound,
      endsRound: endsRound,
      attackMult: effect.attackMult,
      moveMult: effect.moveMult,
      windBonus: effect.windBonus,
      label: effect.label
    };
  }

  function forRound(seed, round, sceneId) {
    var r = safeRound(round);
    var block = Math.floor((r - 1) / ROUNDS_PER_WEATHER);
    var starts = block * ROUNDS_PER_WEATHER + 1;
    return copyWeather(idFor(seed, block, WEIGHTS[sceneKey(sceneId)]), starts, starts + ROUNDS_PER_WEATHER - 1);
  }

  // A hit remains a hit: weather cannot reduce positive damage below one point.
  function applyAttack(weather, damage) {
    var d = isNum(damage) ? damage : 0;
    if (d <= 0) return 0;
    var mult = weather && isNum(weather.attackMult) ? weather.attackMult : 1;
    return Math.max(1, Math.round(d * mult * 10) / 10);
  }

  function applyMove(weather, pixels) {
    var distance = isNum(pixels) ? pixels : 0;
    var mult = weather && isNum(weather.moveMult) ? weather.moveMult : 1;
    return Math.round(distance * mult * 10) / 10;
  }

  function publicState(weather) {
    var w = weather && typeof weather === 'object' ? weather : forRound(0, 1, 'default');
    return {
      id: WEATHER[w.id] ? w.id : 'clear',
      endsRound: safeRound(w.endsRound),
      attackMult: isNum(w.attackMult) ? w.attackMult : 1,
      moveMult: isNum(w.moveMult) ? w.moveMult : 1
    };
  }

  // Kept text-only so a round-state hash can concatenate it without ambiguity.
  function hashText(weather) {
    var w = weather && typeof weather === 'object' ? weather : forRound(0, 1, 'default');
    var p = publicState(w);
    var bonus = isNum(w.windBonus) ? w.windBonus : 0;
    return p.id + ',' + p.endsRound + ',' + p.attackMult.toFixed(1) + ',' + p.moveMult.toFixed(1) + ',' + bonus.toFixed(1);
  }

  return {
    forRound: forRound,
    applyAttack: applyAttack,
    applyMove: applyMove,
    publicState: publicState,
    hashText: hashText,
    WEATHER: WEATHER,
    WEIGHTS: WEIGHTS,
    ROUNDS_PER_WEATHER: ROUNDS_PER_WEATHER
  };
});
