#!/usr/bin/env node
'use strict';
// ROOM-FLOW F1 to F12 and V1, in a real headless Chrome (DevTools Protocol) against the real relay (python3 scripts/pk_relay.py), both on free local ports.
// Part 1, the flow (2v2 and 3v3): the host presses "Play with friends" (one press: a room with a code), a guest opens the lobby link (another origin, so another saved
// name), the host is welcomed by name, the guest takes a second place (3v3), host-only controls are locked for the guest, both lock, the host's start fills the open
// places with computer seats, the countdown runs, both pages enter the match with the names above the heads, the host goes back to the lobby (computer seats gone,
// same people), and a second match starts in the same room.
// Part 2, the layout: in 10 window sizes every lobby control is inside the window and is what a finger hits at its centre; no sideways scroll; all 3 places of each
// team are visible. Needs local sockets: run it outside a socket-blocking sandbox (listed with the socket tests in run_full_suite.sh).
const { spawn } = require('child_process'), fs = require('fs'), http = require('http'), net = require('net'), os = require('os'), path = require('path');
const ROOT = require('path').join(__dirname, '..', '..', '..');
const CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!CHROME) { console.error('test_lobby_browser: no Chrome found'); process.exit(2); }
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.webmanifest': 'application/manifest+json' };
const VIEWS = [[667, 375], [740, 360], [800, 360], [812, 375], [844, 390], [873, 392], [923, 415], [1280, 720], [1366, 768], [1920, 1080]];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const freePort = () => new Promise((resolve, reject) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); }); s.on('error', reject); });
let failed = 0;
const ok = msg => console.log('ok   - ' + msg);
const bad = msg => { failed++; console.error('FAIL - ' + msg); };

async function tab(dbg, url) {   // one page with its own DevTools socket; page errors are collected
  const made = await (await fetch('http://127.0.0.1:' + dbg + '/json/new?' + encodeURIComponent(url), { method: 'PUT' })).json();
  const ws = new WebSocket(made.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = new Map(), errors = [];
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } else if (d.method === 'Runtime.exceptionThrown') errors.push(String(d.params.exceptionDetails.exception && d.params.exceptionDetails.exception.description || d.params.exceptionDetails.text).split('\n')[0]); };
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Runtime.enable');
  const ev = async x => { const r = (await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true })).result; if (r.exceptionDetails) throw new Error('page: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text).split('\n')[0]); return r.result.value; };
  const until = async (x, what, ms = 12000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { try { if (await ev(x)) return; } catch (_) { /* page still loading */ } await sleep(150); } throw new Error('timeout: ' + what + ' (' + x.slice(0, 90) + ')'); };
  return { send, ev, until, errors, close: async () => { try { ws.close(); } catch (_) { /* gone */ } try { await fetch('http://127.0.0.1:' + dbg + '/json/close/' + made.id); } catch (_) { /* gone */ } } };   // closing the tab closes its relay sockets
}
const click = id => "(() => { const el = document.getElementById('" + id + "'); if (!el || el.disabled) return false; el.click(); return true; })()";
const lobbyState = "(window.__lv = () => LobbyModel.view(lobbyState || {}, relaySeatId), true)";

const lv = "(window.__lv = () => LobbyModel.view(lobbyState || {}, relaySeatId), true)";
const ready = "document.readyState === 'complete' && typeof lobbyOpenFromStart === 'function' && !!document.getElementById('friends-btn').onclick";
async function boot(opts = {}) {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; } fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, relayPort = await freePort(), dbg = await freePort();
  const relay = spawn('python3', ['-B', path.join(ROOT, 'scripts', 'pk_relay.py')], { cwd: ROOT, env: Object.assign({}, process.env, { HOST: '127.0.0.1', PORT: String(relayPort), PK_RELAY_MAX_PER_ADDR: '40' }, opts.env || {}), stdio: 'ignore' });
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-rtb-')), '--no-first-run', '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
  for (let i = 0; i < 60; i++) { try { await (await fetch('http://127.0.0.1:' + dbg + '/json/version')).json(); break; } catch (_) { await sleep(200); } }
  await sleep(500);
  return { dbg, base: 'http://127.0.0.1:' + port, alt: 'http://localhost:' + port, relayUrl: 'ws://127.0.0.1:' + relayPort, stop: () => { chrome.kill(); relay.kill(); server.close(); } };
}
module.exports = { tab, click, lv, ready, boot, sleep, ok, bad, fs, path };
