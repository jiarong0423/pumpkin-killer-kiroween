#!/usr/bin/env node
'use strict';
/* Isolated Smart-pick gateway tests. All gateway calls are fake and local. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const begin = '/* SMART_OPPONENT_HELPERS_BEGIN */';
const end = '/* SMART_OPPONENT_HELPERS_END */';
const start = page.indexOf(begin);
const finish = page.indexOf(end);
assert(start >= 0 && finish > start, 'Smart-opponent helpers must be delimited for isolated tests');
const SmartOpponent = new Function(page.slice(start + begin.length, finish) + '\nreturn SmartOpponent;')();

function fakeResponse(ok, status, payload) {
  return { ok, status, json: async () => payload };
}

(async () => {
  const candidates = [
    { id: 1, kind: 'normal', aim: { angle: 54, power: 72 }, predicted_distance_px: 10 },
    { id: 2, kind: 'under', aim: { angle: 54, power: 69 }, predicted_distance_px: 22 },
    { id: 3, kind: 'over', aim: { angle: 54, power: 75 }, predicted_distance_px: 30 }
  ];
  const fields = {
    own_hero_id: 'skeleton', own_position: 1500, enemy_position: 360, enemy_hp: 90,
    wind: 1.2, weather: 'clear', fence_hp: 100, round_number: 1
  };
  const calls = [];
  const timers = [];
  class FakeAbortController {
    constructor() { this.signal = {}; this.aborted = false; }
    abort() { this.aborted = true; }
  }
  const deps = {
    fetchFn: async (url, options) => {
      calls.push({ url, options });
      return fakeResponse(true, 200, { ok: true, result: { pick: 2 } });
    },
    AbortControllerCtor: FakeAbortController,
    setTimeoutFn: (fn, ms) => { timers.push({ fn, ms }); return timers.length; },
    clearTimeoutFn: () => {}
  };
  const accepted = await SmartOpponent.requestPick(fields, candidates, deps);
  assert.deepStrictEqual(accepted, { ok: true, result: { pick: 2 }, status: 200, reason: 'ok' }, 'a valid choice is accepted');
  assert.strictEqual(calls.length, 1, 'the fake gateway receives one request');
  assert.strictEqual(calls[0].url, '/ai');
  const body = JSON.parse(calls[0].options.body);
  assert.deepStrictEqual(body, { prompt_kind: 'pick', fields: Object.assign({}, fields, { candidates }) });
  assert.strictEqual(timers[0].ms, 6000, 'the request timeout is six seconds');
  assert(!/slot|pending|item|secret|api.?key/i.test(JSON.stringify(body)), 'the request has no private slot data or key-shaped field');

  const invalid = await SmartOpponent.requestPick(fields, candidates, Object.assign({}, deps, {
    fetchFn: async () => fakeResponse(true, 200, { ok: true, result: { pick: 99 } })
  }));
  assert.strictEqual(invalid.ok, false, 'an id outside the supplied list is rejected');

  let timeoutTimer;
  let timeoutController;
  let rejectFetch;
  class TimeoutController {
    constructor() { this.signal = {}; timeoutController = this; }
    abort() { this.aborted = true; }
  }
  const timedOut = SmartOpponent.requestPick(fields, candidates, {
    fetchFn: () => new Promise((resolve, reject) => { rejectFetch = reject; }),
    AbortControllerCtor: TimeoutController,
    setTimeoutFn: (fn, ms) => { timeoutTimer = { fn, ms }; return 1; },
    clearTimeoutFn: () => {}
  });
  timeoutTimer.fn();
  assert.strictEqual(timeoutTimer.ms, 6000, 'the fake gateway timeout remains six seconds');
  assert.strictEqual(timeoutController.aborted, true, 'the timeout aborts the pending fake request');
  rejectFetch(new Error('timeout'));
  assert.strictEqual((await timedOut).ok, false);

  assert.strictEqual(SmartOpponent.healthConfigured({ configured: false }), false, 'unconfigured health hides Smart');
  assert.strictEqual(SmartOpponent.healthConfigured({ configured: true }), true);
  const firstUnavailable = SmartOpponent.nextFailure(0, 'unavailable');
  assert.deepStrictEqual(firstUnavailable, { streak: 1, switchToNormal: false });
  assert.deepStrictEqual(SmartOpponent.nextFailure(firstUnavailable.streak, 'unavailable'), { streak: 2, switchToNormal: true },
    'the second consecutive unavailable result switches the seat exactly once');

  assert.match(page, /levelsToShow = smartOpponentConfigured \? \["easy", "normal", "hard", "smart"\] : \["easy", "normal", "hard"\]/,
    'Smart is rendered only after configured health');
  assert.match(page, /fetch\("\/ai\/health"[\s\S]*?2000/, 'health request must time out after two seconds');
  assert.match(page, /SmartOpponent\.requestPick\(view, candidates/, 'Smart uses the constrained pick request');
  assert.match(page, /candidates\.find\(candidate => candidate\.id === result\.result\.pick\)/, 'a valid pick acts through its candidate');
  assert.match(page, /runSmartCandidate\(candidates && candidates\[0\], true\)/, 'invalid and timeout answers play candidate one with the fallback notice');
  assert.match(page, /fallbackToNormalAi[\s\S]*?showSmartFallbackNotice\(\);[\s\S]*?runSmartCandidate/, 'fallback displays the existing notice');
  assert.match(page, /fallbackToNormalAi[\s\S]*?transition\.switchToNormal[\s\S]*?seats\.level\.right = "normal"/, 'two unavailable responses downgrade once per match');
  assert.match(page, /smartOpponentRunsHere\(\)[\s\S]*?seat === "red"/, 'a relay Smart seat is host-only');
  assert.match(page, /broadcastSmartAiThrow[\s\S]*?sendAction/, 'the host broadcasts Smart throws through relay actions');
  assert.match(page, /phase: "throws:" \+ throws/, 'the current round hash includes actual throw numbers');
  assert(!/AIza[A-Za-z0-9_-]{35}/.test(page), 'the page must not contain a provider key shape');
  assert(!/AQ\.[A-Za-z0-9_-]{20,}/.test(page), 'the page must not contain a second provider key shape');
  console.log('test_smart_opponent: fake pick gateway, timeout, fallback, host, and secret checks passed');
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
