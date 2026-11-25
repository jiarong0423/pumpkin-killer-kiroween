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
const ROOT = path.join(__dirname, '..');
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

async function flow(dbg, base, alt, relayUrl, n) {
  const name = n + 'v' + n;
  const host = await tab(dbg, base + '/index.html?relay=' + relayUrl + '&team=' + n);
  const guest = await tab(dbg, alt + '/index.html?relay=' + relayUrl + '&team=' + n);
  try {
    for (const [p, nm] of [[host, '房主' + n], [guest, 'Guest' + n]]) { await p.until("document.readyState === 'complete' && typeof lobbyOpenFromStart === 'function' && !!document.getElementById('friends-btn').onclick", 'page ready'); await p.ev("localStorage.setItem('pk_name', '" + nm + "'), true"); }
    await host.ev("document.getElementById('friends-btn').click(), true");
    try { await host.until("!document.getElementById('lobby').hidden && /^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'host lobby with a code'); }
    catch (e) { throw new Error(e.message + ' | ' + await host.ev("JSON.stringify({ lobbyMode, hidden: document.getElementById('lobby').hidden, code: document.getElementById('lobby-code').textContent, nameDialog: !document.getElementById('name-dialog').hidden, team: TEAM_N, url: location.search, status: relayClient && relayClient.state().status, toast: document.getElementById('lobby-toast').textContent })") + ' errors ' + host.errors.join(' | ')); }
    const code = await host.ev("document.getElementById('lobby-code').textContent");
    if (!(await host.ev("document.getElementById('lobby-count').textContent")).includes('1/' + 2 * n)) throw new Error('host alone should count 1/' + 2 * n);
    await guest.ev("location.href = '" + alt + "/index.html?relay=" + relayUrl + "&team=" + n + "&room=" + code + "&lobby=1'; true");
    await guest.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId && !document.getElementById('lobby').hidden", 'guest in the lobby');
    await host.until("document.getElementById('lobby-toast').textContent.includes('Guest" + n + "')", 'host welcomes the guest by name');
    await guest.until("document.getElementById('lobby-toast').textContent.includes('" + code + "')", 'guest welcomed to the room');
    await host.ev(lobbyState); await guest.ev(lobbyState);
    if (!(await guest.ev("document.getElementById('lobby-start').disabled && document.getElementById('lobby-allow-ai').disabled && document.getElementById('lobby-refresh').disabled"))) throw new Error('host-only controls are not locked for the guest');
    if (await host.ev("document.getElementById('lobby-refresh').disabled") !== true) throw new Error('refresh must lock once someone else sits');
    if (n === 3) {   // the guest takes a second place on its team
      await guest.ev("(() => { const b = [...document.querySelectorAll('#lobby-cells-white .cell-act')].find(x => /Play this one too|也操控/.test(x.textContent))   /* the take-a-place button (renamed in DESIGN-1) */; if (b) b.click(); return !!b; })()");
      await host.until("__lv().teams.white.filter(c => c.kind === 'seat').length === 2", 'guest holds two places');
    }
    const seated = n === 3 ? 3 : 2;
    await host.until("document.getElementById('lobby-count').textContent.includes('" + seated + "/" + 2 * n + "')", 'count after the guest');
    await host.ev(click('lobby-lock')); await guest.ev(click('lobby-lock'));
    await host.until("__lv().myLocked", 'host locked'); await guest.until("__lv().myLocked", 'guest locked');
    if (!(await host.ev("/computer|電腦/i.test(document.getElementById('lobby-start').textContent)"))) throw new Error('the start button should say the computer fills: ' + await host.ev("document.getElementById('lobby-start').textContent"));
    await host.ev(click('lobby-start'));
    await host.until("!document.getElementById('lobby-countdown').hidden || relayPlaying", 'countdown shown', 15000);
    for (const p of [host, guest]) await p.until("relayPlaying && matchStarted && document.getElementById('lobby').hidden", 'match started from the lobby', 15000);
    const labels = await host.ev("JSON.stringify(allUnits().map(u => unitNameLabel(u)))");
    if (!labels.includes('房主' + n) || !labels.includes('Guest' + n) || (n * 2 - seated > 0 && !/Computer|電腦/.test(labels))) throw new Error('names above the heads: ' + labels);
    ok(name + ': one-press room ' + code + ', guest welcomed both ways, host-only controls locked for the guest, ' + (n === 3 ? 'second place taken, ' : '') + 'locks, computer fill, countdown, match started; names ' + labels);
    // back to the lobby and a second match
    await host.ev("gameOver = 'player', turn = 'over', lobbyAfterMatch(true), true");
    for (const p of [host, guest]) await p.until("!relayPlaying && !document.getElementById('lobby').hidden && lobbyState && lobbyState.started === false", 'back in the lobby', 12000);
    await host.until("__lv().count.seated === " + seated + " && (lobbyState.seats || []).every(s => !s.ai)", 'computer seats gone, same people', 12000);
    const names = await guest.ev("JSON.stringify((lobbyState.seats || []).map(s => s.name).sort())");
    await host.ev(click('lobby-lock')); await guest.ev(click('lobby-lock'));
    await host.until("__lv().myLocked", 'host locked again'); await guest.until("__lv().myLocked", 'guest locked again');
    await host.ev(click('lobby-start'));
    for (const p of [host, guest]) await p.until("relayPlaying && matchStarted", 'second match started', 15000);
    ok(name + ': back to the lobby with the same people ' + names + ', computer seats gone, second match started in the same room');
    const errs = host.errors.concat(guest.errors).filter(e => !/favicon|ResizeObserver/.test(e));
    if (errs.length) bad(name + ': page errors: ' + errs.slice(0, 3).join(' | ')); else ok(name + ': no page errors');
  } catch (e) { bad(name + ': ' + e.message); } finally { await host.close(); await guest.close(); await sleep(300); }
}

async function flowInvite(dbg, base, alt, relayUrl) {   // F12: a player invites an agent; a browser agent opens the link and takes one place of the inviter's team
  const host = await tab(dbg, base + '/index.html?relay=' + relayUrl + '&team=2'), agent = await tab(dbg, alt + '/index.html?relay=' + relayUrl + '&team=2');
  try {
    for (const [p, nm] of [[host, 'Inviter'], [agent, 'Bot']]) { await p.until("document.readyState === 'complete' && !!document.getElementById('friends-btn').onclick", 'page ready'); await p.ev("localStorage.setItem('pk_name', '" + nm + "'), true"); }
    await host.ev("document.getElementById('friends-btn').click(), true");
    await host.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'host lobby');
    if (!(await host.ev("document.getElementById('lobby-invite').hidden && !document.getElementById('lobby-allow-agent').checked"))) throw new Error('agents must start off and the invite button hidden');
    await host.ev("document.getElementById('lobby-allow-agent').click(), true");
    await host.until("!document.getElementById('lobby-invite').hidden && !document.getElementById('lobby-invite').disabled", 'invite button after ticking');
    await host.ev(click('lobby-invite'));
    await host.until("!document.getElementById('lobby-invite-box').hidden && lobbyInvite", 'invite box');
    const link = await host.ev("lobbyLink(lobbyState.code, lobbyInvite).replace('127.0.0.1', 'localhost')");
    const text = await host.ev("document.getElementById('lobby-invite-text').textContent");
    if (!text.includes(await host.ev("lobbyState.code")) || !text.includes(await host.ev("lobbyInvite")) || !/\/mcp/.test(text)) throw new Error('invite text lacks code, invite or MCP address: ' + text);
    await host.until("document.getElementById('lobby-invite').disabled", 'one invite per player');
    await agent.ev("location.href = '" + link + "'; true");
    await agent.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'agent in the lobby');
    await host.ev(lobbyState);
    await host.until("__lv().teams.red.some(c => c.agent && c.invitedByName === 'Inviter')", 'agent seat on the red team, bound to its inviter');
    const shown = await host.ev("[...document.querySelectorAll('#lobby-cells-red .lobby-cell.agent small')].map(e => e.textContent).join('|')");
    if (!/Inviter/.test(shown)) throw new Error('the agent place does not say who invited it: ' + shown);
    await host.until("document.getElementById('lobby-invite-box').hidden", 'invite box closes once the ticket is used');
    await agent.ev(click('lobby-lock')); await host.ev(click('lobby-lock'));
    await host.until("__lv().myLocked", 'host locked');
    await host.ev(click('lobby-start'));
    for (const p of [host, agent]) await p.until("relayPlaying && matchStarted", 'match with the invited agent', 15000);
    ok('invite: agents off by default, tick shows the invite, the ticket text has code, invite and MCP address, a browser agent joins the inviter\'s team shown as ' + JSON.stringify(shown) + ', match started');
    const errs = host.errors.concat(agent.errors).filter(e => !/favicon|ResizeObserver/.test(e));
    if (errs.length) bad('invite: page errors: ' + errs.slice(0, 3).join(' | '));
  } catch (e) { bad('invite: ' + e.message); } finally { await host.close(); await agent.close(); await sleep(300); }
}

