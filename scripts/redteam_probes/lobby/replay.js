const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
const S = JSON.stringify;
const HOOK = "window.__toasts = []; window.__states = []; document.addEventListener('DOMContentLoaded', () => { const el = document.getElementById('lobby-toast'); if (el) new MutationObserver(() => { if (el.textContent) window.__toasts.push(el.textContent); }).observe(el, { childList: true, characterData: true, subtree: true }); });";
(async () => {
  const env = await boot(); const tabs = [];
  const join = async (name, hook) => { const p = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(p); await p.until(ready, name); await p.ev("localStorage.setItem('pk_name', " + S(name) + "), true"); if (hook) { await p.send('Page.enable'); await p.send('Page.addScriptToEvaluateOnNewDocument', { source: HOOK }); } await p.ev("location.href = " + S(link) + "; true"); await sleep(2500); await p.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", name + ' in'); return p; };
  let link;
  try {
    const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=2'); tabs.push(h);
    await h.until(ready, 'h'); await h.ev("localStorage.setItem('pk_name','Host'), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
    link = (await h.ev("lobbyLink(lobbyState.code)")).replace('127.0.0.1', 'localhost');
    const a = await join('Alice'), c = await join('Carol');
    await a.ev("lobbyLeave(true), true"); await c.ev("lobbyLeave(true), true"); await sleep(800);
    const b = await join('Bob', true); await sleep(1500);
    const toasts = JSON.parse(await b.ev("JSON.stringify(window.__toasts)"));
    console.log('Bob toasts', S(toasts), 'final seats', await b.ev("JSON.stringify(lobbyState.seats.map(s => s.seat_id + ':' + s.name))"));
    if (toasts.some(t => /Alice|Carol/.test(t))) bad('a newcomer is welcomed with the name of a player who already left (replayed old room_state)'); else ok('no stale welcome');
  } catch (e) { bad(e.message); } finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
