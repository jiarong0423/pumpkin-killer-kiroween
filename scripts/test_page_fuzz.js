'use strict';
// scripts/fuzz_page_break.js small (seed 3, 800 steps per team size) must pass; the heal-without-cap mutant must FAIL (a fuzzer that cannot fail proves nothing).
const assert = require('assert'), { spawnSync } = require('child_process'), path = require('path');
const run = args => spawnSync('node', [path.join(__dirname, 'fuzz_page_break.js'), '--seed', '3', '--steps', '800'].concat(args), { encoding: 'utf8', timeout: 120000 });
const ok = run([]); assert.strictEqual(ok.status, 0, 'real page must pass: ' + ok.stdout.slice(-400));
const bad = run(['--mutant-heal']); assert.strictEqual(bad.status, 1, 'the mutant must make the fuzzer FAIL: ' + bad.stdout.slice(-300));
assert.ok(/REPRODUCE node scripts\/fuzz_page_break\.js --seed 3/.test(bad.stdout), 'a failure must print how to reproduce it');
console.log('test_page_fuzz: OK (real page passes, mutant fails with a reproduce line)');