async function layout(dbg, base, relayUrl) {
  const p = await tab(dbg, 'about:blank');
  try {
    for (const [w, h] of VIEWS) {
      await p.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
      await p.send('Page.navigate', { url: base + '/index.html?relay=' + relayUrl + '&team=3' });
      await p.until("document.readyState === 'complete' && typeof lobbyOpenFromStart === 'function' && !!document.getElementById('friends-btn').onclick", 'page ready');
      await p.ev("localStorage.setItem('pk_name', '南瓜殺手王😀'), true");
      await p.ev("document.getElementById('friends-btn').click(), true");
      await p.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'lobby code');
      await p.ev("(() => { const el = document.getElementById('lobby-allow-agent'); if (!el.checked) el.click(); return true; })()");
      await p.until("!document.getElementById('lobby-invite').hidden", 'invite button shown');
      const m = JSON.parse(await p.ev(`(() => {
        const out = { vw: innerWidth, vh: innerHeight, sw: document.documentElement.scrollWidth, miss: [] };
        const ids = ['lobby-code', 'lobby-copy', 'lobby-refresh', 'lobby-leave', 'lobby-rename', 'lobby-lock', 'lobby-invite', 'lobby-allow-ai', 'lobby-allow-agent', 'lobby-start'];
        document.querySelectorAll('#lobby .hero-pick, #lobby .cell-act').forEach((el, i) => { el.id = el.id || 'auto-' + i; ids.push(el.id); });
        for (const id of ids) {
          const el = document.getElementById(id); if (!el) { out.miss.push(id + ' missing'); continue; }
          const target = el.type === 'checkbox' ? el.closest('label') : el, r = target.getBoundingClientRect();
          if (r.width < 1 || r.left < -0.5 || r.top < -0.5 || r.right > innerWidth + 0.5 || r.bottom > innerHeight + 0.5) { out.miss.push(id + ' outside the window ' + [r.left, r.top, r.right, r.bottom].map(Math.round)); continue; }
          const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
          if (!hit || !(target === hit || target.contains(hit))) out.miss.push(id + ' covered by ' + (hit ? hit.tagName + '#' + hit.id + '.' + hit.className : 'nothing'));
        }
        const cells = [...document.querySelectorAll('#lobby .lobby-cell')];
        out.cells = cells.length;
        cells.forEach((c, i) => { const r = c.getBoundingClientRect(), box = c.closest('.lobby-team').getBoundingClientRect(); if (r.bottom > box.bottom + 0.5 || r.bottom > innerHeight + 0.5) out.miss.push('place ' + i + ' cut off'); });
        return JSON.stringify(out);
      })()`));
      const name = w + 'x' + h;
      if (m.sw > m.vw + 1) bad(name + ': sideways scroll ' + m.sw + ' > ' + m.vw);
      else if (m.cells !== 6) bad(name + ': ' + m.cells + ' places shown, want 6');
      else if (m.miss.length) bad(name + ': ' + m.miss.slice(0, 4).join('; ') + ' rows ' + await p.ev("JSON.stringify(['lobby-bar','lobby-teams','lobby-mine','lobby-foot','lobby-wait'].map(id => { const r = document.getElementById(id).getBoundingClientRect(); return id + ':' + Math.round(r.top) + '+' + Math.round(r.height); }).concat([...document.querySelectorAll('#lobby-cells-red > li, .lobby-team[data-team=red] h3')].map(e => e.tagName + Math.round(e.getBoundingClientRect().height))))"));
      else ok(name + ': every lobby control inside the window and hit at its centre, 6 places visible, no sideways scroll');
      await p.ev("lobbyLeave(true), true");
    }
    const errs = p.errors.filter(e => !/favicon|ResizeObserver/.test(e));
    if (errs.length) bad('layout: page errors: ' + errs.slice(0, 3).join(' | '));
  } catch (e) { bad('layout: ' + e.message); } finally { await p.close(); }
}

