#!/usr/bin/env node
'use strict';
// Red team of the uncommitted lobby changes. Usage: node s.js <scenario>
const { tab, click, lv, ready, boot, sleep } = require('./base.js');
const which = process.argv[2] || 'own';
const S = x => JSON.stringify(x);
const st = "JSON.stringify({ lobbyMode, seat: relaySeatId, code: lobbyState && lobbyState.code, rc: relayRoomCode, TEAM_N, url: location.search, toast: document.getElementById('lobby-toast').hidden ? '' : document.getElementById('lobby-toast').textContent, lobbyHidden: document.getElementById('lobby').hidden, seats: (lobbyState && lobbyState.seats || []).map(s => s.seat_id + ':' + s.team + ':' + (s.name||'') + (s.ai?':ai':'') + (s.ready?':R':'') + ':' + (s.units||[]).join('+') + ':c' + s.claim), started: lobbyState && lobbyState.started, picks: lobbyPicks, start: document.getElementById('lobby-start').textContent, wait: document.getElementById('lobby-wait').textContent, fillers: relayFillers.map(f => f.team + ':' + f.heroes.join('+') + ':' + f.seatId), matchStarted, relayPlaying, startHidden: document.getElementById('start-screen').classList.contains('hidden'), friendsOpen: document.getElementById('start-screen').classList.contains('seats-open'), roomStatus: (document.getElementById('room-status')||{}).textContent, sideChooser: !(document.getElementById('side-chooser')||{hidden:true}).hidden })";
const toasts = "(window.__toasts = [], (() => { const el = document.getElementById('lobby-toast'); new MutationObserver(() => { if (!el.hidden) window.__toasts.push(el.textContent); }).observe(el, { childList: true, attributes: true, characterData: true, subtree: true }); })(), true)";

async function host(env, n, name) {
  const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=' + n);
  await h.until(ready, 'host ready');
  await h.ev("localStorage.setItem('pk_name', " + S(name) + "), true");
  await h.ev(toasts);
  await h.ev("document.getElementById('friends-btn').click(), true");
  await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'host code');
  await h.ev(lv);
  return { h, code: await h.ev("document.getElementById('lobby-code').textContent"), link: await h.ev("lobbyLink(lobbyState.code)") };
}
async function guest(env, link, name, pre) {
  const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl);
  await g.until(ready, 'guest ready');
  await g.ev("localStorage.setItem('pk_name', " + S(name) + "); " + (pre || '') + " true");
  await g.ev("location.href = " + S(link.replace('127.0.0.1', 'localhost')) + "; true");
  await sleep(2500);
  await g.until("typeof lobbyMode !== 'undefined' && !!relaySeatId", 'guest seated');
  await g.ev(lv); await g.ev(toasts);
  return g;
}
const joinCode = (p, code) => p.ev("(document.getElementById('lobby-join-code').click(), document.getElementById('join-code-input').value = " + S(code) + ", document.getElementById('join-code-ok').click(), true)");

