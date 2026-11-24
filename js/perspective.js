/* Pure local/world coordinate mapping. The page's local player is always left. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.Perspective = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var CANVAS_WIDTH = 1920;

  function sideName(value) {
    if (value !== 'left' && value !== 'right') throw new RangeError('side must be left or right');
    return value;
  }

  function dir(value, name) {
    if (value !== -1 && value !== 1) throw new RangeError((name || 'direction') + ' must be -1 or 1');
    return value;
  }

  function flipSide(side) { return side === 'left' ? 'right' : 'left'; }

  function mappedUnitId(value, mapSide) {
    if (typeof value !== 'string' || !value) throw new TypeError('unit id must be a non-empty string');
    var match = /^(left|right)(.*)$/.exec(value);
    return match ? mapSide(match[1]) + match[2] : value;
  }

  function create(ownSeat) {
    sideName(ownSeat);
    var mirrored = ownSeat === 'right';
    function x(worldX) {
      if (typeof worldX !== 'number' || !isFinite(worldX)) throw new TypeError('x must be finite');
      return mirrored ? CANVAS_WIDTH - worldX : worldX;
    }
    function wind(worldWind) {
      if (typeof worldWind !== 'number' || !isFinite(worldWind)) throw new TypeError('wind must be finite');
      return mirrored ? -worldWind : worldWind;
    }
    function side(worldSide) {
      worldSide = sideName(worldSide);
      return mirrored ? flipSide(worldSide) : worldSide;
    }
    function worldSide(localSide) { return side(localSide); }
    function dirX(worldDir) { return mirrored ? -dir(worldDir, 'dirX') : dir(worldDir, 'dirX'); }
    function worldDirX(localDir) { return dirX(localDir); }
    function angle(degrees) {
      if (typeof degrees !== 'number' || !isFinite(degrees)) throw new TypeError('angle must be finite');
      return degrees;
    }
    return Object.freeze({
      ownSeat: ownSeat,
      mirrored: mirrored,
      x: x,
      wind: wind,
      side: side,
      worldSide: worldSide,
      unitId: function (worldUnitId) { return mappedUnitId(worldUnitId, side); },
      worldUnitId: function (localUnitId) { return mappedUnitId(localUnitId, worldSide); },
      meUnitId: function (suffix) { return 'left' + (suffix || '_0'); },
      opponentUnitId: function (suffix) { return 'right' + (suffix || '_0'); },
      worldMeUnitId: function (suffix) { return worldSide('left') + (suffix || '_0'); },
      worldOpponentUnitId: function (suffix) { return worldSide('right') + (suffix || '_0'); },
      dirX: dirX,
      worldDirX: worldDirX,
      angle: angle,
      diceDirection: dirX,
      worldDiceDirection: worldDirX
    });
  }

  return { CANVAS_WIDTH: CANVAS_WIDTH, create: create };
});
