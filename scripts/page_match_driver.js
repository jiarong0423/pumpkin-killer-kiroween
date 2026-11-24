// Page-side match driver (front end of the 240-match matrix, docs/MATRIX_SPEC_20261117.md).
//
// runPageMatch(config) is ONE self-contained function. It runs inside an already loaded index.html (a Node vm built by
// scripts/page_harness.js, or a real Chrome tab over CDP), i.e. in the page's global scope, so it can reach the page's own
// top-level bindings (seats, resetGame, updatePhysics, executeThrow, teams, gameOver ...). It uses no Node-only call.
//   config: { hero, size, seed, heroRight?, tierLeft?, tierRight?, maxSteps?, plainOnly? }   plainOnly defaults to TRUE (see below)
//   The page must have been loaded with ?team=<size> (TEAM_N is a page constant) - the driver refuses a mismatch.
// What it does: both seats computer-controlled (page AI levels hard/normal/easy), left hero = hero for all units, right hero
// from the spec, a FAKE clock (page setTimeout / performance.now / Date.now replaced for the duration of the match; the page's
// own updatePhysics(1/60) is stepped, timers run when due, nothing waits), the page's own AI turns (triggerLeftAiTurn,
// triggerAITurn, dice moves, knight defend, ultimates of the right AI) until gameOver / round cap / 60-round duel guard.
// Math.random is replaced by a seeded generator for the match and restored afterwards. Everything else is restored too.
// Counters come from wrapping the page's own functions: throws (executeThrow), direct_hits (throws that hit a unit directly, pushHitReport "hero", counted once per throw id),
// near_misses (cbNearMiss that took hp), pity_triggers (a projectile whose first damage used a pity charge > 0),
// comeback_hits (a projectile whose combined underdog x pity multiplier was > 1, Comeback.CONSTANTS.MAX_TOTAL cap applied).
// plainOnly (default true, like the engine bot): both seats play plain throws only: ultimates are never armed for the AI (queueAiThrow
// is forced to useUltimate = false), heavy/double/heal charges are 0 so prepareAiShot takes no skill, tryAiDefend returns false (no
// shield), airdrops are not scheduled (no items). The right AI's own dice move (25 percent of its turns, the left AI never moves) is
// kept and counted in record.options.moves_right / moves_left. plainOnly:false plays the page's full AI.
// Page behaviours that shape the numbers (reported in docs/agent_reports_20261117/wave3_matrix_page.md): the left AI seat has
// no ultimate, no move and no skill (triggerLeftAiTurn: one throw at 54 degrees), the right AI has all of them; the coin is
// mapped to the opening side here (0 = left, 1 = right) because showCoinToss hands beginOpeningTurn a number, see the report.
function runPageMatch(config) {
  var HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"];
  var TIERS = ["hard", "normal", "easy"];
  function mulberry(seed) {
    var s = seed >>> 0;
    return function () { s = (s + 0x6D2B79F5) >>> 0; var t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  var seed = Number(config.seed) >>> 0, size = Number(config.size), hero = config.hero;
  var heroRight = config.heroRight || HEROES[(seed * 7 + 3) % 8];
  // Mixed teams (owner 2026-11-17: no hero twice in a team): a team of N units is its first hero followed by the next heroes in the fixed HEROES order, wrapping. One unit per team: just the hero.
  function teamFrom(first, n) { var k = HEROES.indexOf(first), out = [], i; for (i = 0; i < n; i++) out.push(HEROES[(k + i) % HEROES.length]); return out; }
  var teamLeft = config.heroesLeft || (size > 1 ? teamFrom(hero, size) : [hero]), teamRight = config.heroesRight || (size > 1 ? teamFrom(heroRight, size) : [heroRight]);
  var tierRng = mulberry((seed ^ 0x5eed) >>> 0);
  var tierLeft = TIERS[Math.floor(tierRng() * 3)], tierRight = TIERS[Math.floor(tierRng() * 3)];
  if (config.tierLeft) tierLeft = config.tierLeft;
  if (config.tierRight) tierRight = config.tierRight;
  var plainOnly = config.plainOnly !== false;
  var record = {
    options: { plainOnly: plainOnly, moves_left: null, moves_right: null },
    end: "page", hero: hero, hero_right: heroRight, heroes_left: teamLeft, heroes_right: teamRight, size: size, seed: seed, tier_left: tierLeft, tier_right: tierRight, winner: "none", rounds: 0,
    hp_share_left: null, hp_share_right: null, units_left_alive: null, units_right_alive: null, throws: 0, direct_hits: 0,
    near_misses: null, pity_triggers: null, comeback_hits: null, ultimates_left: null, ultimates_right: null, errors: []
  };
  var apiOk = typeof updatePhysics === "function" && typeof resetGame === "function" && typeof switchHero === "function" && typeof applyClassStats === "function" && typeof randomizePositions === "function" &&
    typeof beginOpeningTurn === "function" && typeof executeThrow === "function" && typeof unitsOf === "function" && typeof allUnits === "function" && typeof teamDown === "function" && typeof seedWind === "function" &&
    typeof seats !== "undefined" && typeof teams !== "undefined" && typeof Determinism !== "undefined";
  if (!apiOk) { record.errors.push("page API missing (updatePhysics / resetGame / switchHero / applyClassStats / randomizePositions / beginOpeningTurn / executeThrow / unitsOf / allUnits / teamDown / seedWind / seats / Determinism)"); return record; }
  if (typeof TEAM_N === "undefined" || TEAM_N !== size) { record.errors.push("page loaded with team size " + (typeof TEAM_N === "undefined" ? "?" : TEAM_N) + ", config wants " + size + " (load the page with ?team=" + size + ")"); return record; }
  if (HEROES.indexOf(hero) < 0 || HEROES.indexOf(heroRight) < 0) { record.errors.push("unknown hero " + hero + " / " + heroRight); return record; }

  // ---- fake clock and seeded random, restored in finally
  var STEP = 1 / 60, fakeNow = 0, seq = 0, timers = [];
  var saved = { setTimeout: globalThis.setTimeout, clearTimeout: globalThis.clearTimeout, random: Math.random, dateNow: Date.now, perfNow: null, perfOwn: false, raf: globalThis.requestAnimationFrame };
  try { saved.perfOwn = Object.prototype.hasOwnProperty.call(performance, "now"); saved.perfNow = performance.now; } catch (e) { /* no performance object */ }
  var wrapped = {};
  // Function declarations of the page are properties of the global object: reassigning them redirects every call by name.
  var G = globalThis;
  function hook(name, make) {
    if (typeof G[name] !== "function") return false;
    var original = G[name];
    wrapped[name] = original;
    G[name] = make(original);
    return true;
  }
  var counters = { throws: 0, direct: 0, near: 0, pity: 0, comeback: 0, movesLeft: 0, movesRight: 0 }, hitThrows = {};
  var haveCb = false, haveNear = false;
  try {
    Math.random = mulberry((seed ^ 0xa11ce) >>> 0);
    G.setTimeout = function (fn, ms) { var id = ++seq; timers.push({ t: fakeNow + (Number(ms) > 0 ? Number(ms) : 0), id: id, fn: fn }); return id; };
    G.clearTimeout = function (id) { for (var i = 0; i < timers.length; i++) if (timers[i].id === id) { timers.splice(i, 1); return; } };
    G.requestAnimationFrame = function () { return 0; };
    try { Object.defineProperty(performance, "now", { configurable: true, writable: true, value: function () { return fakeNow; } }); } catch (e) { /* ignore */ }
    try { Date.now = function () { return fakeNow; }; } catch (e) { /* ignore */ }

    var events = {};   // rich mode: how often each player-facing event fired, by name (skills, ultimates by hero, defend, crates)
    function count(key) { events[key] = (events[key] || 0) + 1; }
    hook("executeThrow", function (orig) {
      return function (shooter) {
        counters.throws++;
        var ultBefore = ultUsed.player + ultUsed.ai, hero = shooter === "player" ? currentHero : ai.profile, kind = selectedSkill;
        var result = orig.apply(this, arguments);
        if (!plainOnly) {
          if (ultUsed.player + ultUsed.ai > ultBefore) count("ultimate_" + hero);
          else if (kind === "heavy" || kind === "double") count("skill_" + kind);
        }
        return result;
      };
    });
    hook("pushHitReport", function (orig) { return function (p, hitType) { if (hitType === "hero" && p && !hitThrows[p.throwId]) { hitThrows[p.throwId] = 1; counters.direct++; } return orig.apply(this, arguments); }; });   // throws with at least one direct hit (a bouncing shield or a piercing axe counts once)
    hook("startDiceRoll", function (orig) { return function (owner) { if (owner === "ai") counters.movesRight++; else counters.movesLeft++; return orig.apply(this, arguments); }; });
    if (!plainOnly && typeof tryAiDefend === "function") hook("tryAiDefend", function (orig) { return function () { var r = orig.apply(this, arguments); if (r) count("defend"); return r; }; });
    if (typeof computerKnightWall === "function") hook("computerKnightWall", function (orig) { return function (side) { if (plainOnly) return false; var r = orig.apply(this, arguments); if (r) count("ultimate_knight"); return r; }; });   // plain throws: never; full AI: counted
    if (plainOnly && typeof prepareLeftAiShot === "function") hook("prepareLeftAiShot", function () { return function () { selectedSkill = "normal"; ultArmed.player = false; }; });   // plain throws on the left seat too
    if (plainOnly) {
      hook("queueAiThrow", function (orig) { return function (aim, broadcast) { return orig.call(this, aim, broadcast, false); }; });   // never an ultimate
      hook("tryAiDefend", function () { return function () { return false; }; });                                                       // never the shield
      hook("scheduleAirdrop", function () { return function () {}; });                                                                  // no crates, no items
    }
    haveCb = hook("cbBegin", function (orig) {
      return function (p) {
        var fresh = !p.cb, c = orig.apply(this, arguments);
        if (fresh && c && typeof Comeback !== "undefined") {
          var total = Math.min(Comeback.CONSTANTS.MAX_TOTAL, Comeback.underdogMultiplier(c.own, c.foe) * (1 + Comeback.pityBonus(c.misses)));
          if (c.misses > 0) counters.pity++;
          if (total > 1) counters.comeback++;
        }
        return c;
      };
    });
    haveNear = hook("cbNearMiss", function (orig) {
      return function () {
        var before = 0, units = allUnits(), i;
        for (i = 0; i < units.length; i++) before += units[i].hp;
        var r = orig.apply(this, arguments), after = 0;
        for (i = 0; i < units.length; i++) after += units[i].hp;
        if (after < before) counters.near++;
        return r;
      };
    });

    // ---- start the match like startMatch(), without the start screen and the coin-call overlay
    matchStarted = false;
    seats = { left: "ai", right: "ai", level: { left: tierLeft, right: tierRight } };
    pickedHero = hero; currentHero = hero; aiClass = heroRight;
    resetGame();
    matchSeed = seed; weatherCache.round = -1; weatherFxKey = "";
    leftHeroes = size > 1 ? teamLeft.slice() : []; rightHeroes = size > 1 ? teamRight.slice() : [];
    if (size > 1) unitsOf("left").forEach(function (u, i) { u.profile = leftHeroes[i]; });
    unitsOf("right").forEach(function (u, i) { u.profile = rightHeroes[i] || heroRight; });
    ai.profile = rightHeroes[0] || heroRight;
    switchHero(hero, true);
    applyClassStats();
    if (plainOnly) skillCharges = { player: { double: 0, heavy: 0, heal: 0 }, ai: { double: 0, heavy: 0, heal: 0 } };   // no skills
    var startCharges = JSON.parse(JSON.stringify(skillCharges));
    randomizePositions(false);
    allUnits().forEach(function (u) { u.x = u.targetX; });
    matchStarted = true; wind = seedWind(); lastWeatherNotice = "clear";
    turn = "busy";
    var coin = Determinism.coinToss(matchSeed);                // 0 = the left side opens, 1 = the right side (showCoinToss text: firstSide === 0 ? coin.leftFirst : coin.rightFirst)
    beginOpeningTurn(coin === 0 ? "left" : "right");

    // ---- play with the page's own physics step and a fake clock
    var maxSteps = config.maxSteps || 600000, lastThrows = 0, lastProgress = 0, step, clockStart = fakeNow;
    for (step = 0; step < maxSteps; step++) {
      fakeNow += STEP * 1000;
      for (;;) {                                                 // timers due now, in time then creation order
        var bi = -1;
        for (var k = 0; k < timers.length; k++) if (timers[k].t <= fakeNow && (bi < 0 || timers[k].t < timers[bi].t || (timers[k].t === timers[bi].t && timers[k].id < timers[bi].id))) bi = k;
        if (bi < 0) break;
        var tm = timers.splice(bi, 1)[0];
        if (typeof tm.fn === "function") tm.fn();
      }
      updatePhysics(STEP);
      if (gameOver) break;
      if (size === 1 && roundNum > 60) break;                    // duel guard: no winner
      if (counters.throws !== lastThrows) { lastThrows = counters.throws; lastProgress = fakeNow; }
      else if (fakeNow - lastProgress > 240000) { record.errors.push("stall: no throw for 240 fake seconds in round " + roundNum + " (turn " + turn + ")"); break; }
    }
    if (step >= maxSteps) record.errors.push("step limit " + maxSteps + " reached in round " + roundNum);
    record.options.game_seconds = Math.round((fakeNow - clockStart) / 100) / 10;   // the page's own clock: flight, animation and computer delays, no human aiming time
  } catch (error) {
    record.errors.push("exception: " + String(error && error.stack ? String(error.stack).split("\n").slice(0, 3).join(" | ") : error));
  } finally {
    for (var name in wrapped) if (Object.prototype.hasOwnProperty.call(wrapped, name)) G[name] = wrapped[name];
    G.setTimeout = saved.setTimeout; G.clearTimeout = saved.clearTimeout; Math.random = saved.random; Date.now = saved.dateNow;
    if (saved.raf) G.requestAnimationFrame = saved.raf;
    try { if (saved.perfOwn) Object.defineProperty(performance, "now", { configurable: true, writable: true, value: saved.perfNow }); else delete performance.now; } catch (e) { /* ignore */ }
  }

  // ---- the record, read from the page's own state
  try {
    var left = unitsOf("left"), right = unitsOf("right");
    function share(units) { var hp = 0, max = 0; units.forEach(function (u) { max += u.maxHp; if (u.hp > 0) hp += u.hp; }); return max > 0 ? Math.round(hp / max * 10000) / 10000 : 0; }
    function alive(units) { return units.filter(function (u) { return u.hp > 0; }).length; }
    record.hp_share_left = share(left); record.hp_share_right = share(right);
    record.units_left_alive = alive(left); record.units_right_alive = alive(right);
    var cap = size > 1 && typeof TeamTuning !== "undefined" ? TeamTuning.roundCap(size) : Infinity;
    if (gameOver) {
      var ld = teamDown("left"), rd = teamDown("right");
      if (rd && !ld) record.winner = "left";
      else if (ld && !rd) record.winner = "right";
      else if (!ld && !rd) record.winner = gameOver === "player" ? "cap_left" : "cap_right";
      else record.winner = gameOver === "player" ? "left" : "right";
    }
    record.rounds = (record.winner === "cap_left" || record.winner === "cap_right") ? Math.min(roundNum - 1, cap) : roundNum;
    record.throws = counters.throws; record.direct_hits = counters.direct;
    record.near_misses = haveNear ? counters.near : null;
    record.pity_triggers = haveCb ? counters.pity : null; record.comeback_hits = haveCb ? counters.comeback : null;
    record.ultimates_left = ultUsed.player; record.ultimates_right = ultUsed.ai;
    record.options.moves_left = counters.movesLeft; record.options.moves_right = counters.movesRight;
    if (!plainOnly) {
      events.moves = counters.movesLeft + counters.movesRight;
      if (typeof dropCount === "number") events.crates_dropped = dropCount;
      var used = function (side, name) { return Math.max(0, startCharges[side][name] - skillCharges[side][name]); };
      events.skill_heal = used("player", "heal") + used("ai", "heal");
      record.options.events = events;
    }
    if (plainOnly && (ultUsed.player > 0 || ultUsed.ai > 0 || supply.player || supply.ai)) record.errors.push("plainOnly violated: ultimates " + ultUsed.player + "/" + ultUsed.ai + ", items " + !!supply.player + "/" + !!supply.ai);
  } catch (error) { record.errors.push("record: " + String(error)); }
  return record;
}

// Node side only (the runners): the injectable source, the cell list and the seed rules of the spec.
if (typeof module !== "undefined" && module.exports) {
  const HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"];
  const cellSeed = (heroIndex, size, k) => (k < 10 ? 7000 + 100 * heroIndex + 10 * size + k : 100000 + (heroIndex * 3 + size - 1) * 100000 + k);   // plays 0 to 9: the 240-match spec seeds; from play 10 on every cell has its own range (docs/MATRIX_SPEC_20261117.md)
  const cells = (perCell) => {
    const out = [];
    HEROES.forEach((hero, hi) => { for (let size = 1; size <= 3; size++) for (let k = 0; k < (perCell || 10); k++) out.push({ hero, size, seed: cellSeed(hi, size, k), k }); });
    return out;
  };
  module.exports = { runPageMatch, source: runPageMatch.toString(), HEROES, cellSeed, cells };
}
