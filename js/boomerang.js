/*
 * Pumpkin Killer hunchback boomerang-axe resolution.
 *
 * The axe pierces every living enemy on its outbound polyline. It ignores
 * shields, then returns to the first enemy it reached. Return speed is an
 * invented working value pending owner confirmation.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.Boomerang = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var OUTBOUND_DAMAGE = 21;
  var RETURN_DAMAGE = 31.5;
  var RETURN_SPEED = 1400; // INVENTED: owner did not specify the return speed.
  var HIT_RADIUS = 40;

  function isFiniteNumber(value) {
    return typeof value === 'number' && isFinite(value);
  }

  function distance(a, b) {
    var dx = b.x - a.x;
    var dy = b.y - a.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function pointFor(value) {
    if (!value || typeof value !== 'object' || !isFiniteNumber(value.x) || !isFiniteNumber(value.y)) return null;
    return { x: value.x, y: value.y, t: isFiniteNumber(value.t) && value.t >= 0 ? value.t : null };
  }

  function normalisePath(path, speed) {
    if (!Array.isArray(path)) return [];
    var points = [];
    for (var i = 0; i < path.length; i++) {
      var point = pointFor(path[i]);
      if (point) points.push(point);
    }
    if (points.length < 2) return [];
    var elapsed = 0;
    for (var j = 1; j < points.length; j++) {
      var segment = distance(points[j - 1], points[j]);
      var fallback = elapsed + segment / speed;
      if (points[j - 1].t === null) points[j - 1].t = elapsed;
      elapsed = points[j].t !== null && points[j].t >= points[j - 1].t ? points[j].t : fallback;
      points[j].t = elapsed;
    }
    if (points[0].t === null) points[0].t = 0;
    return points;
  }

  // Returns the first fraction along a segment at which its centre enters the
  // target radius, or null when the segment never reaches the target.
  function contactFraction(from, to, target) {
    var dx = to.x - from.x;
    var dy = to.y - from.y;
    var lengthSquared = dx * dx + dy * dy;
    if (lengthSquared === 0) return distance(from, target) <= HIT_RADIUS ? 0 : null;
    var projection = ((target.x - from.x) * dx + (target.y - from.y) * dy) / lengthSquared;
    var closest = projection < 0 ? 0 : projection > 1 ? 1 : projection;
    var closestX = from.x + dx * closest;
    var closestY = from.y + dy * closest;
    var offsetX = target.x - closestX;
    var offsetY = target.y - closestY;
    if (offsetX * offsetX + offsetY * offsetY > HIT_RADIUS * HIT_RADIUS) return null;
    var segmentLength = Math.sqrt(lengthSquared);
    var along = projection * segmentLength;
    var inside = Math.sqrt(Math.max(0, HIT_RADIUS * HIT_RADIUS - (offsetX * offsetX + offsetY * offsetY)));
    return Math.max(0, Math.min(1, (along - inside) / segmentLength));
  }

  function livingEnemies(enemies) {
    if (!Array.isArray(enemies)) return [];
    var result = [];
    var seen = Object.create(null);
    for (var i = 0; i < enemies.length; i++) {
      var enemy = enemies[i];
      if (!enemy || typeof enemy !== 'object' || enemy.alive !== true || !isFiniteNumber(enemy.x) || !isFiniteNumber(enemy.y)) continue;
      var key = typeof enemy.id + ':' + String(enemy.id);
      if (seen[key]) continue;
      seen[key] = true;
      result.push({ id: enemy.id, x: enemy.x, y: enemy.y, shielded: enemy.shielded === true });
    }
    return result;
  }

  function resolve(outboundPath, enemies, returnSpeed) {
    var speed = isFiniteNumber(returnSpeed) && returnSpeed > 0 ? returnSpeed : RETURN_SPEED;
    var path = normalisePath(outboundPath, speed);
    if (path.length === 0) return [];
    var targets = livingEnemies(enemies);
    var contacts = [];
    var travelled = 0;
    var firstPathDistance = 0;
    var hitIds = Object.create(null);
    for (var segment = 1; segment < path.length; segment++) {
      var from = path[segment - 1];
      var to = path[segment];
      var segmentLength = distance(from, to);
      var segmentHits = [];
      for (var i = 0; i < targets.length; i++) {
        var target = targets[i];
        var key = typeof target.id + ':' + String(target.id);
        if (hitIds[key]) continue;
        var fraction = contactFraction(from, to, target);
        if (fraction !== null) segmentHits.push({ target: target, fraction: fraction, key: key });
      }
      segmentHits.sort(function (a, b) { return a.fraction - b.fraction || (a.key < b.key ? -1 : a.key > b.key ? 1 : 0); });
      for (var j = 0; j < segmentHits.length; j++) {
        var contact = segmentHits[j];
        hitIds[contact.key] = true;
        if (contacts.length === 0) firstPathDistance = travelled + segmentLength * contact.fraction;
        contacts.push({
          phase: 'outbound', target: contact.target.id, x: contact.target.x, y: contact.target.y,
          t: from.t + (to.t - from.t) * contact.fraction, damage: OUTBOUND_DAMAGE,
          blockable: false, shielded: contact.target.shielded
        });
      }
      travelled += segmentLength;
    }
    if (contacts.length === 0) return contacts;
    var first = contacts[0];
    var end = path[path.length - 1];
    var returnDistance = travelled - firstPathDistance;
    contacts.push({
      phase: 'return', target: first.target, x: first.x, y: first.y,
      t: end.t + returnDistance / speed, damage: RETURN_DAMAGE,
      blockable: false
    });
    return contacts;
  }

  return {
    OUTBOUND_DAMAGE: OUTBOUND_DAMAGE,
    RETURN_DAMAGE: RETURN_DAMAGE,
    RETURN_SPEED: RETURN_SPEED,
    HIT_RADIUS: HIT_RADIUS,
    resolve: resolve
  };
});
