# Kiro task 76: 4 vs 4 implementation plan (claude-sonnet-5.5)

Status: plan only. No code, config or other document was edited. Nothing was run, built or tested; every number is a reading of a file or my own hand arithmetic. Tags: **[R path:line]** = read in that file at that line; **[A]** = assumed (no source, or my estimate). Built on `docs/owner_decisions_20261110_agents_headless.md` (agents are the default seat, headless rules, modular) and the rows of `(not published)` (decided, not reopened). Tasks 74 (class and status specs) and 75 (MCP plan) are only referenced; their outputs are not in `docs/` yet.

Could not read or not present: `(not published)` (outside the workspace; I used `docs/roster_design.md`, the task 33 output in this repo, read to its section 6); `docs/kiro_74_*`, `docs/kiro_75_*`; Kiro 44/53/54 outputs; `docs/airdrop_design.md`, `docs/ultimate_mapping.md` (not opened). I read all of `index.html` (2957 lines), `js/particles.js`, `js/ultimate.js`, `js/class_stats.js`, `scripts/sim_ai_nosim.js`, the head of `scripts/sim_balance.js`, and `scripts/mcp_game_server.py` lines 44-234 and 296-386. The brief's counts (about 327 uses of `player`, 79 of `ai.`) were not recounted. No web sources were needed.

## OWNER CORRECTIONS (main line, 2026-11-10, these win over the text below)
1. The bride's bat swarm does NOT hurt allies (owner: "own side takes no damage"). Ignore every "friendly fire" or "both sides" mention for it; the "both sides at zero = draw" rule is dropped. It hits every ENEMY unit only.
2. The wizard blast does NOT apply bleed any more (owner, done in index.html). Blast = 1.5 x normal damage only.
3. The game computes on EACH player's device (deterministic rules module, same seed + same ordered actions); the cloud only serves assets, issues random invitation codes and forwards small action messages; MCP is only a channel. The Python engine is one fixed headless mode. See docs/owner_decisions_20261110_agents_headless.md items 9 to 12.
4. Line numbers below were read BEFORE today's later edits to index.html (about 30+ lines of drift): use function and constant names, not line numbers.
5. First side (Kiro 76 question 1, owner 2026-11-10 'roll the dice, bigger number'): at match start each side rolls one die, the HIGHER number goes first, a tie is rolled again; the roll uses the shared seed so every device gets the same result (no local Math.random).
   Alternative (owner 2026-11-10 'or a coin toss'): the same setting `FIRST_SIDE` also accepts `"coin"`: one seeded coin flip picks the first side (heads = red, tails = white). DECIDED (owner 2026-11-10 'coin toss it is, add a pumpkin coin animation'): the first side is decided by the COIN TOSS (call heads or tails, then flip), dice is dropped as the default; a pumpkin-coin flip animation plays at match start (two pictures, front = pumpkin face = 人頭, back = pumpkin stem and vine = 字; the flip is a code-driven squash and swap of those two pictures; the pictures come from Qwen, see gap A11). Both are drawn from the shared seed.
   Coin call (owner 2026-11-10 'first choose heads or tails'): before the flip one side calls heads (人頭) or tails (字); the call is sent first, THEN the relay creates the match seed, so nobody can know the result beforehand (a seed known earlier would let a device precompute the flip). If the flip matches the call, the caller goes first, otherwise the other side. Who calls: the player who JOINED the room by code (provisional; the room creator may swap it). A sub-agent seat calls through the same action message as a human (`call_coin {face}`).

6. KIRO 76 ANSWERS (owner 2026-11-10, these WIN over sections 1 to 12): Q2 ultimate energy is PER UNIT and each unit may use its ultimate at most TWICE (a personal cap of 2, not a cap of 2 per side). Q3 blast and area attacks LOSE damage with distance by percentage: use the stepped bands (up to 1/3 of the radius 100 percent, up to 2/3 75 percent, up to the full radius 50 percent). Q4 a team may hold each class only ONCE (unique per team), to be changed later; with four playable classes a team is exactly skeleton, wizard, bat, knight. Q5 the intended-unit hit-rate target stays 25 to 30 percent. Q6 the bride's wave is still a THROWN projectile, but the sound-wave effect hits ONLY the aimed unit (the targeted one), not everything on the path. Q7 no round cap, and units should not die too fast (keep the 4 to 6 hits-to-kill band, no quick-kill tuning). Q8 each unit decides for itself: one decision per unit turn.

## 1. Target design (one page)

| Item | Decision | Basis |
|---|---|---|
| Canvas, ground, fence, wind | Unchanged: 1920x1080, feet y 860, fence x 895..1025 (centre 960, 130 wide, top y 610), wind rerolled once per round in -4..4 and shared by all 8 throws | [R index.html:409-416, 1324; shared/constants.json] |
| Start x, red slot 0 (front) to 3 (rear) | 700, 540, 380, 220 | [A] 160 px apart, so the 140 px body boxes do not touch; 60 px slack at each end of the 160..760 zone |
| Start x, white slot 0 to 3 | 1220, 1380, 1540, 1700 | mirror of red (1920 - x) |
| Movement zones | Keep 160..760 and 1160..1760 | [R index.html:742-770 stepDice] |
| Feet height | All units stay at y 860, scale 1 | [A] keeps `simulateLandingX`, launch height and hit boxes identical to today |
| Depth order | Draw rear to front on each side (slot 3 first, slot 0 last); bars, pips and markers in a second pass after all bodies | [A] today the overlay is drawn inside `drawFullArtCharacter` [R :2385-2434], so a front body would cover a rear bar |
| Engine mismatch | `mcp_game_server.py` uses a 2.5D echelon (y 840..885, scale 0.90..1.00) and spawns 120 px apart; its hit test is `abs(dx) < 45` and `abs(y - 60 - cur_y) < 65`; it resolves all pending throws at round end in unit order | [R mcp_game_server.py:57-70, 296-360, 353]. The browser is the reference; task 75 aligns the engine |

