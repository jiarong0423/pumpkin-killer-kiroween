/*
 * Deterministic Smart-opponent candidate builder.
 *
 * This module works from the opponent's noisy public view.  Its optional
 * landing function is supplied by the caller so the page can use its exact
 * fixed-step flight integrator without giving that integrator to the model.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.SmartCandidates = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var MIN_POWER = 15;
  var MAX_POWER = 115;
  var MIN_ANGLE = 25;
  var MAX_ANGLE = 80;
  var MOVE_STEP = 36;
  var MOVE_EXPECTED_STEPS = 3.5;
  var LEFT_LIMITS = [110, 640];
  var RIGHT_LIMITS = [1280, 1810];

  function number(value, fallback) {
    return typeof value === 'number' && isFinite(value) ? value : fallback;
  }

  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  function validAim(aim) {
    return !!aim && typeof aim === 'object' &&
      number(aim.angle, NaN) >= MIN_ANGLE && number(aim.angle, NaN) <= MAX_ANGLE &&
      number(aim.power, NaN) >= MIN_POWER && number(aim.power, NaN) <= MAX_POWER;
  }

  function canonicalAim(aim) {
    return {
      angle: Math.round(clamp(number(aim.angle, 54), MIN_ANGLE, MAX_ANGLE)),
      power: Math.round(clamp(number(aim.power, 54), MIN_POWER, MAX_POWER))
    };
  }

  function fallbackLanding(power, input) {
    // Tests can omit a flight function. This is only a stable ordering fallback;
    // the page always supplies its fixed-step simulateLandingX function.
    var direction = number(input.direction, -1);
    return number(input.own_position, 0) + direction * power * 20;
  }

  function landingDistance(input, aim) {
    var direction = number(input.direction, -1) < 0 ? -1 : 1;
    var landing = typeof input.simulateLandingX === 'function'
      ? input.simulateLandingX(aim.power, number(input.start_x, input.own_position), number(input.start_y, 750), direction, aim.angle, number(input.wind, 0))
      : fallbackLanding(aim.power, input);
    return Math.abs(landing - number(input.enemy_position, 0));
  }

  function addThrow(out, kind, input, aim) {
    var clean = canonicalAim(aim);
    out.push({ kind: kind, aim: clean, predicted_distance_px: landingDistance(input, clean) });
  }

  function recentHitCount(input) {
    return Math.max(0, Math.floor(number(input.recent_enemy_hits, 0)));
  }

  function moveCandidate(input, normalDistance) {
    var own = number(input.own_position, 0);
    var enemy = number(input.enemy_position, 0);
    var isLeft = own <= enemy;
    var limits = isLeft ? LEFT_LIMITS : RIGHT_LIMITS;
    var forward = isLeft ? 1 : -1;
    var expected = MOVE_EXPECTED_STEPS * MOVE_STEP;
    var ahead = clamp(own + forward * expected, limits[0], limits[1]);
    var behind = clamp(own - forward * expected, limits[0], limits[1]);
    var candidates = [
      { kind: 'move_forward', distance: Math.abs(enemy - ahead) },
      { kind: 'move_back', distance: Math.abs(enemy - behind) }
    ].filter(function (candidate) { return candidate.distance < normalDistance; });
    if (!candidates.length) return null;
    candidates.sort(function (a, b) { return a.distance - b.distance || a.kind.localeCompare(b.kind); });
    return { kind: candidates[0].kind, predicted_distance_px: candidates[0].distance };
  }

  function build(input) {
    input = input && typeof input === 'object' ? input : {};
    var normal = validAim(input.normal_aim) ? canonicalAim(input.normal_aim) : { angle: 54, power: 54 };
    var candidates = [];
    addThrow(candidates, 'normal', input, normal);
    addThrow(candidates, 'under', input, { angle: normal.angle, power: normal.power - 3 });
    addThrow(candidates, 'over', input, { angle: normal.angle, power: normal.power + 3 });

    var skills = input.own_skills && typeof input.own_skills === 'object' ? input.own_skills : {};
    if (skills.heavy > 0) addThrow(candidates, 'heavy', input, normal);
    if (input.ultimate_available === true) addThrow(candidates, 'ultimate', input, normal);
    if (input.own_hero_id === 'knight' && recentHitCount(input) >= 2) {
      candidates.push({ kind: 'defend', predicted_distance_px: landingDistance(input, normal) });
    }
    var move = moveCandidate(input, landingDistance(input, normal));
    if (move) candidates.push(move);

    candidates.sort(function (a, b) {
      // Candidate 1 is ALWAYS the built-in Normal aim (the fallback contract: "always pick 1" equals the Normal opponent); the others follow by predicted distance
      if (a.kind === 'normal' || b.kind === 'normal') return a.kind === 'normal' ? -1 : 1;
      var distance = a.predicted_distance_px - b.predicted_distance_px;
      if (distance) return distance;
      // Preserve Normal as the fallback when equally accurate actions tie.
      var rank = { normal: 0, under: 1, over: 2, heavy: 3, ultimate: 4, defend: 5, move_forward: 6, move_back: 7 };
      return (rank[a.kind] || 99) - (rank[b.kind] || 99);
    });
    // The gateway accepts at most six choices. Normal, deliberate ±3, and the
    // three one-turn choices above naturally fit that public contract.
    candidates = candidates.slice(0, 6);
    return candidates.map(function (candidate, index) {
      var result = { id: index + 1, kind: candidate.kind, predicted_distance_px: Math.round(candidate.predicted_distance_px * 100) / 100 };
      if (candidate.aim) result.aim = candidate.aim;
      return result;
    });
  }

  return Object.freeze({ build: build });
});
