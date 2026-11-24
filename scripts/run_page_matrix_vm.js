#!/usr/bin/env node
'use strict';
// Front-end matrix without a browser: 8 heroes x 3 sizes x 10 seeds = 240 matches of the REAL index.html script in the Node vm
// harness (scripts/page_harness.js), driven by scripts/page_match_driver.js. Spec: docs/MATRIX_SPEC_20261117.md.
//   node scripts/run_page_matrix_vm.js [--per-cell N] [--hero name] [--size N] [--out file] [--rich]
// Writes logs_local/matrix_page_vm.json ({ end, started, matches }) and prints a table by (hero, size).
// Exit code 1 when any match recorded an error. No network. Each match gets a freshly loaded page (no state carried over).
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { loadPage } = require('./page_harness');
const D = require('./page_match_driver');

const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf('--' + name); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : def; };
const perCell = Number(opt('per-cell', 10));
const onlyHero = opt('hero', null), onlySize = opt('size', null);
const fromPlay = Number(opt('from', 0)), toPlay = Number(opt('to', perCell));   // a play range (k): a long run is cut into short processes because every match leaves about 1 MB behind in this process
const plainOnly = !argv.includes('--rich');   // default: plain throws only on both seats (like the engine bot); --rich = the page's full AI
const outFile = path.resolve(opt('out', path.join(__dirname, '..', 'logs_local', plainOnly ? 'matrix_page_vm.json' : 'matrix_page_vm_rich.json')));

function playOne(cell) {
  const t0 = Date.now();
  try {
    const P = loadPage({ team: cell.size, seed: cell.seed });
    vm.runInContext(D.source, P.context, { filename: 'page_match_driver.js' });
    const rec = JSON.parse(JSON.stringify(vm.runInContext('runPageMatch(' + JSON.stringify(Object.assign({}, cell, { plainOnly })) + ')', P.context)));
    rec.ms = Date.now() - t0;
    return rec;
  } catch (e) {
    return { options: { plainOnly }, end: 'page', hero: cell.hero, hero_right: null, size: cell.size, seed: cell.seed, tier_left: null, tier_right: null, winner: 'none', rounds: 0, hp_share_left: null, hp_share_right: null, units_left_alive: null, units_right_alive: null, throws: 0, direct_hits: 0, near_misses: null, pity_triggers: null, comeback_hits: null, ultimates_left: null, ultimates_right: null, errors: ['runner: ' + String(e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e)], ms: Date.now() - t0 };
  }
}

function table(matches) {
  const lines = [['hero', 'size', 'n', 'rounds', 'left win', 'cap end', 'hits/throw', 'comeback', 'pity', 'errors'].map((h, i) => (i < 2 ? h.padEnd(10) : h.padStart(10))).join(' ')];
  for (const hero of D.HEROES) for (const size of [1, 2, 3]) {
    const m = matches.filter(x => x.hero === hero && x.size === size);
    if (!m.length) continue;
    const mean = a => a.reduce((s, v) => s + v, 0) / (a.length || 1);
    const win = m.filter(x => x.winner === 'left' || x.winner === 'cap_left').length / m.length;
    const cap = m.filter(x => /^cap_/.test(x.winner)).length;
    const hits = m.reduce((s, x) => s + x.direct_hits, 0) / Math.max(1, m.reduce((s, x) => s + x.throws, 0));
    const cb = size > 1 ? mean(m.map(x => x.comeback_hits || 0)).toFixed(1) : '-', py = size > 1 ? mean(m.map(x => x.pity_triggers || 0)).toFixed(1) : '-';
    const err = m.reduce((s, x) => s + x.errors.length, 0) + m.filter(x => x.winner === 'none').length * 0;
    lines.push([hero.padEnd(10), String(size).padEnd(10), String(m.length).padStart(10), mean(m.map(x => x.rounds)).toFixed(1).padStart(10), (win * 100).toFixed(0).padStart(9) + '%', String(cap).padStart(10), hits.toFixed(2).padStart(10), String(cb).padStart(10), String(py).padStart(10), String(err).padStart(10)].join(' '));
  }
  const all = matches, mean = a => a.reduce((s, v) => s + v, 0) / (a.length || 1);
  for (const size of [1, 2, 3]) {
    const m = all.filter(x => x.size === size); if (!m.length) continue;
    lines.push(('ALL size ' + size).padEnd(10) + ' ' + ('').padEnd(10) + ' ' + String(m.length).padStart(10) + ' ' + mean(m.map(x => x.rounds)).toFixed(1).padStart(10) + ' ' + ((m.filter(x => x.winner === 'left' || x.winner === 'cap_left').length / m.length * 100).toFixed(0) + '%').padStart(10) + ' ' + String(m.filter(x => /^cap_/.test(x.winner)).length).padStart(10));
  }
  return lines.join('\n');
}

const started = new Date().toISOString();
const t0 = Date.now();
const cells = D.cells(Math.max(perCell, toPlay)).filter(c => (!onlyHero || c.hero === onlyHero) && (!onlySize || String(c.size) === String(onlySize)) && c.k >= fromPlay && c.k < toPlay);
const matches = [];
for (const cell of cells) {
  const rec = playOne(cell);
  matches.push(rec);
  if (matches.length % 20 === 0) process.stderr.write('  ' + matches.length + '/' + cells.length + ' matches, ' + ((Date.now() - t0) / 1000).toFixed(0) + ' s\n');
}
fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, JSON.stringify({ end: 'page', source: 'vm', options: { plainOnly }, started, finished: new Date().toISOString(), matches }, null, 1) + '\n');
console.log(table(matches));
const errored = matches.filter(m => m.errors.length);
const noWinner = matches.filter(m => m.winner === 'none');
console.log('run_page_matrix_vm: ' + matches.length + ' matches in ' + ((Date.now() - t0) / 1000).toFixed(1) + ' s, ' + errored.length + ' with errors, ' + noWinner.length + ' without a winner -> ' + path.relative(path.join(__dirname, '..'), outFile));
for (const m of errored.slice(0, 10)) console.log('ERROR seed ' + m.seed + ' (' + m.hero + ' x' + m.size + '): ' + m.errors[0].slice(0, 200));
if (errored.length) process.exitCode = 1;