(async () => {
  const server = http.createServer((req, res) => { const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html')); if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; } fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); res.end(d); }); });
  await new Promise((resolve, reject) => { server.on('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port, relayPort = await freePort(), dbg = await freePort();
  const relay = spawn('python3', ['-B', path.join(ROOT, 'scripts', 'pk_relay.py')], { cwd: ROOT, env: Object.assign({}, process.env, { HOST: '127.0.0.1', PORT: String(relayPort), PK_RELAY_MAX_PER_ADDR: '40' })   /* every tab and computer seat of this test comes from 127.0.0.1 */, stdio: 'ignore' });
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + dbg, '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'pk-lobby-')), '--no-first-run', '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
  try {
    for (let i = 0; i < 60; i++) { try { await (await fetch('http://127.0.0.1:' + dbg + '/json/version')).json(); break; } catch (_) { await sleep(200); } }
    const relayUrl = 'ws://127.0.0.1:' + relayPort;
    const base = 'http://127.0.0.1:' + port, alt = 'http://localhost:' + port;   // two origins: two saved names
    const only = process.argv[2];
    if (!only || only === 'flow') { await flow(dbg, base, alt, relayUrl, 2); await flow(dbg, base, alt, relayUrl, 3); await flowInvite(dbg, base, alt, relayUrl); }
    if (only === 'invite') await flowInvite(dbg, base, alt, relayUrl);
    if (only === 'flow3') await flow(dbg, base, alt, relayUrl, 3);
    if (!only || only === 'layout') await layout(dbg, base, relayUrl);
    if (only === 'shot') {   // evidence picture for the owner (not part of the test): host view of a 3v3 lobby with a guest, phone size, Chinese
      const out = process.argv[3] || 'lobby_shot.png';
      const host = await tab(dbg, base + '/index.html?relay=' + relayUrl + '&team=3'), guest = await tab(dbg, alt + '/index.html?relay=' + relayUrl + '&team=3');
      await host.send('Emulation.setDeviceMetricsOverride', { width: 812, height: 375, deviceScaleFactor: 2, mobile: false });
      for (const [pg, nm] of [[host, '南瓜王😀'], [guest, '小白']]) { await pg.until("document.readyState === 'complete' && !!document.getElementById('friends-btn').onclick", 'ready'); await pg.ev("localStorage.setItem('pk_name', '" + nm + "'); localStorage.setItem('pk_lang', 'zh-TW'); I18N.setLang('zh-TW'); I18N.apply(document); true"); }
      await host.ev("document.getElementById('friends-btn').click(), true");
      await host.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code');
      const code = await host.ev("document.getElementById('lobby-code').textContent");
      await guest.ev("location.href = '" + alt + "/index.html?relay=" + relayUrl + "&team=3&room=" + code + "&lobby=1'; true");
      await guest.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'guest');
      await host.until("document.getElementById('lobby-toast').textContent.length > 0", 'toast');
      await host.ev("document.getElementById('lobby-allow-agent').click(), true");
      await host.until("!document.getElementById('lobby-invite').hidden", 'invite shown');
      await sleep(300);
      const shot = await host.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
      console.log('wrote ' + out);
      await host.close(); await guest.close();
    }
  } finally { chrome.kill(); relay.kill(); server.close(); }
  console.log('test_lobby_browser: ' + (failed ? failed + ' FAILED' : 'OK'));
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('test_lobby_browser: ' + (e && e.stack || e)); process.exit(1); });
