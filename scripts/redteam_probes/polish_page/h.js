#!/usr/bin/env node
'use strict';
// First-turn hint and the paused turn timer. Usage: node h.js local|daily|lobby|nostore
const { tab, click, lv, ready, boot, sleep } = require('./base.js');
const which = process.argv[2] || 'local';
const S = x => JSON.stringify(x);
const hs = "JSON.stringify({ hint: !document.getElementById('first-hint').hidden, turn, timer: +turnTimer.toFixed(2), human: isHumanTurn(), seen: localStorage.getItem('pk_hint_seen'), coin: !document.getElementById('coin-toss').hidden, matchStarted, relayPlaying: typeof relayPlaying !== 'undefined' && relayPlaying })";
const watchHint = "(window.__hintShows = 0, new MutationObserver(() => { if (!document.getElementById('first-hint').hidden) window.__hintShows++; }).observe(document.getElementById('first-hint'), { attributes: true }), true)";

(async () => {
  const env = await boot(); const tabs = [];
  try {
    if (which === 'local' || which === 'daily' || which === 'nostore') {
      const p = await tab(env.dbg, env.base + '/index.html?team=1'); tabs.push(p);
      await p.until(ready, 'ready');
      if (which === 'nostore') await p.ev("(Storage.prototype.setItem = function () { throw new Error('blocked'); }, true)");
      await p.ev("localStorage.removeItem && localStorage.removeItem('pk_hint_seen'), true"); await p.ev(watchHint);
      for (let round = 0; round < (which === 'nostore' ? 2 : 1); round++) {
        await p.ev(which === 'daily' ? "document.getElementById('daily-btn').click(), true" : "document.getElementById('start-go').click(), true");
        await sleep(300);
        console.log('during coin call', await p.ev(hs));
        await p.ev("(() => { const h = document.getElementById('coin-call-heads'); if (h && !document.getElementById('coin-call').hidden) h.click(); return true; })()");
        await sleep(2700);
        const a = await p.ev(hs); await sleep(3000); const b = await p.ev(hs);
        console.log('after toss', a); console.log('+3 s     ', b);
        await sleep(11500); console.log('+15 s    ', await p.ev(hs)); await sleep(2000); console.log('+17 s    ', await p.ev(hs));
        console.log('hint shows', await p.ev("__hintShows"));
        if (which === 'nostore') { await p.ev("resetGame(), showStartScreen(), true"); await sleep(800); }
      }
    }
    if (which === 'lobby') {   // 1v1 lobby, two humans
      const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=1'); tabs.push(h);
      await h.until(ready, 'h'); await h.ev("localStorage.setItem('pk_name','A'); localStorage.removeItem('pk_hint_seen'); true"); await h.ev(watchHint);
      await h.ev("document.getElementById('friends-btn').click(), true");
      await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
      const link = await h.ev("lobbyLink(lobbyState.code)");
      const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(g);
      await g.until(ready, 'g'); await g.ev("localStorage.setItem('pk_name','B'); localStorage.removeItem('pk_hint_seen'); true");
      await g.ev("location.href = " + S(link.replace('127.0.0.1', 'localhost')) + "; true"); await sleep(2500);
      await g.until("typeof lobbyMode !== 'undefined' && !!relaySeatId", 'g seated'); await g.ev(lv); await g.ev(watchHint);
      await h.ev(click('lobby-lock')); await g.ev(click('lobby-lock'));
      await h.until("__lv().myLocked", 'h'); await g.until("__lv().myLocked", 'g');
      await h.ev(click('lobby-start')); await h.until("relayPlaying", 'match', 15000); await g.until("relayPlaying", 'g match', 5000);
      const a1 = await h.ev(hs), b1 = await g.ev(hs); await sleep(3000);
      console.log('A start', a1, '\nB start', b1); console.log('A +3 s ', await h.ev(hs)); console.log('B +3 s ', await g.ev(hs));
      await sleep(13500); console.log('A +16.5', await h.ev(hs)); console.log('B +16.5', await g.ev(hs));
      console.log('shows A/B', await h.ev("__hintShows"), await g.ev("__hintShows"));
    }
    for (const t of tabs) if (t.errors.length) console.log('PAGE ERRORS', JSON.stringify(t.errors));
  } catch (e) { console.log('SCENARIO ERROR', e.message); for (const t of tabs) if (t.errors.length) console.log('PAGE ERRORS', JSON.stringify(t.errors)); }
  finally { for (const t of tabs) await t.close(); env.stop(); }
})();
