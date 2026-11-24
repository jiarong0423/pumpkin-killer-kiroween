'use strict';
// Seat core of the hybrid room test (docs/SIX_SEAT_HYBRID_PLAN_20261117.md, option A): ONE self-contained function that makes a loaded
// index.html play a whole team on one seat of a relay room, by itself, with the page's own computer shot (leftAiShot).
//
// It runs inside the page's global scope, like scripts/page_match_driver.js, in a Node vm (scripts/hybrid_seat_headless.js) or in a real
// Chrome tab over CDP (scripts/hybrid_seat_chrome.mjs, desktop and phone). It uses no Node-only call.
//   installHybridSeat({ team: "red"|"white", heroes: [...N hero ids], level: "easy"|"normal"|"hard", rngSeed, speed, maxRealSeconds, realSetTimeout? })
//   -> globalThis.__hybridSeat.join(code)   joins the room (the page's own RelayClient), startMatch() when the room code arrived
//   -> the loop then runs by itself (real timers; the page's setTimeout / Date.now / performance.now run on a fake clock, rAF is off)
//   -> globalThis.__hybridSeatResult is null while the seat plays and the final record object when the match is over (or the seat gave up)
// The seat never moves, never uses ultimates, skills, the shield or items (the relay carries plain throws; the MCP bridge sends throws only).
// The page keeps doing everything else itself: judging its own units, the round hash, end_turn, the seeded wind and weather.
function installHybridSeat(config) {
  var G = globalThis, STEP = 1 / 60;
  var realSetTimeout = config.realSetTimeout || G.setTimeout;
  var realDateNow = Date.now.bind(Date);
  var team = config.team === "white" ? "white" : "red";
  var speed = Number(config.speed) > 0 ? Number(config.speed) : 0;          // fake seconds per real second while there is something to simulate; 0 = as fast as the loop goes
  var maxReal = (Number(config.maxRealSeconds) > 0 ? Number(config.maxRealSeconds) : 600) * 1000;
  function mulberry(seed) { var s = seed >>> 0; return function () { s = (s + 0x6D2B79F5) >>> 0; var t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  var fakeNow = 0, seq = 0, timers = [], errors = [], relayErrors = [], outOfSync = [], joined = false, started = false, done = false, doneAt = null;
  var counters = { throwsOwn: 0, throwsFoe: 0, directOwn: 0, directFoe: 0, near: 0, pity: 0, comeback: 0 }, hitThrows = {};
  var armedKey = null, fireAt = Infinity, realStart = realDateNow(), simSteps = 0, gameOverSeen = null;
  var cap = 0, maxIterMs = 0, msgLog = [];
  var heldTimer = 12, manual = !!config.manual, manualShot = null, passRequested = false, launched = [], records = [];   // manual: an MCP agent decides the shots (scripts/page_judge_seat.js); the page keeps judging, hashing and ending turns itself

  function note(message) { if (errors.length < 20) errors.push(String(message)); }
  function hook(name, make) { if (typeof G[name] !== "function") return false; G[name] = make(G[name]); return true; }

  // ---- fake clock, seeded random, rAF off (restored never: the page is disposable)
  Math.random = mulberry(Number(config.rngSeed) >>> 0);
  G.setTimeout = function (fn, ms) { var id = ++seq; timers.push({ t: fakeNow + (Number(ms) > 0 ? Number(ms) : 0), id: id, fn: fn }); return id; };
  var cleared = {};
  G.clearTimeout = function (id) { cleared[id] = true; for (var i = 0; i < timers.length; i++) if (timers[i].id === id) { timers.splice(i, 1); return; } };
  G.requestAnimationFrame = function () { return 0; };
  G.__fitSync = true;   // no animation frames here: fitVisibleViewport applies the stage variables at once
  if (config.paintMs && typeof G.setInterval === "function") G.setInterval(function () { try { if (typeof paintFrame === "function") paintFrame(config.paintMs / 1000); } catch (e) { /* a frame that fails to paint is not a seat failure */ } }, config.paintMs);   // a phone or desktop screen shows the match: rAF is off, so paint on a real timer
  try { Object.defineProperty(performance, "now", { configurable: true, writable: true, value: function () { return fakeNow; } }); } catch (e) { /* ignore */ }
  try { Date.now = function () { return fakeNow; }; } catch (e) { /* ignore */ }

  function hpMap() { var m = {}; allUnits().forEach(function (u) { m[localPerspective.worldUnitId(u.id)] = u.hp; }); return m; }
  hook("executeThrow", function (orig) { return function (shooter, power, angle, thrower) { if (shooter === "player") counters.throwsOwn++; else counters.throwsFoe++; try { if (!thrower || !launched.length || launched[launched.length - 1].throwSeq !== throwSeq + 1) { var who = thrower || (shooter === "player" ? player : ai), wKey = shooter === "player" ? "player" : "ai", isUlt = !!(energy[wKey] >= 3 && ultUsed[wKey] < 2 && (ultArmed[wKey] || (wKey === "ai" && aiUltimateCandidate))); launched.push({ throwSeq: throwSeq + 1, team: shooter === "player" ? "own" : "foe", unit: localPerspective.worldUnitId(who.id), angle: angle, power: power, startX: who.x, hp: hpMap(), round: roundNum, wind: localPerspective.wind(wind), ult: isUlt }); } } catch (e) { /* diagnostics only */ } return orig.apply(this, arguments); }; });
  hook("pushHitReport", function (orig) { return function (p, hitType) { if (hitType === "hero" && p && !hitThrows[p.throwId]) { hitThrows[p.throwId] = 1; if (p.team === "player") counters.directOwn++; else counters.directFoe++; } return orig.apply(this, arguments); }; });
  hook("cbBegin", function (orig) { return function (p) { var fresh = !p.cb, c = orig.apply(this, arguments); if (fresh && c && typeof Comeback !== "undefined") { var total = Math.min(Comeback.CONSTANTS.MAX_TOTAL, Comeback.underdogMultiplier(c.own, c.foe) * (1 + Comeback.pityBonus(c.misses))); if (c.misses > 0) counters.pity++; if (total > 1) counters.comeback++; } return c; }; });
  hook("cbNearMiss", function (orig) { return function () { var before = 0, units = allUnits(), i; for (i = 0; i < units.length; i++) before += units[i].hp; var r = orig.apply(this, arguments), after = 0; for (i = 0; i < units.length; i++) after += units[i].hp; if (after < before) counters.near++; return r; }; });

  var hashDumps = {};   // what this page hashed at the end of each round (world frame), so a mismatch can be traced to the field that differs
  hook("currentRoundHash", function (orig) { return function () { var h = orig.apply(this, arguments); try { hashDumps[roundNum] = { hash: h, units: allUnits().map(function (u) { return [localPerspective.worldUnitId(u.id), Math.round(localPerspective.x(u.x) * 100) / 100, Math.round(u.y * 100) / 100, Math.round(u.hp * 100) / 100, publicStatusWords(u).join("|")]; }), wall: wallHp }; } catch (e) { /* diagnostics only */ } return h; }; });

  var throwLog = [];   // after every throw has landed on this page: round, who threw, and every unit's x and hp (world ids), to find the first throw on which two pages part
  hook("advanceAfterAttack", function (orig) { return function (team) { try { var L = launched.shift(), H = historyTrajectories.length ? historyTrajectories[historyTrajectories.length - 1] : null; if (L && H) { var after = hpMap(), foeIds = Object.keys(after).filter(function (id) { return L.team === "own" ? id.indexOf(localPerspective.worldSide("right")) === 0 : id.indexOf(localPerspective.worldSide("left")) === 0; }), hit = null, dmg = 0, vcount = 0; foeIds.forEach(function (id) { var lost = L.hp[id] - after[id]; if (lost > 0.0001) { dmg += lost; vcount++; if (!hit) hit = id; } }); var pts = [], src = H.points || []; for (var pi = 0; pi < src.length; pi += 6) pts.push([Math.round(localPerspective.x(src[pi].x) * 10) / 10, Math.round(src[pi].y * 10) / 10]); records.push({ team: L.team, unit: L.unit, angle: L.angle, power: L.power, wind: L.wind, round: L.round, hit_type: H.hitType === "wall" ? "central_wall" : (H.hitType === "hero" ? "hero" : H.hitType), hit_target: hit, damage: Math.round(dmg * 10) / 10, landing_x: Math.round(localPerspective.x(H.landingX) * 10) / 10, landing_y: Math.round(H.landingY * 10) / 10, path: pts, ultimate: !!L.ult, victims: vcount }); } } catch (e) { /* diagnostics only */ } try { throwLog.push({ r: roundNum, t: team === "player" ? "own" : "foe", u: allUnits().map(function (u) { return [localPerspective.worldUnitId(u.id), Math.round(localPerspective.x(u.x) * 10) / 10, Math.round(u.hp * 10) / 10]; }) }); } catch (e) { /* diagnostics only */ } return orig.apply(this, arguments); }; });

  var turnLog = [];   // every relayAfterTurn call: who, whether it came from a timeout or skip (rotated), the page turn and the turn timer, for a duplicate end_turn
  hook("relayAfterTurn", function (orig) { return function (team, rotated) { try { turnLog.push([roundNum, team, !!rotated, turn, Math.round(turnTimer * 10) / 10, projectiles.length, Math.round(fakeNow)]); if (turnLog.length > 400) turnLog.shift(); } catch (e) { /* diagnostics only */ } return orig.apply(this, arguments); }; });

  hook("beginLeftTurnMidRound", function (orig) { return function () { var r = orig.apply(this, arguments); try { turnLog.push([roundNum, "begin_mid", false, turn, Math.round(turnTimer * 10) / 10, unitOf("left").stun ? 1 : 0, Math.round(fakeNow)]); } catch (e) { /* diagnostics only */ } return r; }; });
  hook("resolveRound", function (orig) { return function () { var r = orig.apply(this, arguments); try { turnLog.push([roundNum, "resolve", false, turn, Math.round(turnTimer * 10) / 10, unitOf("left").stun ? 1 : 0, Math.round(fakeNow)]); } catch (e) { /* diagnostics only */ } return r; }; });

  function runDueTimers() {   // the timers due now, in time then creation order; a timer that re-arms itself with 0 ms runs in the NEXT step, never in a loop of its own
    var due = timers.filter(function (t) { return t.t <= fakeNow; });
    if (!due.length) return;
    due.sort(function (x, y) { return x.t - y.t || x.id - y.id; });
    timers = timers.filter(function (t) { return t.t > fakeNow; });
    for (var k = 0; k < due.length; k++) { if (cleared[due[k].id]) { delete cleared[due[k].id]; continue; } if (typeof due[k].fn === "function") due[k].fn(); }
  }

  // The computer plays the local team: one plain throw per turn, 1.9 s after the turn opened (the page's own charge animation takes 0.9 s).
  function autoplay() {
    if (gameOver || !relayLive() || turn !== "player") { if (turn !== "player") armedKey = null; return; }
    if (projectiles.length || diceRoll) return;
    var key = roundNum + ":" + unitOf("left").id;
    if (manual) {   // the agent's shot (or a pass) goes out 0.4 s after the turn opened; until then the page just waits
      if (armedKey !== key) { armedKey = key; fireAt = fakeNow + 400; heldTimer = turnTimer; return; }
      if (!manualShot && !passRequested) { turnTimer = heldTimer; return; }   // the agent's own clock (the bridge) decides how long it may take; the page's 12 s must not run while it thinks
      if (fakeNow < fireAt) return;
      if (manualShot) { var ms = manualShot; manualShot = null; fireAt = Infinity; if (ms.ult) ultArmed.player = true; executeThrow("player", ms.power, ms.angle); }
      else if (passRequested) { passRequested = false; fireAt = Infinity; turnTimer = 0.001; }
      return;
    }
    if (armedKey !== key) { armedKey = key; fireAt = fakeNow + 1900; return; }
    if (fakeNow < fireAt) return;
    fireAt = Infinity;
    var shot = leftAiShot();
    executeThrow("player", shot.power, shot.angle);
  }

  function step() {
    fakeNow += STEP * 1000; simSteps++;
    runDueTimers();
    autoplay();
    updatePhysics(STEP);
  }

  function busy() { return projectiles.length > 0 || !!diceRoll || turn === "player"; }   // something to simulate; otherwise the seat waits for the network

  function finalRecord(reason) {
    var own = unitsOf("left"), foe = unitsOf("right");
    function row(u) { return { id: u.id, hero: u.profile || (sideOfUnit(u) === "left" ? currentHero : ai.profile), hp: Math.round(u.hp * 10) / 10, maxHp: u.maxHp }; }
    return {
      team: team, reason: reason, gameOver: gameOver || null, roundNum: roundNum, cap: cap, seed: matchSeed,
      own: own.map(row), foe: foe.map(row), counters: counters, errors: errors.slice(), relayErrors: relayErrors.slice(), outOfSync: outOfSync.slice(),
      relayStatus: relayClient ? relayClient.state().status : null, relayRound: relayClient ? relayClient.state().round : null, relayPhase: relayClient ? relayClient.state().phase : null,
      hashDumps: hashDumps, throwLog: throwLog, msgLog: msgLog.slice(-40), turnLog: turnLog.slice(-60), pageState: pageState(), fakeSeconds: Math.round(fakeNow / 100) / 10, realMs: realDateNow() - realStart, simSteps: simSteps, level: config.level
    };
  }
  function pageState() {   // what the page is waiting for, for a stuck seat
    try { return { turn: turn, roundNum: roundNum, relayIncoming: relayIncoming, relayRemoteOpen: relayRemoteOpen, relayWait: relayWait ? relayWait.round : null, diceRoll: !!diceRoll, projectiles: projectiles.length, timers: timers.length, activeOwn: unitOf("left").id, activeFoe: unitOf("right").id, hitStop: hitStop, remoteApplying: remoteApplying, animFoe: unitOf("right").animState, onReleaseFoe: !!unitOf("right").onRelease }; } catch (e) { return { error: String(e) }; }
  }
  function finish(reason) { if (!done) { done = true; G.__hybridSeatResult = finalRecord(reason); } }

  function loop() {
    if (done) return;
    var realNow = realDateNow(), idle = true;
    var iterStart = realNow;
    try {
      if (joined && !started && relayRoomCode) { started = true; startMatch(); }
      if (started) {
        cap = typeof TeamTuning !== "undefined" ? TeamTuning.roundCap(TEAM_N) : 0;
        var allowed = speed > 0 ? Math.max(0, Math.floor((realNow - realStart) * speed / 1000 / STEP) - simSteps) : 60;
        if (allowed > 600) allowed = 600;
        for (var i = 0; i < allowed; i++) {
          if (!busy() && !gameOver && i > 0) break;   // waiting for the remote seat: do not run the fake clock ahead
          step();
          idle = idle && !busy();
          if (gameOver) { if (gameOverSeen === null) gameOverSeen = fakeNow; if (!manual && fakeNow - gameOverSeen > 4000 && !(G.__pacedPending > 0)) { finish("game_over"); return; } }
        }
        if (!busy() && !gameOver) { fakeNow += STEP * 1000; runDueTimers(); updatePhysics(STEP); simSteps++; }   // one idle tick keeps the page's own timers (end_turn waits, round timers) moving
      }
    } catch (e) {
      note("exception: " + String(e && e.stack ? String(e.stack).split("\n").slice(0, 3).join(" | ") : e));
      if (errors.length > 5) { finish("exception"); return; }
    }
    var iterMs = realDateNow() - iterStart; if (iterMs > maxIterMs) maxIterMs = iterMs;
    if (!manual && realNow - realStart > maxReal) { finish("timeout"); return; }
    realSetTimeout(loop, idle ? 2 : 0);
  }

  G.__hybridSeatResult = null;
  G.__hybridSeat = {
    join: function (code) {
      pickedHero = config.heroes[0]; teamPick = config.heroes.slice();
      relayClaimCount = config.claim >= 1 && config.claim < config.heroes.length ? config.claim : null;   // unit slot fill: this seat names only its first `claim` heroes (the rest of the team belongs to other seats)
      seats.left = "human"; seats.right = "human"; seats.level = { left: config.level, right: config.level };
      setLocalPerspective(team === "white" ? "right" : "left");
      var client = connectRelay();
      if (!client) throw new Error("no relay client (missing ?relay=)");
      client.onMessage(function (m) {
        if (m.type !== "room_state" && m.type !== "round_hash") { msgLog.push([m.type, m.seq === undefined ? null : m.seq, m.unit === undefined ? null : m.unit, m.round === undefined ? null : m.round, m.phase || m.next_phase || null, m.kind || null, m.hit === undefined ? null : m.hit, m.hp_after === undefined ? null : m.hp_after, Math.round(fakeNow)]); if (msgLog.length > 60) msgLog.shift(); }
        if (m.type === "error") relayErrors.push(m.code || "error");
        else if (m.type === "out_of_sync") outOfSync.push(m.round);
      });
      client.join(code, team);
      joined = true;
      realSetTimeout(loop, 0);
    },
    status: function () { return { joined: joined, started: started, done: done, round: roundNum, turn: turn, gameOver: gameOver || null, relayLive: relayLive(), errors: errors.length, relayErrors: relayErrors.length, fakeSeconds: Math.round(fakeNow / 100) / 10, maxIterMs: maxIterMs, timers: timers.length, projectiles: projectiles.length, floatTexts: floatTexts.length, history: historyTrajectories.length }; },
    abort: function (reason) { finish(reason || "aborted"); },
    submit: function (angle, power, ult) { manualShot = { angle: Math.round(angle), power: power, ult: !!ult }; passRequested = false; },
    pass: function () { manualShot = null; passRequested = true; },
    drain: function () { return records.splice(0); },
    snapshot: function () {   // the whole match as the page sees it, in world frame, for the MCP bridge's public view (scripts/mcp_stdio_server.py PageJudgeRelay)
      var st = relayClient ? relayClient.state() : null;
      return {
        started: started, joined: joined, live: relayLive(), round: roundNum, gameOver: gameOver || null, seed: matchSeed, scene: typeof pickedScene === "string" ? pickedScene : null,
        relay: st ? { status: st.status, round: st.round, phase: st.phase, seat: st.seat } : null, myTurn: turn === "player" && !projectiles.length && !diceRoll, turn: turn, projectiles: projectiles.length,
        wallHp: wallHp, wind: localPerspective.wind(wind), activeOwn: localPerspective.worldUnitId(unitOf("left").id), activeFoe: localPerspective.worldUnitId(unitOf("right").id),
        pity: { own: pityMisses.player, foe: pityMisses.ai }, energy: { own: energy.player, foe: energy.ai }, ultUsed: { own: ultUsed.player, foe: ultUsed.ai }, cap: typeof TeamTuning !== "undefined" ? TeamTuning.roundCap(TEAM_N) : 0, outOfSync: outOfSync.length, relayErrors: relayErrors.slice(-5), errors: errors.slice(-3),
        units: allUnits().map(function (u) { return { id: localPerspective.worldUnitId(u.id), hero: u.profile || (sideOfUnit(u) === "left" ? currentHero : ai.profile), x: Math.round(localPerspective.x(u.x) * 100) / 100, y: Math.round(u.y * 100) / 100, hp: Math.round(u.hp * 100) / 100, maxHp: u.maxHp, statuses: publicStatusWords(u) }; })
      };
    }
  };
  return "installed";
}

// The send pacer: the relay refuses a socket above 10 messages per second (MAX_MESSAGES_PER_SECOND). A fast simulated page can burst more
// than that, which no real person's device does, so every message waits for a minimum gap (default 130 ms) before it goes out. Order is kept.
// Source text for a page global (Chrome: Page.addScriptToEvaluateOnNewDocument; the vm host installs the same function with its own WebSocket class).
function pacedSocketInstall(gapMs, NativeWS, scope, now, realSetTimeout) {
  scope.__pacedPending = 0;   // messages waiting for their turn: a seat must not end its process before this is 0 (its last action would be lost)
  scope.WebSocket = function (url) {
    var ws = new NativeWS(url), queue = [], last = 0, timer = null;
    function pump() {
      timer = null;
      if (!queue.length) return;
      var wait = last + gapMs - now();
      if (wait > 0 || ws.readyState !== 1) { timer = realSetTimeout(pump, Math.max(wait, 4)); return; }
      last = now(); ws.send(queue.shift()); scope.__pacedPending--;
      if (queue.length) timer = realSetTimeout(pump, gapMs);
    }
    return new Proxy(ws, {
      get: function (t, k) { if (k === "send") return function (d) { queue.push(d); scope.__pacedPending++; if (!timer) pump(); }; var v = t[k]; return typeof v === "function" ? v.bind(t) : v; },
      set: function (t, k, v) { t[k] = v; return true; }
    });
  };
  scope.WebSocket.OPEN = 1; scope.WebSocket.CONNECTING = 0; scope.WebSocket.CLOSING = 2; scope.WebSocket.CLOSED = 3;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    installHybridSeat: installHybridSeat,
    installSource: installHybridSeat.toString(),
    pacedSocketInstall: pacedSocketInstall,
    // text for a Chrome page: the real WebSocket is replaced by the paced one BEFORE any page script runs (the real setTimeout is kept in the closure)
    pacedSocketPageSource: function (gapMs) { return "(" + pacedSocketInstall.toString() + ")(" + Number(gapMs) + ", window.WebSocket, window, Date.now.bind(Date), window.setTimeout.bind(window));" }
  };
}
