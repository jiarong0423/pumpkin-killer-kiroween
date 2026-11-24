#!/usr/bin/env node
'use strict';
// Owner 2026-11-24 (Gemini T1 path 7, re-measured by Claude): in a landscape phone the friends panel after Create room is taller than its
// 86vh box, so the room code, QR and invite link sit below the fold of an inner scroll (812x375: content 399 > box 320, link bottom 404 > 375).
// The invite details must be fully visible without scrolling in every common landscape phone size: code, QR and link inside the panel's visible
// box AND inside the viewport, no inner scroll, no sideways scroll. A real Chrome (DevTools Protocol) and the real relay (python3 scripts/pk_relay.py)
// are started on free local ports; needs local sockets, so it cannot run inside a socket-blocking sandbox.
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), net = require('net'), os = require('os'), path = require('path');
const ROOT = path.join(__dirname, '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_invite_panel_fit: no Chrome found'); process.exit(2); }
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VIEWS = [[667, 375], [740, 360], [800, 360], [812, 375], [844, 390], [873, 392], [923, 415]];
const freePort = () => new Promise((resolve, reject) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); }); s.on('error', reject); });
(async () => {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); } }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, relayPort = await freePort(), dbg = await freePort();
  const relay = spawn('python3', ['-B', path.join(ROOT, 'scripts', 'pk_relay.py')], { cwd: ROOT, env: Object.assign({}, process.env, { HOST: '127.0.0.1', PORT: String(relayPort) }), stdio: 'ignore' });
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-invite-')), '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let failed = false;
  try {
    await sleep(800);
    let tabs; for (let i = 0; i < 60; i++) { try { tabs = await (await fetch('http://127.0.0.1:' + dbg + '/json')).json(); if (tabs.length) break; } catch (_) { /* starting */ } await sleep(200); }
    const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async x => (await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true })).result.result.value;
    for (const [w, h] of VIEWS) {
      await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
      await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/index.html?relay=ws://127.0.0.1:' + relayPort + '&team=3' }); await sleep(2500);
      const m = JSON.parse(await ev("(async () => { const wait = ms => new Promise(r => setTimeout(r, ms)); const fb = document.getElementById('friends-btn'); if (fb) fb.click(); await wait(500); const rc = document.getElementById('room-create'); if (rc) rc.click(); for (let i = 0; i < 30; i++) { const c = document.getElementById('room-code'); if (c && /^[A-Z0-9]{6}$/.test(c.textContent.trim())) break; await wait(150); } const q = id => { const e = document.getElementById(id); if (!e || !e.offsetParent) return null; const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }; const fp = document.getElementById('friends-panel'); return JSON.stringify({ vw: innerWidth, vh: innerHeight, code: (document.getElementById('room-code') || {}).textContent || '', panel: q('friends-panel'), scrollH: fp.scrollHeight, clientH: fp.clientHeight, code_r: q('room-code'), qr: q('room-qr'), link: q('room-link'), scrollW: document.documentElement.scrollWidth }); })()"));
      try {
        const name = w + 'x' + h;
        if (!/^[A-Z0-9]{6}$/.test(m.code.trim())) throw new Error(name + ': no room was created (code "' + m.code + '")');
        if (!m.panel || !m.code_r || !m.qr || !m.link) throw new Error(name + ': panel, code, QR or link is not visible');
        const inside = (o, box, what) => { if (o.l < box.l - 0.5 || o.t < box.t - 0.5 || o.r > box.r + 0.5 || o.b > box.b + 0.5) throw new Error(name + ': ' + what + ' is not fully inside ' + (box === m.panel ? 'the panel' : 'the viewport') + ' ' + JSON.stringify({ o: [o.l, o.t, o.r, o.b].map(Math.round), box: [box.l, box.t, box.r, box.b].map(Math.round) })); };
        const view = { l: 0, t: 0, r: m.vw, b: m.vh };
        for (const [what, o] of [['room code', m.code_r], ['QR', m.qr], ['invite link', m.link]]) { inside(o, m.panel, what); inside(o, view, what); }
        if (m.scrollH > m.clientH + 1) throw new Error(name + ': the panel scrolls inside (content ' + m.scrollH + ' > box ' + m.clientH + ')');
        if (m.scrollW > m.vw + 1) throw new Error(name + ': sideways scroll (' + m.scrollW + ' > ' + m.vw + ')');
        console.log('ok   - ' + name + ': code, QR and link fully visible, panel ' + Math.round(m.panel.r - m.panel.l) + 'x' + Math.round(m.panel.b - m.panel.t) + ', no inner scroll');
      } catch (e) { failed = true; console.error('FAIL - ' + e.message); }
    }
    ws.close();
  } finally { chrome.kill(); relay.kill(); server.close(); }
  console.log('test_invite_panel_fit: ' + (failed ? 'FAILED' : VIEWS.length + ' views passed'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_invite_panel_fit: ' + (e && e.stack || e)); process.exit(1); });
