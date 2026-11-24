#!/usr/bin/env node
'use strict';

var fs = require('fs');
var path = require('path');
var QrCode = require('../js/qr_code.js');

function usage() {
  console.error('Usage: node scripts/make_site_qr.js <https-url> [--out path]');
}

function parseArguments(argv) {
  var values = { url: null, out: path.join('assets', 'ui', 'site_qr.svg') };
  for (var index = 0; index < argv.length; index += 1) {
    if (argv[index] === '--out') {
      index += 1;
      if (!argv[index]) throw new Error('--out requires a path');
      values.out = argv[index];
    } else if (!values.url) values.url = argv[index];
    else throw new Error('only one URL is allowed');
  }
  if (!values.url) throw new Error('a public site URL is required');
  var parsed = new URL(values.url);
  if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') throw new Error('site URL must use http or https');
  return values;
}

function encodeSiteUrl(url) {
  try {
    return { level: 'M', matrix: QrCode.encode(url, 'M') };
  } catch (error) {
    if (!(error instanceof RangeError)) throw error;
    return { level: 'L', matrix: QrCode.encode(url, 'L') };
  }
}

function svgFor(matrix) {
  var quietZone = 4;
  var side = matrix.length + quietZone * 2;
  var pathData = [];
  matrix.forEach(function (row, y) {
    row.forEach(function (dark, x) {
      if (dark) pathData.push('M' + (x + quietZone) + ' ' + (y + quietZone) + 'h1v1h-1z');
    });
  });
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + side + ' ' + side + '" role="img" aria-label="Site QR code">',
    '<rect width="100%" height="100%" fill="#fff"/>',
    '<path fill="#000" d="' + pathData.join('') + '"/>',
    '</svg>',
    ''
  ].join('\n');
}

function main() {
  var values;
  try { values = parseArguments(process.argv.slice(2)); } catch (error) { usage(); console.error(error.message); process.exitCode = 1; return; }
  var encoded;
  try { encoded = encodeSiteUrl(values.url); } catch (error) { console.error('QR generation failed: ' + error.message); process.exitCode = 1; return; }
  fs.mkdirSync(path.dirname(values.out), { recursive: true });
  fs.writeFileSync(values.out, svgFor(encoded.matrix), 'utf8');
  console.log('site QR: version ' + ((encoded.matrix.length - 17) / 4) + ', level ' + encoded.level + ', output ' + values.out);
}

if (require.main === module) main();
module.exports = { encodeSiteUrl: encodeSiteUrl, svgFor: svgFor, parseArguments: parseArguments };
