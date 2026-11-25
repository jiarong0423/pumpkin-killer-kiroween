const { tab, click, lv, ready, boot, sleep, ok, bad } = require('../lobby/base.js');
(async () => {
  const env = await boot(); let h;
  try {
    h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=2');
    await h.until(ready, 'r'); await h.ev("localStorage.setItem('pk_name','H13'), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
    await h.ev(click('lobby-lock')); await h.until("__lv().myLocked", 'lock');
    await h.ev(click('lobby-start')); await sleep(600); await h.ev(click('lobby-start')); await sleep(600);
    const s1 = await h.ev("JSON.stringify(lobbyState.seats.map(s=>s.seat_id+(s.ai?'(ai)':'')))");
    await h.ev("document.getElementById('lobby-allow-ai').click(), true"); await sleep(2500);
    const s2 = await h.ev("JSON.stringify({ seats: lobbyState.seats.map(s=>s.seat_id+(s.ai?'(ai)':'')), toast: document.getElementById('lobby-toast').textContent, fillers: relayFillers.map(f=>f.seatId+':'+f.client.state().status) })");
    await h.ev("document.getElementById('lobby-allow-ai').click(), true"); await sleep(500);
    await h.ev(click('lobby-start')); await sleep(6000);
    const s3 = await h.ev("JSON.stringify({ playing: relayPlaying, seats: (lobbyState.seats||[]).map(s=>s.seat_id+(s.ai?'(ai)':'')), fillers: relayFillers.map(f=>f.seatId+':'+f.client.state().status), status: (document.getElementById('room-status')||{}).textContent })");
    console.log('after fill+cancel', s1); console.log('after AI off', s2); console.log('after AI on + start', s3);
    // play a few seconds: the AI turn must be taken by a live filler
    console.log(JSON.parse(s3).playing ? 'ok started' : 'FAIL - no start after AI off/on');
    console.log('filler picked per AI seat', await h.ev("JSON.stringify(lobbyState.seats.filter(s=>s.ai).map(s => { const f = relayFillers.find(x => x.team === s.team && x.seatId === s.seat_id); return s.seat_id + '->' + (f ? f.client.state().status : 'none'); }))"));
    const t0 = Date.now(); const seen = new Set();
    while (Date.now() - t0 < 75000) { const r = await h.ev("JSON.stringify({ round: relaySnap().round, phase: relaySnap().phase, over: !!gameOver })"); seen.add(r); await sleep(1000); }
    console.log('phases seen', JSON.stringify([...seen]));
    console.log('errors', JSON.stringify(h.errors));
  } catch (e) { bad(e.message); } finally { if (h) await h.close(); env.stop(); }
  process.exit(0);
})();
