const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
const S = JSON.stringify;
(async () => {
  const env = await boot(); const tabs = [];
  try {
    const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=3'); tabs.push(h);
    await h.until(ready, 'h'); await h.ev("localStorage.setItem('pk_name','HostR'), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
    const link = (await h.ev("lobbyLink(lobbyState.code)")).replace('127.0.0.1', 'localhost');
    const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(g);
    await g.until(ready, 'g'); await g.ev("localStorage.setItem('pk_name','GuestR'), true");
    await g.ev("location.href = " + S(link) + "; true"); await sleep(2500);
    await g.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'g in'); await g.ev(lv);
    await h.ev(click('lobby-lock')); await h.until("__lv().myLocked", 'h lock');
    // the guest sends "take a second place" through its client; the host's Start fires 0 ms later, before the host has seen the new state
    await g.ev("relayClient.move({ claim: 2 }), true");
    await h.ev(click('lobby-start'));
    await sleep(1500);
    await g.ev(click('lobby-lock')); await sleep(5000);
    const st = await h.ev("JSON.stringify({ playing: relayPlaying, seats: lobbyState.seats.map(s => s.seat_id + (s.ai ? '(ai)' : '') + (s.ready ? ':R' : ':-') + ':u' + s.units.length + ':c' + s.claim), begin: lobbyState.begin, wait: document.getElementById('lobby-wait').textContent, start: document.getElementById('lobby-start').textContent, fillers: relayFillers.map(f => f.team + ':' + f.client.state().status) })");
    console.log(st);
    if (!JSON.parse(st).playing) bad('race: computer seat sized from a stale count never locks (or never joins); the room cannot start'); else ok('race: started');
  } catch (e) { bad(e.message); } finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
