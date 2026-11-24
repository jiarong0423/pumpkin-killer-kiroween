#!/usr/bin/env node
'use strict';
// Owner 2026-11-24: the choose-a-side screen of a private-room invite (link with choose=1) must fit every phone-sized view: the card inside the viewport, both side buttons big enough to tap and not overlapping, no sideways scroll.
// A real Chrome (DevTools Protocol) loads the page with a room code and choose=1 (no relay is reachable on purpose: nothing is sent before the choice) and measures the card. Needs a local socket and Chrome: not for the Claude sandbox.
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), os = require('os'), path = require('path');
const ROOT = path.join(__dirname, '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_safe_area_center: no Chrome found'); process.exit(2); }
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VIEWS = [[640, 300], [720, 266], [800, 360], [873, 392], [923, 415], [360, 662], [1440, 900]];
(async () => {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' }); res.end(d); } }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, dbg = 9900 + Math.floor(Math.random() * 90);
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-side-')), '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let failed = false;
  try {
    let tabs; for (let i = 0; i < 60; i++) { try { tabs = await (await fetch('http://127.0.0.1:' + dbg + '/json')).json(); if (tabs.length) break; } catch (_) { /* starting */ } await sleep(200); }
    const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async x => (await send('Runtime.evaluate', { expression: x, returnByValue: true })).result.result.value;
    for (const [w, h] of VIEWS) {
      await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
      await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/index.html?relay=ws://127.0.0.1:1&team=3&room=ABCDE&choose=1' }); await sleep(2800);
      const m = JSON.parse(await ev("JSON.stringify((() => { const q = e => { const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height }; }; const box = document.getElementById('side-chooser'), card = box.querySelector('.side-card'), sides = [...box.querySelectorAll('[data-side]')].map(q), claims = [...box.querySelectorAll('[data-claim]')].filter(b => b.offsetParent).map(q); return { shown: !box.hidden && getComputedStyle(box).display !== 'none', card: q(card), sides, claims, scrollW: document.scrollingElement.scrollWidth, vw: innerWidth, vh: innerHeight, joined: relayAutoJoined, text: card.innerText.slice(0, 60) }; })())"));
      try {
        const name = w + 'x' + h;
        if (!m.shown) throw new Error(name + ': the chooser is not shown');
        if (m.joined) throw new Error(name + ': the page joined before the choice');
        const c = m.card; if (c.l < -0.5 || c.t < -0.5 || c.r > m.vw + 0.5 || c.b > m.vh + 0.5) throw new Error(name + ': the card leaves the viewport ' + JSON.stringify(c) + ' in ' + m.vw + 'x' + m.vh);
        if (m.sides.length !== 2) throw new Error(name + ': two side buttons expected');
        for (const s of m.sides) if (s.w < 100 || s.h < 44) throw new Error(name + ': a side button is too small ' + Math.round(s.w) + 'x' + Math.round(s.h));
        const [a, b] = m.sides; if (a.r > b.l + 0.5 && a.b > b.t + 0.5 && a.t < b.b - 0.5) throw new Error(name + ': the side buttons overlap');
        for (const s of m.claims) if (s.h < 36) throw new Error(name + ': a claim button is too short ' + Math.round(s.h));
        if (m.scrollW > m.vw + 1) throw new Error(name + ': sideways scroll (' + m.scrollW + ' > ' + m.vw + ')');
        console.log('ok   - ' + name + ': card ' + Math.round(c.w) + 'x' + Math.round(c.h) + ' inside, side buttons ' + Math.round(a.w) + 'x' + Math.round(a.h));
      } catch (e) { failed = true; console.error('FAIL - ' + e.message); }
    }
    // an old link must not show the chooser
    await send('Emulation.setDeviceMetricsOverride', { width: 800, height: 360, deviceScaleFactor: 2, mobile: false });
    await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/index.html?relay=ws://127.0.0.1:1&team=3&room=ABCDE' }); await sleep(2800);
    const old = await ev("(() => { const box = document.getElementById('side-chooser'); return !box.hidden && getComputedStyle(box).display !== 'none'; })()");
    if (old) { failed = true; console.error('FAIL - an old link (no choose=) shows the chooser'); } else console.log('ok   - an old link (no choose=) does not show the chooser');
    ws.close();
  } finally { chrome.kill(); server.close(); }
  console.log('test_side_chooser_layout: ' + (failed ? 'FAILED' : VIEWS.length + ' views and the old-link case passed'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_side_chooser_layout: ' + (e && e.stack || e)); process.exit(1); });
