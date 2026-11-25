'use strict';
// Runs scripts/sim_items_landing.js small (40 seeds) and its two negative controls: the real page must pass, each broken copy must FAIL.
const assert = require('assert'), { spawnSync } = require('child_process'), path = require('path');
const run = args => spawnSync('node', [path.join(__dirname, 'sim_items_landing.js'), '--seeds', '40'].concat(args), { encoding: 'utf8', timeout: 120000 });
const ok = run([]);
assert.strictEqual(ok.status, 0, 'the real page must pass: ' + ok.stdout.slice(-400));
for (const m of ['--mutant-far', '--mutant-fence']) {
  const r = run([m]);
  assert.strictEqual(r.status, 1, m + ' must make the simulation FAIL (a check that never fails proves nothing): ' + r.stdout.slice(-300));
}
console.log('test_items_landing: OK (real page passes, both mutants fail)');
