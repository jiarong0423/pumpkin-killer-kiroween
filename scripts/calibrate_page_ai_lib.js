#!/usr/bin/env node
'use strict';
// Calibration of the page computer by the REAL page: one-unit matches in the Node vm harness (scripts/page_harness.js + scripts/page_match_driver.js, plain throws only),
// both sides at the same level, every hero, many seeds. Reports direct hits per throw (a throw with at least one direct hit counts once) and the match length per level.
// Targets (owner 2026-11-17): easy 0.15, normal 0.30, hard 0.45. The old AI measured 0.43 / 0.54 / 0.87 (docs/GAP_QUEUE_OPEN_20261117.md).
//   node scripts/calibrate_page_ai.js [--per-hero N] [--size 1] [--seed-base 31000] [--json]
// Exit code 0 always (a measurement, not a test); scripts/test_page_ai_hit_rates.js pins the bands.
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');

const seedBaseDefault = 31000;
function measure(level, perHero, size, seedBase) {
  let throws = 0, hits = 0, rounds = 0, matches = 0, errors = 0, finished = 0;
  D.HEROES.forEach((hero, hi) => {
    for (let k = 0; k < perHero; k++) {
      const seed = seedBase + 1000 * ['easy', 'normal', 'hard'].indexOf(level) + 100 * hi + k;
      const P = loadPage({ team: size, seed });
      vm.runInContext(D.source, P.context, { filename: 'page_match_driver.js' });
      const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify({ hero, size, seed, tierLeft: level, tierRight: level, plainOnly: true }) + ')', P.context)));
      matches++; throws += rec.throws; hits += rec.direct_hits; rounds += rec.rounds; errors += rec.errors.length;
      if (rec.winner !== 'none') finished++;
    }
  });
  const rate = hits / throws;
  const z = 1.96, centre = (rate + z * z / (2 * throws)) / (1 + z * z / throws), radius = z * Math.sqrt(rate * (1 - rate) / throws + z * z / (4 * throws * throws)) / (1 + z * z / throws);
  return { level, matches, finished, throws, hits, rate, ciLow: centre - radius, ciHigh: centre + radius, rounds: rounds / matches, errors };
}
module.exports = { measure };
