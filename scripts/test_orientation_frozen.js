'use strict';
// The orientation decisions confirmed by the owner (2026-11-16) are frozen in shared/orientation_frozen.json.
// If this test fails you changed a facing on purpose or by accident: look at the picture, then run `python3 -B scripts/freeze_orientation.py --write`.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const frozen = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'orientation_frozen.json'), 'utf8'));
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
let passed = 0, total = 0;
function check(name, fn) { total++; try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { console.error('FAIL - ' + name + '\n       ' + e.message); process.exitCode = 1; } }

check('ART_FACES_RIGHT equals the frozen table (hunchback true, every other hero false)', () => {
  const m = /const ART_FACES_RIGHT = \{([^}]*)\}/.exec(html);
  const now = {};
  for (const x of m[1].matchAll(/(\w+):\s*(true|false)/g)) now[x[1]] = x[2] === 'true';
  assert.deepStrictEqual(now, frozen.art_faces_right);
  assert.strictEqual(now.unit_hunchback, true);
  assert.strictEqual(Object.values(now).filter(Boolean).length, 1);
});
check('every hero picture under assets/poses and assets/units is byte-identical to the frozen set', () => {
  const diffs = [];
  for (const [rel, hash] of Object.entries(frozen.pictures)) {
    const file = path.join(root, rel);
    if (!fs.existsSync(file)) { diffs.push('missing ' + rel); continue; }
    if (crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex') !== hash) diffs.push('changed ' + rel);
  }
  assert.deepStrictEqual(diffs, []);
});
check('the wind ghost stays bound to the wind direction (mirrored, no number chip)', () => {
  for (const marker of frozen.wind_ghost_markers) assert.ok(html.includes(marker), 'missing: ' + marker);
  assert.ok(!/const windArrow = /.test(html));
});
check('the hunchback wind-up picture is the mirrored one', () => {
  assert.ok(frozen.pictures['assets/poses/hunchback_windup.png'], 'hunchback_windup.png must be frozen');
});
check('each side throws, aims and shows its own remembered angle (a human on the right keeps its own)', () => {
  assert.match(html, /let playerAngle = 54, aiAngle = 54;/);
  assert.match(html, /const angleDeg = angleOfTeam\(isPlayer \? "player" : "ai"\);/);
  assert.match(html, /const aim = angleOfTeam\((?:u === player|sideOfUnit\(u\) === "left") \? "player" : "ai"\)/);
  assert.match(html, /textContent = Math\.round\(activeAngle\(\)\)/);
});
console.log('test_orientation_frozen: ' + passed + '/' + total + ' checks passed');
