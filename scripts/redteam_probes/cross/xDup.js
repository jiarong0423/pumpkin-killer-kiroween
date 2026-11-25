#!/usr/bin/env node
'use strict';
// Red-team B scenarios against the lobby. Usage: node scen.js A|B|C|D|E|F|G
const { tab, click, lv, ready, boot, sleep, ok, bad } = require('../lobby/base.js');
const which = process.argv[2] || 'A';
const S = x => JSON.stringify(x);
const state = "JSON.stringify({ lobbyMode, seat: relaySeatId, host: relayIsHost, TEAM_N, url: location.search, toast: document.getElementById('lobby-toast').textContent, toastHidden: document.getElementById('lobby-toast').hidden, lobbyHidden: document.getElementById('lobby').hidden, seats: (lobbyState && lobbyState.seats || []).map(s => s.seat_id + ':' + s.team + ':' + (s.name||'') + (s.ai?':ai':'') + (s.ready?':R':'') + ':u' + (s.units||[]).length + ':c' + s.claim), begin: lobbyState && lobbyState.begin, started: lobbyState && lobbyState.started, start: document.getElementById('lobby-start').textContent, startDis: document.getElementById('lobby-start').disabled, wait: document.getElementById('lobby-wait').textContent, fillers: relayFillers.length, playing: relayPlaying })";

async function hostLobby(env, n, name) {
  const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + (n > 1 ? '&team=' + n : '&team=1'));
  await h.until(ready, 'host ready');
  await h.ev("localStorage.setItem('pk_name', " + S(name) + "), true");
  await h.ev("document.getElementById('friends-btn').click(), true");
  await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'host code');
  await h.ev(lv);
  return { h, code: await h.ev("document.getElementById('lobby-code').textContent"), link: await h.ev("lobbyLink(lobbyState.code)") };
}
async function guestVia(env, link, name, pre) {
  const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl);
  await g.until(ready, 'guest ready');
  await g.ev("localStorage.setItem('pk_name', " + S(name) + "); " + (pre || '') + " true");
  await g.ev("location.href = " + S(link.replace('127.0.0.1', 'localhost')) + "; true");
  await sleep(2500);
  await g.until("typeof lobbyMode !== 'undefined'", 'guest loaded');
  await g.ev(lv);
  return g;
}

(async () => {
  const env = await boot();
  const tabs = [];
  try {
    // B4 attack: a duplicated tab (Chrome copies sessionStorage) opens the same lobby link with the same stored seat token
    const { h, link } = await hostLobby(env, 2, 'Host2'); tabs.push(h);
    const g = await guestVia(env, link, 'Guest2'); tabs.push(g);
    await g.until("!!relaySeatId", 'guest seated');
    const stored = await g.ev("sessionStorage.getItem('pk_lobby_seat')");
    console.log('guest stored seat', stored ? 'present' : 'missing');
    const d = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(d);
    await d.until(ready, 'dup ready');
    await d.ev("sessionStorage.setItem('pk_lobby_seat', " + S(stored) + "), localStorage.setItem('pk_name','Guest2'), true");
    await d.ev("location.href = " + S(link.replace('127.0.0.1', 'localhost')) + "; true");
    await sleep(Number(process.env.WAIT_MS || 9000));
    await d.ev(lv);
    console.log('dup', await d.ev(state + " + ' status=' + (relayClient ? relayClient.state().status : 'none')"));
    console.log('orig', await g.ev("relaySeatId + ' status=' + relayClient.state().status"));
    const dupSeated = await d.ev("!!(relayClient && relaySeatId && relayClient.state().status === 'waiting')");
    if (!dupSeated) bad('B4 dup tab: the copied seat token leaves the duplicate tab without a seat (seat_in_use loop), it never joins afresh'); else ok('dup tab seated');
  } catch (e) { bad(e.message); } finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
