#!/usr/bin/env node
'use strict';
// Measure the page computer's direct hits per throw at other AI_LEVEL_MULTIPLIERS values (owner 2026-11-19: "the computer is too weak, raise its strength 5-7%").
// Same matches as scripts/calibrate_page_ai.js (same seeds), the page constant replaced through the harness mutation, so nothing on disk changes.
//   node scripts/sweep_ai_multiplier.js --level normal --values 0.52,0.6,0.5 [--per-hero 12] [--seed-base 31000]
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');
const argv = process.argv.slice(2), opt = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : d; };
const level = opt('level', 'normal'), values = opt('values', '0.52').split(',').map(Number), perHero = +opt('per-hero', 12), seedBase = +opt('seed-base', 31000);
const CUR = { easy: 2.25, normal: 0.52, hard: 0.27 };
const MODEL = argv.includes('--model');
const ANGLE = argv.includes('--angle-min');   // sweep AI_ANGLE_MIN_BY_LEVEL[level] (hard 42 now; 25 reproduces the capped 0.384 of commit 23a02165) for BOTH seats; red-team H1 R1-B2: it used to mutate AI_ANGLE_MIN, which the table overrides, and printed the same number for every value   // sweep AI_MODEL_SCALE[level] (1.5 / 1 / 0.6) instead of AI_LEVEL_MULTIPLIERS
for (const v of values) {
  const from = level + ': ' + CUR[level] + ' ' , cur = 'AI_LEVEL_MULTIPLIERS = Object.freeze({ easy: 2.25, normal: 0.52, hard: 0.27 });';
  const to = 'AI_LEVEL_MULTIPLIERS = Object.freeze({ easy: ' + (level === 'easy' ? v : 2.25) + ', normal: ' + (level === 'normal' ? v : 0.52) + ', hard: ' + (level === 'hard' ? v : 0.27) + ' });';
  const MCUR = 'AI_MODEL_SCALE = Object.freeze({ easy: 1.5, normal: 1, hard: 0.6 });', MTO = 'AI_MODEL_SCALE = Object.freeze({ easy: ' + (level === 'easy' ? v : 1.5) + ', normal: ' + (level === 'normal' ? v : 1) + ', hard: ' + (level === 'hard' ? v : 0.6) + ' });';
  const ACUR = 'AI_ANGLE_MIN_BY_LEVEL = Object.freeze({ easy: 25, normal: 25, hard: 42 });', ATO = 'AI_ANGLE_MIN_BY_LEVEL = Object.freeze({ easy: ' + (level === 'easy' ? v : 25) + ', normal: ' + (level === 'normal' ? v : 25) + ', hard: ' + (level === 'hard' ? v : 42) + ' });';
  const mut = ANGLE ? [[ACUR, ATO]] : MODEL ? [[MCUR, MTO]] : [[cur, to]];
  let throws = 0, hits = 0, matches = 0, rounds = 0, errors = 0;
  D.HEROES.forEach((hero, hi) => { for (let k = 0; k < perHero; k++) {
    const seed = seedBase + 1000 * ['easy', 'normal', 'hard'].indexOf(level) + 100 * hi + k;
    const P = loadPage({ team: 1, seed, mutate: mut });
    vm.runInContext(D.source, P.context, { filename: 'page_match_driver.js' });
    const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify({ hero, size: 1, seed, tierLeft: level, tierRight: level, plainOnly: true }) + ')', P.context)));
    matches++; throws += rec.throws; hits += rec.direct_hits; rounds += rec.rounds; errors += rec.errors.length;
  } });
  console.log(JSON.stringify({ level, knob: ANGLE ? 'AI_ANGLE_MIN_BY_LEVEL' : MODEL ? 'AI_MODEL_SCALE' : 'AI_LEVEL_MULTIPLIERS', value: v, matches, throws, hits, rate: Math.round(hits / throws * 1000) / 1000, roundsPerMatch: Math.round(rounds / matches * 10) / 10, errors }));
}
