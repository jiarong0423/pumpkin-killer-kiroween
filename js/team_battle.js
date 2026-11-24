/* Pure helpers for 1–3 unit team rotations; no DOM or match mutation. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.TeamBattle = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function alive(units) { return (units || []).filter(function (unit) { return unit && unit.alive !== false && unit.hp > 0; }); }
  function orderedAlive(units) { return alive(units).slice().sort(function (a, b) { return String(a.id).localeCompare(String(b.id)); }); }
  function nextActive(units, currentId) {
    var list = orderedAlive(units);
    if (!list.length) return null;
    var index = list.findIndex(function (unit) { return unit.id === currentId; });
    return list[(index + 1 + list.length) % list.length];
  }
  function winner(left, right) {
    var leftAlive = alive(left).length > 0, rightAlive = alive(right).length > 0;
    return leftAlive && rightAlive ? null : leftAlive ? 'left' : rightAlive ? 'right' : 'draw';
  }
  function slots(seed, side, count, startX) {
    if (!Number.isInteger(count) || count < 1 || count > 3) throw new RangeError('count must be 1..3');
    var first = side === 0 ? 252 : 1296;
    var last = side === 0 ? 612 : 1656;
    var spacing = count === 1 ? 0 : (last - first) / (count - 1);
    var phase = startX(seed, side, 0) % 2;
    var values = [];
    for (var slot = 0; slot < count; slot++) values.push({ slot: slot, x: first + spacing * slot, staggerY: (slot + phase) % 2 ? 14 : 0 });
    return values;
  }
  function spacing(values) {
    for (var i = 1; i < values.length; i++) if (Math.abs(values[i].x - values[i - 1].x) < 90) return false;
    return true;
  }
  function unitsOf(teams, side) { return teams && Array.isArray(teams[side]) ? teams[side] : []; }
  function activeUnit(teams, side) { return unitsOf(teams, side)[0] || null; }
  function unitState(teams, side, field) {
    var unit = activeUnit(teams, side);
    return unit ? unit[field] : undefined;
  }
  return { alive: alive, orderedAlive: orderedAlive, nextActive: nextActive, winner: winner, slots: slots, spacing: spacing, unitsOf: unitsOf, activeUnit: activeUnit, unitState: unitState };
});
