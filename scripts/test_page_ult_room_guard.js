#!/usr/bin/env node
'use strict';
/*
 * M6 (Z8): the page's own ultimate button in a ROOM. The knight's and the necromancer's ultimates must be refused (nothing armed, nothing placed, the hint shown),
 * the other six must arm normally; outside a room every hero arms (the knight starts its placing). Runs the page's real `toggleUltimate` in the node vm.
 * Run: node scripts/test_page_ult_room_guard.js      Exit 0 = pass, 1 = fail.
 */
const assert = require('assert');
const { loadPage } = require('./page_harness');

function press(hero, inRoom, mutate) {
  const P = loadPage(mutate ? { team: 3, mutate } : { team: 3 });
  P.eval('matchStarted = true; gameOver = false; turn = "player"; currentHero = ' + JSON.stringify(hero) + '; energy.player = 3; ultUsed.player = 0; ultArmed.player = false; defendMode = false; knightPlacing = false;');
  if (inRoom) P.eval('relayPlaying = true; relayClient = {}; relayRoomCode = "TESTRM";');
  const before = P.eval('floatTexts.length');
  P.eval('toggleUltimate()');
  return {
    armed: P.eval('ultArmed.player'), placing: P.eval('knightPlacing'), defend: P.eval('defendMode'),
    texts: P.eval('floatTexts.slice(' + before + ').map(f => f.text)').map(String)
  };
}

let failed = 0;
function check(name, fn) { try { fn(); console.log('ok   - ' + name); } catch (e) { failed++; console.error('FAIL - ' + name + '\n       ' + String(e && e.message ? e.message : e)); } }

for (const hero of ['knight', 'reaper']) {
  check(hero + ': refused in a room (nothing armed, nothing placed, hint shown)', () => {
    const r = press(hero, true);
    assert.strictEqual(r.armed, false, 'ultArmed must stay false');
    assert.strictEqual(r.placing, false, 'knightPlacing must stay false');
    assert.strictEqual(r.defend, false, 'defendMode must stay false');
    assert.ok(r.texts.length >= 1, 'the hint was not shown: ' + JSON.stringify(r.texts));
  });
}
for (const hero of ['skeleton', 'wizard', 'bat', 'bride', 'hunchback', 'hag']) {
  check(hero + ': arms in a room', () => {
    const r = press(hero, true);
    assert.strictEqual(r.armed, true, 'the ultimate did not arm: ' + JSON.stringify(r));
  });
}
check('reaper outside a room arms (the refusal is room-only)', () => { assert.strictEqual(press('reaper', false).armed, true); });
check('knight outside a room starts its placing (the refusal is room-only)', () => { const r = press('knight', false); assert.ok(r.placing || r.defend || r.armed, JSON.stringify(r)); });

check('mutant: without the guard line the necromancer ultimate would arm in a room (the test must notice)', () => {
  const r = press('reaper', true, [['if (relayLive() && (currentHero === "knight" || currentHero === "reaper")) { relayNote("relay.noItems"); return; }', '']]);
  assert.strictEqual(r.armed, true, 'the mutant should arm; the refusal test above would then fail');
});

if (failed) { console.error('test_page_ult_room_guard: ' + failed + ' FAILED'); process.exit(1); }
console.log('test_page_ult_room_guard: OK');