(async () => {
  const env = await boot(); const tabs = [];
  try {
    if (which === 'own') {   // host alone presses Join code with its own room's code
      const { h, code } = await host(env, 2, 'Host'); tabs.push(h);
      console.log('before', await h.ev(st));
      await joinCode(h, code); await sleep(2500);
      console.log('after own code', await h.ev(st)); console.log('toasts', await h.ev("JSON.stringify(__toasts)"));
    }
    if (which === 'ownguest') {   // host with a guest: host joins own code
      const { h, code, link } = await host(env, 2, 'Host'); tabs.push(h);
      const g = await guest(env, link, 'Guest'); tabs.push(g);
      await joinCode(h, code); await sleep(2500);
      console.log('host after', await h.ev(st)); console.log('guest after', await g.ev(st));
    }
    if (which === 'unknown') {   // a code nobody uses, with a guest waiting in the old room
      const { h, link } = await host(env, 2, 'Host'); tabs.push(h);
      const g = await guest(env, link, 'Guest'); tabs.push(g);
      await joinCode(g, 'ZZZZZZ'); await sleep(2500);
      console.log('guest after unknown', await g.ev(st)); console.log('toasts', await g.ev("JSON.stringify(__toasts)"));
      console.log('host', await h.ev(st));
      console.log('guest buttons', await g.ev("JSON.stringify(['lobby-lock','lobby-start','lobby-join-code','lobby-leave','lobby-copy'].map(id => id + ':' + document.getElementById(id).disabled))"));
    }
    if (which === 'started') {   // a code of a room whose match runs
      const a = await host(env, 1, 'A'); tabs.push(a.h);
      const b = await guest(env, a.link, 'B'); tabs.push(b);
      await a.h.ev(click('lobby-lock')); await b.ev(click('lobby-lock'));
      await a.h.until("__lv().myLocked", 'a locked'); await b.until("__lv().myLocked", 'b locked');
      await a.h.ev(click('lobby-start')); await a.h.until("relayPlaying", 'match', 15000);
      const c = await host(env, 1, 'C'); tabs.push(c.h);
      await joinCode(c.h, a.code); await sleep(2500);
      console.log('C after started code', await c.h.ev(st)); console.log('toasts', await c.h.ev("JSON.stringify(__toasts)"));
    }
    if (which === 'size') {   // a 1v1 room's code typed on a 3v3 lobby page
      const a = await host(env, 1, 'A'); tabs.push(a.h);
      const c = await host(env, 3, 'C'); tabs.push(c.h);
      await joinCode(c.h, a.code); await sleep(5000);
      await c.h.until(ready, 'reloaded'); await sleep(2500);
      console.log('C after size code', await c.h.ev(st));
      console.log('A', await a.h.ev(st));
    }
    if (which === 'lower') {
      const a = await host(env, 2, 'A'); tabs.push(a.h);
      const c = await host(env, 2, 'C'); tabs.push(c.h);
      for (const v of [' ' + a.code.toLowerCase(), a.code.slice(0, 3) + ' ' + a.code.slice(3), a.link]) {
        await c.h.ev("(document.getElementById('lobby-join-code').click(), true)");
        const typed = await c.h.ev("(() => { const i = document.getElementById('join-code-input'); i.focus(); document.execCommand('insertText', false, " + S(v) + "); return i.value; })()");
        await c.h.ev("document.getElementById('join-code-ok').click(), true"); await sleep(300);
        console.log(S(v.slice(0, 40)), '-> field', S(typed), 'err shown', await c.h.ev("!document.getElementById('join-code-error').hidden"), 'dialog open', await c.h.ev("!document.getElementById('join-code-dialog').hidden"));
        await c.h.ev("document.getElementById('join-code-dialog').hidden = true, true");
      }
      await c.h.ev("(document.getElementById('lobby-join-code').click(), document.getElementById('join-code-input').value = " + S(a.code.toLowerCase()) + ", document.getElementById('join-code-ok').click(), true)"); await sleep(2500);
      console.log('lowercase join', await c.h.ev(st));
    }
    if (which === 'double') {   // Enter twice (key repeat) and OK twice in one tick
      const a = await host(env, 2, 'A'); tabs.push(a.h);
      const c = await host(env, 2, 'C'); tabs.push(c.h);
      await c.h.ev("(document.getElementById('lobby-join-code').click(), document.getElementById('join-code-input').value = " + S(a.code) + ", true)");
      await c.h.ev("(() => { const i = document.getElementById('join-code-input'); for (let k = 0; k < 2; k++) i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, repeat: k > 0 })); return true; })()");
      await sleep(3000);
      console.log('C after double', await c.h.ev(st)); console.log('A after', await a.h.ev(st));
      console.log('C toasts', await c.h.ev("JSON.stringify(__toasts)"));
    }
    if (which === 'ime') {   // Safari/old WebKit Enter that commits IME: keyCode 229, isComposing false
      const a = await host(env, 2, 'A'); tabs.push(a.h);
      await a.h.ev("(document.getElementById('lobby-join-code').click(), document.getElementById('join-code-input').value = 'ab', true)");
      await a.h.ev("(() => { const e = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }); Object.defineProperty(e, 'keyCode', { get: () => 229 }); document.getElementById('join-code-input').dispatchEvent(e); return true; })()");
      console.log('err shown after IME-commit Enter', await a.h.ev("!document.getElementById('join-code-error').hidden"));
    }
    if (which === 'countdown') {   // guest presses Join code (to an unrelated room) during the countdown
      const a = await host(env, 1, 'A'); tabs.push(a.h);
      const b = await guest(env, a.link, 'B'); tabs.push(b);
      const c = await host(env, 1, 'C'); tabs.push(c.h);
      await a.h.ev(click('lobby-lock')); await b.ev(click('lobby-lock'));
      await a.h.until("__lv().myLocked", 'a'); await b.until("__lv().myLocked", 'b');
      await a.h.ev(click('lobby-start')); await b.until("!document.getElementById('lobby-countdown').hidden", 'countdown');
      console.log('join-code disabled in countdown', await b.ev("document.getElementById('lobby-join-code').disabled"));
      await joinCode(b, c.code); await sleep(6000);
      console.log('A', await a.h.ev(st)); console.log('B', await b.ev(st)); console.log('C', await c.h.ev(st));
    }
    if (which === 'stack') {   // join dialog over QR, then rename: what is on top
      const a = await host(env, 2, 'A'); tabs.push(a.h);
      await a.h.ev("document.getElementById('lobby-code').click(), true");
      await a.h.ev("document.getElementById('lobby-join-code').click(), true");
      console.log(await a.h.ev("JSON.stringify({ qr: !document.getElementById('lobby-qr').hidden, join: !document.getElementById('join-code-dialog').hidden, top: (() => { const e = document.elementFromPoint(innerWidth/2, innerHeight/2); return e.id || e.className || e.tagName; })(), active: document.activeElement.id })"));
      await a.h.ev("(() => { const i = document.getElementById('join-code-input'); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); return true; })()");
      console.log('after Esc', await a.h.ev("JSON.stringify({ qr: !document.getElementById('lobby-qr').hidden, join: !document.getElementById('join-code-dialog').hidden, top: (() => { const e = document.elementFromPoint(innerWidth/2, innerHeight/2); return e.id || e.tagName; })() })"));
    }
    if (which === 'filler') {   // 2v2 host alone, never locked, picks the hero the computer filler will take, presses Start
      const { h } = await host(env, 2, 'Host'); tabs.push(h);
      const want = await h.ev("(() => { const pool = Object.keys(HERO_PROFILES); let seed = 0; for (let i = 0; i < relayRoomCode.length; i++) seed = (seed * 31 + relayRoomCode.charCodeAt(i)) >>> 0; return pool[seed % pool.length]; })()");
      await h.ev("lobbyPicks[0] = " + S(want) + ", lobbyRender(), true");
      console.log('host picks', want, await h.ev("JSON.stringify(lobbyPicks)"));
      await h.ev(click('lobby-start')); await sleep(9000);
      console.log('host after start', await h.ev(st)); console.log('toasts', await h.ev("JSON.stringify(__toasts)"));
    }
    if (which === 'samehero') {   // 3v3: two humans on red pick the same hero and lock at the same moment
      const { h, link } = await host(env, 3, 'Host'); tabs.push(h);
      const g = await guest(env, link, 'Guest'); tabs.push(g);
      await sleep(500);
      const gteam = await g.ev("(lobbyState.seats.find(s => s.seat_id === relaySeatId) || {}).team");
      const hteam = await h.ev("(lobbyState.seats.find(s => s.seat_id === relaySeatId) || {}).team");
      if (gteam !== hteam) { await g.ev("relayClient.move({ team: " + S(hteam) + " }), true"); await sleep(800); }
      console.log('teams', hteam, await g.ev("(lobbyState.seats.find(s => s.seat_id === relaySeatId) || {}).team"));
      await h.ev("lobbyPicks[0] = 'knight', lobbyRender(), true"); await g.ev("lobbyPicks[0] = 'knight', lobbyRender(), true");
      await Promise.all([h.ev(click('lobby-lock')), g.ev(click('lobby-lock'))]);
      await sleep(1500);
      console.log('host', await h.ev(st)); console.log('host toasts', await h.ev("JSON.stringify(__toasts)"));
      console.log('guest', await g.ev(st)); console.log('guest toasts', await g.ev("JSON.stringify(__toasts)"));
      console.log('guest lock label/disabled', await g.ev("document.getElementById('lobby-lock').textContent + '/' + document.getElementById('lobby-lock').disabled"), 'hero btn', await g.ev("document.getElementById('lobby-heroes').textContent"));
      await g.ev(click('lobby-lock')); await sleep(1000);
      console.log('guest after 2nd lock', await g.ev(st));
    }
    if (which === 'unlockhold') {   // a mate locks knight, unlocks and wants archer: is knight still blocked for me?
      const { h, link } = await host(env, 3, 'Host'); tabs.push(h);
      const g = await guest(env, link, 'Guest'); tabs.push(g);
      const hteam = await h.ev("(lobbyState.seats.find(s => s.seat_id === relaySeatId) || {}).team");
      await g.ev("relayClient.move({ team: " + S(hteam) + " }), true"); await sleep(800);
      await h.ev("lobbyPicks[0] = 'knight', lobbyRender(), true"); await h.ev(click('lobby-lock')); await sleep(600);
      await h.ev(click('lobby-lock')); await sleep(600);   // unlock
      await h.ev("lobbyPicks[0] = 'bat', lobbyRender(), true");
      console.log('host unlocked, local pick bat', await h.ev(st));
      console.log('guest picks / can guest choose knight?', await g.ev("JSON.stringify({ picks: lobbyPicks, taken: LobbyModel.takenByMates(lobbyState, relaySeatId) })"));
      await g.ev("lobbyPicks[0] = 'knight', true"); await g.ev(click('lobby-lock')); await sleep(800);
      console.log('guest after forced knight lock', await g.ev(st), await g.ev("JSON.stringify(__toasts)"));
    }
    for (const t of tabs) if (t.errors.length) console.log('PAGE ERRORS', JSON.stringify(t.errors));
  } catch (e) { console.log('SCENARIO ERROR', e.message); for (const t of tabs) if (t.errors.length) console.log('PAGE ERRORS', JSON.stringify(t.errors)); }
  finally { for (const t of tabs) await t.close(); env.stop(); }
})();
