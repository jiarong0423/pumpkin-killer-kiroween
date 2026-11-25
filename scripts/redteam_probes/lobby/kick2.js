const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
const S = JSON.stringify;
const st = "JSON.stringify({ lobbyMode, seat: relaySeatId, url: location.search, toast: document.getElementById('lobby-toast').textContent, lobbyHidden: document.getElementById('lobby').hidden, startHidden: document.getElementById('start-screen').classList.contains('hidden'), seats: (lobbyState && lobbyState.seats || []).map(s => s.seat_id + (s.agent ? '(agent of ' + s.invited_by + ')' : '') + (s.ai ? '(ai)' : '') + ':' + (s.name || '')), invites: lobbyState && lobbyState.invites, myInvite: lobbyInvite, box: !document.getElementById('lobby-invite-box').hidden })";
(async () => {
  const env = await boot(); const tabs = [];
  try {
    const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=2'); tabs.push(h);
    await h.until(ready, 'h'); await h.ev("localStorage.setItem('pk_name','HostK'), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
    await h.ev("document.getElementById('lobby-allow-agent').click(), true"); await sleep(300);
    const link = (await h.ev("lobbyLink(lobbyState.code)")).replace('127.0.0.1', 'localhost');
    const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(g);
    await g.until(ready, 'g'); await g.ev("localStorage.setItem('pk_name','GuestK'), true");
    await g.ev("location.href = " + S(link) + "; true"); await sleep(2500);
    await g.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'g in'); await g.ev(lv);
    // guest invites an agent
    await g.until("!document.getElementById('lobby-invite').disabled", 'guest can invite');
    await g.ev(click('lobby-invite')); await g.until("!!lobbyInvite", 'invite');
    const inv = (await g.ev("lobbyLink(lobbyState.code, lobbyInvite)")).replace('localhost', '127.0.0.1');
    // guest cancels, then invites again (cancel path)
    await g.ev(click('lobby-invite-cancel')); await sleep(500);
    console.log('after cancel guest', await g.ev(st));
    const a0 = await tab(env.dbg, inv); tabs.push(a0); await sleep(3000);
    console.log('agent with cancelled ticket', await a0.ev(st));
    await a0.close(); tabs.pop();
    await g.ev(click('lobby-invite')); await g.until("!!lobbyInvite", 'invite 2');
    const inv2 = (await g.ev("lobbyLink(lobbyState.code, lobbyInvite)")).replace('localhost', '127.0.0.1');
    const a = await tab(env.dbg, inv2); tabs.push(a);
    await a.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'agent in', 12000); await a.ev(lv);
    console.log('agent in', await a.ev(st));
    console.log('agent controls', await a.ev("JSON.stringify({ lock: document.getElementById('lobby-lock').disabled, heroes: [...document.querySelectorAll('.hero-pick')].map(b => b.disabled), acts: document.querySelectorAll('.cell-act').length, invite: [document.getElementById('lobby-invite').hidden, document.getElementById('lobby-invite').disabled] })"));
    // the same ticket a second time
    const a2 = await tab(env.dbg, inv2); tabs.push(a2); await sleep(3000);
    console.log('second use of the ticket', await a2.ev(st));
    // the guest (inviter) leaves: the agent is removed
    await g.ev("lobbyLeave(true), true");
    await sleep(2500);
    console.log('agent after inviter left', await a.ev(st));
    console.log('host after inviter left', await h.ev(st));
    // a new guest joins and is kicked by the host
    const g2 = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(g2);
    await g2.until(ready, 'g2'); await g2.send('Page.enable'); await g2.send('Page.addScriptToEvaluateOnNewDocument', { source: "window.__toasts = []; document.addEventListener('DOMContentLoaded', () => { const el = document.getElementById('lobby-toast'); if (el) new MutationObserver(() => { if (el.textContent) window.__toasts.push(el.textContent); }).observe(el, { childList: true, characterData: true, subtree: true }); });" }); await g2.ev("location.href = " + S(link) + "; true"); await sleep(2500);
    await g2.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'g2 in');
    await h.until("document.querySelectorAll('.cell-kick').length > 0", 'kick btn');
    await h.ev("document.querySelector('.cell-kick').click(), true"); await sleep(300); await h.ev("document.querySelector('.cell-kick').click(), true");
    await sleep(2500);
    console.log('kicked guest', await g2.ev(st), await g2.ev('JSON.stringify(window.__toasts)'));
    console.log('host after kick', await h.ev(st));
    for (const t of tabs) { const e = t.errors.filter(x => !/favicon|ResizeObserver/.test(x)); if (e.length) bad('page errors: ' + e.slice(0, 3).join(' | ')); }
  } catch (e) { bad(e.message); for (const t of tabs) { try { console.log(await t.ev(st)); } catch (_) {} } }
  finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
