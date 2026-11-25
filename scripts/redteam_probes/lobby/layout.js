const { tab, click, lv, ready, boot, sleep, ok, bad } = require('./base.js');
const VIEWS = [[667, 375], [740, 360], [812, 375], [844, 390], [923, 415]];
const MEASURE = `(ids) => { const out = []; for (const id of ids) { const el = document.getElementById(id); if (!el) { out.push(id + ' missing'); continue; } const t = el.type === 'checkbox' ? el.closest('label') : el; if (t.closest('[hidden]')) { out.push(id + ' hidden'); continue; } const r = t.getBoundingClientRect();
  if (r.width < 1 || r.left < -0.5 || r.top < -0.5 || r.right > innerWidth + 0.5 || r.bottom > innerHeight + 0.5) { out.push(id + ' outside ' + [r.left, r.top, r.right, r.bottom].map(Math.round)); continue; }
  const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); if (!hit || !(t === hit || t.contains(hit))) out.push(id + ' covered by ' + (hit ? hit.tagName + '#' + hit.id : 'nothing')); } return out; }`;
(async () => {
  const env = await boot(); let p;
  const lang = process.argv[2] || 'en';
  try {
    p = await tab(env.dbg, 'about:blank');
    for (const [w, h] of VIEWS) {
      await p.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: true });
      await p.send('Page.navigate', { url: env.base + '/index.html?relay=' + env.relayUrl + '&team=3' });
      await sleep(400); await p.until(ready, 'ready');
      await p.ev("localStorage.setItem('pk_name', 'WWWWWWWWWW'); localStorage.setItem('pk_lang', '" + lang + "'); I18N.setLang('" + lang + "'); I18N.apply(document); true");
      await p.ev("document.getElementById('friends-btn').click(), true");
      await p.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await p.ev(lv);
      await p.ev("(() => { const el = document.getElementById('lobby-allow-agent'); if (!el.checked) el.click(); return true; })()");
      await p.until("!document.getElementById('lobby-invite').hidden && !document.getElementById('lobby-invite').disabled", 'invite btn');
      await p.ev(click('lobby-invite'));
      await p.until("!document.getElementById('lobby-invite-box').hidden", 'invite box');
      await sleep(200);
      const ids = ['lobby-code', 'lobby-copy', 'lobby-refresh', 'lobby-leave', 'lobby-rename', 'lobby-lock', 'lobby-allow-ai', 'lobby-allow-agent', 'lobby-start', 'lobby-invite-copy', 'lobby-invite-cancel'];
      const miss = await p.ev('(' + MEASURE + ')(' + JSON.stringify(ids) + ')');
      const cells = await p.ev("[...document.querySelectorAll('#lobby .lobby-cell')].map(c => { const r = c.getBoundingClientRect(), b = c.closest('.lobby-team').getBoundingClientRect(); return r.bottom > b.bottom + 0.5 || r.bottom > innerHeight + 0.5 || r.height < 12 ? 'cut' : 'ok'; }).join(',')");
      const sw = await p.ev("document.documentElement.scrollWidth + '/' + innerWidth");
      // QR dialog and name dialog
      await p.ev(click('lobby-code')); await sleep(150);
      const qr = await p.ev('(' + MEASURE + ')(["lobby-qr-close"])');
      await p.ev(click('lobby-qr-close'));
      await p.ev(click('lobby-rename')); await sleep(150);
      const nd = await p.ev('(' + MEASURE + ')(["name-input","name-ok","name-cancel"])');
      await p.ev(click('name-cancel'));
      const tag = lang + ' ' + w + 'x' + h;
      const all = miss.concat(qr, nd);
      if (all.length || /cut/.test(cells)) bad(tag + ' invite box open: ' + all.join('; ') + ' cells ' + cells + ' sw ' + sw + ' rows ' + await p.ev("JSON.stringify(['lobby-bar','lobby-teams','lobby-mine','lobby-invite-box','lobby-foot'].map(id => { const el = document.getElementById(id), r = el.getBoundingClientRect(); return (id === 'lobby-invite-box' ? [...el.children].map(k => k.id + '=' + Math.round(k.getBoundingClientRect().height) + 'x' + Math.round(k.getBoundingClientRect().width)).join(',') + ' ' : '') + id + ':' + Math.round(r.top) + '+' + Math.round(r.height); }))"));
      else ok(tag + ' invite box open: all controls hit, cells ' + cells + ' sw ' + sw);
      if (w === 667) { const s = await p.send('Page.captureScreenshot', { format: 'png' }); require('fs').writeFileSync(__dirname + '/layout_' + lang + '_667.png', Buffer.from(s.result.data, 'base64')); }
      await p.ev("lobbyLeave(true), true");
    }
    console.log('errors', p.errors);
  } catch (e) { bad(e.message); } finally { if (p) await p.close(); env.stop(); }
  process.exit(0);
})();
