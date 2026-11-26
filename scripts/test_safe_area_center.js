#!/usr/bin/env node
'use strict';
// Owner 2026-11-24 (option 1, symmetric): on a landscape phone the screen's safe area (camera hole) was only kept clear on ONE side, so the stage was left-aligned and a strip of background showed on the other side
// (real phone: safe-area-inset-right 36 px, stage 764 px wide at left 0, right gap 39 px against 3 px on the left). Now the same inset is kept clear on both sides and the stage is centred.
// 2026-11-26 (owner, MOBILE-RATIO-1): the stage is locked to 16:9, and later the same day drawn as one scaled picture filling left and right (up to 2.4 : 1), so the no-inset numbers below were re-pinned on purpose.
// A real Chrome (DevTools Protocol, Emulation.setSafeAreaInsetsOverride) loads the page, starts a match and measures the stage. The cases WITHOUT an inset are pinned to the numbers measured before the change (they must not move).
// Needs a local socket and Chrome: not for the Claude sandbox.
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), os = require('os'), path = require('path');
const ROOT = path.join(__dirname, '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_safe_area_center: no Chrome found'); process.exit(2); }
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
// [viewport w, h, insets {top,right,bottom,left}, expected canvas rect or null (null = only check that the two side gaps are equal)]
const CASES = [
  { name: 'no inset 800x360 (one picture)', w: 800, h: 360, ins: { top: 0, right: 0, bottom: 0, left: 0 }, canvas: [2, 1, 797, 357] },
  { name: 'no inset 923x415 (one picture)', w: 923, h: 415, ins: { top: 0, right: 0, bottom: 0, left: 0 }, canvas: [2, 2, 920, 412] },
  { name: 'no inset 873x392 (one picture)', w: 873, h: 392, ins: { top: 0, right: 0, bottom: 0, left: 0 }, canvas: [2, 2, 870, 389] },
  { name: 'no inset 720x266 (one picture)', w: 720, h: 266, ins: { top: 0, right: 0, bottom: 0, left: 0 }, canvas: [42, 1, 636, 264] },
  { name: 'camera hole on the right, 800x360, inset 36 (the owner\'s phone)', w: 800, h: 360, ins: { top: 0, right: 36, bottom: 0, left: 0 }, canvas: null },
  { name: 'camera hole on the left, 800x360, inset 36', w: 800, h: 360, ins: { top: 0, right: 0, bottom: 0, left: 36 }, canvas: null },
  { name: 'both sides 24, 873x392', w: 873, h: 392, ins: { top: 0, right: 24, bottom: 0, left: 24 }, canvas: null },
];
(async () => {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' }); res.end(d); } }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, dbg = 9600 + Math.floor(Math.random() * 300);
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-safe-')), '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let failed = false, supported = true;
  try {
    let tabs; for (let i = 0; i < 60; i++) { try { tabs = await (await fetch('http://127.0.0.1:' + dbg + '/json')).json(); if (tabs.length) break; } catch (_) { /* starting */ } await sleep(200); }
    const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async x => (await send('Runtime.evaluate', { expression: x, returnByValue: true })).result.result.value;
    for (const c of CASES) {
      await send('Emulation.setDeviceMetricsOverride', { width: c.w, height: c.h, deviceScaleFactor: 3, mobile: false });
      await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 }); await send('Emulation.setEmulatedMedia', { features: [{ name: 'pointer', value: 'coarse' }, { name: 'hover', value: 'none' }] });   // these are phone cases
      const so = await send('Emulation.setSafeAreaInsetsOverride', { insets: c.ins });
      if (so.error) { supported = false; console.error('FAIL - ' + c.name + ': this Chrome cannot override the safe area (' + so.error.message + ')'); failed = true; continue; }
      await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/index.html?team=3' }); await sleep(3000);
      await ev("(() => { const b = document.getElementById('start-go'); if (b) b.click(); return 1; })()"); await sleep(2500);
      await ev("(() => { const b = document.getElementById('coin-call-heads'); if (b) b.click(); return 1; })()"); await sleep(6500);
      const m = JSON.parse(await ev("JSON.stringify((() => { const q = r => [r.left, r.top, r.width, r.height].map(Math.round); const cv = document.getElementById('gameCanvas').getBoundingClientRect(), g = document.getElementById('game-container').getBoundingClientRect(); const p = document.createElement('div'); p.style.cssText = 'position:fixed;left:0;top:0;visibility:hidden;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)'; document.body.appendChild(p); const cs = getComputedStyle(p), ins = [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft]; p.remove(); return { vp: [innerWidth, innerHeight], canvas: q(cv), container: q(g), gapLeft: Math.round(cv.left), gapRight: Math.round(innerWidth - cv.right), insets: ins }; })())"));
      try {
        if (c.ins.right || c.ins.left) { if (m.insets[1] !== c.ins.right + 'px' || m.insets[3] !== c.ins.left + 'px') throw new Error('the page did not see the inset (it saw ' + m.insets.join(' ') + ')'); }
        if (c.canvas) { if (JSON.stringify(m.canvas) !== JSON.stringify(c.canvas)) throw new Error('canvas ' + JSON.stringify(m.canvas) + ' moved from ' + JSON.stringify(c.canvas)); }
        else {
          if (Math.abs(m.gapLeft - m.gapRight) > 1) throw new Error('stage not centred: left gap ' + m.gapLeft + ' px, right gap ' + m.gapRight + ' px');
          const need = Math.max(c.ins.left, c.ins.right); if (m.gapLeft < need || m.gapRight < need) throw new Error('the safe area is not kept clear on both sides: gaps ' + m.gapLeft + ' and ' + m.gapRight + ' px, inset ' + need + ' px');
          if (m.canvas[3] < c.h - 12) throw new Error('stage lost height: ' + m.canvas[3] + ' of ' + c.h);
        }
        console.log('ok   - ' + c.name + ': canvas ' + JSON.stringify(m.canvas) + ' gaps ' + m.gapLeft + '/' + m.gapRight);
      } catch (e) { failed = true; console.error('FAIL - ' + c.name + ': ' + e.message); }
    }
    ws.close();
  } finally { chrome.kill(); server.close(); }
  console.log('test_safe_area_center: ' + (failed ? 'FAILED' : CASES.length + ' cases passed'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_safe_area_center: ' + (e && e.stack || e)); process.exit(1); });
