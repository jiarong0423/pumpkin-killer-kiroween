const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
(async () => {
  const env = await boot(); let h;
  try {
    h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=3');
    await h.until(ready, 'ready');
    const NAME = process.argv[2] || '﷽'.repeat(10);
    await h.ev("localStorage.setItem('pk_name', " + JSON.stringify(NAME) + "), true");
    await h.ev("document.getElementById('friends-btn').click(), true");
    await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code');
    await h.ev(lv);
    await h.ev(click('lobby-lock')); await h.until("__lv().myLocked", 'locked');
    await h.ev(click('lobby-start'));
    await h.until("relayPlaying && matchStarted", 'match', 15000);
    await sleep(1500);
    const r = JSON.parse(await h.ev(`(() => { const c = document.getElementById('gameCanvas').getContext('2d'); c.save(); c.font = 'bold ' + Math.round(22 * uiScale()) + 'px' + FONT_BODY;
      const us = allUnits().map(u => ({ id: u.id, x: Math.round(u.x), label: unitNameLabel(u), w: Math.round(Math.min(170, c.measureText(unitNameLabel(u)).width)) }   /* the page draws the name with maxWidth 170 (red team B8 fix) */)); c.restore();
      return JSON.stringify({ stored: lobbyName(), us }); })()`));
    console.log(JSON.stringify(r));
    const left = r.us.filter(u => /^left/.test(u.id)).sort((a, b) => a.x - b.x);
    for (let i = 1; i < left.length; i++) { const gap = left[i].x - left[i - 1].x, need = (left[i].w + left[i - 1].w) / 2; console.log('pair', left[i - 1].id, left[i].id, 'gap', gap, 'half-widths', need, need > gap ? 'OVERLAP' : 'ok'); }
    const me = r.us.find(u => u.label === r.stored);
    if (me && me.w > 400) bad('long-glyph name draws ' + me.w + ' px wide above the head (no maxWidth)'); else ok('name width ' + (me && me.w));
    const shot = await h.send('Page.captureScreenshot', { format: 'png' }); require('fs').writeFileSync(__dirname + '/names_shot.png', Buffer.from(shot.result.data, 'base64'));
    console.log('errors', h.errors);
  } catch (e) { bad(e.message); } finally { if (h) await h.close(); env.stop(); }
  process.exit(0);
})();
