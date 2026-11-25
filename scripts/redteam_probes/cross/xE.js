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
    // E2 (red-team A cross-check): host leaves a finished match, guest reopens the lobby; can the new host start again?
    const { h, link } = await hostLobby(env, 2, 'Host2'); tabs.push(h);
    const g = await guestVia(env, link, 'Guest2'); tabs.push(g);
    await g.until("!!relaySeatId", 'guest seated'); await h.until("__lv().count.seated === 2", 'two');
    await h.ev(click('lobby-lock')); await g.ev(click('lobby-lock'));
    await h.until("__lv().myLocked", 'h'); await g.until("__lv().myLocked", 'g');
    await h.ev(click('lobby-start'));
    for (const p of [h, g]) await p.until("relayPlaying && matchStarted", 'match', 15000);
    await h.ev("gameOver = 'player', turn = 'over', lobbyAfterMatch(false), true");
    await sleep(1000);
    await g.ev("gameOver = 'ai', turn = 'over', lobbyAfterMatch(true), true");
    await sleep(3000);
    console.log('guest back', await g.ev(state));
    await g.ev(click('lobby-lock')); await sleep(800);
    await g.ev(click('lobby-start'));
    await sleep(Number(process.env.WAIT_MS || 12000));
    console.log('guest after lock+start', await g.ev(state));
    if (!(await g.ev("relayPlaying"))) bad('E2: new host cannot start: the old host\'s computer seats stay in the room unlocked (their browser is gone)'); else ok('E2: rematch started');
  } catch (e) { bad(e.message); } finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
