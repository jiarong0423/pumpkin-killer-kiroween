#!/usr/bin/env node
'use strict';
// LATE-JOIN-1 (Gemini T1 path 5): a guest who opens an invite link of a room whose match has already started must read that the match started (not a silent lobby).
// Real Chrome + real relay. (header of the sibling test_invite_panel_fit.js, which this file was copied from: )
// Owner 2026-11-24 (Gemini T1 path 7, re-measured by Claude): in a landscape phone the friends panel after Create room is taller than its
// 86vh box, so the room code, QR and invite link sit below the fold of an inner scroll (812x375: content 399 > box 320, link bottom 404 > 375).
// The invite details must be fully visible without scrolling in every common landscape phone size: code, QR and link inside the panel's visible
// box AND inside the viewport, no inner scroll, no sideways scroll. A real Chrome (DevTools Protocol) and the real relay (python3 scripts/pk_relay.py)
// are started on free local ports; needs local sockets, so it cannot run inside a socket-blocking sandbox.
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), net = require('net'), os = require('os'), path = require('path');
const ROOT = path.join(__dirname, '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_late_join_page: no Chrome found'); process.exit(2); }
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VIEWS = [[667, 375], [740, 360], [800, 360], [812, 375], [844, 390], [873, 392], [923, 415]];
const freePort = () => new Promise((resolve, reject) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); }); s.on('error', reject); });
(async () => {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(d); } }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, relayPort = await freePort(), dbg = await freePort();
  const relay = spawn('python3', ['-B', path.join(ROOT, 'scripts', 'pk_relay.py')], { cwd: ROOT, env: Object.assign({}, process.env, { HOST: '127.0.0.1', PORT: String(relayPort) }), stdio: 'ignore' });
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-latejoin-')), '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let failed = false;
  try {
    await sleep(800);
    let tabs; for (let i = 0; i < 60; i++) { try { tabs = await (await fetch('http://127.0.0.1:' + dbg + '/json')).json(); if (tabs.length) break; } catch (_) { /* starting */ } await sleep(200); }
    const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async x => (await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true })).result.result.value;
    const code = await new Promise((resolve, reject) => {
      const a = new WebSocket('ws://127.0.0.1:' + relayPort + '/ws'); const socks = [a]; global.__socks = socks;
      a.onopen = () => a.send(JSON.stringify({ type: 'create_room', seat: 'red' }));
      a.onmessage = m => { const d = JSON.parse(m.data);
        if (d.type === 'room_state' && d.code && !socks.b) {
          const b = socks.b = new WebSocket('ws://127.0.0.1:' + relayPort + '/ws'); socks.push(b);
          b.onopen = () => b.send(JSON.stringify({ type: 'join', code: d.code, seat: 'white' }));
          b.onmessage = n => { const e = JSON.parse(n.data); if (e.type === 'room_state') { a.send(JSON.stringify({ type: 'ready' })); b.send(JSON.stringify({ type: 'ready' })); } if (e.type === 'start') resolve(d.code); };
        } };
      setTimeout(() => reject(new Error('the room did not start')), 5000);
    });
    await send('Emulation.setDeviceMetricsOverride', { width: 844, height: 390, deviceScaleFactor: 2, mobile: false });
    await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/index.html?relay=ws://127.0.0.1:' + relayPort + '&team=1&room=' + code }); await sleep(3500);
    const m = JSON.parse(await ev("JSON.stringify((() => { const s = document.getElementById('room-status'); return { hidden: !s || s.hidden, text: s ? s.textContent : '', open: document.getElementById('start-screen').classList.contains('seats-open') }; })())"));
    try {
      if (m.hidden || !m.text) throw new Error('late guest sees nothing (silent lobby): ' + JSON.stringify(m));
      if (!/已經開始|already started/.test(m.text)) throw new Error('late guest sees the wrong text: ' + JSON.stringify(m));
      if (!m.open) throw new Error('the friends panel is not opened, so the text cannot be seen: ' + JSON.stringify(m));
      console.log('ok   - late guest reads: ' + m.text);
    } catch (e) { failed = true; console.error('FAIL - ' + e.message); }
    for (const s of global.__socks || []) { try { s.close(); } catch (_) { /* gone */ } }
    ws.close();
  } finally { chrome.kill(); relay.kill(); server.close(); }
  console.log('test_late_join_page: ' + (failed ? 'FAILED' : 'passed'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_late_join_page: ' + (e && e.stack || e)); process.exit(1); });
