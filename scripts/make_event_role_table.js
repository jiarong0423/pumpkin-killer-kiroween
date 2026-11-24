#!/usr/bin/env node
'use strict';
// Builds docs/event_role_table.html: an event x role table the owner can LISTEN to (owner 2026-11-18: "make an HTML event-role table", "I will listen").
// Data comes from the code, not from memory: the event map of js/audio.js (the same one the game plays), THROW_SOUND, HERO_PROFILES, ULT_RING_COLOR / ULT_RING_STYLE of index.html, the file system.
// The page plays through the REAL js/audio.js (so extra layers and the synthesized fallbacks are heard exactly as in the game) and also offers the plain main file.
// usage: node scripts/make_event_role_table.js   (serve the project folder, e.g. http://localhost:8080/docs/event_role_table.html)
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const A = require(path.join(ROOT, 'js', 'audio.js'));
const EV = A.DEFAULT_EVENT_MAP.events || A.DEFAULT_EVENT_MAP;
const page = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const en = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets', 'i18n', 'en.json'), 'utf8'));
const zh = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets', 'i18n', 'zh-TW.json'), 'utf8'));

const ROLES = ['skeleton', 'wizard', 'bat', 'knight', 'reaper', 'bride', 'hunchback', 'hag'];
const obj = (name) => { const m = page.match(new RegExp('const ' + name + ' = \\{([^}]*)\\}')); const o = {}; if (m) for (const kv of m[1].matchAll(/(\w+):\s*"([^"]*)"/g)) o[kv[1]] = kv[2]; return o; };
const THROW = obj('THROW_SOUND'), RING_COLOR = obj('ULT_RING_COLOR'), RING_STYLE = obj('ULT_RING_STYLE');
const prof = {};
for (const r of ROLES) {
  const m = page.match(new RegExp('\\n      ' + r + ': \\{(.*?)\\n      \\}', 's'));
  const b = m ? m[1] : '';
  prof[r] = { weapon: (b.match(/weapon: "(\w+)"/) || [])[1], dmg: (b.match(/dmg: (\d+)/) || [])[1], hp: (b.match(/hp: (\d+)/) || [])[1] };
}
const tabOf = (r) => (zh['hero.' + r + '.tab'] || en['hero.' + r + '.tab'] || r);
const nameOf = (r) => (zh['hero.' + r + '.name'] || en['hero.' + r + '.name'] || zh['hero.' + r] || en['hero.' + r] || r);

// role by role: what the code shows for each action (facts from index.html, checked 2026-11-18)
const ROLEINFO = {
  skeleton: { trail: ['weapon_trail_spear', 'own'], hit: '流血（噴血）', ult: '三連標槍（模組 skeleton_triple_javelin）', ultSound: null },
  wizard: { trail: ['weapon_trail_cannon', 'own'], hit: '中毒（冒煙）', ult: '南瓜大爆炸（模組 wizard_pumpkin_blast）+ 地面火焰', ultSound: null },
  bat: { trail: ['weapon_trail_dart', 'own'], hit: '減速', ult: '飛鏢雨（模組 bat_shuriken_rain）', ultSound: null },
  knight: { trail: ['weapon_trail_shield', 'own'], hit: '吸血（5%）', ult: '盾牆（程式碼）', ultSound: null },
  reaper: { trail: ['紫色餘燼（自繪）', 'own'], hit: '燃燒', ult: '幻覺火焰（程式碼）', ultSound: null },
  bride: { trail: ['音波環（Kenney 螺旋 + 擴散環）', 'new'], hit: '中毒', ult: '蝙蝠群（程式碼）', ultSound: null },
  hunchback: { trail: ['axe_spin_trail', 'own'], hit: '流血 + 擊退 50px', ult: '迴旋斧（程式碼）', ultSound: null },
  hag: { trail: ['cross_spin_trail', 'own'], hit: '電擊麻痺 + 二次接觸', ult: '雙十字架 + 暈眩（程式碼）', ultSound: null },
};
const weaponEvent = (w) => THROW[w] || '';
// who triggers an event (from the code): throw events by weapon, the rest shared
const sharedEvents = new Set(['ui_click', 'ui_hover', 'round_start', 'round_end', 'dice_rattle', 'dice_result', 'move_step', 'ko', 'low_hp_heartbeat', 'heal', 'item_pickup', 'impact_unit', 'impact_unit_heavy', 'impact_fence', 'impact_fence_break', 'impact_ground', 'impact_ground_heavy', 'shield_block', 'shield_place', 'ultimate_ready', 'charge', 'poison_tick']);
const rolesOfEvent = (ev) => {
  if (ev.startsWith('throw_')) return ROLES.filter(r => weaponEvent(prof[r].weapon) === ev);
  if (ev.startsWith('flight_')) { const m = { flight_spear: 'proj_spear', flight_shuriken: 'proj_shuriken', flight_cannon: 'cannonball', flight_shield: 'proj_shield' }; return ROLES.filter(r => prof[r].weapon === m[ev]); }
  if (ev.startsWith('ult_')) return ROLES.filter(r => ev === 'ult_' + r || ev === 'ult_' + r + '_hit');   // an ultimate sound (cast, or its _hit part) belongs to one role
  if (ev === 'impact_flame') return ['reaper'];   // the necromancer's flame hit
  if (ev === 'throw_bomb') return ROLES.slice();   // the heavy bomb shot (any role)
  if (ev === 'poison_tick') return ['wizard', 'bride'];
  if (ev === 'shield_block' || ev === 'shield_place') return ['knight'];
  return sharedEvents.has(ev) ? ROLES.slice() : [];
};
const exists = (f) => f && fs.existsSync(path.join(ROOT, f));
const sourceLabel = (e) => {
  if (!e.file) return (e.extras || []).some(x => exists(x.file)) ? ['extra', '疊加檔（主聲為合成）'] : ['synth', '只有合成音（缺檔）'];
  const s = e.source || '';
  if (s.startsWith('owner-gemini')) return ['gemini', '你的 Gemini 音效'];
  if (s === 'kenney-rpg' || s === 'kenney-impact') return ['kenney', 'Kenney 新增（CC0）'];
  return ['own', '既有檔案（' + s + '）'];
};
const esc = (s) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const rel = (f) => '../' + f;

const rows = Object.keys(EV).map(k => {
  const e = EV[k], [cls, label] = sourceLabel(e), who = rolesOfEvent(k);
  const placeholder = /^throw_(flame|soundwave)$/.test(k) && !String(e.source).startsWith('owner-gemini') ? ' · 暫代' : '';
  return `<tr class="${cls}" data-ev="${esc(k)}"><td class="ev"><code>${esc(k)}</code><br><small>${esc(e.sound || '')}</small></td>` +
    ROLES.map(r => `<td class="dot">${who.includes(r) ? '●' : ''}</td>`).join('') +
    `<td class="play"><button data-play="${esc(k)}" title="用遊戲的音訊模組播放（含疊加層與合成備用）">▶ 遊戲播放</button>` + (exists(e.file) ? ` <button data-file="${esc(rel(e.file))}" class="alt" title="只播主檔">▶ 原檔</button>` : '') + `</td>` +
    `<td><span class="badge ${cls}">${esc(label)}${placeholder}</span></td><td>${esc(e.duration)}s</td><td><small>${esc(e.file ? path.basename(e.file) : '—')}${(e.extras || []).length ? '<br>+ ' + esc(e.extras.map(x => path.basename(x.file || '')).join(', ')) : ''}</small></td></tr>`;
}).join('\n');

const roleCards = ROLES.map(r => {
  const p = prof[r], i = ROLEINFO[r], ev = weaponEvent(p.weapon), e = EV[ev] || {}, [cls, label] = sourceLabel(e);
  const col = RING_COLOR[r] || '255,255,255';
  return `<tr><td><img src="${rel('assets/avatars/avatar_' + r + '.png')}" width="44" height="44" alt=""> <b>${esc(nameOf(r))}</b><br><small>${r} · HP ${esc(p.hp)} · 攻 ${esc(p.dmg)}</small></td>` +
    `<td><code>${esc(p.weapon)}</code></td>` +
    `<td><button data-play="${esc(ev)}">▶ ${esc(ev)}</button><br><span class="badge ${cls}">${esc(label)}</span></td>` +
    `<td>${esc(i.trail[0])}<br><span class="badge ${i.trail[1] === 'gap' ? 'synth' : i.trail[1] === 'new' ? 'gemini' : 'own'}">${i.trail[1] === 'gap' ? '缺：要專用尾跡' : i.trail[1] === 'new' ? '新（Kenney）' : '既有'}</span></td>` +
    `<td>${esc(i.hit)}</td><td>${esc(i.ult)}<br><span class="badge gemini">大招音效：有（${EV['ult_' + r + '_hit'] ? '施放 + 命中兩段' : '整段'}）</span><br><button data-play="ult_${r}">▶ 施放</button>${EV['ult_' + r + '_hit'] ? ` <button data-play="ult_${r}_hit">▶ 命中</button>` : ''}</td>` +
    `<td><span class="sw" style="background:rgb(${col})"></span> ${esc(RING_STYLE[r] || '')}<br><small>${esc(col)}</small></td></tr>`;
}).join('\n');

const gaps = [
  ['（已補）8 個角色的大招音效', 'pumpkin_slayer_ultimates_sfx 全數就位：全部 7 支投射型大招（骷髏、巫師、蝙蝠、死靈、新娘、鐘樓怪人、修女）皆已切成「施放＋命中」兩段，騎士盾牆於鎖定時播放'],
  ['（已補）火焰投擲、飛行循環、節奏層與標題音樂', 'throw_flame、flight_spear / cannon / shield、music.rhythm 皆已補入 OpenGameArt CC0 實檔；charge 採用 4 層上升聚氣合成音；開始畫面播放 title 氛圍層'],
  ['選配待補：新娘哭泣、通用大吼、回合鐘聲獨立檔', '目前由既有事件與疊加層涵蓋；若有新 Gemini 錄音可再替換'],
];

const html = `<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>事件角色對應表</title>
<style>
:root{--bg:#120a22;--card:#1c1233;--line:#3a2a63;--text:#f1ecff;--mut:#b7a8de;--gold:#ffd32a;--cyan:#4deeea;--red:#ff7675;--green:#7bed9f}
@media (prefers-color-scheme: light){:root{--bg:#f6f2ff;--card:#fff;--line:#cfc3ee;--text:#1b1233;--mut:#5b4d85;--gold:#9a6a00;--cyan:#006d77;--red:#b3261e;--green:#1b6b3a}}
body{margin:0;padding:16px;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,"Noto Sans TC",sans-serif}
h1{font-size:22px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 8px;color:var(--gold)}p.n{color:var(--mut);margin:4px 0 12px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:900px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{position:sticky;top:0;background:var(--card);font-size:13px;color:var(--mut)}td.dot{text-align:center;color:var(--cyan);font-size:16px;width:34px}
th.r{text-align:center;padding:6px 2px;font-size:12px;width:44px}td.play{white-space:nowrap}
button{background:var(--bg);color:var(--text);border:1.5px solid var(--gold);border-radius:8px;padding:5px 10px;min-height:32px;cursor:pointer;font-size:13px;white-space:nowrap}
button.alt{border-color:var(--cyan)}button:hover{background:var(--line)}
.badge{display:inline-block;border-radius:999px;padding:1px 9px;font-size:12px;border:1px solid var(--line)}
.badge.own{color:var(--green);border-color:var(--green)}.badge.kenney{color:var(--cyan);border-color:var(--cyan)}.badge.gemini{color:var(--gold);border-color:var(--gold)}
.badge.extra{color:var(--gold);border-color:var(--gold)}.badge.synth{color:var(--red);border-color:var(--red)}
tr.synth td.ev code{color:var(--red)}.sw{display:inline-block;width:16px;height:16px;border-radius:4px;border:1px solid var(--line);vertical-align:middle}
small{color:var(--mut)}code{font-size:13px}.gap{list-style:none;padding:0;margin:0}.gap li{padding:8px 12px;border:1px solid var(--line);border-left:4px solid var(--red);border-radius:8px;margin:6px 0;background:var(--card)}
#status{position:sticky;top:0;z-index:5;padding:6px 10px;border-radius:8px;background:var(--card);border:1px solid var(--line);margin-bottom:10px;font-size:13px;color:var(--mut)}
</style></head><body>
<h1>事件 × 角色對應表（可以直接聽）</h1>
<p class="n">由程式碼產生（node scripts/make_event_role_table.js），不是手寫：音效事件表來自 js/audio.js，角色武器與顏色來自 index.html。「▶ 遊戲播放」走遊戲真正的音訊模組（含疊加層、合成備用）；「▶ 原檔」只播主檔。我沒有聽過任何一個音效。</p>
<div id="status">按任何一個 ▶ 開始（瀏覽器需要一次點擊才能發聲）。</div>
<h2>1. 音效事件（${Object.keys(EV).length} 個）</h2>
<div class="wrap"><table><thead><tr><th>事件</th>${ROLES.map(r => `<th class="r" title="${esc(nameOf(r))}">${esc(tabOf(r))}</th>`).join('')}<th>播放</th><th>狀態</th><th>長度</th><th>檔案</th></tr></thead><tbody>
${rows}
</tbody></table></div>
<p class="n">● ＝ 這個角色會觸發這個事件（投擲音依武器；其餘共用事件對所有角色）。紅色事件名 ＝ 只有合成音，沒有真檔。</p>
<h2>2. 角色對應（武器、投擲音、尾跡、受擊狀態、大招、光環顏色）</h2>
<div class="wrap"><table><thead><tr><th>角色</th><th>武器</th><th>投擲音效</th><th>飛行尾跡</th><th>命中狀態</th><th>大招</th><th>大招光環</th></tr></thead><tbody>
${roleCards}
</tbody></table></div>
<h2>3. 目前的缺口</h2>
<ul class="gap">${gaps.map(g => `<li><b>${esc(g[0])}</b><br><small>${esc(g[1])}</small></li>`).join('')}</ul>
<script src="${rel('js/audio.js')}"></script>
<script>
(function(){
  var status=document.getElementById('status'), ctx=null, audio=null, cur=null;
  function loader(f){ return fetch('../'+f.replace(/^\\//,'')).then(function(r){ if(!r.ok) throw new Error('missing '+f); return r.arrayBuffer(); }).then(function(b){ return ctx.decodeAudioData(b); }); }
  function ensure(){
    if(audio) return Promise.resolve(audio);
    ctx=new (window.AudioContext||window.webkitAudioContext)({latencyHint:'interactive'});
    audio=GameAudio.createAudio({ctx:ctx, loader:loader, random:Math.random});
    return audio.unlock().then(function(){ return audio; });
  }
  document.addEventListener('click', function(e){
    var b=e.target.closest('button'); if(!b) return;
    var ev=b.getAttribute('data-play'), file=b.getAttribute('data-file');
    if(ev){ status.textContent='載入中…'; ensure().then(function(a){ a.preload && a.preload(); return (a.preload?a.preload():Promise.resolve()); }).then(function(){ audio.play(ev); status.textContent='播放：'+ev+'（遊戲音訊模組）'; }).catch(function(err){ status.textContent='失敗：'+err; }); }
    else if(file){ if(cur){ cur.pause(); } cur=new Audio(file); cur.play().then(function(){ status.textContent='播放原檔：'+file.split('/').pop(); }).catch(function(err){ status.textContent='失敗：'+err; }); }
  });
})();
</script></body></html>
`;
fs.writeFileSync(path.join(ROOT, 'docs', 'event_role_table.html'), html);
const gapEvents = Object.keys(EV).filter(k => !EV[k].file && !(EV[k].extras || []).some(x => exists(x.file)));
console.log(JSON.stringify({ events: Object.keys(EV).length, synthOnly: gapEvents, out: 'docs/event_role_table.html', bytes: html.length }));
