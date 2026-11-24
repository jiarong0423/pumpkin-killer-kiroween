/* Offline QR encoder: byte mode, EC levels L (versions 1–10) and M (versions 1–7). */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.QrCode = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var LEVELS = {
    L: {
      dataWords: [19, 34, 55, 80, 108, 136, 156, 194, 232, 274],
      ecWords: [7, 10, 15, 20, 26, 18, 20, 24, 30, 18],
      blocks: [1, 1, 1, 1, 1, 2, 2, 2, 2, 4],
      maxVersion: 5,   // versions 6 and up are not accepted: OpenCV decodes L-v6 only 4 of 6 and L/M-v7+ 0 of 6 (the version information blocks are missing); a scanner-proof code beats capacity (2026-11-16)
      formatBits: 1
    },
    M: {
      dataWords: [16, 28, 44, 64, 86, 108, 124],
      ecWords: [10, 16, 26, 18, 24, 16, 18],
      blocks: [1, 1, 1, 2, 2, 4, 4],
      maxVersion: 6,
      formatBits: 0
    }
  };
  var ALIGNMENT = [[], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42], [6, 26, 46], [6, 28, 50]];
  var EXP = [], LOG = [];
  (function buildGaloisTables() {
    var value = 1, i;
    for (i = 0; i < 255; i += 1) { EXP[i] = value; LOG[value] = i; value <<= 1; if (value & 256) value ^= 285; }
    for (i = 255; i < 512; i += 1) EXP[i] = EXP[i - 255];
  })();
  function multiply(a, b) { return !a || !b ? 0 : EXP[LOG[a] + LOG[b]]; }
  function generator(degree) {
    var poly = [1], i, j, next;
    for (i = 0; i < degree; i += 1) {
      next = Array(poly.length + 1).fill(0);
      for (j = 0; j < poly.length; j += 1) { next[j] ^= poly[j]; next[j + 1] ^= multiply(poly[j], EXP[i]); }
      poly = next;
    }
    return poly;
  }
  function ecc(data, degree) {
    var remainder = Array(degree).fill(0), gen = generator(degree), i, j, factor;
    for (i = 0; i < data.length; i += 1) {
      factor = data[i] ^ remainder.shift(); remainder.push(0);
      for (j = 0; j < degree; j += 1) remainder[j] ^= multiply(gen[j + 1], factor);
    }
    return remainder;
  }
  function bits(value, count, out) { for (var i = count - 1; i >= 0; i -= 1) out.push((value >>> i) & 1); }
  function toBytes(text) {
    var encoded = unescape(encodeURIComponent(String(text))), out = [], i;
    for (i = 0; i < encoded.length; i += 1) out.push(encoded.charCodeAt(i));
    return out;
  }
  function levelFor(options) {
    var level = typeof options === 'string' ? options : options && options.level;
    level = level || 'L';
    if (!LEVELS[level]) throw new RangeError('Unsupported QR error-correction level: ' + level);
    return { name: level, table: LEVELS[level] };
  }
  function payloadCapacity(version, level) {
    return level.dataWords[version - 1] - (version < 10 ? 2 : 3);
  }
  function usesUtf8Eci(text) {
    return /[^\x00-\x7f]/.test(String(text));
  }
  function requiredBits(byteLength, version, withEci) {
    return (withEci ? 12 : 0) + 4 + (version < 10 ? 8 : 16) + byteLength * 8;
  }
  function selectVersion(byteLength, level, withEci) {
    var version = 1;
    while (version <= level.maxVersion && requiredBits(byteLength, version, withEci) > level.dataWords[version - 1] * 8) version += 1;
    if (version > level.maxVersion) throw new RangeError('QR byte payload exceeds version ' + level.maxVersion + '-' + level.name + ' capacity');
    return version;
  }
  function interleave(data, version, level) {
    var index = version - 1, blockCount = level.blocks[index], ecCount = level.ecWords[index];
    var shortDataLength = Math.floor(level.dataWords[index] / blockCount);
    var shortBlockCount = blockCount - (level.dataWords[index] % blockCount);
    var blocks = [], cursor = 0, block, i, column, words = [];
    for (i = 0; i < blockCount; i += 1) {
      block = data.slice(cursor, cursor + shortDataLength + (i >= shortBlockCount ? 1 : 0));
      cursor += block.length;
      blocks.push({ data: block, ec: ecc(block, ecCount) });
    }
    for (column = 0; column <= shortDataLength; column += 1) {
      blocks.forEach(function (entry) { if (column < entry.data.length) words.push(entry.data[column]); });
    }
    for (column = 0; column < ecCount; column += 1) blocks.forEach(function (entry) { words.push(entry.ec[column]); });
    return words;
  }
  function codewords(text, options) {
    var chosen = levelFor(options), level = chosen.table, raw = toBytes(text), withEci = usesUtf8Eci(text), version = selectVersion(raw.length, level, withEci);
    var stream = [], data = [], i;
    if (withEci) { bits(7, 4, stream); bits(26, 8, stream); }
    bits(4, 4, stream); bits(raw.length, version < 10 ? 8 : 16, stream); raw.forEach(function (byte) { bits(byte, 8, stream); });
    for (i = 0; i < 4 && stream.length < level.dataWords[version - 1] * 8; i += 1) stream.push(0);
    while (stream.length % 8) stream.push(0);
    for (i = 0; i < stream.length; i += 8) data.push(parseInt(stream.slice(i, i + 8).join(''), 2));
    for (i = 0; data.length < level.dataWords[version - 1]; i += 1) data.push(i % 2 ? 17 : 236);
    return { version: version, level: chosen.name, words: interleave(data, version, level) };
  }
  function makeMatrix(size) { return Array.from({ length: size }, function () { return Array(size).fill(null); }); }
  function finder(matrix, x, y) {
    for (var dy = -1; dy <= 7; dy += 1) for (var dx = -1; dx <= 7; dx += 1) {
      var row = y + dy, col = x + dx;
      if (row < 0 || col < 0 || row >= matrix.length || col >= matrix.length) continue;
      matrix[row][col] = dx >= 0 && dx <= 6 && dy >= 0 && dy <= 6 && (dx === 0 || dx === 6 || dy === 0 || dy === 6 || (dx >= 2 && dx <= 4 && dy >= 2 && dy <= 4));
    }
  }
  function alignment(matrix, x, y) { for (var dy = -2; dy <= 2; dy += 1) for (var dx = -2; dx <= 2; dx += 1) matrix[y + dy][x + dx] = Math.max(Math.abs(dx), Math.abs(dy)) !== 1; }
  function formatBits(mask, level) {
    var value = (level.formatBits << 3) | mask, rem = value << 10, i;
    for (i = 14; i >= 10; i -= 1) if (rem & (1 << i)) rem ^= 0x537 << (i - 10);
    return ((value << 10) | rem) ^ 0x5412;
  }
  function versionBits(version) {
    var rem = version << 12, i;
    for (i = 17; i >= 12; i -= 1) if (rem & (1 << i)) rem ^= 0x1f25 << (i - 12);
    return (version << 12) | rem;
  }
  function reserved(matrix, version) {
    var size = matrix.length, i, pos = ALIGNMENT[version - 1];
    finder(matrix, 0, 0); finder(matrix, size - 7, 0); finder(matrix, 0, size - 7);
    for (i = 8; i < size - 8; i += 1) { if (matrix[6][i] === null) matrix[6][i] = i % 2 === 0; if (matrix[i][6] === null) matrix[i][6] = i % 2 === 0; }
    pos.forEach(function (row) { pos.forEach(function (col) { if (matrix[row][col] === null) alignment(matrix, col, row); }); });
    for (i = 0; i < 9; i += 1) { if (matrix[8][i] === null) matrix[8][i] = false; if (matrix[i][8] === null) matrix[i][8] = false; }
    for (i = 0; i < 8; i += 1) { matrix[8][size - 1 - i] = false; matrix[size - 1 - i][8] = false; }
    if (version >= 7) for (i = 0; i < 18; i += 1) {
      matrix[Math.floor(i / 3)][size - 11 + (i % 3)] = false;
      matrix[size - 11 + (i % 3)][Math.floor(i / 3)] = false;
    }
    matrix[size - 8][8] = true;
  }
  function maskAt(mask, row, col) { return [function () { return (row + col) % 2 === 0; }, function () { return row % 2 === 0; }, function () { return col % 3 === 0; }, function () { return (row + col) % 3 === 0; }, function () { return (Math.floor(row / 2) + Math.floor(col / 3)) % 2 === 0; }, function () { return (row * col) % 2 + (row * col) % 3 === 0; }, function () { return ((row * col) % 2 + (row * col) % 3) % 2 === 0; }, function () { return ((row + col) % 2 + (row * col) % 3) % 2 === 0; }][mask](); }
  function placeData(matrix, words, mask) {
    var bitsOut = []; words.forEach(function (word) { bits(word, 8, bitsOut); });
    var size = matrix.length, bit = 0, upward = true, col, row, c;
    for (col = size - 1; col > 0; col -= 2) {
      if (col === 6) col -= 1;
      for (c = 0; c < size; c += 1) {
        row = upward ? size - 1 - c : c;
        for (var dc = 0; dc < 2; dc += 1) if (matrix[row][col - dc] === null) { var value = bit < bitsOut.length ? !!bitsOut[bit] : false; bit += 1; matrix[row][col - dc] = maskAt(mask, row, col - dc) ? !value : value; }
      }
      upward = !upward;
    }
  }
  function placeFormat(matrix, mask, level) {
    var value = formatBits(mask, level), size = matrix.length, i;
    for (i = 0; i < 15; i += 1) {
      var dark = !!((value >>> i) & 1);
      if (i < 6) matrix[i][8] = dark; else if (i < 8) matrix[i + 1][8] = dark; else matrix[size - 15 + i][8] = dark;
      if (i < 8) matrix[8][size - i - 1] = dark; else if (i < 9) matrix[8][15 - i] = dark; else matrix[8][15 - i - 1] = dark;
    }
    matrix[size - 8][8] = true;
  }
  function placeVersion(matrix, version) {
    if (version < 7) return;
    var value = versionBits(version), size = matrix.length;
    for (var i = 0; i < 18; i += 1) {
      var dark = !!((value >>> i) & 1);
      matrix[Math.floor(i / 3)][size - 11 + (i % 3)] = dark;
      matrix[size - 11 + (i % 3)][Math.floor(i / 3)] = dark;
    }
  }
  function penalty(matrix) {
    var size = matrix.length, total = 0, row, col, run, color, dark = 0;
    for (row = 0; row < size; row += 1) for (col = 0; col < size; col += 1) {
      dark += matrix[row][col] ? 1 : 0;
      if (row && col && matrix[row][col] === matrix[row - 1][col] && matrix[row][col] === matrix[row][col - 1] && matrix[row][col] === matrix[row - 1][col - 1]) total += 3;
    }
    for (var axis = 0; axis < 2; axis += 1) for (row = 0; row < size; row += 1) { run = 0; color = null; for (col = 0; col < size; col += 1) { var next = axis ? matrix[col][row] : matrix[row][col]; if (next === color) run += 1; else { if (run >= 5) total += run - 2; color = next; run = 1; } } if (run >= 5) total += run - 2; }
    // rule 3 of the standard: a finder-like run (dark 1, light 1, dark 3, light 1, dark 1) with four light modules on either side costs 40 each; without it the encoder could pick a mask whose data looks like a finder pattern and real scanners then fail to find the symbol
    var PAT_A = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], PAT_B = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];
    for (var ax = 0; ax < 2; ax += 1) for (row = 0; row < size; row += 1) for (col = 0; col + 11 <= size; col += 1) {
      var hitA = true, hitB = true;
      for (var q = 0; q < 11; q += 1) { var cell = ax ? matrix[col + q][row] : matrix[row][col + q]; hitA = hitA && (cell ? 1 : 0) === PAT_A[q]; hitB = hitB && (cell ? 1 : 0) === PAT_B[q]; }
      if (hitA) total += 40;
      if (hitB) total += 40;
    }
    return total + Math.floor(Math.abs(dark * 100 / (size * size) - 50) / 5) * 10;
  }
  function encode(text, options) {
    var coded = codewords(text, options), size = 17 + coded.version * 4, best = null, bestScore = Infinity, level = LEVELS[coded.level];
    for (var mask = 0; mask < 8; mask += 1) { var matrix = makeMatrix(size); reserved(matrix, coded.version); placeData(matrix, coded.words, mask); placeFormat(matrix, mask, level); placeVersion(matrix, coded.version); var score = penalty(matrix); if (score < bestScore) { best = matrix; bestScore = score; } }
    return best;
  }
  function draw(canvas, text, options) {
    var matrix;
    try { matrix = encode(text, options); } catch (error) { if (error instanceof RangeError) return false; throw error; }
    var margin = options && options.margin !== undefined ? options.margin : 2, n = matrix.length + margin * 2, size = canvas.width >= 64 ? canvas.width : 240, cell = Math.floor(size / n), actual = cell * n, ctx = canvas.getContext('2d');
    canvas.width = actual; canvas.height = actual; ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, actual, actual); ctx.fillStyle = '#120A22';
    matrix.forEach(function (row, y) { row.forEach(function (dark, x) { if (dark) ctx.fillRect((x + margin) * cell, (y + margin) * cell, cell, cell); }); });
    return matrix;
  }
  return { encode: encode, draw: draw, codewords: codewords, capacity: function (version, level) { var chosen = levelFor(level); if (version < 1 || version > chosen.table.maxVersion) return 0; return payloadCapacity(version, chosen.table); } };
});
