#!/usr/bin/env node
'use strict';
// Layout of the lobby with three hero portraits (3v3, one seat claims 3) at phone sizes, both languages; portraits loaded.
const { tab, lv, ready, boot, sleep, fs } = require('./base.js');
const OUT = __dirname;
(async () => {
  const env = await boot(); const tabs = [];
  try {
    for (const lang of ['en', 'zh-TW']) {
      const h = await tab(env.dbg, env.base + '/index.html?relay=' + env.relayUrl + '&team=3&lang=' + lang); tabs.push(h);
      await h.until(ready, 'ready');
      await h.ev("localStorage.setItem('pk_name','Pumpkin King The Third'); localStorage.setItem('pk_lang'," + JSON.stringify(lang) + "); I18N.setLang(" + JSON.stringify(lang) + "); I18N.apply(document); true");
      await h.ev("document.getElementById('friends-btn').click(), true");
      await h.until("/^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'code'); await h.ev(lv);
      await h.ev("relayClient.move({ claim: 3 }), true"); await sleep(1000);
      for (const [w, ht] of [[667, 375], [740, 360], [360, 740]]) {
        await h.send('Emulation.setDeviceMetricsOverride', { width: w, height: ht, deviceScaleFactor: 1, mobile: true });
        await sleep(700);
        const r = await h.ev(`JSON.stringify((() => {
          const vw = innerWidth, vh = innerHeight, out = [];
          document.querySelectorAll('#lobby button, #lobby .hero-pick-ico').forEach(el => { if (el.offsetParent === null) return; const b = el.getBoundingClientRect(); const cx = b.left + b.width / 2, cy = b.top + b.height / 2; const hit = document.elementFromPoint(cx, cy);
            if (b.left < -1 || b.right > vw + 1 || b.top < -1 || b.bottom > vh + 1) out.push('outside:' + (el.id || el.className) + ':' + Math.round(b.left) + ',' + Math.round(b.top) + ',' + Math.round(b.right) + ',' + Math.round(b.bottom));
            else if (el.tagName === 'BUTTON' && hit && !el.contains(hit)) out.push('covered:' + (el.id || el.className) + ' by ' + (hit.id || hit.className));
          });
          const imgs = [...document.querySelectorAll('#lobby-heroes img')].map(i => i.complete && i.naturalWidth > 0);
          return { lang: document.documentElement.lang, picks: lobbyPicks, imgs, heroBtns: [...document.querySelectorAll('#lobby-heroes .hero-pick')].map(b => Math.round(b.getBoundingClientRect().height) + 'px:' + b.textContent), sideScroll: document.documentElement.scrollWidth > vw || document.getElementById('lobby').scrollWidth > document.getElementById('lobby').clientWidth, lobbyVScroll: document.getElementById('lobby').scrollHeight - document.getElementById('lobby').clientHeight, problems: out };
        })())`);
        console.log(lang, w + 'x' + ht, r);
        const shot = await h.send('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(OUT + '/lobby_' + lang + '_' + w + 'x' + ht + '.png', Buffer.from(shot.result.data, 'base64'));
      }
      if (h.errors.length) console.log('PAGE ERRORS', JSON.stringify(h.errors));
      await h.close(); tabs.pop();
    }
  } catch (e) { console.log('SCENARIO ERROR', e.message); }
  finally { for (const t of tabs) await t.close(); env.stop(); }
})();
