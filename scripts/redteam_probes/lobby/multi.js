const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
const S = JSON.stringify;
(async () => {
  const env = await boot(); const tabs = [];
  const n = +(process.argv[2] || 2);
  try {
    const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=' + n); tabs.push(h);
    await h.until(ready, 'h'); await h.ev("localStorage.setItem('pk_name','HostM'), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
    const link = (await h.ev("lobbyLink(lobbyState.code)")).replace('127.0.0.1', 'localhost');
    const g = await tab(env.dbg, env.alt + '/index.html?relay=' + env.relayUrl); tabs.push(g);
    await g.until(ready, 'g'); await g.ev("localStorage.setItem('pk_name','<b>G</b>'), true");
    await g.ev("location.href = " + S(link) + "; true"); await sleep(2500);
    await g.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId", 'g in'); await g.ev(lv);
    for (let round = 1; round <= 3; round++) {
      if (round === 3) {   // guest changes side before the third match
        const before = await g.ev("__lv().myTeam");
        await g.ev("(() => { const b = [...document.querySelectorAll('.cell-act')].find(x => x.closest('#lobby-cells-' + (__lv().myTeam === 'red' ? 'white' : 'red'))); if (b) b.click(); return !!b; })()");
        await g.until("__lv().myTeam !== " + S(before), 'guest switched side');
      }
      await h.until("__lv().count.seated === 2 && (lobbyState.seats||[]).every(s => !s.ai)", 'no AI seats before match ' + round, 12000);
      await h.ev(click('lobby-lock')); await g.ev(click('lobby-lock'));
      await h.until("__lv().myLocked", 'h lock'); await g.until("__lv().myLocked", 'g lock');
      await h.ev(click('lobby-start'));
      for (const p of [h, g]) await p.until("relayPlaying && matchStarted && document.getElementById('lobby').hidden", 'match ' + round, 15000);
      await sleep(800);
      const info = async p => JSON.parse(await p.ev("JSON.stringify({ seat: relaySnap().seat, persp: localPerspective.ownSeat, seats: relaySeats.map(s => s.seat_id + (s.ai ? '(ai)' : '') + ':' + (s.name||'')), labels: allUnits().map(u => u.id + '=' + unitNameLabel(u)), fillers: relayFillers.length })"));
      const hi = await info(h), gi = await info(g);
      console.log('match', round, 'host', S(hi)); console.log('match', round, 'guest', S(gi));
      const ai = hi.seats.filter(s => /\(ai\)/.test(s)).length;
      if (ai !== 2 * n - 2) bad('match ' + round + ': ' + ai + ' AI seats, want ' + (2 * n - 2));
      const wantPersp = gi.seat === 'red' ? 'left' : 'right';
      if (gi.persp !== wantPersp) bad('match ' + round + ': guest seat ' + gi.seat + ' but perspective ' + gi.persp);
      if (!gi.labels.some(l => /HostM/.test(l)) || !hi.labels.some(l => /<b>G<\/b>/.test(l))) bad('match ' + round + ': names missing ' + S(gi.labels));
      await h.ev("gameOver = 'player', turn = 'over', lobbyAfterMatch(true), true");
      for (const p of [h, g]) await p.until("!relayPlaying && !document.getElementById('lobby').hidden && lobbyState && lobbyState.started === false", 'back ' + round, 12000);
    }
    ok('three matches done');
    for (const t of tabs) { const e = t.errors.filter(x => !/favicon|ResizeObserver/.test(x)); if (e.length) bad('page errors: ' + e.slice(0, 3).join(' | ')); }
  } catch (e) { bad(e.message); for (const t of tabs) { try { console.log(await t.ev("JSON.stringify({seat: relaySeatId, seats: (lobbyState&&lobbyState.seats||[]).map(s=>s.seat_id+(s.ai?'(ai)':'')+(s.ready?'R':'')), toast: document.getElementById('lobby-toast').textContent, wait: document.getElementById('lobby-wait').textContent, start: document.getElementById('lobby-start').textContent})")); } catch (_) {} } }
  finally { for (const t of tabs) await t.close(); env.stop(); }
  process.exit(0);
})();
