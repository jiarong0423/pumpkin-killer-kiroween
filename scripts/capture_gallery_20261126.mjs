#!/usr/bin/env node
'use strict';
/**
 * Capture up-to-date 1200x800 gallery PNGs & animated GIFs from the live build into:
 *   - docs/release_drafts/gallery/
 *   - docs/gifs/
 * Uses Chrome DevTools Protocol + local static server + local pk_relay.py (no external network).
 */
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const http = require('http');
const net = require('net');
const os = require('os');
const path = require('path');
const { fileURLToPath } = require('url');
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const ROOT = path.join(__dirname, '..');
const GALLERY = path.join(ROOT, 'docs', 'release_drafts', 'gallery');
const GIFS = path.join(ROOT, 'docs', 'gifs');
const CHROME = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
].find(p => fs.existsSync(p));
if (!CHROME) {
  console.error('capture_gallery: Chrome not found');
  process.exit(2);
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp',
  '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.svg': 'image/svg+xml',
  '.mp3': 'audio/mpeg', '.webmanifest': 'application/manifest+json',
};

const sleep = ms => new Promise(r => setTimeout(r, ms));
const freePort = () => new Promise((res, rej) => {
  const s = net.createServer();
  s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); });
  s.on('error', rej);
});

async function openTab(dbg, url, w = 1200, h = 800) {
  const made = await (await fetch(`http://127.0.0.1:${dbg}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' })).json();
  const ws = new WebSocket(made.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0;
  const pend = new Map();
  ws.onmessage = m => {
    const d = JSON.parse(m.data);
    if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); }
  };
  const send = (method, params = {}) => new Promise(r => {
    const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params }));
  });
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  const ev = async expr => {
    const r = (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result;
    if (r && r.exceptionDetails) {
      const ex = r.exceptionDetails;
      throw new Error((ex.exception && ex.exception.description) || ex.text || 'eval error');
    }
    return r ? r.result.value : undefined;
  };
  const until = async (expr, label, ms = 15000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) {
      try { if (await ev(expr)) return; } catch (_) {}
      await sleep(120);
    }
    throw new Error('timeout waiting for ' + label);
  };
  const snap = async outPath => {
    const r = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(outPath, Buffer.from(r.result.data, 'base64'));
  };
  return {
    send, ev, until, snap,
    close: async () => {
      try { ws.close(); } catch (_) {}
      try { await fetch(`http://127.0.0.1:${dbg}/json/close/${made.id}`); } catch (_) {}
    },
  };
}

function startStaticServer() {
  const srv = http.createServer((req, res) => {
    const raw = (req.url || '/').split('?')[0];
    const rel = raw === '/' ? 'index.html' : decodeURIComponent(raw.replace(/^\/+/, ''));
    const full = path.resolve(ROOT, rel);
    if (!full.startsWith(ROOT) || !fs.existsSync(full) || fs.statSync(full).isDirectory()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(full)] || 'application/octet-stream' });
    fs.createReadStream(full).pipe(res);
  });
  return srv;
}

