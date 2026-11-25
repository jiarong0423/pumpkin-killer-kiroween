#!/usr/bin/env node
'use strict';
// Overlay reachability (owner 2026-11-25, after UI-CLIP-1): every button of the OTHER overlays must be clickable by a person, not only the friends panel:
// the settings sheet, the red/white side chooser and the agent waiting panel (copy command, cancel). Real headless Chrome (no window) and the real relay,
// 10 window sizes. A person can only scroll the overlay itself, so only that scroller is scrolled (scrollIntoView would also scroll overflow:hidden ancestors
// and hide the defect). Needs local sockets; not part of the socket-free suite.
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), net = require('net'), os = require('os'), path = require('path');
const ROOT = path.join(__dirname, '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_invite_panel_fit: no Chrome found'); process.exit(2); }
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VIEWS = [[667, 375], [740, 360], [800, 360], [812, 375], [844, 390], [873, 392], [923, 415], [1280, 720], [1366, 768], [1920, 1080]];   // phones (no inner scroll allowed) and desktops (the panel may scroll inside, but every button must be reachable)
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

    const reachJs = `(async () => {
      const wait = ms => new Promise(r => setTimeout(r, ms));
      window.__reach = async (rootSel, scrollSel) => {
        const root = document.querySelector(rootSel), out = { root: rootSel, shown: false, bad: [], checked: 0 };
        if (!root) { out.missing = true; return out; }
        const rr = root.getBoundingClientRect(); out.shown = rr.width > 0 && rr.height > 0 && !root.closest('[hidden]');
        if (!out.shown) return out;
        const sc = scrollSel ? document.querySelector(scrollSel) : null;
        for (const el of root.querySelectorAll('button')) {
          const r0 = el.getBoundingClientRect(); if (!(r0.width > 0 && r0.height > 0) || el.closest('[hidden]') || getComputedStyle(el).visibility === 'hidden') continue;
          if (sc) { const pr = sc.getBoundingClientRect(), q = el.getBoundingClientRect(); if (q.bottom > pr.bottom) sc.scrollTop += q.bottom - pr.bottom + 4; if (q.top < pr.top) sc.scrollTop -= pr.top - q.top + 4; await wait(30); }
          const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2; out.checked++;
          const t = (cx >= 0 && cy >= 0 && cx < innerWidth && cy < innerHeight) ? document.elementFromPoint(cx, cy) : null;
          if (!(t && (t === el || el.contains(t)))) out.bad.push((el.id || el.className || el.textContent.trim().slice(0, 20)) + ' covered by ' + (t ? (t.id || t.className || t.tagName) : 'nothing (outside the window)'));
        }
        return out;
      };
      return true;
    })()`;
    for (const [w, h] of VIEWS) {
      const name = w + 'x' + h;
      await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
      const base = 'http://127.0.0.1:' + port + '/index.html?relay=ws://127.0.0.1:' + relayPort;
      try {
        // A: settings sheet
        await send('Page.navigate', { url: base + '&team=3' }); await sleep(2500); await ev(reachJs);
        await ev("(async () => { document.getElementById('settings-btn').click(); await new Promise(r => setTimeout(r, 400)); return 1; })()");
        const A = JSON.parse(await ev("(async () => JSON.stringify(await window.__reach('#settings-sheet', '#settings-sheet')))()"));
        // C: agent waiting panel (after a room exists)
        await ev("(async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const c = document.getElementById('settings-close'); if (c) c.click(); document.getElementById('start-screen').classList.add('seats-open');   /* ROOM-FLOW F11: Friends opens the lobby now; the old panel is still shown for an old ?room= link */ await w(300); document.getElementById('room-create').click(); for (let i = 0; i < 40 && !/\\w{4,}/.test((document.getElementById('room-code') || {}).textContent || ''); i++) await w(100); const x = document.getElementById('friends-close'); if (x) x.click(); await w(200); showAgentWaiting('left'); await w(500); return 1; })()");
        const C = JSON.parse(await ev("(async () => JSON.stringify(await window.__reach('#agent-wait', null)))()"));
        // B: side chooser from an invite link
        await send('Page.navigate', { url: base + '&room=ZZZZZZ&choose=1' }); await sleep(2500); await ev(reachJs);
        const B = JSON.parse(await ev("(async () => JSON.stringify(await window.__reach('#side-chooser', '#side-chooser .side-card')))()"));
        const problems = [];
        for (const [what, r] of [['settings sheet', A], ['agent waiting panel', C], ['side chooser', B]]) {
          if (r.missing || !r.shown) problems.push(what + ' did not open (' + JSON.stringify(r) + ')');
          else if (r.checked === 0) problems.push(what + ': no button found');
          else if (r.bad.length) problems.push(what + ': ' + r.bad.join('; '));
        }
        if (problems.length) throw new Error(name + ': ' + problems.join(' | '));
        console.log('ok   - ' + name + ': settings ' + A.checked + ', agent panel ' + C.checked + ', side chooser ' + B.checked + ' buttons clickable');
      } catch (e) { failed = true; console.error('FAIL - ' + e.message); }
    }
    ws.close();
  } finally { chrome.kill(); relay.kill(); server.close(); }
  console.log('test_overlay_reachability: ' + (failed ? 'FAILED' : VIEWS.length + ' views passed'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_overlay_reachability: ' + (e && e.stack || e)); process.exit(1); });
