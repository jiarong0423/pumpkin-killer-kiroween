#!/usr/bin/env node
'use strict';
var assert = require('assert');
var crypto = require('crypto');
var QrCode = require('../js/qr_code.js');
var SiteQr = require('./make_site_qr.js');

var hello = QrCode.codewords('HELLO WORLD');
assert.strictEqual(hello.version, 1);
assert.strictEqual(hello.level, 'L');
assert.strictEqual(hello.words.length, 26);
assert.deepStrictEqual(hello.words, [64, 180, 132, 84, 196, 196, 242, 5, 116, 245, 36, 196, 64, 236, 17, 236, 17, 236, 17, 200, 70, 38, 65, 232, 248, 246]);
var matrix = QrCode.encode('HELLO WORLD');
assert.strictEqual(matrix.length, 21);
assert.strictEqual(matrix[0].length, 21);
assert.strictEqual(matrix[0][0], true);
assert.strictEqual(matrix[6][8], true);
// re-pinned after the mask choice gained rule 3 (finder-like patterns); the matrix was decoded back to HELLO WORLD with OpenCV
assert.strictEqual(crypto.createHash('sha256').update(JSON.stringify(matrix)).digest('hex'), '778c7c4bf005645e70e890ec063b7fcecb05f80e076441fab0c32ec3708e52d0');

var expectedL = [17, 32, 53, 78, 106];
var expectedM = [14, 26, 42, 62, 84, 106];
expectedL.forEach(function (capacity, index) {
  var version = index + 1;
  assert.strictEqual(QrCode.capacity(version, 'L'), capacity);
  assert.strictEqual(QrCode.codewords('x'.repeat(capacity), 'L').version, version);
  if (version < 5) assert.strictEqual(QrCode.codewords('x'.repeat(capacity + 1), 'L').version, version + 1);
  else assert.throws(function () { QrCode.codewords('x'.repeat(capacity + 1), 'L'); }, /capacity/);
});
expectedM.forEach(function (capacity, index) {
  var version = index + 1;
  assert.strictEqual(QrCode.capacity(version, 'M'), capacity);
  assert.strictEqual(QrCode.codewords('x'.repeat(capacity), 'M').version, version);
  if (version < 6) assert.strictEqual(QrCode.codewords('x'.repeat(capacity + 1), 'M').version, version + 1);
  else assert.throws(function () { QrCode.codewords('x'.repeat(capacity + 1), 'M'); }, /capacity/);
});
assert.strictEqual(QrCode.capacity(7, 'M'), 0);
assert.strictEqual(QrCode.capacity(6, 'L'), 0);
assert.throws(function () { QrCode.codewords('x'.repeat(107), 'M'); }, /capacity/);   // M stops at version 6 (106 bytes)
assert.throws(function () { QrCode.encode('x'.repeat(107), 'L'); }, /capacity/);   // L stops at version 5 (106 bytes)

var typicalJoinLink = 'https://' + 'a'.repeat(30) + '/?room=ABC234';
assert.strictEqual(Buffer.byteLength(typicalJoinLink, 'utf8'), 51);
assert.strictEqual(QrCode.codewords(typicalJoinLink, 'M').version, 4); // Version 3-M holds 42 byte-mode bytes, not this 51-byte URL.
assert.strictEqual(QrCode.codewords(typicalJoinLink, 'L').version, 3); // Version 3-L holds 53 byte-mode bytes.

var fakeCanvas = {
  width: 240,
  getContext: function () { return { fillStyle: '', fillRect: function () {} }; }
};
assert.strictEqual(QrCode.draw(fakeCanvas, 'x'.repeat(272)), false);
assert.ok(Array.isArray(QrCode.draw(fakeCanvas, 'HELLO WORLD')));
// A canvas that still has the 1 px placeholder width of the HTML (room-qr and agent-room-qr start as width="1") drew nothing before 2026-11-18 (red-team review R1, B P1-1): it now gets a sensible size.
var tinyCanvas = { width: 1, height: 1, getContext: function () { return { fillStyle: '', fillRect: function () {} }; } };
assert.ok(Array.isArray(QrCode.draw(tinyCanvas, 'HELLO WORLD')) && tinyCanvas.width >= 100, 'a 1 px canvas is drawn at a real size: ' + tinyCanvas.width);

var siteQr = SiteQr.encodeSiteUrl('https://' + 'a'.repeat(30) + '/?room=ABC234');
assert.strictEqual(siteQr.level, 'M');
assert.strictEqual(siteQr.matrix.length, 33);
var svg = SiteQr.svgFor(siteQr.matrix);
assert.match(svg, /viewBox="0 0 41 41"/);
assert.match(svg, /<rect width="100%" height="100%" fill="#fff"\/>/);
assert.throws(function () { SiteQr.parseArguments(['ftp://example.test']); }, /http or https/);
console.log('qr code capacity L v1-v5 and M v1-v6: ok');
