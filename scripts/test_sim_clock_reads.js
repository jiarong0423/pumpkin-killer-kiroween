#!/usr/bin/env node
'use strict';
/*
 * Guard against clock- or random-driven simulation (gap N10).
 *
 * Every read of performance.now(), Date.now(), Math.random() and new Date() in index.html and js/*.js must be listed in
 * scripts/sim_clock_reads_allowlist.json with a class and a reason. A read that is not listed fails the test, so a new move that
 * "computes a position from the clock" (like the necromancer flame orbit `orbitAt`, which desynced two pages in a room) cannot arrive unnoticed.
 *
 * An entry is matched by file, the text of the line before it (`before`, first 60 characters, whitespace collapsed), the line itself (`needle`,
 * first 110 characters) and the number of reads on it (`count`). An entry with status `unreviewed` FAILS the test (every read must be reviewed by a person: set
 * `reviewed`, or fix the code); an entry with status `known_issue` (a clock-driven move that rooms refuse) is printed as a warning.
 * Stale entries (a listed read that is gone or changed) also fail, so the list stays exact.
 *
 * Run: node scripts/test_sim_clock_reads.js      Exit 0 = pass, 1 = fail.
 *      node scripts/test_sim_clock_reads.js --suggest   also prints allowlist entry skeletons for unlisted reads (class and why are left for a person to fill in).
 *
 * Editing the line before a listed read, or the read's own line, makes the entry stale on purpose: look at the read again and update the entry.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const ALLOWLIST = path.join(__dirname, 'sim_clock_reads_allowlist.json');
// calls AND references (`rng: Math.random`, `const f = Date.now`), plus the bracket form Math['random']
const TOKEN = /performance\.now\b|Date\.now\b|Math\.random\b|Math\s*\[\s*['"]random['"]\s*\]|new Date\(/g;
const CLASSES = new Set(['draw', 'ui_input', 'ai_choice', 'setup', 'seed_source', 'net', 'wind_replaced', 'seeded_in_rooms', 'local_dice', 'frame_dt', 'known_issue_sim_clock', 'known_issue_sim_random', 'rng_plumbing', 'sound']);
const STATUSES = new Set(['reviewed', 'unreviewed', 'known_issue']);

function norm(text, max) { return text.trim().split(/\s+/).join(' ').slice(0, max); }

// Returns every read as { file, line, before, needle, count, text }.
function scan(file, source) {
  const lines = source.split('\n');
  const found = [];
  lines.forEach((text, i) => {
    const trimmed = text.trim();
    if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*')) return;
    const count = (text.match(TOKEN) || []).length;
    if (!count) return;
    let j = i - 1;
    while (j >= 0 && !lines[j].trim()) j--;
    found.push({ file, line: i + 1, before: j >= 0 ? norm(lines[j], 60) : '', needle: norm(text, 110), count, text: trimmed.slice(0, 160) });
  });
  return found;
}

// Compares reads with the allowlist: { unlisted: [...], stale: [...], ambiguous: [...], warnings: [...] }.
function check(reads, entries) {
  const tally = entries.map(() => 0);
  const unlisted = [], ambiguous = [];
  reads.forEach(read => {
    const hits = [];
    entries.forEach((entry, index) => { if (entry.file === read.file && entry.before === read.before && entry.needle === read.needle) hits.push(index); });
    if (hits.length === 0) unlisted.push(read);
    else if (hits.length > 1) ambiguous.push(read);
    else tally[hits[0]] += read.count;
  });
  const stale = [];
  entries.forEach((entry, index) => { if (tally[index] !== entry.count) stale.push({ entry, found: tally[index] }); });
  const warnings = entries.filter(entry => entry.status !== 'reviewed');
  return { unlisted, ambiguous, stale, warnings };
}

function filesToScan() {
  const files = ['index.html'];
  fs.readdirSync(path.join(ROOT, 'js')).filter(name => name.endsWith('.js')).sort().forEach(name => files.push('js/' + name));
  return files;
}

let failures = 0;
function expect(condition, message) { if (condition) return; failures++; console.error('FAIL ' + message); }

// ---- the real tree
const allow = JSON.parse(fs.readFileSync(ALLOWLIST, 'utf8'));
const entries = allow.entries;
entries.forEach((entry, i) => {
  expect(entry.file && typeof entry.needle === 'string' && Number.isInteger(entry.count) && entry.count > 0, 'entry ' + i + ' has file, needle and a positive count');
  expect(CLASSES.has(entry.class), 'entry ' + i + ' class "' + entry.class + '" is not a known class');
  expect(STATUSES.has(entry.status), 'entry ' + i + ' status "' + entry.status + '" is not known');
  expect(entry.status !== 'unreviewed', 'entry ' + i + ' is still unreviewed: ' + String(entry.needle).slice(0, 80));
  expect(typeof entry.why === 'string' && entry.why.length > 10, 'entry ' + i + ' needs a reason (why)');
});
const reads = [];
filesToScan().forEach(file => reads.push(...scan(file, fs.readFileSync(path.join(ROOT, file), 'utf8'))));
const result = check(reads, entries);
if (process.argv.includes('--suggest')) result.unlisted.forEach(read => console.log(JSON.stringify({ file: read.file, before: read.before, needle: read.needle, count: read.count, class: 'TODO', status: 'unreviewed', why: 'TODO' })));
result.unlisted.forEach(read => expect(false, 'unlisted clock/random read at ' + read.file + ':' + read.line + ': ' + read.text));
result.ambiguous.forEach(read => expect(false, 'read matches more than one entry at ' + read.file + ':' + read.line));
result.stale.forEach(item => expect(false, 'allowlist entry expects ' + item.entry.count + ' read(s) but found ' + item.found + ': ' + item.entry.needle.slice(0, 80)));

// ---- the scanner itself must catch what it is for (mutants)
expect(scan('sample.js', 'const res = resolve({ rng: Math.random });\n').length === 1, 'a reference such as `rng: Math.random` is found, not only calls');
expect(scan('sample.js', 'const r = Math["random"]();\n').length === 1, 'the bracket form Math["random"] is found');
expect(check(reads.concat(scan('index.html', 'function f() {\n  const g = resolve({ rng: Math.random });\n}\n')), entries).unlisted.length === 1, 'a new `rng: Math.random` reference added to the page would fail');
const sample = 'function a() {\n  const x = 1;\n  const orbit = performance.now() / 1000 * 1.7;\n}\n';
const sampleReads = scan('sample.js', sample);
expect(sampleReads.length === 1 && sampleReads[0].count === 1, 'scanner finds one performance.now read in the sample');
expect(check(sampleReads, []).unlisted.length === 1, 'an unlisted performance.now read is reported');
const added = reads.concat(scan('index.html', 'function newMove() {\n  const startX = u.x + Math.cos(Date.now() / 100) * 96;\n}\n'));
expect(check(added, entries).unlisted.length === 1, 'a new Date.now read added to the page would fail');
const dropped = entries.slice(1);
expect(check(reads, dropped).unlisted.length >= 1, 'removing an entry makes its read unlisted');
const grown = entries.map((entry, i) => (i === 0 ? Object.assign({}, entry, { count: entry.count + 1 }) : entry));
expect(check(reads, grown).stale.length === 1, 'an entry that expects more reads than exist is stale');
const doubled = reads.concat([Object.assign({}, reads[0], { line: 99999 })]);
expect(check(doubled, entries).stale.length >= 1, 'a second identical read makes the count wrong');

const byClass = {};
entries.forEach(entry => { byClass[entry.class] = (byClass[entry.class] || 0) + entry.count; });
console.log('reads scanned: ' + reads.reduce((sum, read) => sum + read.count, 0) + ' in ' + reads.length + ' lines; ' + entries.length + ' allowlist entries');
console.log('by class: ' + JSON.stringify(byClass));
result.warnings.forEach(entry => console.log('WARN ' + entry.status + ' [' + entry.class + '] ' + entry.needle.slice(0, 90) + ' -- ' + entry.why.slice(0, 120)));
if (failures) { console.error('test_sim_clock_reads: ' + failures + ' FAILED'); process.exit(1); }
console.log('test_sim_clock_reads: OK');
