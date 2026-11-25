#!/usr/bin/env node
'use strict';
// ROOM-FLOW R7: the page's name cleaner (js/relay_client.js) against the golden vectors shared with the relay, and the wire fields it sends.
const assert = require('assert');
const R = require('../js/relay_client.js');
const vectors = require('./name_vectors.json');

let failed = 0;
function check(name, fn) { try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.error('FAIL - ' + name + '\n       ' + e.message.split('\n')[0]); } }

vectors.forEach(v => check('vector ' + v.case, () => assert.strictEqual(R.cleanName(v.in), v.out)));
check('not a string is empty', () => [null, undefined, 5, [], {}].forEach(x => assert.strictEqual(R.cleanName(x), '')));
check('create, join, ready and set_name send the cleaned name', () => {
  const sent = [], socket = { readyState: 1, send: raw => sent.push(JSON.parse(raw)), close() {} };
  const make = () => R.createClient({ socketFactory: () => socket, now: () => 0, setTimeoutFn: () => 0 });
  make().createRoom({ name: ' a\u200bb ' });
  const c = make(); c.join('abc234', 'white', { name: '小明小明小明' }); c.sendReady({ name: 'z' }); c.setName('\u202eq');
  assert.deepStrictEqual(sent.map(m => [m.type, m.name]), [['create_room', 'ab'], ['join', '小明小明小'], ['ready', 'z'], ['set_name', 'q']]);
});
console.log('test_name_rules: ' + (failed ? failed + ' FAILED' : 'OK'));
process.exitCode = failed ? 1 : 0;
