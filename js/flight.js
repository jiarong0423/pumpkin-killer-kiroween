/* Shared fixed-step flight model. Browser global: Flight; Node: module.exports. */
(function (root, factory) {
  'use strict';
  var constants = null;
  if (typeof module === 'object' && module && module.exports && typeof require === 'function') {
    constants = require('../shared/constants.json');
  }
  var api = factory(constants);
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.Flight = api;
})(typeof self !== 'undefined' ? self : this, function (shared) {
  'use strict';
  // The browser has no JSON module loader; these fallbacks mirror shared/constants.json.
  var C = shared || { GROUND_Y: 860, GRAVITY: 980, V0_PER_POWER: 13.8, FENCE_X: 960, FENCE_W: 238, FENCE_H: 282, WIND_TAIL: 56, WIND_HEAD: 84 };
  var STEP = 1 / 60;
  // Headwind (wind against the shot) drags harder than tailwind helps: owner 2026-11-16 wanted a clear difference and every target must stay hittable (scripts/test_wind_reach.js: every start position can hit every target in every wind from -4 to 4; tail above about 85 or head above about 84 breaks the nearest or the farthest case).
  function windAccel(wind, dirX) { return wind * (wind * dirX > 0 ? C.WIND_TAIL : C.WIND_HEAD); }
  var CANVAS_W = 1920;
  var MAX_STEPS = 1200;

  function number(value, name) {
    if (typeof value !== 'number' || !isFinite(value)) throw new TypeError(name + ' must be finite');
    return value;
  }

  function simulate(input) {
    if (!input || typeof input !== 'object') throw new TypeError('input must be an object');
    var startX = number(input.startX, 'startX');
    var startY = number(input.startY, 'startY');
    var dirX = number(input.dirX, 'dirX');
    var angleDeg = number(input.angleDeg, 'angleDeg');
    var power = number(input.power, 'power');
    var wind = number(input.wind, 'wind');
    var dt = input.step === undefined ? STEP : number(input.step, 'step');
    if (input.wave !== undefined && typeof input.wave !== 'boolean') throw new TypeError('wave must be a boolean');
    var wave = input.wave === true;   // the bride's wave counts where it REALLY lands (page tCross, engine twin, owner 2026-11-17 / 2026-11-19): the step that crosses the ground is cut back to the crossing point
    if (input.wall !== undefined && typeof input.wall !== 'boolean') throw new TypeError('wall must be a boolean');
    var wall = input.wall !== false;   // owner 2026-11-19: broken central fence (wallHp <= 0) lets flat shots pass straight through
    if (!(dt > 0)) throw new RangeError('step must be positive');

    var rad = angleDeg * Math.PI / 180;
    var v0 = power * C.V0_PER_POWER;
    var vx = v0 * Math.cos(rad) * dirX;
    var vy = -v0 * Math.sin(rad);
    var x = startX;
    var y = startY;
    var points = [{ x: x, y: y }];
    for (var i = 0; i < MAX_STEPS; i++) {
      vx += windAccel(wind, dirX) * dt;
      vy += C.GRAVITY * dt;
      var prevX = x, prevY = y;
      x += vx * dt;
      y += vy * dt;
      if (wave && prevY < C.GROUND_Y && y > C.GROUND_Y) { var tCross = (C.GROUND_Y - prevY) / (y - prevY); x = prevX + (x - prevX) * tCross; y = C.GROUND_Y; }
      points.push({ x: x, y: y });
      // This is the page's collision order: wall before ground (only while the fence stands).
      if (wall && x >= C.FENCE_X - C.FENCE_W / 2 && x <= C.FENCE_X + C.FENCE_W / 2 && y >= C.GROUND_Y - C.FENCE_H) {
        return { landingX: x, landingY: y, hit: 'wall', points: points };
      }
      if (y >= C.GROUND_Y && vy > 0) return { landingX: x, landingY: y, hit: 'ground', points: points };
      if (x < 0 || x > CANVAS_W) return { landingX: x, landingY: y, hit: 'out', points: points };
    }
    return { landingX: x, landingY: y, hit: 'out', points: points };
  }

  function roundToGrid(value, grid) {
    return Math.round(value / grid) * grid;
  }

  function coarsePath(points) {
    if (!Array.isArray(points) || points.length === 0) return [];
    var count = Math.min(5, points.length);
    var out = [];
    for (var i = 0; i < count; i++) {
      var index = Math.round(i * (points.length - 1) / Math.max(1, count - 1));
      out.push({ x: roundToGrid(points[index].x, 10), y: roundToGrid(points[index].y, 10) });
    }
    return out;
  }

  return { simulate: simulate, coarsePath: coarsePath, constants: C };
});
