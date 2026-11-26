#!/usr/bin/env node
'use strict';
// MOBILE-RATIO-1 (owner 2026-11-26: "every device shows the same thing; fill left and right"; foldables excepted). Landscape screens show ONE picture of a fixed design size, scaled by CSS; it must not depend on the
// meta viewport (Android full screen ignores it). Runs the REAL pictureFit of index.html in a vm.
const assert = require('assert'), fs = require('fs'), path = require('path'), vm = require('vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const from = html.indexOf('const PIC_H'), to = html.indexOf('const mutedRules');
assert.ok(from > 0 && to > from, 'the picture block is in index.html');
const context = vm.createContext({});
vm.runInContext(html.slice(from, to), context);
const call = (...a) => JSON.parse(vm.runInContext('JSON.stringify(pictureFit(' + a.join(',') + '))', context));
let ok = 0, failed = 0;
function check(name, fn) { try { fn(); ok++; console.log('ok   - ' + name); } catch (e) { failed++; console.log('FAIL - ' + name + '\n       ' + e.message); } }

check('LOCKED: the picture is 744 px high with a 1323 px (16:9) core on every landscape screen', () => {
  for (const [w, h, coarse] of [[667, 375, true], [720, 266, true], [800, 360, true], [844, 390, true], [932, 430, true], [1024, 768, true], [1366, 1024, true], [1366, 768, false], [1920, 1080, false], [2560, 1080, false], [600, 380, true]]) {
    const r = call(w, h, coarse), m = coarse ? 0 : 24;
    assert.strictEqual(r.h, 744, w + 'x' + h);
    assert.ok(r.w >= 1323 && r.w <= Math.round(744 * 2.4), w + 'x' + h + ' width ' + r.w);
    assert.ok(r.w * r.scale <= w - m + 0.5 && r.h * r.scale <= h - m + 0.5, w + 'x' + h + ' the whole picture is on the screen');
  }
});
check('a screen wider than 16:9 is filled left and right, up to 2.4 : 1', () => {
  const r = call(800, 360, true);
  assert.ok(Math.abs(r.w * r.scale - 800) < 1 && Math.abs(r.h * r.scale - 360) < 1, JSON.stringify(r));
  assert.strictEqual(call(1200, 360, true).w, Math.round(744 * 2.4));
});
check('portrait keeps the responsive layout', () => { assert.strictEqual(call(390, 844, true), null); assert.strictEqual(call(0, 0, true), null); });
check('LOCKED: no meta viewport rewriting; folding screens keep the responsive layout', () => {
  assert.ok(!/meta\.setAttribute\("content"/.test(html));
  assert.match(html, /const pic = applyPicture\(width, height, !!seg\);/);
});
check('the stage is scaled as one picture, the dock stays inside the core, drag distance follows the picture', () => {
  assert.match(html, /html\.one-picture #game-container \{ position:fixed !important;[^\n]*scale\(var\(--pic-scale\)\) !important/);
  assert.match(html, /html\.one-picture #bottom-dock \{ width:calc\(min\(84cqw, 1111px\)/);
  assert.match(html, /slingFrom\(\(e\.clientX - sling\.ax\) \/ pictureScale, \(e\.clientY - sling\.ay\) \/ pictureScale\)/);
});
check('LOCKED: the lobby is one 1024 x 576 picture', () => {
  assert.match(html, /#lobby \{ position:fixed; left:50%; top:50%; width:1024px; height:576px; transform:translate\(-50%,-50%\) scale\(var\(--lobby-fit,1\)\)/);
});
check('a lobby without a room code says why (connecting or unreachable)', () => {
  assert.match(html, /if \(!v\.code\) \{ el\.textContent = T\(lobbyNet === "reconnecting" \|\| lobbyNet === "closed" \? "room\.unreachable" : "room\.connecting"\)/);
});
check('nothing behind the lobby can be tapped, and a new attempt starts as connecting', () => {
  assert.match(html, /html\.in-lobby #start-screen, html\.in-lobby #top-controls \{ visibility:hidden !important; \}/);
  assert.match(html, /relaySeats = \[\]; lobbyNet = "connecting";/);
});
check('a computer seat claims the landing its own throw really has', () => {
  assert.match(html, /const land = relayFlightLanding\(start\.x, start\.y, power, angle, dirX, prof\.weapon === "proj_soundwave"\);/);
  assert.ok(!/claimed_landing: \{ x: tgt \?/.test(html));
});
check('the keyboard does not shrink the picture while typing', () => {
  assert.match(html, /classList\.toggle\("typing", typing\);\n\s+if \(typing && window\.innerWidth === lastFitWidth\) return;/);
  assert.match(html, /html\.typing #name-dialog, html\.typing #join-code-dialog \{ align-items:flex-start; \}/);
});
check('full screen is asked after the tapped button ran; copy, share and links keep their tap', () => {
  assert.match(html, /textarea, #name-dialog, #join-code-dialog, a\[href\], \[id\*=copy\], \[id\*=share\]"\)\)\) setTimeout\(enterPhoneFullscreen, 0\);/);
});
check('a computer seat that stays unlocked keeps trying, at most ten times', () => {
  assert.match(html, /const confirmLock = \(\) => \{/);
  assert.match(html, /\(filler\.relocks = \(filler\.relocks \|\| 0\) \+ 1\) > 10\) return;\n\s+readyNow\(\);/);
});
console.log('test_phone_viewport: ' + ok + ' ok, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
