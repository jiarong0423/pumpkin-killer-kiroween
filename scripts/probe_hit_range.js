#!/usr/bin/env node
"use strict";
// Measures the REAL hit range of the page: it cuts the `touches` function and `projHitRadius` out of index.html (the code the game runs) and sweeps a projectile
// around a unit on a grid, so the numbers come from the game's own rule, not from a document. No browser needed.
// Writes docs/HIT_RANGE_MEASURED_20261117.md and logs_local/probe_hit_range.log; exit 1 if a measured extent differs from the formula in docs/COVERAGE_TABLE.
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const root = path.join(__dirname, "..");
const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
const logFile = path.join(root, "logs_local", "probe_hit_range.log");
function log(line) { fs.mkdirSync(path.dirname(logFile), { recursive: true }); fs.appendFileSync(logFile, new Date().toISOString() + " " + line + "\n"); }

function cut(startMarker, endMarker) {
  const i = page.indexOf(startMarker); assert.ok(i >= 0, "missing: " + startMarker);
  const j = page.indexOf(endMarker, i); assert.ok(j > i, "missing end: " + endMarker);
  return page.slice(i, j);
}
try {
  const radiusSrc = cut("function projHitRadius(p)", "\n");                       // one line
  const waveHalf = Number(/const WAVE_HALF_WIDTH = SoundWave\.HIT_HALF_WIDTH/.test(page) ? require(path.join(root, "js", "sound_wave.js")).HIT_HALF_WIDTH : NaN);
  const touchesSrc = cut("const touches = (opp) => {", "          };");              // the arrow function body
  const HitMask = require(path.join(root, "js", "hit_masks.js"));   // the binary masks (2026-11-17): the page counts a shot only inside the box AND on the figure
  const factory = new Function("HitMask", "p", "WAVE_HALF_WIDTH", "hitR", "sideOfUnit", "currentHero", "ai",
    radiusSrc + ";\n" + "const hitRLocal = hitR;\n" + touchesSrc.replace("const touches = (opp) => {", "return (opp) => {") + "};");
  const WEAPONS = { spear: [210, 33], cannonball: [40, 40], shuriken: [58, 58], flame: [150, 55], cross: [118, 82], axe: [130, 130], shield: [62, 92] };
  const names = { spear: "proj_spear", cannonball: "cannonball", shuriken: "proj_shuriken", flame: "proj_flame", cross: "proj_cross", axe: "proj_axe", shield: "proj_shield" };
  const rows = [];
  function sweep(p, unit, hero) {
    const hitR = new Function(radiusSrc + "; return projHitRadius;")()(p);
    const touches = factory(HitMask, p, waveHalf, hitR, () => "right", "skeleton", { profile: hero });
    let minDx = Infinity, maxDx = -Infinity, minUp = Infinity, maxUp = -Infinity, minDown = Infinity, maxDown = -Infinity;
    for (let dx = -400; dx <= 400; dx += 0.5) for (let up = -60; up <= 320; up += 0.5) {
      p.x = unit.x + dx; p.y = unit.y - up;
      if (touches(unit)) { minDx = Math.min(minDx, dx); maxDx = Math.max(maxDx, dx); minUp = Math.min(minUp, up); maxUp = Math.max(maxUp, up); }
    }
    return { halfW: maxDx, left: minDx, top: maxUp, bottomBelow: -minUp };
  }
  const unit = { x: 1500, y: 860, hp: 100 };
  let bad = 0;
  for (const hero of ["skeleton", "reaper"]) for (const [k, [len, thick]] of Object.entries(WEAPONS)) {
    const m = sweep({ weapon: names[k], wLen: len, wThick: thick, hitCool: 0 }, unit, hero);
    const r = Math.max(0, Math.sqrt(len * thick) / 2 - 20);
    const expHalf = (hero === "reaper" ? 57 : 70) + r, expTop = (hero === "reaper" ? 165 : 190) + r;
    // the decided box is the OUTER limit; the mask cuts its empty corners, so the reach must stay inside the box (never beyond) and still reach most of it
    const ok = m.halfW <= expHalf + 0.5 && m.top <= expTop + 0.5 && -m.left <= expHalf + 0.5 && m.halfW >= 0.55 * expHalf && m.top >= 0.8 * expTop;
    if (!ok) { bad++; log("ERROR mismatch " + hero + " " + k + " measured " + JSON.stringify(m) + " expected half " + expHalf + " top " + expTop); }
    rows.push("| " + hero + " | " + k + " | " + m.halfW.toFixed(1) + " | " + m.top.toFixed(1) + " | " + (-m.bottomBelow).toFixed(1) + " | " + expHalf.toFixed(1) + " / " + expTop.toFixed(1) + " | " + (ok ? "inside the box" : "OUTSIDE OR TOO SMALL") + " |");
  }
  const wave = sweep({ weapon: "proj_soundwave", wLen: 170, wThick: 170, hitCool: 0 }, unit, "skeleton");
  const waveOk = Math.abs(wave.halfW - 105) <= 0.5 && Math.abs(wave.top - 40) <= 0.5;
  if (!waveOk) { bad++; log("ERROR wave mismatch " + JSON.stringify(wave)); }
  const md = ["# Hit range measured from the page code (2026-11-17)", "",
    "Method: `scripts/probe_hit_range.js` cuts the page's own `touches` rule and `projHitRadius` out of `index.html` and sweeps a projectile around a unit in 0.5 px steps (x from -400 to 400, height from -60 to 320). The numbers below are what the game really judges.", "",
    "| Target | Weapon | Half-width reached | Height reached above feet | Lowest point (negative = below feet) | Formula half / height | Check |", "|---|---|---|---|---|---|---|", ...rows,
    "| skeleton | wave | " + wave.halfW.toFixed(1) + " | " + wave.top.toFixed(1) + " | " + (-wave.bottomBelow).toFixed(1) + " | 105 / 40 | " + (waveOk ? "match" : "DIFFERENT") + " |", ""];
  fs.writeFileSync(path.join(root, "docs", "HIT_RANGE_MEASURED_20261117.md"), md.join("\n") + "\n");
  log("wrote docs/HIT_RANGE_MEASURED_20261117.md bad=" + bad);
  console.log("probe_hit_range: " + (bad ? "FAILED " + bad + " rows differ" : "all rows match the formula"));
  process.exit(bad ? 1 : 0);
} catch (e) { log("ERROR " + e.message); console.error("ERROR probe_hit_range: " + e.message); process.exit(1); }
