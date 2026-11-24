'use strict';
// Character size is locked (owner 2026-11-16). If this fails you changed a size or a foot/offset table: look at every hero on screen, then update shared/size_frozen.json on purpose.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const pin = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'size_frozen.json'), 'utf8'));
let passed = 0, total = 0;
function check(name, fn) { total++; try { fn(); passed++; console.log('ok   - ' + name); } catch (e) { console.error('FAIL - ' + name + '\n       ' + e.message); process.exitCode = 1; } }
function literal(name) {
  const i = html.indexOf('const ' + name + ' =');
  const j = html.indexOf('};', i) + 2;
  return html.slice(i, j).replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\s+/g, '');
}
check('both units are drawn in a 220 x 220 box on the ground line 860', () => {
  for (const name of ['player', 'ai']) {
    let i = html.indexOf('const ' + name + ' = {'); if (i < 0) i = html.indexOf('let ' + name + ' = {');   // team battle re-points player / ai at the active unit, so they are let
    const block = html.slice(i, html.indexOf('};', i));
    assert.match(block, new RegExp('w: ' + pin.unit_w + ','), name + ' w');
    assert.match(block, new RegExp('h: ' + pin.unit_h + ','), name + ' h');
  }
  assert.match(html, new RegExp('const GROUND_Y = ' + pin.ground_y + ';'));
});
check('the foot and offset tables of the art are unchanged', () => {
  for (const [name, hash] of Object.entries(pin.offset_table_hashes)) {
    assert.strictEqual(crypto.createHash('sha256').update(literal(name)).digest('hex'), hash, name);
  }
});
check('the HP bar above a unit is 150 x 13', () => {
  // the bar is still 150 x 13 for one unit per team: the width lives in hpBarWidthFor (never wider than 85 percent of the gap to a living teammate in a team match)
  assert.match(html, /function hpBarWidthFor\(u\) \{\n\s+const full = 150 \* uiScale\(\);\n\s+if \(TEAM_N < 2\) return full;/);
  assert.match(html, /const hpBarWidth = hpBarWidthFor\(u\), hpBarHeight = 13 \* uiScale\(\), hpBarX = -hpBarWidth \/ 2, hpBarY = -218;/);
});
check('the aspect ratio is locked in the draw code and every hero picture has an allowed ratio', () => {
  assert.match(html, /const dw = u\.w \* aspect;/);
  const sizeOf = f => { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
  const bad = [];
  for (const dir of ['assets/poses', 'assets/units']) for (const name of fs.readdirSync(path.join(root, dir))) {
    if (!name.endsWith('.png')) continue;
    const rel = dir + '/' + name; if (pin.unused_crops_exempt.includes(rel)) continue;
    const [w, h] = sizeOf(path.join(root, rel));
    if (!pin.allowed_picture_sizes.some(([a, b]) => a === w && b === h)) bad.push(rel + ' ' + w + 'x' + h);
  }
  assert.deepStrictEqual(bad, []);
});
check('the opponent item slot never shows the item (a question mark only)', () => {
  assert.match(html, /e2\.textContent = ai_it \? \(\(seats\.right === "human" && activeSide\(\) === "right"\) \? ai_it\.icon : "\?"\) : "";/);
});
console.log('test_size_frozen: ' + passed + '/' + total + ' checks passed');