function heroesAndBattlefieldsHtml(baseUrl) {
  const heroes = [
    ['Skeleton Spearman', 'Ricochet Spear', 'assets/portraits/skeleton_front.png'],
    ['Pumpkin Wizard', 'Arcane Ember', 'assets/portraits/wizard_front.png'],
    ['Bat-cat Assassin', 'Dagger Volley', 'assets/portraits/bat_front.png'],
    ['Heavy Pumpkin Guard', 'Shield Slam', 'assets/portraits/knight_front.png'],
    ['Ghost Bride', 'Spectral Wave', 'assets/portraits/bride_front.png'],
    ['Bell Tower Hunchback', 'Boomerang Axe', 'assets/portraits/hunchback_front.png'],
    ['Silver Cross Sister', 'Piercing Cross', 'assets/portraits/hag_front.png'],
    ['Necromancer', 'Soul Flame', 'assets/portraits/reaper_front.png'],
  ];
  const bgs = [
    ['Graveyard', 'assets/env/bg_graveyard.png'],
    ['Bell Tower', 'assets/env/bg_belltower.png'],
    ['Ruined Church', 'assets/env/bg_ruined_church.png'],
    ['Abandoned School', 'assets/env/bg_abandoned_school.png'],
  ];
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{width:1200px;height:800px;overflow:hidden;background:linear-gradient(135deg,#0b0f1e,#1b1230 55%,#0e1828);color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;padding:24px 28px}
    h1{font-size:24px;color:#fbbf24;margin-bottom:4px}
    .sub{font-size:13px;color:#cbd5e1;margin-bottom:14px}
    .sec{font-size:12px;font-weight:800;letter-spacing:1px;color:#38bdf8;margin:10px 0 8px}
    .heroes{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
    .hcard{background:rgba(30,41,59,.85);border:1px solid rgba(251,191,36,.38);border-radius:12px;padding:10px;display:flex;align-items:center;gap:10px;height:142px}
    .hcard img{width:104px;height:118px;object-fit:contain;border-radius:8px;background:rgba(15,23,42,.7)}
    .hname{font-size:14px;font-weight:700;color:#fff;line-height:1.25}
    .hskill{font-size:12px;color:#fde68a;margin-top:4px}
    .bgs{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:4px}
    .bcard{background:rgba(15,23,42,.9);border:1px solid rgba(56,189,248,.4);border-radius:12px;overflow:hidden;height:212px;display:flex;flex-direction:column}
    .bcard img{width:100%;height:178px;object-fit:cover}
    .bcard span{padding:7px 10px;font-size:13px;font-weight:700;color:#e2e8f0;text-align:center}
  </style></head><body>
    <h1>Pumpkin Killer — 8 Playable Heroes &amp; 4 Haunted Battlefields</h1>
    <div class="sub">Shipped front-facing hero portraits &amp; scenes (Resurrection build · 1v1 to 3v3 · wind &amp; 5 weather states)</div>
    <div class="sec">THE 8 HEROES (NO DUPLICATE HEROES PER TEAM)</div>
    <div class="heroes">${heroes.map(([n, w, p]) => `<div class="hcard"><img src="${baseUrl}/${p}"><div><div class="hname">${n}</div><div class="hskill">${w}</div></div></div>`).join('')}</div>
    <div class="sec" style="margin-top:16px">THE 4 BATTLEFIELDS</div>
    <div class="bgs">${bgs.map(([n, p]) => `<div class="bcard"><img src="${baseUrl}/${p}"><span>${n}</span></div>`).join('')}</div>
  </body></html>`;
}

async function run() {
  fs.mkdirSync(GALLERY, { recursive: true });
  fs.mkdirSync(GIFS, { recursive: true });

  const httpPort = await freePort();
  const httpAltPort = await freePort();
  const relayPort = await freePort();
  const dbgPort = await freePort();

  const srv1 = startStaticServer();
  const srv2 = startStaticServer();
  await new Promise(r => srv1.listen(httpPort, '127.0.0.1', r));
  await new Promise(r => srv2.listen(httpAltPort, '127.0.0.1', r));
  const base1 = `http://127.0.0.1:${httpPort}`;
  const base2 = `http://localhost:${httpAltPort}`;
  const relayUrl = `ws://127.0.0.1:${relayPort}`;

  const relayProc = spawn('python3', ['-B', path.join(__dirname, 'pk_relay.py')], {
    env: { ...process.env, HOST: '127.0.0.1', PORT: String(relayPort), PK_RELAY_MAX_PER_ADDR: '50' },
    stdio: 'ignore',
  });
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'pk_cap_'));
  const chromeProc = spawn(CHROME, [
    `--remote-debugging-port=${dbgPort}`,
    `--user-data-dir=${prof}`,
    '--headless=new', '--no-sandbox', '--disable-gpu', '--mute-audio',
    '--window-size=1200,800', '--disable-background-timer-throttling',
    'about:blank',
  ], { stdio: 'ignore' });

  const frameDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pk_frames_'));

  try {
    // Wait for Chrome CDP
    const deadline = Date.now() + 12000;
    while (Date.now() < deadline) {
      try { if ((await fetch(`http://127.0.0.1:${dbgPort}/json/version`)).ok) break; } catch (_) {}
      await sleep(150);
    }

    // 1. Render 05_architecture_and_kiro_20261126.png from updated SVG
    const svgTab = await openTab(dbgPort, `${base1}/docs/release_drafts/gallery/05_architecture_and_kiro_20261126.svg`);
    await svgTab.until("document.readyState === 'complete'", 'svg ready');
    await sleep(300);
    await svgTab.snap(path.join(GALLERY, '05_architecture_and_kiro_20261126.png'));
    await svgTab.close();
    console.log('Saved 05_architecture_and_kiro_20261126.png');

    // 2. Render 04_heroes_and_battlefields_20261126.png
    const gridHtmlPath = path.join(frameDir, 'roster_grid.html');
    fs.writeFileSync(gridHtmlPath, heroesAndBattlefieldsHtml(base1), 'utf8');
    const gridTab = await openTab(dbgPort, `file://${gridHtmlPath}`);
    await gridTab.until("document.readyState === 'complete' && [...document.images].every(i => i.complete && i.naturalWidth > 0)", 'grid images');
    await sleep(300);
    await gridTab.snap(path.join(GALLERY, '04_heroes_and_battlefields_20261126.png'));
    await gridTab.close();
    console.log('Saved 04_heroes_and_battlefields_20261126.png');

    // 3. Start Screen (3v3, EN, new avatar_bat + Play with friends + Join code)
    const startTab = await openTab(dbgPort, `${base1}/index.html?lang=en&team=3`);
    await startTab.until("document.readyState === 'complete' && !document.getElementById('start-screen').hidden", 'start screen ready');
    await startTab.ev("localStorage.setItem('pk_lang','en'); if (typeof setLang==='function') setLang('en'); const t3=document.querySelector('[data-team=\"3\"]'); if(t3) t3.click(); true");
    await sleep(600);
    await startTab.snap(path.join(GALLERY, '01_start_screen_3v3.png'));
    await startTab.close();
    console.log('Saved 01_start_screen_3v3.png');

    // 4. Full-screen Multiplayer Lobby + Guest + Invite Ticket + Live 3v3 Battle + Throw GIF
    const host = await openTab(dbgPort, `${base1}/index.html?lang=en&relay=${encodeURIComponent(relayUrl)}&team=3`);
    const guest = await openTab(dbgPort, `${base2}/index.html?lang=en&relay=${encodeURIComponent(relayUrl)}&team=3`);
    for (const [p, nm] of [[host, 'Alice'], [guest, 'Bob']]) {
      await p.until("document.readyState === 'complete' && typeof lobbyOpenFromStart === 'function' && !!document.getElementById('friends-btn').onclick", 'page ready');
      await p.ev(`localStorage.setItem('pk_lang','en'); localStorage.setItem('pk_name','${nm}'); if (typeof setLang==='function') setLang('en'); true`);
    }
    await host.ev("document.getElementById('friends-btn').click(), true");
    await host.until("!document.getElementById('lobby').hidden && /^[A-Z0-9]{6}$/.test(document.getElementById('lobby-code').textContent)", 'host lobby code');
    const code = await host.ev("document.getElementById('lobby-code').textContent");
    await guest.ev(`location.href='${base2}/index.html?lang=en&relay=${encodeURIComponent(relayUrl)}&team=3&room=${code}&lobby=1'; true`);
    await guest.until("typeof lobbyMode !== 'undefined' && lobbyMode && relaySeatId && !document.getElementById('lobby').hidden", 'guest in lobby');

    // Ensure Computer fills open places + Allow agents are BOTH ticked, pick Bat on host & Hag on guest
    await host.ev("if (!document.getElementById('lobby-allow-ai').checked) document.getElementById('lobby-allow-ai').click(); true");
    await host.ev("if (!document.getElementById('lobby-allow-agent').checked) document.getElementById('lobby-allow-agent').click(); true");
    await sleep(250);
    // Open #lobby-heroes selector if collapsed, pick 'bat' for host and 'hag' for guest
    await host.ev("(() => { const h = document.getElementById('lobby-heroes'); const btns = [...h.querySelectorAll('button')]; if (btns.length === 1) btns[0].click(); const pick = [...h.querySelectorAll('button')].find(x => (x.dataset.hero === 'bat') || /Bat/i.test(x.textContent)); if (pick) pick.click(); return true; })()");
    await guest.ev("(() => { const h = document.getElementById('lobby-heroes'); const btns = [...h.querySelectorAll('button')]; if (btns.length === 1) btns[0].click(); const pick = [...h.querySelectorAll('button')].find(x => (x.dataset.hero === 'hag') || /Silver/i.test(x.textContent)); if (pick) pick.click(); return true; })()");
    await sleep(250);
    await host.ev("document.getElementById('lobby-lock').click(), true");
    await guest.ev("document.getElementById('lobby-lock').click(), true");
    await sleep(350);
    await host.ev("const ib = document.getElementById('lobby-invite'); if (ib && !ib.hidden && !ib.disabled) ib.click(); true");
    await host.until("!document.getElementById('lobby-invite-box').hidden", 'invite box visible');
    await sleep(350);
    await host.snap(path.join(GALLERY, '03_multiplayer_lobby_qr_mcp.png'));
    console.log('Saved 03_multiplayer_lobby_qr_mcp.png');

    // Cancel pending invite via real UI button so host Start begins the 3v3 match cleanly with AI fill
    await host.ev("document.getElementById('lobby-invite-cancel').click(), true");
    await host.until("document.getElementById('lobby-invite-box').hidden && !document.getElementById('lobby-start').disabled", 'start enabled');
    await host.ev("document.getElementById('lobby-start').click(), true");
    await host.until("relayPlaying && matchStarted && document.getElementById('lobby').hidden", '3v3 match started', 20000);

    // Wait past coin toss & dismiss first hint if open
    await host.until("typeof coinActive === 'undefined' || !coinActive", 'coin toss done', 10000);
    await host.ev("localStorage.setItem('pk_hint_seen','1'); const fh=document.getElementById('first-hint'); if(fh) fh.hidden=true; true");
    await sleep(700);
    await host.snap(path.join(GALLERY, '02_battle_3v3.png'));
    console.log('Saved 02_battle_3v3.png');

    await host.close();
    await guest.close();

    // 5. Capture live Silver Cross Sister + 3v3 gameplay throw GIF frames in clean solo 3v3 match
    const gifTab = await openTab(dbgPort, `${base1}/index.html?lang=en&team=3`);
    await gifTab.until("document.readyState === 'complete' && !document.getElementById('start-screen').hidden", 'gifTab ready');
    await gifTab.ev("localStorage.setItem('pk_lang','en'); localStorage.setItem('pk_hint_seen','1'); if (typeof setLang==='function') setLang('en'); const t3=document.querySelector('[data-n=\"3\"]'); if(t3) t3.click(); selectTeamSlot(0); selectPickedHero('hag'); true");
    await sleep(300);
    await gifTab.ev("document.getElementById('start-go').click(); true");
    await gifTab.until("matchStarted && (typeof coinActive==='undefined' || !coinActive)", 'solo 3v3 started', 10000);
    await gifTab.ev("const fh=document.getElementById('first-hint'); if(fh) fh.hidden=true; setAngleOf('left', 56); executeThrow('player', 74, 56, player); true");
    for (let i = 0; i < 24; i++) {
      await gifTab.snap(path.join(frameDir, `f_${String(i).padStart(2, '0')}.png`));
      await sleep(110);
    }
    await gifTab.close();

    // Assemble GIFs + 8-hero Showcase GIF cleanly via Python Pillow
    execFileSync('python3', ['-B', '-c', `
import glob, os
from PIL import Image, ImageDraw, ImageFont

frame_dir = ${JSON.stringify(frameDir)}
gallery_gif = ${JSON.stringify(path.join(GALLERY, '08_live_gameplay_20261126.gif'))}
docs_gif = ${JSON.stringify(path.join(GIFS, 'gameplay_20261126.gif'))}
frames = [Image.open(p).convert('RGB').resize((900, 600), Image.Resampling.LANCZOS) for p in sorted(glob.glob(os.path.join(frame_dir, 'f_*.png')))]
frames[0].save(gallery_gif, save_all=True, append_images=frames[1:], duration=110, loop=0, optimize=True)
frames[0].save(docs_gif, save_all=True, append_images=frames[1:], duration=110, loop=0, optimize=True)
print('Saved', gallery_gif, 'and', docs_gif, 'frames=', len(frames))

# Build 8-hero animated showcase GIF from shipped portraits (zero old 4-hero prototype)
heroes = [
    ('Skeleton Spearman', 'assets/portraits/skeleton_front.png', (0, 210, 211)),
    ('Pumpkin Wizard', 'assets/portraits/wizard_front.png', (255, 159, 67)),
    ('Bat-cat Assassin', 'assets/portraits/bat_front.png', (162, 155, 254)),
    ('Heavy Pumpkin Guard', 'assets/portraits/knight_front.png', (77, 238, 234)),
    ('Ghost Bride', 'assets/portraits/bride_front.png', (196, 181, 253)),
    ('Bell Tower Hunchback', 'assets/portraits/hunchback_front.png', (134, 239, 172)),
    ('Silver Cross Sister', 'assets/portraits/hag_front.png', (226, 232, 240)),
    ('Necromancer', 'assets/portraits/reaper_front.png', (192, 132, 252)),
]
root = ${JSON.stringify(ROOT)}
imgs = [Image.open(os.path.join(root, p)).convert('RGBA').resize((156, 156), Image.Resampling.LANCZOS) for _, p, _ in heroes]
font = ImageFont.load_default()
gframes = []
for step in range(8):
    canvas = Image.new('RGB', (860, 440), (14, 15, 32))
    draw = ImageDraw.Draw(canvas)
    draw.text((22, 14), 'PUMPKIN KILLER - 8 PLAYABLE HEROES (RESURRECTION BUILD)', fill=(251, 191, 36), font=font)
    for idx, (name, _, col) in enumerate(heroes):
        col_i, row_i = idx % 4, idx // 4
        x = 22 + col_i * 208
        y = 44 + row_i * 192
        hi = (step == idx)
        border = col if hi else (71, 85, 105)
        draw.rounded_rectangle((x, y, x + 194, y + 180), radius=12, fill=(24, 30, 54), outline=border, width=3 if hi else 1)
        canvas.paste(imgs[idx], (x + 19, y + (4 if hi else 8)), imgs[idx])
        draw.text((x + 12, y + 160), name, fill=(255, 255, 255) if hi else (203, 213, 225), font=font)
    gframes.append(canvas)
all_gif = ${JSON.stringify(path.join(GIFS, 'all_heroes_20261126.gif'))}
gframes[0].save(all_gif, save_all=True, append_images=gframes[1:], duration=650, loop=0, optimize=True)
print('Saved', all_gif)
`], { stdio: 'inherit' });
  } finally {
    try { chromeProc.kill(); } catch (_) {}
    try { relayProc.kill(); } catch (_) {}
    await sleep(400);
    await new Promise(r => srv1.close(r));
    await new Promise(r => srv2.close(r));
    try { fs.rmSync(prof, { recursive: true, force: true }); } catch (_) {}
    try { fs.rmSync(frameDir, { recursive: true, force: true }); } catch (_) {}
  }
}

run().catch(e => { console.error(e); process.exit(1); });