**Who plays together.** Playable classes today: skeleton, wizard, bat, knight [R :486-530]. Recommendation: a team is 4 units, duplicates allowed, at most 2 of one class and at most 1 knight (the floating shield is one object per side [R :605-640] and `canControlShield` reads one class [R :812]). Once 6 or more classes are playable, switch to "no duplicates in a team" by changing one constant (`TEAM_RULES.maxPerClass` 2 to 1). Both sides may pick the same classes. The default line-up for the first build is one of each class, in a player-chosen slot order.

**Turns.** Sequential unit turns (confirmed text: the opposing side attacks one unit after another [R docs/game_mode.md:52]). The mockup flow "everyone picks, then Lock" [R docs/game_mode.md:54-58] is not used.
1. Match start: line-ups fixed, seats assigned, wind rolled, `firstSide` chosen. The brief says a die decides the first team; the only die rule I found in the log is the sky-target die. The confirmed text is "human phase, then agent phase" [R docs/game_mode.md:14]. Build `FIRST_SIDE = "die" | "red"`, default `"die"`, owner to confirm (question 1).
2. A round has two side phases. In a phase every living unit of that side acts once, one at a time. Human phase: the next unacted unit in slot order (front to rear) is pre-selected and the player may click another unacted unit. Agent or built-in AI phase: slot order unless the agent picks another unacted unit.
3. A unit turn: optional Move once (does not end the turn), then one Attack; or Defend (knight only, ends the turn); or the ultimate in place of the attack [R docs/ultimate_rules.md section 2].
4. Timer: 12 s per unit turn [R :556], 7 s if the unit is stunned [R :559]. Clicking another unit before charging does not reset the countdown. Timeout forfeits that unit's turn only.
5. A unit turn ends when its last projectile has landed or been blocked plus 0.8 s [R :1779-1785], or on lock, defend or forfeit.
6. After the second phase, round end: poison and bleed tick (never lethal, they stop at 1 HP [R :1502-1512]), shield rounds count down [R :1326-1344], airdrop check [R :1428], `roundNum++`.
7. Win: a side with no living unit loses. Both sides cannot reach zero at once any more (the bride's swarm hits enemies only; OWNER 2026-11-10), so there is no draw rule. No round cap in v1 (none is confirmed); the sim reports the length (section 7).
8. Dead unit: leaves the queue, the collision set and the spacing set. Survivors do not close ranks. Its pips are lost, the side's used-ultimate count is not [R js/ultimate.js registerKO]. A tombstone is cosmetic.
9. Length estimate [A, from docs/roster_design.md section 3]: human turn about 7.5 s, AI turn about 4.3 s, so a full round is 4x7.5 + 4x4.3 + 1.5 = about 49 s; 7 to 9 rounds is 5.7 to 7.3 min against the under-8-minute target of task 33.

## 2. Seats and controllers (B9)

| Controller | Who decides | Receives | Input path |
|---|---|---|---|
| `human` | the person at this browser | the canvas, which draws only public information | pointer and keys call `submitAction(seatId, unitId, action)` |
| `agent` | the seat owner's own sub-agent, through MCP | `publicView(state, seatId)` only | an MCP tool calls the same function |
| `builtin-ai` | the page's practice opponent | `publicView(state, seatId)` plus its own memory | `decide(view, memory, rng)` returns an action for the same function |

- Data: `seat = { id, side, controller, unitIds[], name }`; `unit = { id, side, slot, classKey, seatId, controller, ... }`. A side is one seat in v1; the model allows two seats of two units later. Hot-seat is out of scope. The engine writes `"subagent"` [R mcp_game_server.py:104]; map it to `"agent"`.
- Today the browser does not call the MCP server (`.kiro/steering/tech.md`); the page runs its own rules and AI. The bridge is step S10 and depends on task 75. Until then the supported demo is `human` vs `builtin-ai`.
- Rule: `submitAction` rejects (without using the turn, as the protocol already says [R docs/mcp_agent_protocol.md]) when the unit is not in the caller's seat, is not the active unit, is dead, already acted, or the phase is wrong. The UI gets no other write path ("nothing in the UI changes game state directly", `product.md`); today it does, for example `executeThrow` pushes projectiles directly [R :930-1040].
- One exporter: `publicView(state, seatId)` in `(not published)`. It lists fields; it never serialises `state`.
  - Every seat sees, for all 8 units: side, class, slot, alive, x, health as a bar fraction, lit pips (drawn above heads), body statuses (bleed, poison, frost, slow chain, stun stars), who is active, wind, wall health, landing points and flight paths of past throws, ultimates remaining per side (diamonds), the enemy item slot.
  - Own seat only: which of its units acted, moved, hold an armed ultimate, its floating shield and (later) hidden A-B-C points, its unrolled-dice state.
  - Never exported: seed or rng, future wind, unsubmitted actions, dice before they roll, the opponent shield (the page already hides it until it blocks, `revealT` 1.4 s [R :1672, draw step 5]), the built-in AI's aim state (`aiAimPending`, `aiCal`).
  - Quantisation (position to the 36 px grid, health to 5 percent steps, wind to the ghost's notches) follows the owner's fair-information rule; the amounts belong to task 75 [A].
- What the human sees of the other side: the same list above. No numbers for health (owner 2026-11-10), no enemy angle or power, no enemy shield until it blocks.
- A spectator seat gets the same view as a human seat. A human giving orders to their own agent is not in v1 (`seat.advisorSeatId` reserved [A]).
- Protocol conflicts for task 75: the doc says the agent phase times out after 12 s in total [R docs/mcp_agent_protocol.md]; this plan gives 12 s per unit turn. `product.md` says "one decision per round"; this plan gives one decision per unit turn so an agent can use the landings of its earlier units like a human (question 8).

## 3. Refactor path (playable at every step)

New modules, UMD like `js/class_stats.js`, DOM-free, no `Math.random`, no `Date`, each with a node test. `index.html` loads only five scripts today [R :253-257]; `class_stats.js` and `ultimate.js` are not loaded by the page.

| File | Owns | First used |
|---|---|---|
| `(not published)` | seeded `mulberry32` (same algorithm as [R js/particles.js:73-81]) | S5 |
| `(not published)` | `makeUnit`, formation, `MIN_GAP`, `clampMove`, `validateLineup` | S1, S6 |
| `(not published)` | phase machine, queue, per-unit timer in game seconds, `firstSide` | S5 |
| `(not published)` | body and head tests, first-hit with overlap tie-break, splash bands, friendly-fire filter | S7 |
| `(not published)` | `decide(view, memory, rng)` | S9 |
| `(not published)` | `publicView`, `canAct`, deny-list | S10 |
| `(not published)` | the rest of the rules (projectile step, damage, statuses, events), runnable in node | S12 |

Constraint: `scripts/test_sim_balance.js` greps `index.html` for literals such as `const GROUND_Y = 860;` and `const FENCE_X = 960;` [R scripts/test_sim_balance.js:28-31]; keep those lines in `index.html` until the tests read a module. `sim_balance.js` carries `WALL_DMG = 15` while the page has `WALL_HIT_DMG = 8` [R sim_balance.js constants, index.html:412]; I did not check whether a test covers it.

**S0. Preflight (S).** Add read-only `window.__pk = { units, turn, wind, wallHp, round, log }`. No behaviour change. Write the browser smoke list (section 7).

**S1. Unit registry with aliases (S).** Replace the two object literals `player` [R :568-583] and `ai` [R :585-600] by `makeUnit(side, slot, classKey)`; `const units = { red: [..], white: [..] }; const player = units.red[0], ai = units.white[0];`. Add fields `id, side, slot, classKey, controller, seatId, alive`. One unit per side still. Pass: smoke list identical; `node (not published)`.

**S2. Actor pointer for input (M).** `let actor = units.red[0]`. Replace `player` by `actor` and `currentHero` by `actor.classKey` in input, menu and dock code: `updateMovePoint` 704, `actionMenuItems` 709, `chooseMenuItem` 715, `moveWithDice` 724, `chooseMoveDir` 734, `selectSkill` 788, `toggleShieldDefend` 814, `lockShield` 838, `cancelDefendMode` 852, `canControlShield` 812, `startCharging` 888, `releaseAndThrow` 900, `aimFromPointer` 1055, pointer handlers 1071-1170, `keydown` 1176-1203, `useSupply` 1438, `updateDock` 1521-1552, `drawRuleOverlay` 2833-2925, the charge arc call in `draw` (step 7 of the draw order). Change `executeThrow(shooter, power)` [R :930] to take a unit; callers: :913, :917, :1267. Pass: identical in 1v1.

**S3. Loops over all units (M).** Replace every `[player, ai]` pair with `allUnits()`: animation [R :1599-1617], resupply and recoil [R :1790-1808], face glow (the `fxClock.face` block after the resupply loop), low-HP audio [R :1561-1565, use the lowest side fraction], airdrop pickup [R :1461] and `scheduleAirdrop` [R :1428-1437], round-end ticks [R :1319], `resetGame` [R :1352-1394], `applyClassStats` [R :861], `draw` unit drawing [R :1898-1906], `drawTopHUD` [R :2705-2707], `drawThrowingHand` aim `(u === player ? ...)` [R :2186]. Projectiles get `p.side` and `p.shooterId`; the target is `enemiesOf(p.side)` instead of `p.team === "player" ? ai : player` [R :1689]. Pass: identical in 1v1.

**S4. Per-unit and per-side data (M).** Pips and armed state move to the unit (`u.pips`, `u.ultArmed`); `ultUsed` stays per side (cap 2). Sites: `energy`, `ultArmed` [R :534-536], `toggleUltimate` 539-548, ultimate branches in `executeThrow` [R :962-1008], pip count on hit [R :1711], `updateDock` ultimate block, pip drawing [R :2423-2432], `drawBackFires` 2437, banner diamonds [R :2705-2706], reset. `supply` becomes per unit (`u.supply`, one slot per unit, a new crate replaces the old [R docs/game_mode.md]). Shields stay per side. `js/ultimate.js` keys pips, armed and uses on one side string [R ultimate.js createLedger, canArm checks `ctx.turn !== side`]; extend it to `createLedger({ sides, units })` (pips and armed per unit, uses and `lastUseRound` per side) and wire it. Pass: extended `node scripts/test_ultimate.js`; 1v1 identical.

**S5. Turn flow and seeded rules (L).** `(not published)` replaces the `turn` string [R :553, used in about 40 places] and the wall-clock chains: `setTimeout(triggerAITurn, 900)` [:849], `setTimeout(resolveRound, 1500)` [:1293], `setTimeout(triggerAITurn, 600)` [:1576], `setTimeout(triggerAITurn, 1000)` and `setTimeout(resolveRound, 800)` [:1781-1783], and the inner timers of `triggerAITurn` 1271-1308 and `aiAttackNow` 1237-1269. Use a game-time `after(seconds, fn)` stepped inside `updatePhysics` so hit-stop [R :1567] pauses them. One `endUnitTurn(unit)` call at four sites: projectiles gone, lock, forfeit, AI knight defend. `resolveRound` 1310-1344 runs only after the last side phase. Keep `turn` as a derived getter for old code. Replace `Math.random` in rule paths by `rng()` (seed from `?seed=`): dice [:689, 746 stays visual], wind [:1324], AI noise [:1245-1262], AI move and defend chance [:1275, 1299], bounce die and shuriken spread [:980-1010], `randomizePositions` [:773-775], `aiClass` pick [:346, 376]. Visual randomness stays. Pass: with N=1 and a fixed seed two runs give the same `__pk.log`; node test_turnflow.

**S6. Formation and movement (M).** `TEAM_SIZE` constant (also `?size=4`), default 1 until S9 passes. Spawn from `units.js` formation. `stepDice` 742-770 clamps through `clampMove`; `randomizePositions` 771-783 is replaced by formation placement. Pass: node property test (section 7); browser shows 8 units.

**S7. Hits, overlap, splash (L).** Section 3 of the projectile loop [R :1688-1735] calls `findHit`; the blast [R :1753-1766] calls `splash`; wall damage per section 10. Friendly fire off. KO is not game over: the 1v1 shortcut `gameOver = p.team` [R :1712, :1763] becomes a `checkWin()` that tests whether a side has no living unit. Per-unit crit, stun, statuses, volley counter. Pass: node tests with the worked numbers of sections 9 and 10.

**S8. HUD, dock, selection, line-up picker (L).** Section 4. `buildStartScreen` 349-371 and `startMatch` 373-382 pick 4 units instead of `pickedHero`.

**S9. Built-in AI for several units (M).** Section 5.

**S10. Seats and public view (M, needs task 75).** Section 2.

**S11. Particle budget and level of detail (M).** Section 11.

**S12. Rules extraction (L, after the freeze if time is short).** Move projectile step, damage, statuses and the event stream into `(not published)`; the page becomes input + renderer + audio glue. Node plays full matches with the same module.

## 4. HUD and dock with 4 units

- Banners [R :2688-2713]: the plate shows the seat name (custom name when set), not a class. The two diamonds stay per side (ultimates left, cap 2 per match). The active side's banner keeps its glow, driven by `flow.activeSide`.
- Above each unit: active unit bar 110x9 at (x-55, y-214) as today [R :2390-2393]; others 80x6. Neighbours may stand 100 px apart (`MIN_GAP`), so the widest adjacent pair is 55 + 40 = 95 px [A arithmetic], which fits. No health numbers (owner 2026-11-10). Marker 1-4 (red) or A-D (white) on the ground under the feet, y 884 [A; mockup marker, docs/game_mode.md:60]. Pips (r 8) stay at y-232. Acted units get a small check on the bar.
- Active unit: a ground ellipse under the feet and a small down arrow above the pips; nothing else is enlarged.
- Existing overlap found while reading: the angle label is drawn at `player.y - 232` [R :2897] and the pips at `cy = -232` [R :2424]. Move the label to y-262 for the actor.
- Click-to-select (human phase only):
  1. Click a living, unacted own unit that is not the actor: it becomes the actor, unless a charge or dice roll is running. The countdown continues.
  2. Click the actor: toggles the action menu, as now [R :1105].
  3. Click an acted own unit or any enemy unit: ignored.
  4. Click elsewhere on the field: aim and charge for the actor, as now [R :1111].
  5. Hit zone: x within 70 px (90 for the actor) of the centre, y-230..y+30 [R :1105]. With overlapping zones the nearest centre wins, a tie goes to the lower slot. Keys 1-4 select a slot (free: used keys are Space, Esc, arrows, W S A D, M, H, U, T, F [R :1176-1203]).
  6. In the other side's phase clicks on units do nothing; sound, help and reset still work.
- Dock: shows the actor (portrait, name, bar, skills, angle, power). The old hero chips stay hidden [R :17-19]; in that space add a squad strip of 4 tiles (portrait or glyph [R :1519], mini bar, acted check). Click = select.
- Supply slots [R :195-196]: the left slot shows the actor's item and uses it on the actor; the right slot stays display-only and shows up to four small icons, one per enemy unit that holds an item [A: needs the `.ts-box` width checked in `css/dock.css`].
- Floating texts: per unit at most 3 lanes, 24 px apart; messages longer than 14 characters (for example the shield-block text [R :1685]) go to the centre line y 220, the same place the mode messages use [R :731].
- Layout rule: after S8 rerun the owner's overlap method (canvas HUD rectangles and DOM rectangles at 1078 and 634 px wide, log row "Top objects must not overlap"). Expected: 0 overlaps including 8 bars, 8 pip rows, 8 markers, both banners, both supply slots, the two coffins (x 120..520 and 1400..1800, y 262..514 [R :1856-1859]) and the dock (its top is about y 940 on the canvas [A]).

## 5. AI for several units

- Which unit acts: the next unacted unit in slot order (front to rear) [A]. Pause before each unit 1.0 s now [R :1274-1306]; make it 0.5 s from the second unit on, which saves about 1.5 s per phase [A].
- Target choice, from `publicView` only: the enemy with the lowest visible health bar (5 percent steps), ties to the nearest to the fence. A 25 percent chance to Move first stays [R :1299], clamped by `clampMove`.
- Aim keeps the no-simulator rule of thumb [R :1245-1262]: `power = aiCal * 2.32 * sqrt(gap) + AI_WIND_K * seenWind + error`, with the target x misread by up to 150 px on the 36 px grid, the wind by up to 1.2, `AI_AIM_ERROR` 6 [R :549-550]. Change: `aiCal` is learned per seat from every landing of its side, not only its own throw (all are public), with the same exponent 0.35 [R :1751]. The sim decides whether to lower the exponent.
- Angle: today a fixed 54 degrees [R :936]. A 54 degree flat-ground shot to a target 520 px away (front unit to front unit) passes the fence plane at about y 617 against a top at 610 [A, hand estimate], so close targets would hit the fence. Rule of thumb by gap: >= 900 px 54, 650-899 58, 450-649 64, below 450 70 degrees [A, to tune].
- Ultimate: use the four public rules of `docs/ultimate_rules.md` section 2h (finish, crowd, dialled in, deadline) instead of the auto-fire at 3 pips [R :1004, `who === "ai"`].
- Knight defend: the existing rule [R :1275-1296] generalises to the side's shield; with one knight per team nothing else changes.
- Cost: negligible CPU per turn (a square root, a few random draws). Wall time about 4.3 s per unit [A].
- Hit-rate target. In 1v1 the target 25 to 30 percent is the chance to hit the one enemy [R GAP_QUEUE B4; index.html:550 comment]. With four enemies a throw can hit a neighbour. Hand model [A]: if the 1v1 landing error is triangular with half-width a, then 30 percent = P(|e| <= 70) gives a of about 430 px; with neighbours 160 px apart a throw aimed at a middle unit hits some unit about 79 percent of the time, an end unit about 59 percent. Forcing 27 percent "any unit" would need a of about 1400 px, so the AI would hit its intended unit only about 10 percent and look random.
  - Recommendation: keep the AI's skill and measure two numbers, intended-unit hit rate (target 25 to 30) and any-unit hit rate (reported, expected 55 to 80 before tuning). Owner decides (question 5).
  - Tuning order if intended-unit leaves the band: `AI_VIEW_POS_NOISE`, then `AI_AIM_ERROR`, then the `aiCal` exponent.
  - Consequence [A]: each side lands about 4 x 0.6 = 2.4 hits per round at an any-unit rate of 0.6; one side's total health is about 395 and an average hit is about 25, so a wipe takes about 7 rounds.
- Both sides must improve round by round (`product.md`): record the intended-unit rate by round in the sim and expect it to rise.

## 6. Balance and rules that change with 4 units (all provisional)

| Topic | Proposal | Basis and risk |
|---|---|---|
| Ultimate energy | Pips per unit (3 hits light that unit's pips); uses capped at 2 per side per match and 1 per side per round | [R docs/ultimate_rules.md 2a, 2g]. Open: log section 4 item 3 (per controller or per unit). Alternative: one team pool |
| Pip count | A hit counts once per throw id; a volley hitting several units gives one pip to the thrower | [R :1711] |
| Supply drops | Keep one crate every 2nd round, sides alternate [R :1429-1431]; it lands 140..279 px in front of the favoured side's lowest-health living unit [A, replaces the single reference unit]; any unit of either side within 70 px takes it [R :1462]; the AI unit takes it only when hurt (health <= max - 20) [R :1467]; one slot per unit, a new crate replaces the old | the drop count is the same but 4 units reach it more often |
| Status stacking | Per unit, no stacking: poison and bleed take the larger remaining count [R :1500-1501], frost sets 2 throws [R :1726], slow 1, stun not on a unit stunned last turn [R :1699]. Area attacks apply a status once per unit | |
| Friendly fire | Off for every projectile, blast and status. No exception: OWNER 2026-11-10 the bride's bat swarm hits enemy units only (allies take no damage); the earlier text said it hits everyone [log rows "Bride ultimate (bat swarm)", "indiscriminate"] | not built |
| Wall | Shared, 100 percent, 8 per projectile hit [R :412]. Eight throws a round may break it by round 2 or 3 [A]. The sim reports the median round of the break; if it is under 3 ask the owner about 4 per hit | owner raised the wall already |
| Frost, stun, slow | Per unit; frost counts that unit's own throws; stun shortens that unit's next turn to 7 s | [R :556-559] |
| Heal skill | Applies to the actor [R :788-808]; the sky-target heal (not built) heals the whole side | log rows |
| Time to kill | 4 to 5 clean hits per unit (health 85..120 against damage 22..30 [R :486-530]) | |

## 7. Test plan (nothing here was run)

Node tests, plain `assert`, run from the repo root. Keep these green after every step: `node scripts/test_particles.js`, `test_class_stats.js`, `test_ultimate.js`, `test_sim_balance.js`, and the python tests in `tech.md`.

| Test (new file) | Expected |
|---|---|
| `test_units.js` | start x red [700,540,380,220], white [1220,1380,1540,1700], gaps 160; `validateLineup`: 4 valid combos pass; 3 of one class, 2 knights, 3 or 5 members fail |
| `test_units.js` property | 20 seeds x 10 000 random moves and knockbacks: living neighbours never closer than 100, order never changes, x always in the zone, moved distance <= requested |
| `test_turnflow.js` | 200 seeded matches with random kills: each living unit acts exactly once per phase, dead units are skipped, `roundNum` rises once per round, every match ends, same seed gives the same log |
| `test_hitcheck.js` | worked example of section 9 (shot 1 A 96; shot 2 B 55; shot 3 B 61; volley 12.0 / 12.6 / 16.5); edges: dx 70 hits, 70.01 misses; y = top hits, top - 0.01 misses; head dx 35 and y-142.5 are inside |
| `test_hitcheck.js` splash | section 10: flat 36/36/36/0 (total 108), stepped 36/27/18/0 (81), linear 31.4/25.2/19.1/0 (75.7); distance 234 inside, 234.01 outside; no ally ever damaged |
| `test_seatview.js` | for each seat, JSON of the view holds none of `seed, rng, pending, dice, shieldPoints, aiAim, aiCal`; enemy shield absent unless revealed; health is a multiple of 5 percent; an agent seat cannot act for another seat, out of phase, twice, or for a dead unit, and a rejected call leaves the turn unused |
| `test_ultimate.js` (extended) | pips per unit, uses per side; second ultimate in a round rejected; KO clears that unit's pips only |
| `sim_4v4.js` | see below |

`(not published)` (extends `sim_ai_nosim.js`, which copies the page physics and the 70 px box [R sim_ai_nosim.js:1-30]): seeded; four enemy boxes with first-hit; the AI of section 5 against a scripted human bot (exact view, error 14); 200 matches, then 3 000 AI throws for the rate. Expected [A until run]: all matches end, no spacing violation, intended-unit hit rate 24 to 31 percent (standard error about 0.8 points at 3 000 throws), any-unit rate reported, mean rounds reported (hand guess 6 to 9), the share of matches under 8 minutes by the timing model of section 1, first-side win-rate gap at most 10 points (otherwise alternate the opener each round), same seed same result.

Browser checklist (the main line's browser pane), after S6, S8 and S11:
1. `?size=4`: 8 units, none touching at start.
2. Click a rear own unit: it becomes active, the ring moves, the dock changes, the countdown keeps running.
3. Click an acted or an enemy unit: nothing happens. Click the field: aim and charge.
4. Move into a teammate: stops 100 px short and says it was blocked.
5. A flat throw hurts only the first enemy; the unit behind is unhurt.
6. Wizard ultimate on a cluster: ring radius 234 with two inner marks, per-unit numbers match section 10.
7. A KO: wisps, queue skips the unit, survivors do not move.
8. All four down: result panel, click returns to the start screen. Reset works in rounds 1-2.
9. Overlap method of section 4: 0 overlaps. Frame probe of section 11 inside its limits.

## 8. Step schedule

Sizes are my guesses [A]: S = 0.5 day, M = 1 day, L = 2 days; total about 16 days against the provisional freeze 2026-11-27 [R docs/kiro_task_75.md] from 2026-11-10 (17 days). Must-have before the freeze: S0 to S9, a minimal S10 and the level-of-detail part of S11, about 13 days. S12 after.

| Step | Size | Testable after | Needs owner | Rollback |
|---|---|---|---|---|
| S0 | S | smoke list recorded | no | revert the commit |
| S1 | S | `test_units.js` partial; 1v1 identical | no | revert |
| S2 | M | 1v1 identical (smoke list) | no | revert |
| S3 | M | 1v1 identical | no | revert |
| S4 | M | extended `test_ultimate.js`; 1v1 identical | question 2 | revert |
| S5 | L | `test_turnflow.js`; same-seed log equality | question 1 | revert; this is the riskiest step, merge only after S2-S4 are stable |
| S6 | M | spacing property test; `?size=4` shows 8 units | no | set `TEAM_SIZE = 1` |
| S7 | L | `test_hitcheck.js` with section 9 and 10 numbers | question 3 | set `TEAM_SIZE = 1` or revert |
| S8 | L | browser checklist 1-3, 7-9, overlap method | question 4 | `TEAM_SIZE = 1` restores the old HUD path |
| S9 | M | `sim_4v4.js` band | question 5 | keep the old `aiAttackNow` behind a flag |
| S10 | M | `test_seatview.js`; MCP check | task 75 | disable the bridge |
| S11 | M | `bench_fx.js`, frame probe | no | flag `FX_LOD = 0` |
| S12 | L | node plays a full match with `match_rules.js` | no | the page keeps its old loop until parity |

One branch `kiro/4v4`, one commit per step, merge to main only after the tests of the touched area pass (`structure.md`). From S6 on, `TEAM_SIZE = 1` is the one-line way back to the 1v1 game.

## 9. Overlap and damage

Facts [R]: body box |dx| <= 70 and y between `u.y - 190` and `u.y` [:1688-1692]; head box |dx| <= 35 and y <= `u.y - 142.5` (top quarter) [:559, 1695]; crit x1.25, one per projectile [:559, 1695-1697]; the sprite is 220x220 but only draws [:571-572]; per step order: fence, the target side's sky shield, unit, ground [:1646-1747]; physics step 1/60 s [:2924]. At power 100 a projectile moves 100 x 13.8 / 60 = 23 px per step [A], far below the 140 px box, so no tunnelling.

Rules:
1. **Targets.** Living enemy units only. Friendly fire off. Dead units have no box.
2. **One projectile, one unit.** The first box entered takes the hit and the projectile is consumed. The unit behind takes nothing and no splash (normal hits have none).
3. **Pass over.** A point above a unit's box (y < `u.y - 190`) is not in it; the projectile flies on and may enter a unit behind.
4. **Overlap tie.** Only possible when enemies stand less than 140 px apart: if one step enters two boxes, the smaller |dx| to the projectile wins; equal goes to the lower slot (nearer the fence).
5. **Exceptions to rule 2.** (a) Knight shield: hops back onto the same unit while it lives [R :1730-1734], lost if it dies, never jumps to another unit. (b) Volleys (bat 5, skeleton 3) are separate projectiles; each hits at most one unit and the units may differ. (c) Hunchback boomerang (log rows): pierces the last living enemy by slot and returns to the first; not built. (d) Bride wave: `class_stats.js` says one unit with falloff, the start-screen card says "everything on the path" [R index.html:337]; for tasks 74 and the owner, not built here.
6. **Crit and stun** are evaluated against the unit that is hit, using the contact point. Stun only if it survives and was not stunned last turn [R :1699].
7. **Statuses** (bleed from spear, skull, axe; poison from wizard shells; slow from shuriken; frost from the spear [R :1706-1709, 1725-1728]) apply only to the unit damaged.
8. **Shields.** The sky bar is side-level and is tested before bodies, so it covers every unit of its side under it; each projectile that touches it costs one charge of two [R :1663-1686] (a 5-shuriken volley can lose two and let three pass; provisional). The knight's hidden A-B-C points (not built) guard a place on a remembered path, not a unit, and are tested at the same place in the order.
9. **Skeleton chain.** One counter per volley, shared by its three javelins [R :1001 `Object.assign` copies the same `ultGroup` object created at :999]; +5 percent per earlier hit of the volley on any enemy unit; the third of three is a crit with stun for that unit [R :1701-1705]. If only two hit, no crit.
10. **Spacing.** `MIN_GAP` = 100 px centre to centre between living teammates [A]: heads (70 px wide) never overlap, bodies may overlap by up to 40 px. Start gap 160. A Move or knockback stops at 100 px from the next unit, never pushes it, and is clamped to the zone (160..760, 1160..1760). Order among living units never changes. Knockback (hunchback axe 50 px, class_stats; knight bash same 50 [A]) pushes away from the thrower, so toward the rear; at the zone edge or a neighbour it moves less.

**Worked example, three units in a line.** Red A knight (120 HP) x 700, B wizard (85) x 600, C bat (90) x 500, all y 860. Boxes: A 630..770, B 530..670, C 430..570 (A and B overlap on 630..670), tops y 670. A white skeleton spear does 24, crit 30.0.
- Shot 1, flat at y 760 from the right: enters A at x 770, body (y 760 > 717.5). A 120 to 96. B and C untouched. A also bleeds and is frosted.
- Shot 2, steep lob (slope 2.75 per px) crossing x 770 at y 200: at x 630 it is at y 585, above A's top, so A is passed over. It reaches y 670 at x 599.1, inside B's box, |dx| 0.9 <= 35 and y <= 717.5, so a head hit: 24 x 1.25 = 30.0. B 85 to 55, stunned (survives, not stunned before). C untouched.
- Shot 3, steeper, reaching y 670 at x 640: inside A (|dx| 60) and B (|dx| 40). B has the smaller |dx| and takes it. 40 > 35, so a body hit: B 85 to 61. At x 650 both are 50 and A would take it.
- Skeleton ultimate: three javelins of 24 x 1.5 / 3 = 12.0 [R :999], one lands on each. A takes 12.0 (120 to 108). B takes 12 x 1.05 = 12.6 (85 to 72.4). C takes 12 x 1.10 = 13.2, then x 1.25 = 16.5 (90 to 73.5) and is stunned. Total 41.1.

## 10. Spread and splash

| Area attack | Radius | Source |
|---|---|---|
| Wizard ultimate blast | 234 px (13 steps x 36 / 2), damage 1.5 x normal = 36.0 for damage 24, no bleed (removed by the OWNER 2026-11-10); measured on x only, unit centre to impact [R :1753-1766, 1006] | built; the shell itself is a normal hit and a directly hit unit takes both |
| Wizard fire on the ground | 13 flames, centres at impact +- 216 px [R :1757]; only a stand-in sprite, no fire damage in code | not built; no number invented |
| Wizard normal shell burning ground | chance, 5 steps (180 px) working value in the log | not built |
| Bride wave | one unit, full damage within 40 px, falling to 45 percent at 105 px [R js/class_stats.js bride.special.wave] | class not playable; width, not a blast |
| Bride bat swarm | every ENEMY unit (allies take no damage, OWNER 2026-11-10), 1.3 x normal; no radius in the log | not built |
| Hunchback | the log replaced the bell by an axe with knockback 50 px and a boomerang ultimate; `class_stats.js` still names `proj_bell` and `tower_toll` (stale) | no splash exists |

Rules:
- **Measure** from the impact point to the unit centre on x for ground impacts, as the code does. A hitbox-edge test would reach 70 px further (304 px centre distance), so a unit whose centre is outside the drawn ring could be hurt; reject.
- **Falloff, recommended: stepped, 3 bands** matching the drawn rings: <= 78 px (R/3) 100 percent, <= 156 px (2R/3) 75 percent, <= 234 px 50 percent. This changes the confirmed "each unit hit by an ultimate takes 1.5 x" (log row "Ultimate damage per unit"); without owner approval keep the flat built behaviour (question 3).
- **Targets:** all living enemy units in range, any number; friendly fire off (no exceptions).
- **Fence:** it does not block the blast (the code never checks it [R :1753-1759]), so units just behind an intact fence are hit. Wall damage: the projectile's own hit costs 8; add one more 8 if the impact is within 117 px of the fence box, once per blast. Provisional.
- **Display:** a ground ring of radius 234 (new preset `blast_ring`) with two thin inner rings at 78 and 156, fading in 0.9 s like `landRings` [R :1842 and the ring loop after the ground draw]; each unit hit shows its own number. The flame sprites must not extend the visible size past the ring.
- **Worked example:** wizard damage 24, blast 36.0, enemies at 60, 140, 220, 300 px from the impact (centre distance).

| Distance | Flat (built) | Stepped (recommended) | Linear 100 to 50 percent |
|---|---|---|---|
| 60 | 36.0 | 36.0 (band 1) | 36 x (1 - 0.5 x 60/234) = 31.4 |
| 140 | 36.0 | 27.0 (band 2) | 25.2 |
| 220 | 36.0 | 18.0 (band 3) | 19.1 |
| 300 | 0 (outside) | 0 | 0 |
| Total | 108.0 | 81.0 | 75.7 |

## 11. Particle and effect budget (8 units)

Facts [R]: pool cap 500, drop-oldest [index.html:651; js/particles.js emit]; `fxEmit` multiplies scale by 1.25 and caps it at 4 [:654-662]; a preset's count is `round(base x sqrt(scale))` [js/particles.js `cnt`]; every `glow` particle creates a radial gradient when drawn [js/particles_draw.js:105]; the old `particles` array (`spawnParticles`) has no cap and draws one `arc` with save and restore per dot [:1395, draw step 9].

Reused presets by name (all exist in `js/particles.js`): `muzzle_flash, smoke_puff, impact_burst, hit_sparks, landing_ring_dust, shield_ricochet_sparks, shield_materialize_ripple, ko_wisps, sprite_mist, sprite_impact_flash, sprite_ghostfire, sprite_stardust, sprite_rune_circle, sprite_poison, blood_spray, poison_drip, frost_shatter, bounce_ring, heal_rain, weapon_rune_halo, weapon_charge_aura, weapon_trail_spear, weapon_trail_dart, weapon_trail_cannon, weapon_trail_shield, weapon_enchant_stardust, face_glow_pumpkin, face_glow_skeleton, ult_fires`. Defined but not emitted in the code I read, usable now: `bounce_ring` (knight bounce), `poison_drip` (poison tick, 5 particles instead of 13), `frost_shatter` (frost apply).

Particle counts per event at today's call scales [A, hand arithmetic from the formulas above]:

| Event | Plays now | Pool | Old dots |
|---|---|---|---|
| Throw release | `weapon_rune_halo` 0.6, `muzzle_flash` 0.45 (wizard 1.3 plus `smoke_puff` 1.2) | 19 (wizard 35) | 12 (wizard 50) |
| Hit | `impact_burst` 1.2 (41), `hit_sparks` 1.1 (20), `sprite_impact_flash` (1); spear adds `blood_spray` (10) | 62 to 73 | 55 |
| Crit | float text only now | 0 | 0 |
| Block | `shield_ricochet_sparks` 1.1 | 17 | 45 |
| Wall hit | `impact_burst` 0.9 (35), `sprite_impact_flash` | 36 | 20 |
| Wall break | same as a hit, no special effect | 36 | 20 |
| Ground land | `landing_ring_dust` | 15 | 12 |
| Wizard blast | `impact_burst` 3 (65), `sprite_stardust`, 13 x `sprite_ghostfire` 1.6 (39) | 105 | 0 |
| Status tick | poison: `sprite_poison` + `blood_spray` 13; bleed: `blood_spray` 10 | 10 to 13 | 0 |
| KO | `ko_wisps` 1.2 (16), `sprite_mist` (4) | 20 | 0 |
| Ultimate start | text and the existing release effects | 0 | 0 |
| Flight trail, per projectile, alive at once | spear 14, shuriken 16, shield 18, cannon 60, plus stardust 17 | 31 to 77 | 0 |
| Ambient, 8 units | `face_glow_*` 1 per 0.3 s per pumpkin or skeleton unit (about 11 alive), status drips (a few) | about 15 | 0 |

New presets (3):

| Name | Look | Count | Life | Layer |
|---|---|---|---|---|
| `blast_ring` | three flat-gold rings at radius R, 2R/3, R/3 (option `radius`), ember rim | 3 | 0.5 to 0.9 s | GLOW |
| `fence_shatter` | brown plank splinters and grey dust flying out of the fence when it breaks | 14 | 0.6 to 1.1 s | BODY |
| `crit_flash` | gold star burst with 6 streaks at the head contact point | 9 | 0.12 to 0.3 s | GLOW |

Plays after the change: hit 62 + 10; crit adds `crit_flash` (9) and `frost_shatter` (about 9) where frost applies; block as now; wall hit `impact_burst` at 0.6 plus `sprite_impact_flash`; wall break `fence_shatter` plus the wall hit effect; blast `blast_ring` + the 105; status tick `poison_drip` / `blood_spray`; KO `ko_wisps` for each, `sprite_mist` for the first KO of a group.

Budget:
- Pool: keep 500 as the hard cap, aim for 300 alive or fewer (about 400 is the alarm line). Sustained emission 600 per second or fewer (alive is about rate x mean life 0.55 s [A]). At most 120 new pool particles per frame; a bigger event is split over the next frames (up to 3 frames, 50 ms).
- Old dots: cap 150 alive (new), and none for secondary victims. Longer term replace them by presets.
- Glow-shaped particles alive: 200 or fewer (each draws a gradient).
- Level of detail (the `FX_LOD` flag): when alive > 300, or three events start inside 0.25 s, the next events use scale x 0.6.
  - A secondary victim of the same event (second to fourth unit hit in 0.5 s) gets `hit_sparks` 0.8 plus `sprite_impact_flash` (18 particles) and no old dots, instead of 73 + 55. A bat volley hitting five units: 73 + 4 x 18 = 145 instead of 365.
  - Extra projectiles of a volley (`extra: true` [R :990-1001]) emit their trail every second step and no stardust: 5 shuriken trails 165 alive become about 65.
  - `face_glow_*` runs only for the active unit and the acting enemy while alive > 200. Status ambient drips at most one per 0.5 s across all units.
- Worst cases [A]: wizard blast hitting 4 clustered enemies with 2 KOs: 105 + 73 + 3 x 18 + 36 = about 268 pool particles in 0.5 s, peak alive about 390 with trail and ambient (under the cap, above the 300 target, so LOD kicks in). Bat volley with 5 hits: about 145 + 65 + 15 = 225.
- Frame-time check, headless: `(not published)` creates `Particles.createSystem({ seed: 1, maxParticles: 500 })`, plays the two worst cases and 10 s of ambient at 60 steps per second, times `update()` with `process.hrtime.bigint()`, counts alive and glow-shaped particles each step, and runs `ParticlesDraw.drawParticles` on a counting stub context. Expected limits [A, machine-dependent]: update p95 <= 0.3 ms and max <= 2 ms; alive never above 500, p95 <= 400; glow alive p95 <= 200; gradients created per frame <= 250.
- Frame-time check, browser: add `window.__perf` (ring buffer of `performance.now()` around the `updatePhysics` loop and around `draw()` + `drawRuleOverlay()` in `loop` [R :2928-2950]) and a `?stress=1` script that runs both worst cases on 8 units for 20 s. Expected [A]: median work per frame <= 6 ms, p95 <= 10 ms, p99 <= 14 ms, no frame over 33 ms. If it fails, lower the cap to 400 and tighten LOD before cutting effects.

## 12. Owner questions (one line each, recommendation first)

1. First side each match: die (as the brief says) or human first (confirmed text)? Recommend die, same opener all match.
2. Ultimate pips per unit with a cap of 2 per side? Recommend yes.
3. Blast falloff: stepped 100/75/50 percent, or keep flat 1.5x? Recommend stepped.
4. Duplicates: allow up to 2 per class and 1 knight until 6 classes exist? Recommend yes.
5. Hit-rate target: keep the intended-unit rate at 25 to 30 percent? Recommend yes; any-unit rate will be higher.
6. Bride wave: one unit or everything on the path? (task 74 decides the class table.)
7. Round cap: none in v1, or a cap such as 7 (roster_design) with a health tie-break? Recommend none, decide after the sim.
8. "One decision per round" for agents: read it as one per unit turn? Recommend yes.

## 13. Not verified

- Nothing was executed: no test, sim, benchmark or browser run. All hit rates, counts, timings and frame limits are hand arithmetic or guesses and are marked [A].
- Line numbers are from one read of `index.html` as it stands; lines marked with a range may shift if the file changes before S1.
- I did not check `css/dock.css` (slot box width, dock height), `scripts/test_constants_sync.py` internals, or whether `test_sim_balance.js` covers the wall damage constant.
- The die for the first side and the "ultimate energy per unit" reading are not confirmed in the log; they are questions 1 and 2.
