#!/usr/bin/env node
'use strict';
// Owner 2026-11-18: "the move sound is stuck too long". The dice roll used to start the 6 s power-charge hum (event charge, a loop nothing stopped). startDiceRoll must play the dice rattle and nothing that loops.
const assert = require('assert');
const { loadPage } = require('./page_harness');
const P = loadPage({ team: 1, seed: 5 });
const src = P.eval('startDiceRoll.toString()');
assert.ok(/snd\("dice_rattle"\)/.test(src), 'the dice rattle is played');
assert.ok(!/sfx\.charge\(\)|"charge"/.test(src.replace(/\/\/[^\n]*/g, '')), 'the roll must not start the charge hum');
const A = require('../js/audio.js'); const ev = (A.DEFAULT_EVENT_MAP.events || A.DEFAULT_EVENT_MAP).dice_rattle;
assert.ok(!ev.loop && ev.duration <= 0.6, 'the rattle is short and does not loop: ' + ev.duration);
console.log('ok   - the dice roll plays a short rattle and does not start the charge hum');
console.log('test_dice_no_charge: 1 ok, 0 failed');
