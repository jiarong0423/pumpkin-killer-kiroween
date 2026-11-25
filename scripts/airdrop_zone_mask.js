'use strict';
// Owner 2026-11-26: draw where a unit may stand (from the real dice move) and where supply crates land (from the real scheduleAirdrop), on one strip.
// usage: node scripts/airdrop_zone_mask.js --out file.svg [--before]   (--before replays the old placement rule)
const fs = require('fs'), path = require('path');
const { loadPage } = require('./page_harness');
const argv = process.argv, arg = (k, d) => { const i = argv.indexOf('--' + k); return i > 0 ? argv[i + 1] : d; };
const before = argv.includes('--before');
const opts = { team: 3 };
if (before) opts.mutate = [[   // the rule before AIRDROP-REACH-1 (redteam/backups/bak_airdrop_reach_20261126/index.html): clamp to the fence band only
  'x = Math.max(lo, Math.min(hi, x));\n      if (Math.abs(x - u.targetX) < 141) x = Math.max(lo, Math.min(hi, u.targetX - dir * dist));',
  'const lo2 = FENCE_X - FENCE_W / 2 - 60, hi2 = FENCE_X + FENCE_W / 2 + 60; if (dropSide > 0) x = Math.min(x, lo2); else x = Math.max(x, hi2);']];
const P = loadPage(opts);
const W = P.get('CANVAS_W'), FX = P.get('FENCE_X'), FW = P.get('FENCE_W');
const zone = {};
for (const [side, owner] of [['left', 'player'], ['right', 'ai']]) {
  zone[side] = [1, -1].map(dir => {
    P.eval('resetGame(); unitsOf("' + side + '").slice(1).forEach(u => { u.hp = 0; }); diceRoll = null;');
    P.place(side, [side === 'left' ? 400 : W - 400]);
    for (let i = 0; i < 12; i++) P.eval('startDiceRoll("' + owner + '", ' + dir + ', function () {}); diceRoll.final = 6; for (let k = 0; k < 300 && diceRoll; k++) stepDice(1/60); unitOf("' + side + '").x = unitOf("' + side + '").targetX;');
    return P.eval('unitOf("' + side + '").targetX');
  }).sort((a, b) => a - b);
}
const xs = { left: [], right: [] };
for (let seed = 1; seed <= 300; seed++) {
  P.eval('resetGame(); matchSeed = ' + seed + '; carrier = null; drops = []; dropSide = -1; dropCount = 0; cratesTaken.player = 0; cratesTaken.ai = 0;');   // once per match: the sides alternate over its rounds
  for (let round = 2; round <= 24; round += 2) {
  const lx = zone.left[0] + ((seed * 53 + round * 31) % (zone.left[1] - zone.left[0] + 1)), rx = zone.right[1] - ((seed * 71 + round * 17) % (zone.right[1] - zone.right[0] + 1));
  P.place('left', [lx]); P.place('right', [rx]);
  P.eval('roundNum = ' + round + '; carrier = null; drops = []; scheduleAirdrop()');
  const c = P.eval('carrier'); if (c) xs[P.get('dropSide') > 0 ? 'left' : 'right'].push(c.targetX);
  }
}
const PICK = 70, S = 0.5, H = 260;
const reach = s => [zone[s][0] - PICK, zone[s][1] + PICK];
const bad = s => xs[s].filter(x => x < reach(s)[0] || x > reach(s)[1]).length;
const bins = {}; ['left', 'right'].forEach(s => xs[s].forEach(x => { const b = Math.floor(x / 10) * 10; bins[b] = (bins[b] || 0) + 1; }));
const maxBin = Math.max(...Object.values(bins));
let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W * S} ${H}" width="${W * S}" height="${H}" font-family="sans-serif" font-size="13">`;
svg += `<rect width="100%" height="100%" fill="#1b1530"/><text x="10" y="20" fill="#fff" font-weight="bold">${before ? '修正前' : '修正後'}：綠＝人物可站範圍，淺綠＝站著撿得到（±${PICK}px），橘點＝寶箱落點（${xs.left.length + xs.right.length} 個），紅＝撿不到</text>`;
for (const s of ['left', 'right']) {
  const [a, b] = reach(s); svg += `<rect x="${a * S}" y="40" width="${(b - a) * S}" height="90" fill="#7bed9f" opacity="0.25"/>`;
  svg += `<rect x="${zone[s][0] * S}" y="40" width="${(zone[s][1] - zone[s][0]) * S}" height="90" fill="#2ed573" opacity="0.55"/>`;
  svg += `<text x="${zone[s][0] * S + 4}" y="58" fill="#fff">${zone[s].join('–')}</text>`;
}
svg += `<rect x="${(FX - FW / 2) * S}" y="30" width="${FW * S}" height="110" fill="#57606f"/><text x="${FX * S}" y="90" fill="#fff" text-anchor="middle">柵欄</text>`;
for (const [b, n] of Object.entries(bins)) {
  const x = +b, s = x < FX ? 'left' : 'right', out = x < reach(s)[0] || x + 10 > reach(s)[1] + 10 && x > reach(s)[1];
  const h = 90 * n / maxBin; svg += `<rect x="${x * S}" y="${230 - h}" width="${10 * S}" height="${h}" fill="${out ? '#ff4757' : '#ffa502'}"/>`;
}
svg += `<line x1="0" y1="230" x2="${W * S}" y2="230" stroke="#aaa"/><text x="10" y="250" fill="#ddd">落點分布（每 10px 一格）。撿不到：左 ${bad('left')}、右 ${bad('right')}</text></svg>`;
fs.writeFileSync(arg('out', 'airdrop_zone.svg'), svg);
console.log(JSON.stringify({ before, zone, drops: xs.left.length + xs.right.length, unreachable: { left: bad('left'), right: bad('right') } }));
