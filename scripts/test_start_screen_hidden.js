#!/usr/bin/env node
'use strict';
// After Start Battle the start screen must be gone, at every phone-sized view. Regression of 2026-11-24 (introduced by 86a2cf06, 2026-11-19): in the "start-compact" views
// (visible width under 800 or height under 360) the rule `html.start-compact #start-screen { display: grid }` beat `#start-screen.hidden { display: none }`, so the start screen stayed on top
// of the running battle on a phone ("the screen is covered and nothing changes"). A real Chrome (DevTools Protocol, Node 22 WebSocket) loads the page, presses Start and reads the computed style.
// Needs a local socket and Chrome, so it cannot run inside the Claude sandbox; the runner reports that as FAIL and the owner's terminal run decides.
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), os = require('os'), path = require('path'), assert = require('assert');
const ROOT = path.join(__dirname, '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_start_screen_hidden: no Chrome found'); process.exit(2); }
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VIEWS = [[640, 300], [720, 266], [799, 400], [800, 359], [844, 390], [923, 415], [1280, 720]];   // compact (narrower than 800 or lower than 360) and not compact
(async () => {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); } else { res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream', 'cache-control': 'no-store' }); res.end(d); } }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, dbg = 9500 + Math.floor(Math.random() * 400);
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-hidden-')), '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  let failed = false;
  try {
    let tabs; for (let i = 0; i < 60; i++) { try { tabs = await (await fetch('http://127.0.0.1:' + dbg + '/json')).json(); if (tabs.length) break; } catch (_) { /* Chrome is starting */ } await sleep(200); }
    assert.ok(tabs && tabs.length, 'Chrome did not start');
    const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    for (const [w, h] of VIEWS) {
      await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
      await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/index.html?team=1' }); await sleep(2500);
      const before = (await send('Runtime.evaluate', { expression: "getComputedStyle(document.getElementById('start-screen')).display", returnByValue: true })).result.result.value;
      await send('Runtime.evaluate', { expression: "document.getElementById('start-go').click(); 1", returnByValue: true }); await sleep(1800);
      const after = JSON.parse((await send('Runtime.evaluate', { expression: "JSON.stringify({ display: getComputedStyle(document.getElementById('start-screen')).display, cls: document.getElementById('start-screen').className, compact: document.documentElement.className.indexOf('start-compact') >= 0, started: matchStarted })", returnByValue: true })).result.result.value);
      try { assert.notStrictEqual(before, 'none', w + 'x' + h + ': the start screen is shown before Start'); assert.strictEqual(after.started, true, w + 'x' + h + ': Start began the match'); assert.strictEqual(after.display, 'none', w + 'x' + h + ': the start screen is still displayed after Start (compact=' + after.compact + ', class=' + after.cls + ')'); console.log('ok   - ' + w + 'x' + h + (after.compact ? ' (compact)' : '') + ': the start screen is gone after Start'); }
      catch (e) { failed = true; console.error('FAIL - ' + e.message); }
    }
    ws.close();
  } finally { chrome.kill(); server.close(); }
  console.log('test_start_screen_hidden: ' + (failed ? 'FAILED' : VIEWS.length + ' views passed'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_start_screen_hidden: ' + (e && e.stack || e)); process.exit(1); });
