'use strict';
// Data matching between what the player SEES and what the game DECIDES (backend only, no browser).
// For every simulated throw and every weapon/target pair: does the drawn projectile visibly overlap the target's body, and does the page's hit rule fire?
// Bug class reported: "overlaps the target but no damage". Rules mirrored from index.html (opponent-collision block): point test |x-ox| <= 70 (57 reaper), oy-190 <= y <= oy (oy-165 reaper).
// Usage: node scripts/hit_match_overlap.js [out.json]   (HIT_SCALE=0 reproduces the old centre-point rule; default 1 = the rule now in the page and the engine)
const fs = require('fs');
const Flight = require('../js/flight.js');
const OUT = process.argv[2] || '';
const GROUND = 860, MUZZLE = 58, START_Y = 750, MARGIN = 15;
const WEAPON = { skeleton: [210, 33], wizard: [40, 40], bat: [58, 58], reaper: [150, 55], hag: [118, 82], bride: [170, 170], hunchback: [130, 130], knight: [62, 92] };
// body box of each hero relative to (unit x, ground y): x range (5..95 percent of the alpha mass), top/bottom of the alpha, from the drawn files (see docs/hit_jitter_30000_20261116.md method)
const BODY = { skeleton: [-47, 59, -176, -1], wizard: [-52, 42, -192, 4], bat: [-49, 52, -188, 0], knight: [-67, 62, -188, 4], reaper: [-56, 53, -184, 10], bride: [-55, 53, -170, 10], hunchback: [-70, 72, -174, 10], hag: [-33, 63, -189, 1] };
const HEROES = Object.keys(BODY);
const HIT_R0 = parseFloat(process.env.HIT_R0 || '20');
const HIT_SCALE = parseFloat(process.env.HIT_SCALE || '1');   // 0 = the old centre-point rule; > 0 = the drawn projectile counts: collision radius = HIT_SCALE * sqrt(wLen * wThick) / 2
function hitRule(p, ox, target, weapon) {
  const half = target === 'reaper' ? 57 : 70, top = target === 'reaper' ? 165 : 190;
  const r = HIT_SCALE > 0 ? Math.max(0, HIT_SCALE * Math.sqrt(WEAPON[weapon][0] * WEAPON[weapon][1]) / 2 - HIT_R0) : 0;   // radius beyond what the 70 px box already allows
  return Math.abs(p.x - ox) <= half + r && p.y >= GROUND - top - r && p.y <= GROUND + r;
}
function distToBox(px, py, b) { const dx = Math.max(b[0] - px, 0, px - b[1]), dy = Math.max(b[2] - py, 0, py - b[3]); return Math.hypot(dx, dy); }
function overlaps(p, prev, weapon, ox, target) {
  const [L, T] = WEAPON[weapon], r = T / 2, seg = Math.max(0, L - T);
  let dx = p.x - prev.x, dy = p.y - prev.y; const n = Math.hypot(dx, dy) || 1; dx /= n; dy /= n;
  const bb = BODY[target], box = [ox + bb[0] + MARGIN, ox + bb[1] - MARGIN, GROUND + bb[2] + MARGIN, GROUND + bb[3] - MARGIN];
  for (let k = -2; k <= 2; k++) { const s = seg / 4 * k; if (distToBox(p.x + dx * s, p.y + dy * s, box) <= r) return true; }
  return false;
}
const stats = {};
for (const w of HEROES) { stats[w] = { paths: 0, overlap: 0, overlapNoHit: 0, hitNoOverlap: 0, causes: { above: 0, below: 0, side: 0 }, examples: [] }; }
let nPaths = 0;
for (const sx of [240, 460, 680]) for (let ang = 25; ang <= 80; ang += 3) for (let pw = 15; pw <= 100; pw += 1) for (let wd = -4; wd <= 4; wd += 2) {
  const r = Flight.simulate({ startX: sx + MUZZLE, startY: START_Y, dirX: 1, angleDeg: ang, power: pw, wind: wd });
  const pts = r.points; nPaths++;
  for (const tx of [1240, 1460, 1680]) {
    let near = false; for (const q of pts) if (Math.abs(q.x - tx) < 260) { near = true; break; }
    if (!near) continue;
    for (const weapon of HEROES) for (const target of HEROES) {
      if (weapon === 'bride') continue;   // the wave is landing-based by owner design; reported separately below
      const S = stats[weapon]; S.paths++;
      let hitAt = -1, ovAt = -1, ovPt = null;
      for (let i = 1; i < pts.length; i++) {
        if (hitAt < 0 && hitRule(pts[i], tx, target, weapon)) hitAt = i;
        if (ovAt < 0 && overlaps(pts[i], pts[i - 1], weapon, tx, target)) { ovAt = i; ovPt = pts[i]; }
        if (hitAt >= 0) break;   // the page stops the shot at its first hit
      }
      if (ovAt >= 0) { S.overlap++; if (hitAt < 0) { S.overlapNoHit++; const c = ovPt.y < GROUND - 190 ? 'above' : (ovPt.y > GROUND ? 'below' : 'side'); S.causes[c]++; if (S.examples.length < 3) S.examples.push({ target, sx, ang, pw, wd, tx, at: [Math.round(ovPt.x), Math.round(ovPt.y)], cause: c }); } }
      else if (hitAt >= 0) S.hitNoOverlap++;
    }
  }
}
// the wave: counts only where it lands (within 105 px, bands 100/75/50 percent at 40/75/105) by design; how often does it cross a body in the air without damage?
const wave = { overlapInAir: 0, landsInRange: 0, airNoDamage: 0 };
for (const sx of [240, 460, 680]) for (let ang = 25; ang <= 80; ang += 3) for (let pw = 15; pw <= 100; pw += 1) for (let wd = -4; wd <= 4; wd += 2) {
  const r = Flight.simulate({ startX: sx + MUZZLE, startY: START_Y, dirX: 1, angleDeg: ang, power: pw, wind: wd }), pts = r.points;
  for (const tx of [1240, 1460, 1680]) for (const target of HEROES) {
    let ov = false; for (let i = 1; i < pts.length; i++) if (overlaps(pts[i], pts[i - 1], 'bride', tx, target)) { ov = true; break; }
    if (!ov) continue; wave.overlapInAir++;
    const lands = r.hit === 'ground' && Math.abs(r.landingX - tx) <= 105;
    if (lands) wave.landsInRange++; else wave.airNoDamage++;
  }
}
const out = { paths: nPaths, margin: MARGIN, byWeapon: {}, wave };
console.log('paths ' + nPaths + '; overlap = drawn projectile penetrates the body box by >= ' + MARGIN + ' px; hit = the page rule');
console.log('weapon     evals   overlap  overlap-no-hit (share)  above/below/side        hit-without-overlap');
for (const w of HEROES) { if (w === 'bride') continue; const S = stats[w]; out.byWeapon[w] = S;
  console.log(w.padEnd(10) + String(S.paths).padEnd(8) + String(S.overlap).padEnd(9) + (String(S.overlapNoHit) + ' (' + (100 * S.overlapNoHit / Math.max(1, S.overlap)).toFixed(1) + '%)').padEnd(24) + (S.causes.above + '/' + S.causes.below + '/' + S.causes.side).padEnd(20) + S.hitNoOverlap); }
console.log('bride wave: crossings of a body in the air ' + wave.overlapInAir + ', of which land within 105 px: ' + wave.landsInRange + ', no damage: ' + wave.airNoDamage + ' (' + (100 * wave.airNoDamage / Math.max(1, wave.overlapInAir)).toFixed(1) + '%)');
if (OUT) fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n');
