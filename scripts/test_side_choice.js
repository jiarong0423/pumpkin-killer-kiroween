'use strict';
// The built-in opponent is always on the right; relay rooms retain two-human seats.
const assert = require('assert');
const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const Determinism = require(path.join(root, 'js', 'determinism.js'));
const golden = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'determinism_golden.json'), 'utf8'));
const page = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const en = JSON.parse(fs.readFileSync(path.join(root, 'assets', 'i18n', 'en.json'), 'utf8'));
const zh = JSON.parse(fs.readFileSync(path.join(root, 'assets', 'i18n', 'zh-TW.json'), 'utf8'));

// The relay can retain its independent seeded side draw without exposing it to a solo match.
const vectors = golden.vectors.sideDraw;
assert.ok(Array.isArray(vectors) && vectors.length >= 40, 'sideDraw needs at least 40 golden vectors');
for (const vector of vectors) {
  assert.strictEqual(Determinism.sideDraw(vector.input.seed), vector.output,
    'sideDraw golden vector ' + JSON.stringify(vector.input));
}
assert.match(fs.readFileSync(path.join(root, 'js', 'determinism.js'), 'utf8'),
  /sideDraw:\s*0x[0-9a-f]+/i, 'sideDraw needs its own hash domain');
assert.match(fs.readFileSync(path.join(root, 'scripts', 'determinism_py.py'), 'utf8'),
  /"sideDraw":\s*0x[0-9A-F]+/, 'Python needs the same named hash domain');

for (const pattern of [/id="side-picker"/, /data-side-choice/, /chooseHumanSide/, /applyHumanSideChoice/, /humanSideChoice/, /sideChoice\./, /start\.pickSide/]) {
  assert.doesNotMatch(page, pattern, 'solo side-choice UI or code remains: ' + pattern);
}
for (const key of ['start.pickSide', 'sideChoice.left', 'sideChoice.right', 'sideChoice.computer']) {
  assert.ok(!(key in en), 'obsolete English key remains: ' + key);
  assert.ok(!(key in zh), 'obsolete Traditional Chinese key remains: ' + key);
}

assert.match(page, /let seats = \{ left: "human", right: "ai" \};/,
  'the initial solo seats must put the human left and the built-in AI right');
assert.match(page, /if \(!relayAddress\) \{[\s\S]*?seats = \{ left: "human", right: "ai", level: levels \};[\s\S]*?host\.hidden = true;/,
  'the solo start screen must restore left-human/right-AI seats and hide seat controls');
assert.match(page, /showCoinToss\(Determinism\.coinToss\(matchSeed\)\)/,
  'the independent opening coin toss must remain unchanged');

const seatOptionsSource = page.match(/function seatOptionsValid\(left, right\) \{[^\n]*\}\n    function seatOptionAllowed\(left, right\) \{[^\n]*\}/);
assert.ok(seatOptionsSource, 'seat option guard is missing');
const seatOptionAllowed = new Function(seatOptionsSource[0] + '; return seatOptionAllowed;')();
assert.strictEqual(seatOptionAllowed('human', 'ai'), true, 'the solo left human/right AI pair must be valid');
assert.strictEqual(seatOptionAllowed('ai', 'human'), false,
  'seat options must never offer a right-side human against the built-in AI');
assert.strictEqual(seatOptionAllowed('human', 'human'), true,
  'a relay room must retain a valid two-human pair');
assert.match(page, /\["left", "right"\]\.forEach\(side => \{[\s\S]*?"seat\.left"[\s\S]*?"seat\.right"/,
  'relay seat rows must continue to expose both left and right sides');

const orientationOutput = childProcess.execFileSync(process.execPath,
  [path.join(root, 'scripts', 'test_orientation_frozen.js')], { encoding: 'utf8' });
assert.match(orientationOutput, /5\/5 checks passed/);

console.log('test_side_choice.js: ' + vectors.length + ' sideDraw golden vectors passed');
console.log('test_side_choice.js: solo left-human/right-AI and relay two-human seats passed');
console.log('test_side_choice.js: no side-choice UI and frozen orientation passed');
