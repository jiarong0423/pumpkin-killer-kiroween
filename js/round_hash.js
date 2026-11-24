/* Canonical public-round text and portable SHA-256 short hash. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.RoundHash = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function assertFinite(value, name) {
    if (typeof value !== 'number' || !isFinite(value)) throw new TypeError(name + ' must be finite');
    return value;
  }
  function roundHalfUp(value, decimals) {
    var factor = Math.pow(10, decimals);
    return Math.floor(assertFinite(value, 'number') * factor + 0.5) / factor;
  }
  function fixed(value, decimals) { return roundHalfUp(value, decimals).toFixed(decimals); }
  var MAX_TEAM_SIZE = 3;
  var UNIT_ID = /^[A-Za-z0-9_.:-]+$/;   // ASCII only and nothing below ',' so that sorting by id and sorting by row text give the same order in every runtime
  function unitsOf(state) {
    if (Array.isArray(state.units)) return state.units.slice();
    if (state.units && typeof state.units === 'object') return Object.keys(state.units).map(function (id) {
      return Object.assign({ id: id }, state.units[id]);
    });
    throw new TypeError('state.units must be an array or object');
  }
  function statusText(statuses) {
    if (statuses === undefined || statuses === null) return '';
    var canonical = /^(?:(?:bleed|poison|burn|weak|slow):[1-9][0-9]*|stun)$/;
    if (!Array.isArray(statuses) || !statuses.every(function (status) { return typeof status === 'string' && canonical.test(status); })) {
      throw new TypeError('statuses must be canonical status words');
    }
    return statuses.slice().sort().join('|');
  }
  /* Team-battle ids on the wire and in the hash are world ids: left_0..left_2 and right_0..right_2.
     The MCP engine names the same units red_1..red_3 and white_1..white_3 (one-based); this maps them. */
  function worldUnitId(id) {
    var match = typeof id === 'string' ? /^(?:(left|right)(?:_([0-2]))?|(red|white)_([1-3]))$/.exec(id) : null;
    if (!match) throw new TypeError('unit id has no world form: ' + String(id));
    if (match[1]) return match[2] === undefined ? match[1] : match[1] + '_' + match[2];
    return (match[3] === 'red' ? 'left_' : 'right_') + (Number(match[4]) - 1);
  }
  function unitIds(teamSize) {
    if (!Number.isInteger(teamSize) || teamSize < 1 || teamSize > MAX_TEAM_SIZE) throw new RangeError('teamSize must be 1..' + MAX_TEAM_SIZE);
    var ids = [], i;
    for (i = 0; i < teamSize; i++) ids.push('left_' + i);
    for (i = 0; i < teamSize; i++) ids.push('right_' + i);
    return ids;
  }
  function checkTeamSize(state, ids) {
    var size = state.teamSize === undefined ? state.team_size : state.teamSize;
    if (size === undefined) return;
    var expected = unitIds(size);   // throws unless 1..3
    if (ids.length !== expected.length) throw new TypeError('state must list every unit of both teams: expected ' + expected.length + ', got ' + ids.length);
    if (size > 1 && expected.some(function (id, index) { return ids[index] !== id; })) {
      throw new TypeError('team units must be ' + expected.join(','));
    }
  }
  function canonicalText(state) {
    if (!state || typeof state !== 'object') throw new TypeError('state must be an object');
    var rows = unitsOf(state).map(function (unit) {
      if (!unit || typeof unit.id !== 'string' || !UNIT_ID.test(unit.id)) throw new TypeError('unit id is invalid');
      if (typeof unit.alive !== 'boolean') throw new TypeError('unit.alive must be boolean');
      return { id: unit.id, text: unit.id + ',' + fixed(unit.x, 0) + ',' + fixed(unit.y, 0) + ',' + fixed(unit.hp, 1) + ',' +
        (unit.alive ? 'true' : 'false') + ',' + statusText(unit.statuses) };
    }).sort(function (a, b) { return a.id < b.id ? -1 : a.id > b.id ? 1 : 0; });
    var ids = rows.map(function (row) { return row.id; });
    ids.forEach(function (id, index) { if (index && ids[index - 1] === id) throw new TypeError('duplicate unit id: ' + id); });
    checkTeamSize(state, ids);
    var wallHp = state.wallHp === undefined ? state.wall_hp : state.wallHp;
    return rows.map(function (row) { return row.text; }).concat([
      'wall_hp,' + fixed(wallHp, 1), 'round,' + fixed(state.round, 0),
      'phase,' + String(state.phase), 'seed,' + String(state.seed)
    ]).join('\n');
  }

  function sha256(text) {
    var encoded = unescape(encodeURIComponent(String(text)));
    var bytes = [];
    var i;
    for (i = 0; i < encoded.length; i++) bytes.push(encoded.charCodeAt(i));
    var bitLength = bytes.length * 8;
    bytes.push(0x80);
    while (bytes.length % 64 !== 56) bytes.push(0);
    for (i = 7; i >= 0; i--) bytes.push(Math.floor(bitLength / Math.pow(2, i * 8)) & 0xff);
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var k = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    for (var offset = 0; offset < bytes.length; offset += 64) {
      var w = new Array(64).fill(0);
      for (i = 0; i < 16; i++) w[i] = (bytes[offset + i * 4] << 24) | (bytes[offset + i * 4 + 1] << 16) | (bytes[offset + i * 4 + 2] << 8) | bytes[offset + i * 4 + 3];
      for (i = 16; i < 64; i++) {
        var x = w[i - 15], y = w[i - 2];
        var s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3);
        var s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
      }
      var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], q = h[7];
      for (i = 0; i < 64; i++) {
        var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
        var t1 = (q + S1 + ((e & f) ^ (~e & g)) + k[i] + w[i]) | 0;
        var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
        var t2 = (S0 + ((a & b) ^ (a & c) ^ (b & c))) | 0;
        q = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      h[0] = (h[0] + a) | 0; h[1] = (h[1] + b) | 0; h[2] = (h[2] + c) | 0; h[3] = (h[3] + d) | 0;
      h[4] = (h[4] + e) | 0; h[5] = (h[5] + f) | 0; h[6] = (h[6] + g) | 0; h[7] = (h[7] + q) | 0;
    }
    return h.map(function (value) { return ('00000000' + (value >>> 0).toString(16)).slice(-8); }).join('');
  }
  function hash(state) { return sha256(canonicalText(state)).slice(0, 8); }
  return { MAX_TEAM_SIZE: MAX_TEAM_SIZE, canonicalText: canonicalText, sha256: sha256, hash: hash, worldUnitId: worldUnitId, unitIds: unitIds };
});
