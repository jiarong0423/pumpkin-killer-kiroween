'use strict';
/* The nun's thrown cross is a 512 px picture drawn at about 70 px. Drawn in one step the browser aliases it ("糊掉").
 * Static check on index.html: the picture goes through a pre-scaled copy made by stepwise halving (every step at most 2x). */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

const helper = html.match(/function crossSharp\s*\(([^)]*)\)\s*\{([\s\S]*?)\n    \}\n/);
assert.ok(helper, 'index.html must define function crossSharp(pic)');
const body = helper[2];
assert.ok(/while\s*\(/.test(body) && /\/\s*2|>>\s*1|\*\s*0\.5/.test(body), 'crossSharp must halve stepwise in a loop');
assert.ok(/imageSmoothingQuality\s*=\s*["']high["']/.test(body), 'each halving step uses high quality smoothing');
assert.ok(/createElement\(["']canvas["']\)/.test(body), 'crossSharp makes an offscreen canvas');
assert.ok(/_cache|cache/i.test(body) || /crossSharpCache/.test(html), 'the scaled copy is made once and reused');

const branch = html.match(/else if \(p\.weapon === "proj_cross"\) \{[\s\S]*?const crossPic = images\.fx_cross_silver;[^\n]*\n[^\n]*\n/);
assert.ok(branch, 'proj_cross branch found');
assert.ok(/crossSharp\(crossPic\)/.test(branch[0]), 'the cross is drawn from crossSharp(crossPic), not the 512 px original');
assert.ok(!/ctx\.drawImage\(crossPic,/.test(branch[0]), 'no direct drawImage(crossPic, ...) any more');
console.log('test_cross_sprite_sharp: OK');
