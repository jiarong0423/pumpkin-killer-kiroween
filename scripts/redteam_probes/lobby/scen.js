#!/usr/bin/env node
'use strict';
// Red-team B scenarios against the lobby. Usage: node scen.js A|B|C|D|E|F|G
const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
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
    if (which === 'A') {   // 1v1 lobby link opened by a browser whose last team size was 3
      const { h, link } = await hostLobby(env, 1, 'Host1'); tabs.push(h);
      console.log('link', link);
      const g = await guestVia(env, link, 'Guest1', "localStorage.setItem('pk_team_n','3');"); tabs.push(g);
      await sleep(1500);
      console.log('guest', await g.ev(state));
      console.log('host ', await h.ev(state));
      const seated = await g.ev("!!relaySeatId && (lobbyState && lobbyState.seats || []).some(s => s.seat_id === relaySeatId)");
      if (!seated) bad('A: guest with pk_team_n=3 is not seated in the 1v1 lobby after the team-size reload'); else ok('A: guest seated');
    }
    if (which === 'B') {   // 1v1 guest refreshes the lobby tab
      const { h, link } = await hostLobby(env, 1, 'Host1'); tabs.push(h);
      const g = await guestVia(env, link, 'Guest1', "localStorage.setItem('pk_team_n','1');"); tabs.push(g);
      await g.until("!!relaySeatId", 'guest seated');
      console.log('before reload guest', await g.ev(state));
      await g.send('Page.reload', {});
      await sleep(3000); await g.until(ready, 'reloaded');
      await sleep(1500); await g.ev(lv);
      console.log('after reload guest', await g.ev(state));
      console.log('host', await h.ev(state));
      const seated = await g.ev("!!relaySeatId");
      if (!seated) bad('B: 1v1 guest cannot get back into the lobby after a refresh'); else ok('B: guest back');
    }
    if (which === 'C') {   // 2v2: start with computer fill, guest leaves during the countdown, host presses start again
      const { h, link } = await hostLobby(env, 2, 'Host2'); tabs.push(h);
      const g = await guestVia(env, link, 'Guest2'); tabs.push(g);
      await g.until("!!relaySeatId", 'guest seated'); await h.until("__lv().count.seated === 2", 'two seated');
      await h.ev(click('lobby-lock')); await g.ev(click('lobby-lock'));
      await h.until("__lv().myLocked", 'h locked'); await g.until("__lv().myLocked", 'g locked');
      await h.ev(click('lobby-start'));
      await h.until("!document.getElementById('lobby-countdown').hidden", 'countdown');
      await g.ev("lobbyLeave(true), true");   // the guest presses Leave during the countdown
      await sleep(800);
      console.log('host after guest left', await h.ev(state));
      // host presses start (cancel) and start again, as a user would
      if (await h.ev("__lv().start.pressed")) { await h.ev(click('lobby-start')); await sleep(500); }
      await h.ev(click('lobby-start')); await sleep(6000);
      console.log('host after re-start', await h.ev(state));
      if (!(await h.ev("relayPlaying"))) bad('C: the host cannot start again: the place the guest left is never filled, start stays pressed'); else ok('C: started');
    }
    if (which === 'D') {   // double tap on Start and on Lock
      const { h } = await hostLobby(env, 2, 'Host2'); tabs.push(h);
      await h.ev("(() => { const b = document.getElementById('lobby-lock'); b.click(); return true; })()");
      await h.until("__lv().myLocked", 'locked');
      // two taps 120 ms apart on Start
      await h.ev("(async () => { const b = document.getElementById('lobby-start'); b.click(); await new Promise(r => setTimeout(r, 120)); b.click(); return true; })()");
      await sleep(5000);
      console.log('host after double tap on start', await h.ev(state));
      if (!(await h.ev("relayPlaying"))) bad('D: a double tap on Start (120 ms) cancels the start'); else ok('D: start survived a double tap');
      const h2 = (await hostLobby(env, 2, 'HostL')).h; tabs.push(h2);
      await h2.ev("(async () => { const b = document.getElementById('lobby-lock'); b.click(); await new Promise(r => setTimeout(r, 120)); b.click(); return true; })()");
      await sleep(1500);
      console.log('lock after double tap', await h2.ev("__lv().myLocked"));
      if (!(await h2.ev("__lv().myLocked"))) bad('D2: a double tap on Lock (120 ms) leaves the hero unlocked'); else ok('D2: lock ok');
    }
    if (which === 'E') {   // host leaves the room after a match; guest presses "Back to lobby"
      const { h, link } = await hostLobby(env, 2, 'Host2'); tabs.push(h);
      const g = await guestVia(env, link, 'Guest2'); tabs.push(g);
      await g.until("!!relaySeatId", 'guest seated'); await h.until("__lv().count.seated === 2", 'two');
      await h.ev(click('lobby-lock')); await g.ev(click('lobby-lock'));
      await h.until("__lv().myLocked", 'h'); await g.until("__lv().myLocked", 'g');
      await h.ev(click('lobby-start'));
      for (const p of [h, g]) await p.until("relayPlaying && matchStarted", 'match', 15000);
      await h.ev("gameOver = 'player', turn = 'over', lobbyAfterMatch(false), true");   // host: Leave room
      await sleep(1000);
      await g.ev("gameOver = 'ai', turn = 'over', lobbyAfterMatch(true), true");   // guest: Back to lobby
      await sleep(3000);
      console.log('guest', await g.ev(state));
      if (await g.ev("document.getElementById('lobby').hidden")) bad('E: after the host left a finished match, the guest\'s Back to lobby only says "waiting for the host" for ever'); else ok('E: guest back in lobby');
    }
    if (which === 'F') {   // host refreshes its lobby tab
      const { h, link, code } = await hostLobby(env, 2, 'Host2'); tabs.push(h);
      const g = await guestVia(env, link, 'Guest2'); tabs.push(g);
      await g.until("!!relaySeatId", 'guest seated');
      await h.send('Page.reload', {}); await sleep(3000); await h.until(ready, 'reloaded');
      await sleep(1000);
      console.log('host after reload', await h.ev("JSON.stringify({ lobbyMode, url: location.search, lobbyHidden: document.getElementById('lobby').hidden })"));
      await g.ev(lv);
      console.log('guest', await g.ev(state));
      if (!(await h.ev("lobbyMode"))) bad('F: the host refreshes the lobby tab and lands on the first page: the room ' + code + ' is lost to them; guest still sees the host for the grace period'); else ok('F');
    }
    if (which === 'G') {   // 3v3: AI fill, cancel, guest releases a place, host presses start again
      const { h, link } = await hostLobby(env, 3, 'Host3'); tabs.push(h);
      const g = await guestVia(env, link, 'Guest3'); tabs.push(g);
      await g.until("!!relaySeatId", 'guest seated');
      await g.ev("(() => { const b = [...document.querySelectorAll('.cell-act')].find(x => x.closest('#lobby-cells-' + __lv().myTeam) && /Sit|坐|Take|take|Play this|操控/i.test(x.textContent)); if (b) b.click(); return !!b; })()");
      await g.until("__lv().myClaim === 2", 'guest holds two');
      await h.ev(click('lobby-lock')); await g.ev(click('lobby-lock'));
      await h.until("__lv().myLocked", 'h'); await g.until("__lv().myLocked", 'g');
      await h.ev(click('lobby-start')); await sleep(450); await h.ev(click('lobby-start'));   // start, then cancel during the countdown (two deliberate presses, 450 ms apart: the page's double-tap guard is 350 ms)
      await sleep(800);
      console.log('host after cancel', await h.ev(state));
      await g.ev(click('lobby-lock')); await sleep(300);
      await g.ev("(() => { const b = [...document.querySelectorAll('.cell-act')].find(x => /Give|放|release|Leave|Free/i.test(x.textContent)); if (b) b.click(); return !!b; })()");
      await sleep(500); await g.ev(click('lobby-lock')); await sleep(500);
      await h.ev(click('lobby-start')); await sleep(6000);
      console.log('host after second start', await h.ev(state));
      if (!(await h.ev("relayPlaying"))) bad('G: once the computer filled, a place freed later is never filled: start pressed, no countdown'); else ok('G: started');
    }
    for (const t of tabs) { const e = t.errors.filter(x => !/favicon|ResizeObserver/.test(x)); if (e.length) console.log('page errors:', e.slice(0, 3).join(' | ')); }
  } catch (e) { bad(which + ': ' + e.message); for (const t of tabs) { try { console.log('state', await t.ev(state)); } catch (_) {} } }
  finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
