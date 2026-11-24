'use strict';
// Every inline <script> of index.html must parse. (2026-11-16: a comment placed in the middle of a one-line block swallowed two closing braces and the whole page stopped working while every other test stayed green.)
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert.ok(scripts.length >= 1, 'no inline script found');
scripts.forEach((src, i) => { try { new Function(src); } catch (e) { assert.fail('inline script ' + i + ' does not parse: ' + e.message); } });
for (const file of fs.readdirSync(path.join(__dirname, '..', 'js')).filter(f => f.endsWith('.js'))) {
  const src = fs.readFileSync(path.join(__dirname, '..', 'js', file), 'utf8');
  try { new Function(src); } catch (e) { assert.fail('js/' + file + ' does not parse: ' + e.message); }
}
console.log('test_page_parses: ' + scripts.length + ' inline scripts and every js/*.js parse');
