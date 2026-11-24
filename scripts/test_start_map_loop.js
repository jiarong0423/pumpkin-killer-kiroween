#!/usr/bin/env node
'use strict';
// Start screen map list (owner 2026-11-18): looping pages 1234 1234 (a copy of the last card before the first, a copy of the first after the last), a mouse can change the map (icons, click, wheel),
// the picture covers the whole card (no brown fill), no hover lift, semi-transparent icons, one selectScene path. Source pins, because the browser pane here does not run animation frames.
const assert = require('assert'), fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
let n = 0; const ok = (name, c) => { assert.ok(c, name); n++; console.log('ok   - ' + name); };
ok('copies of the last and first card make the list loop', /insertBefore\(cloneOf\(realCards\[nS - 1\]\), realCards\[0\]\); sb\.appendChild\(cloneOf\(realCards\[0\]\)\)/.test(src));
ok('after a page turn onto a copy the list jumps onto the real card', /if \(raw < 0\) sb\.scrollLeft = pageLeft\(nS\); else if \(raw >= nS\) sb\.scrollLeft = pageLeft\(1\)/.test(src));
ok('a pending scroll settle cannot overwrite a click choice (navUntil)', /navUntil = performance\.now\(\)/.test(src) && /if \(performance\.now\(\) < navUntil\)/.test(src));
ok('icons, a click on the card and the wheel all go through selectScene', /b\.onclick = ev => \{ ev\.stopPropagation\(\); selectScene\(curIdx\(\) \+ d, true\)/.test(src) && /sb\.addEventListener\("click"/.test(src) && /sb\.addEventListener\("wheel"/.test(src));
ok('the map card has no inset and no card colour behind the picture', /#pick-scenes \.scene-card \.th \{ inset:0 !important/.test(src) && /#pick-scenes \.scene-card \{ border-radius:12px !important; background:transparent !important; \}/.test(src));
ok('the map card does not move up when pointed at', /#pick-scenes \.scene-card:hover \{ transform:none !important; \}/.test(src));
ok('the pages are exactly one card wide (border-box)', /#pick-scenes \.scene-card \{ box-sizing:border-box !important; \}/.test(src));
ok('the map icons are semi-transparent and keep a 44 px touch area', /background:rgba\(18,10,34,\.4\)/.test(src) && /\.scene-nav \{[^}]*width:44px; height:44px/.test(src));
ok('the seats panel is an overlay at every window size (outside the short-landscape media query)', /\n    #start-screen\.seats-open #friends-panel \{ display: block; position: fixed;/.test(src));
ok('the start-screen backdrop is never put back over a running match, and a hidden list does not settle', /if \(matchStarted\) return;   \/\/ never put the start-screen backdrop back/.test(src) && /if \(matchStarted \|\| sb\.clientWidth < 10\) return;/.test(src));
console.log('test_start_map_loop: ' + n + ' ok, 0 failed');
