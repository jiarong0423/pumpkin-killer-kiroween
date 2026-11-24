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

const { measure } = require('./calibrate_page_ai_lib');
const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf('--' + name); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : def; };
const perHero = Number(opt('per-hero', 6)), size = Number(opt('size', 1)), seedBase = Number(opt('seed-base', 31000));

const rows = ['easy', 'normal', 'hard'].map(l => measure(l, perHero, size, seedBase));
if (argv.includes('--json')) console.log(JSON.stringify(rows));
else {
  console.log('| level | matches | throws | direct hits | hits per throw | 95% interval | rounds per match | target |');
  console.log('|---|---:|---:|---:|---:|---:|---:|---:|');
  const target = { easy: 0.15, normal: 0.30, hard: 0.45 };
  rows.forEach(r => console.log(`| ${r.level} | ${r.matches} | ${r.throws} | ${r.hits} | ${r.rate.toFixed(3)} | ${r.ciLow.toFixed(3)}-${r.ciHigh.toFixed(3)} | ${r.rounds.toFixed(1)} | ${target[r.level].toFixed(2)} |`));
  if (rows.some(r => r.errors)) console.log('ERRORS in ' + rows.filter(r => r.errors).map(r => r.level).join(', '));
}
