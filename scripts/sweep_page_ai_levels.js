'use strict';
/*
 * Calibrates the browser opponent without giving it a ballistic solver.
 * Physics and prior_wind decision math copy scripts/sim_ai_nosim.js lines 14-50.
 */
const AiLevelsPage = require('../js/ai_levels_page.js');

const DEFAULT_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808];
const ROUNDS_PER_MATCH = 8;
const WIND_K = 4;
const GRAVITY = 980;
const WIND_ACCEL = 108;
const GROUND_Y = 860;
const ANGLE = 54;

function seededRandom(seed) {
  let state = seed >>> 0;
  return function random() {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function fly(power, sx, sy, wind, playerX) {
  const dt = 1 / 60;
  const rad = ANGLE * Math.PI / 180;
  const v0 = power * 13.8;
  let vx = -v0 * Math.cos(rad);
  let vy = -v0 * Math.sin(rad);
  let x = sx;
  let y = sy;
  for (let step = 0; step < 1200; step += 1) {
    vx += wind * WIND_ACCEL * dt;
    vy += GRAVITY * dt;
    x += vx * dt;
    y += vy * dt;
    if (x > 895 && x < 1025 && y > 610) return { hit: false, x };
    if (Math.abs(x - playerX) <= 70 && y >= GROUND_Y - 190 && y <= GROUND_Y) return { hit: true, x };
    if (y >= GROUND_Y && vy > 0) break;
  }
  return { hit: false, x };
}

function landing(power, sx, sy, wind) {
  const dt = 1 / 60;
  const rad = ANGLE * Math.PI / 180;
  const v0 = power * 13.8;
  let vx = -v0 * Math.cos(rad);
  let vy = -v0 * Math.sin(rad);
  let x = sx;
  let y = sy;
  for (let step = 0; step < 1200; step += 1) {
    vx += wind * WIND_ACCEL * dt;
    vy += GRAVITY * dt;
    x += vx * dt;
    y += vy * dt;
    if (y >= GROUND_Y && vy > 0) break;
  }
  return x;
}

function wilsonInterval(hits, throws) {
  if (!throws) return [0, 0];
  const z = 1.959963984540054;
  const rate = hits / throws;
  const denominator = 1 + z * z / throws;
  const centre = (rate + z * z / (2 * throws)) / denominator;
  const radius = z * Math.sqrt(rate * (1 - rate) / throws + z * z / (4 * throws * throws)) / denominator;
  return [centre - radius, centre + radius];
}

function measureLevel(levelNumber, totalThrows = 4000, seeds = DEFAULT_SEEDS) {
  if (!Number.isInteger(totalThrows) || totalThrows < 1) throw new RangeError('totalThrows must be a positive integer');
  if (!Array.isArray(seeds) || seeds.length !== 8) throw new RangeError('exactly eight fixed seeds are required');
  const knobs = AiLevelsPage.knobsFor(levelNumber);
  let hits = 0;
  let firstHits = 0;
  let firstThrows = 0;
  let laterHits = 0;
  let laterThrows = 0;
  let throwIndex = 0;
  for (let seedIndex = 0; seedIndex < seeds.length; seedIndex += 1) {
    const random = seededRandom(seeds[seedIndex]);
    const limit = Math.floor(totalThrows / seeds.length) + (seedIndex < totalThrows % seeds.length ? 1 : 0);
    let cal = 1;
    for (let localIndex = 0; localIndex < limit; localIndex += 1) {
      const round = localIndex % ROUNDS_PER_MATCH;
      if (round === 0) cal = 1;
      const aiX = 1160 + random() * 600;
      const playerX = 160 + random() * 600;
      const wind = Math.round((random() * 2 - 1) * 4);
      const seenX = Math.round((playerX + (random() * 2 - 1) * knobs.viewPosNoise) / 36) * 36;
      const seenWind = wind + (random() * 2 - 1) * knobs.viewWindNoise;
      const sx = aiX - 58;
      const sy = GROUND_Y - 110;
      let power = cal * 2.32 * Math.sqrt(Math.max(50, sx - seenX)) + WIND_K * seenWind;
      power += (random() - 0.5) * 2 * knobs.aimError;
      power = Math.max(30, Math.min(100, power));
      const result = fly(power, sx, sy, wind, playerX);
      const hit = result.hit;
      hits += Number(hit);
      if (round < 3) {
        firstThrows += 1;
        firstHits += Number(hit);
      } else {
        laterThrows += 1;
        laterHits += Number(hit);
      }
      const reach = sx - landing(power, sx, sy, wind);
      const wanted = sx - seenX;
      if (reach > 80) cal = Math.max(0.7, Math.min(1.4, cal * Math.pow(wanted / reach, 0.5 * 0.7)));
      throwIndex += 1;
    }
  }
  if (throwIndex !== totalThrows) throw new Error('incorrect throw allocation');
  const interval = wilsonInterval(hits, totalThrows);
  return {
    level: AiLevelsPage.levelName(levelNumber),
    throws: totalThrows,
    hits,
    hitRate: hits / totalThrows,
    ciLow: interval[0],
    ciHigh: interval[1],
    firstThreeRate: firstHits / firstThrows,
    throwsFourToEightRate: laterHits / laterThrows
  };
}

function runSweep(totalThrows = 4000, seeds = DEFAULT_SEEDS) {
  return [1, 2, 3].map((level) => measureLevel(level, totalThrows, seeds));
}

function renderTable(rows) {
  const lines = [
    '| level | throws | hits | hit rate | 95% Wilson interval | throws 1-3 | throws 4-8 |',
    '|---|---:|---:|---:|---:|---:|---:|'
  ];
  for (const row of rows) {
    lines.push(`| ${row.level} | ${row.throws} | ${row.hits} | ${(row.hitRate * 100).toFixed(1)}% | ${(row.ciLow * 100).toFixed(1)}%-${(row.ciHigh * 100).toFixed(1)}% | ${(row.firstThreeRate * 100).toFixed(1)}% | ${(row.throwsFourToEightRate * 100).toFixed(1)}% |`);
  }
  return lines;
}

function parseThrows(argv) {
  const index = argv.indexOf('--throws');
  if (index === -1) return 4000;
  const value = Number(argv[index + 1]);
  if (!Number.isInteger(value) || value < 1) throw new RangeError('--throws needs a positive integer');
  return value;
}

if (require.main === module) {
  const rows = runSweep(parseThrows(process.argv.slice(2)));
  for (const line of renderTable(rows)) console.log(line);
  const ordered = rows[0].hitRate < rows[1].hitRate && rows[1].hitRate < rows[2].hitRate;
  const separate = rows[0].ciHigh < rows[1].ciLow && rows[1].ciHigh < rows[2].ciLow;
  console.log(ordered && separate ? 'PASS: ordered, non-overlapping level rates' : 'FAIL: level rates overlap or are unordered');
  process.exitCode = ordered && separate ? 0 : 1;
}

module.exports = { DEFAULT_SEEDS, measureLevel, runSweep, renderTable, wilsonInterval };
