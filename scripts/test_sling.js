#!/usr/bin/env node
'use strict';
// Direct arrow aim (owner 2026-11-18): on a touch screen press anywhere on the field, drag the arrow where you want it, let go. The throw goes the same way as the drag; the power is the hold time.
// Runs the REAL slingFrom of index.html in the Node vm and checks the wiring in the source. A mutant with the wrong sign (the throw goes WITH the pull) must fail.
const assert = require('assert');
const vm = require('vm');
const fs = require('fs');
const path = require('path');
const { loadPage } = require('./page_harness');
const from = (P, dx, dy) => JSON.parse(vm.runInContext('JSON.stringify(slingFrom(' + dx + ', ' + dy + '))', P.context));
const P = loadPage({ team: 1, seed: 7171 });
let r = from(P, 60, -60);
assert.ok(Math.abs(r.angle - 45) < 1e-9, 'drag up-right 60/60 throws at 45 degrees: ' + r.angle);
assert.strictEqual(r.power, undefined, 'the pull no longer sets the power (hold time does)');
r = from(P, 100, 0); assert.ok(Math.abs(r.angle) < 1e-9, 'a flat drag to the right is 0 degrees (the game then clamps to its lowest angle)');
r = from(P, 30, -90); assert.ok(r.angle > 70 && r.angle < 72, 'a steep drag throws steeply: ' + r.angle);
assert.ok(Math.abs(from(P, 90, 0).pull - 90) < 1e-9 && Math.abs(from(P, 40, 0).pull - 40) < 1e-9, 'the pull length is still reported (the dead zone uses it)');
r = from(P, -50, -20); assert.strictEqual(r.angle, null, 'dragging to the LEFT (the wrong way) gives no angle (JSON NaN)');
r = from(P, 40, 30); assert.strictEqual(r.angle, null, 'dragging DOWN (the throw would go into the ground) gives no angle');
r = from(P, 0, -80); assert.ok(r.angle > 85, 'a straight drag up throws almost straight up: ' + r.angle);
console.log('ok   - slingFrom: angle = direction of the drag (the arrow follows the finger); no power in it (the power is the hold time)');
const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
assert.ok(/if \(e\.pointerType !== "mouse"\) slingStart\(e\); else \{ aimFromPointer\(e\); startCharging\(\); \}/.test(src), 'touch uses the slingshot, the mouse keeps hover aim');
assert.ok(/\/\/ Hold-to-Charge Ping-Pong Power Meter[^\n]*\n      if \(isCharging\) \{/.test(src), 'the time-based power sweep runs for touch too (owner 2026-11-18: power from the hold time)');
assert.ok(!/chargePower = r\.power/.test(src), 'slingMove does not set the power from the pull');
assert.ok(/performance\.now\(\) - chargeStart < 250 \|\| chargePower < 12/.test(src) && !/\(!sling && performance\.now\(\) - chargeStart/.test(src), 'one cancel rule for mouse and touch: a tap (< 250 ms) or a release near zero power cancels');
assert.ok(/if \(sling && e && e\.type === "pointercancel"\)/.test(src), 'a cancelled touch never throws');
assert.ok(/toast\.slingCancel/.test(src) && /slingCancel/.test(fs.readFileSync(path.join(__dirname, '..', 'assets', 'i18n', 'en.json'), 'utf8')) && /slingCancel/.test(fs.readFileSync(path.join(__dirname, '..', 'assets', 'i18n', 'zh-TW.json'), 'utf8')), 'the cancel message exists in both languages');
console.log('ok   - touch uses the sling, the mouse path is untouched, release and cancel rules are wired, texts exist in both languages');
let caught = null;
try { const M = loadPage({ team: 1, seed: 7172, mutate: [['Math.atan2(-dy, Math.max(dx, 1))', 'Math.atan2(dy, Math.max(-dx, 1))']] }); const m = from(M, 60, -60); assert.ok(Math.abs(m.angle - 45) < 1e-9, 'mutant angle'); } catch (e) { caught = e; }
assert.ok(caught instanceof assert.AssertionError, 'a mutant where the throw goes AGAINST the drag must fail: ' + caught);
console.log('ok   - [negative: a throw against the drag is caught]');
console.log('test_sling: 3 ok, 0 failed');
