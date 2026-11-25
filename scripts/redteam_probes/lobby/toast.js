const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
const S = JSON.stringify;
const HOOK = "window.__toasts = []; document.addEventListener('DOMContentLoaded', () => { const el = document.getElementById('lobby-toast'); if (el) new MutationObserver(() => { if (el.textContent) window.__toasts.push(el.textContent); }).observe(el, { childList: true, characterData: true, subtree: true }); });";
(async () => {
  const env = await boot(); const tabs = [];
  try {
    const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=2'); tabs.push(h);
    await h.until(ready, 'h'); await h.ev("localStorage.setItem('pk_name','HostK'), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
    const link = (await h.ev("lobbyLink(lobbyState.code)")).replace('127.0.0.1', 'localhost');
    const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(g);
    await g.until(ready, 'g'); await g.ev("localStorage.setItem('pk_name','GuestK'), true");
    await g.send('Page.enable'); await g.send('Page.addScriptToEvaluateOnNewDocument', { source: HOOK });
    await g.ev("location.href = " + S(link) + "; true"); await sleep(3000);
    await g.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'g in');
    console.log('guest toasts after join', await g.ev("JSON.stringify(window.__toasts)"));
    await h.until("document.querySelectorAll('.cell-kick').length > 0", 'kick btn');
    await h.ev("document.querySelector('.cell-kick').click(), true"); await sleep(400);
    await h.ev("document.querySelector('.cell-kick').click(), true"); await sleep(2500);
    console.log('guest toasts after kick', await g.ev("JSON.stringify(window.__toasts)"), await g.ev("JSON.stringify({lobbyMode, url: location.search, start: !document.getElementById('start-screen').classList.contains('hidden')})"));
    console.log('host', await h.ev("JSON.stringify((lobbyState.seats||[]).map(s=>s.seat_id))"));
    for (const t of tabs) { const e = t.errors.filter(x => !/favicon|ResizeObserver/.test(x)); if (e.length) bad('page errors: ' + e.slice(0, 3).join(' | ')); }
  } catch (e) { bad(e.message); } finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
