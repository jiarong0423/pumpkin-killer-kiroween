# Ultimate rules: WHEN an ultimate may be used (Kiro task 39)

Status: **design only.** I changed no code, art or sound. I cannot play the game, see images or hear audio, so every statement about how something looks or feels is **unverified**. Numbers marked "guess" are first values for a playtest.

Owner words (2026-11-09): "An ultimate cannot be used at any time (不能隨時放大招)." "Kiro, design it."

Owner rules this document obeys (all from `(not published)`, which wins over every other document): a normal attack is ONE shot at ONE unit; THREE successful hits light three pips above the unit's head and only then can the ultimate be triggered; each player counts their own hits; at most 2 ultimates per match; no confirm step and no preview before a throw; the screen stays clean.

What the unit-by-unit effects are lives in `docs/ultimate_mapping.md`. This file only decides WHEN.

## 0. What I read, and the code facts the rules depend on

Read: `docs/ultimates_design.md`, `docs/roster_design.md`, `docs/converge_characters.md`, `docs/sound_mapping.md`, `(not published)`, `docs/airdrop_design.md` (item and turn rules), `docs/mcp_agent_protocol.md`, `docs/game_mode.md` (ultimate section), `scripts/mcp_stdio_server.py` (grep), `index.html` (energy, `executeThrow`, click menu, defend, move, skills, `resolveRound`), the preset names in `js/particles.js`.
**Not present:** `docs/review_reconcile.md`, `(not published)`. I worked without them.

| Fact in `index.html` | Value | Why it matters |
|---|---|---|
| Pip counters | `energy = {player, ai}`, `ultUsed = {player, ai}`, one counter **per side**, not per unit. A hit adds 1 (once per `throwId`) only while `ultUsed < 2`; max 3 | The rules below say "per unit"; the code needs a per-unit counter for 4 v 4. |
| Only user of the counters | `executeThrow`: if the weapon is the shuriken, not heavy, `energy >= 3` and `ultUsed < 2`, the throw **turns into the scatter by itself** (energy to 0, `ultUsed++`) | Today there is no arming and no choice: the cat's ultimate fires on the first throw after the third pip, for the player and for the AI. That is the behaviour the owner said must not happen "at any time". |
| After the scatter | the 5 shuriken share one `throwId`, so a landing adds 1 pip | The ultimate throw gives 1 pip in the built code. Rule below: 0. |
| Pip drawing | I found no drawing code for the three pips in `index.html` (search for `energy`, `pip`, `ultUsed`). The owner log says "done" | **Could not verify** the pips are drawn in this checkout. |
| Click menu | `actionMenuItems()`: move, attack, defend (knight only). Click on the unit opens it; the next click on an entry runs `chooseMenuItem` | The ultimate entry fits here. |
| Move | `movedThisTurn`, once per turn, does not use the throw | Move can come before an ultimate. |
| Defend | `toggleShieldDefend` / `lockShield`: uses the whole turn, "a defend turn cannot also attack" | Defend and ultimate exclude each other. |
| Sky shield | `shields[targetTeam]` blocks only the **enemy's** projectiles; lasts 2 rounds | A placed shield does not affect the owner's own ultimate. |
| Skills | `selectedSkill` normal / double / heavy; heal is instant and free (+35 HP, no turn) | Heavy and double must not combine with an ultimate (the built code already requires `!isHeavy`). |
| Charging | press anywhere on the field starts charging at once (`startCharging`), release throws | Arming must happen before that press. |
| Frost curse | `unit.weak` = number of next throws at 70 % damage; applied to `pj.dmg` before the ultimate branch | A weakened unit's ultimate is 1.5 x 0.7 in the built code. |
| Freeze / stun | no such state exists (searched `frozen`, `freeze`, `stun`) | "Frozen" in the task text has no code to block on. Frost curse is the only debuff. |
| Round | `resolveRound()` runs after the agent's turn and does `roundNum++`; one round = the human turn plus the agent turn | "Once a round" is well defined. In 4 v 4 each side has a phase, units act once per phase (`docs/roster_design.md` section 3). |
| Timer | `TURN_SECONDS = 12` | Arming does not pause it. |
| Public ultimate field today | `ultimates_remaining` per team (`red`, `white`), value 2 (`mcp_stdio_server.py`) | The new fields below extend it. |

## 1. The rule, in two short sentences (to show on screen)

English: "Hit three times to light your pips. On your turn, pick ✨ Ultimate instead of Attack: it is your throw for that turn, and each side can use one per round and two per match."

中文：「命中 3 次點亮 3 顆能量珠。輪到你時，選「✨ 大招」來代替攻擊，這回合就用這一發；每方每回合最多 1 次、整場最多 2 次。」

## 2. Recommended rule: "arm from the menu, it IS your throw"

### 2a. The gate (all must be true, or the menu entry is not offered)

1. It is the owner's own turn and the unit has not thrown yet this turn.
2. The unit has 3 lit pips (`ult_ready`).
3. The side has an ultimate left (`ultimates_remaining` above 0, so used count 0 or 1).
4. The side has not used one yet this round.
5. The unit is alive and is not in a defend turn.

Nothing else gates it. In particular there is **no round-1 lockout and no "not two rounds in a row" lockout**, because they would never trigger: a unit needs three successful throws, so it cannot be ready before the start of its 4th turn, and after use its pips return to 0 so the same unit needs three more. Two different units of one side can fire in consecutive rounds; rule 4 stops them firing in the same round. If a playtest shows back-to-back ultimates swing matches too hard, the lever is a published constant `ULT_COOLDOWN_ROUNDS` (default 0, so no code path unless raised).

### 2b. Input

| Step | What the player does | Notes |
|---|---|---|
| 1 | Click the unit | The existing action menu opens above the head. |
| 2 | Click the gold entry `✨ 大招` | Appears only when the gate is open. It sits right of `🎯 攻擊`. Choosing it **arms** the ultimate. |
| 3 | Move the pointer, press and hold to charge, release | Exactly the attack input: angle follows the pointer, hold charges. No confirm step, no preview, no aim line. |
| Cancel | Esc, or click the unit again and pick `取消大招`, `🎯 攻擊` or `🎲 移動` | Arming costs nothing until release, so cancelling is free. |

- **Button or menu?** Menu entry only. No dock button: the old skill buttons are an open owner question (log section 4, item 6) and a new button would add clutter. Optional keyboard key `U` toggles arming (accelerator, off by default until the owner asks).
- **What the pips do when ready:** they are display only. Clicking them does nothing, so there is exactly one way in.
- **Must it be armed before aiming?** Yes. Pressing on the field starts charging at once, so there is no moment after aiming to choose. Arm first, then aim and hold.
- **Does it replace the normal attack?** Yes. The ultimate throw is the unit's one throw for the turn.

### 2c. Order of actions inside a turn

| Action | Allowed before arming | Allowed after arming | Effect |
|---|---|---|---|
| Move (dice) | Yes, then arm | Choosing Move **disarms**; arm again after the move | Menu choices are "last choice wins". |
| Heal skill, supply item | Yes (both are free actions) | Yes | They do not touch arming. |
| Heavy or double skill | Choosing one **disarms** | Choosing one **disarms**, with a one-line toast | An ultimate is never heavy and never doubled. |
| Defend (knight) | Defend uses the whole turn: no throw, so no ultimate | Choosing Defend disarms | Pips are kept. |
| A floating shield placed on an earlier turn | No effect | No effect | The shield only blocks enemy shots. I remove the old claim that a knight with an active shield has an empty hand (no code basis). |
| Attack | n/a | Choosing Attack disarms | |
| Switch to another own unit (4 v 4) | n/a | **Disarms**; arming belongs to one unit and one turn | |

### 2d. When it is spent

- **Spent at release**, when the projectile leaves the hand. Pips go to 0 and the side's used count goes up by 1.
- **Spent even if it misses**, is blocked by the sky shield, or hits the fence. Reason: a refund on a miss would let a player probe with free throws, which the product rules forbid for the AI and which would turn the ultimate into a trial shot for humans. The trigger hit is part of the risk (see the mapping file: no trigger hit, no follow-up). **Owner to confirm (question 1).**
- **Not spent** if the player cancels before release, switches unit, or the 12 s timer ends with no throw. If the timer forces the throw out while armed, it counts as released and is spent (it left the hand).
- The ultimate throw gives **0 pips**, even if it lands. (The built code gives 1; this is an engine change.)
- Pips never decay: being hit, moving or waiting do not remove them. Only the unit's death or using the ultimate clears them.
- When the side's used count reaches 2, pips stop counting and are hidden for that side.

### 2e. Armed state, hit or killed while armed

Turns do not overlap: the opponent does not act during the owner's turn, and nothing in version 1 damages a unit during its own turn (the supply ghost drops items, it does not hurt). So **an armed unit cannot be hit or killed while armed**, and no interrupt rule is needed. If a future effect does hurt or kill it mid-turn: damage does not disarm; death removes the unit, its pips and its arming, and the side's used count is **not** spent. Alternative B below is the only variant where this question has a real answer.

### 2f. What blocks it

| Condition | Blocks? | Rule |
|---|---|---|
| Dead | Yes | No turn, no pips. A dead unit's pips vanish; the side's used count is unchanged. |
| Frost curse (weakened, `weak > 0`) | **No** | It is a damage cut, not a lock. Every strike of the ultimate uses the unit's current normal damage, so the whole ultimate is 30 % lower, and it consumes one of the two weakened throws. The menu entry shows `🧊 -30%`. The player may wait. |
| Frozen / stunned (skip-turn status) | Would block | Does not exist in the code today. If added: a unit that cannot throw cannot be armed. |
| Defend turn | Yes | See 2c. |
| Used count already 2 | Yes | `no_ultimates_left`. |
| Side already used one this round | Yes | `ultimate_used_this_round`. The entry is shown greyed with the text "本回合已用". |
| Wrong turn / phase | Yes | `wrong_phase`. |

### 2g. What the opponent sees (human) and what sub-agents see

Human opponent: three pips above every enemy unit (always, so progress is readable), a gold glow and a ground rune ring under an enemy unit that is ready, and when it fires a short name text "✨ 大招：<名稱>" (the same floating-text style the built scatter already uses). They cannot see the owner's arming, because arming happens in the owner's turn and the other side is idle then; the visible warning is the ready ring. Counter-play: the ultimate needs its trigger hit, so the sky shield, the fence, a changed distance (Move) or standing apart in 4 v 4 all weaken it.

Sub-agents get **public information only**, one decision per round, and the same published aim error. Field names only:

| Where | Field |
|---|---|
| `get_public_state`, per unit | `ult_pips` (0 to 3), `ult_ready` (true or false), `ult_armed` (true or false), `ult_kind` (rule id: `ghost_spears`, `chain_blast`, `shuriken_scatter`, `shield_chain`, `piercing_wail`, `tower_toll`, `reaper_combo`), `statuses` (list of `id`, `throws_left`; id `frost_curse`) |
| `get_public_state`, per side | `ultimates_remaining` (exists), `ultimates_used`, `ult_used_this_round` |
| Throw call (`submit_action` with a throw; the project rules call it `submit_throw`) | new optional argument `ultimate` (true or false). For an agent, arming and throwing are one call, so no separate arm step exists. |
| `get_history`, per throw | `ultimate`, `ult_kind`, `trigger_hit` (true, false or null), `hits` (list of `unit`, `damage`, `strike`), `pips_after` |
| Rejection reasons (a rejected call does not use the turn) | `ultimate_not_ready`, `no_ultimates_left`, `ultimate_used_this_round`, `unit_dead`, `wrong_phase`, `ultimate_with_defend`, `ultimate_with_heavy` |
| Published constants (`shared/constants.json`) | `ULT_PIPS` 3, `ULT_MAX_PER_MATCH` 2, `ULT_PER_ROUND` 1, `ULT_COOLDOWN_ROUNDS` 0, `ULT_MULT` 1.5 |

`ult_armed` is only ever true for a human's unit during that human's own turn, so an agent never sees it true when it decides. Not exposed: the seed, the future knight die, any landing prediction. Follow-up targets are chosen by public rules (nearest by public x, or the unit order), so an agent can reason about them from public positions.

### 2h. How the AI decides to use its own

Same gate, same single decision, same aim error, no trial throw, no simulator. At the start of its turn, when the gate is open, it uses the ultimate if **any** of these is true (public data only); otherwise it attacks normally:

1. **Finish.** A living enemy has public `hp` at or below the ultimate's total on one unit (trigger plus follow-up: 2.5 x normal; cat 1.5 x).
2. **Crowd.** Two or more living enemies sit inside the class's follow-up reach (public x and the public class card). Never true in 1 v 1.
3. **Dialled in.** Its own last two landings (from its own `get_history` record) were both within 60 px of an enemy. This is the same "dialled in" test as `docs/airdrop_design.md`.
4. **Deadline.** It has held a ready ultimate for 3 of its own turns (guess), or its side has one living unit left.

The in-page scripted AI follows this list as a stand-in; the MCP sub-agents are the real opponents and receive the same list in their prompt as advice, not as a forced rule. In 1 v 1 only rules 1, 3 and 4 can fire. (Open owner question 5 in the log, whether the in-page AI may use the projectile integrator, is not affected.)

### 2i. What the UI shows

| State | Display |
|---|---|
| Counting | Three empty sockets above the head (`ult_pip_socket`, lit state reuses the existing `fx_ghostfire` sprite). Each successful hit lights one with a small `sprite_ghostfire`. |
| Ready (third pip lit) | The three pips turn gold and pulse once (0.3 s). Event `ultimate_ready` plays once. `sprite_rune_circle` flat at the feet, then a slow breathing ring (alpha about 0.25) until used. Only ready units have a ring. Menu gets the gold `✨ 大招` entry. |
| Armed | The pips change to flame (`sprite_ghostfire` on each pip), a steady `weapon_charge_aura` on the held weapon, a small label "大招 已備" beside the pips. The menu entry becomes `取消大招`. |
| Blocked | Entry greyed with a one-word reason: "本回合已用" or `🧊 -30%` (the latter still usable). Dead or defending units show no entry. |
| Used count | In the top plate, two small runes next to the portrait: both dark = 0/2, one filled = 1/2, both filled = 2/2. For 4 v 4, one pair per side. |
| Firing | Short gold text "✨ 大招：<名稱>" above the unit for about 1.2 s, then the class effect. No full-screen cut-in, no dimming in version 1 (the owner wants a clean screen). |
| Cancel | Esc or the `取消大招` entry; the armed look stops at once. |

## 3. Alternatives and trade-offs

| | Recommended: arm from menu, replaces the throw | Alt A: auto-fire when ready (the cat today) | Alt B: wind-up round |
|---|---|---|---|
| How | Menu entry, then normal hold and release | No input. The first throw after the third pip becomes the ultimate | Arm on turn N: no throw that turn, pips burn. On turn N+1 the throw is the ultimate. A hit on the armed unit cancels it and keeps the pips |
| Matches "cannot be used at any time" | Yes: needs full pips, the owner's own turn, a deliberate choice, a per-round and per-match limit | Weak: it fires at the first chance, the owner never chooses the moment | Strongest: telegraphed and interruptible |
| Feel first (no confirm, no preview) | Kept: one extra click on a menu already in use | Kept | Broken for that turn: the player gives up a throw and waits |
| Choice for the player | Full: hold for a crowd or a finisher | None. Bad luck can waste it on a weak position, and the AI cannot save it | Full, with a price |
| Sub-agent fit (one decision per round) | One call with `ultimate: true` | Nothing to decide | Two calls in two rounds; `ult_armed` becomes a real public state |
| Two-sentence rule | Yes (section 1) | Yes, one sentence | No: needs interrupt, refund and wind-up rules |
| Match pace | Unchanged | Unchanged | Each ultimate costs an extra turn; with a 7 round cap that is a visible loss |
| Engine work | Small: per-unit pips, armed flag, one argument, six rejection reasons | Smallest, but the cat already has it | Larger: persistent armed state, interrupt on damage, refunds |
| Main risk | Players hold it too long (answered by the AI deadline and by 2 per match) | Wasted on turns where it cannot hit; reads as random | Slow and fiddly; weak team may never get the turn |

Why the recommendation: it is the only option that is deliberate, fits "press anywhere, hold, release" without a confirm step, keeps one decision per round for agents and can be explained in two sentences. Alt B is the right fallback if the owner finds the ultimate too easy to land, since it adds counter-play.

## 4. Edge cases

| # | Situation | Rule |
|---|---|---|
| 1 | Third pip lights on this turn's throw | The turn is over; the earliest arming is the unit's next turn. |
| 2 | Moved with the dice, then wants the ultimate | Allowed. Move first, then arm (arming before the move is cleared by the move). |
| 3 | Armed, then the player picks Move, Attack or Defend | Disarmed. Pips and used count unchanged. |
| 4 | Knight places or moves the floating shield | That is a defend turn: no throw, no ultimate. Pips kept. A shield placed earlier does not matter. |
| 5 | Heavy or double skill selected | Arming clears it, selecting it clears arming. Never combined. |
| 6 | Heal skill or a supply item | Free actions; arming is untouched. |
| 7 | 12 s timer ends before release | Not spent, unless the timer forces a throw out (then spent). |
| 8 | Trigger projectile is blocked by the sky shield, hits the fence, or lands on the ground | Spent. No trigger hit, no follow-up strikes. The sky shield loses one charge, as for any projectile. |
| 9 | Trigger hit kills the target | Follow-ups still resolve on the other units chosen at the moment of impact. If there are none (reaper, 1 v 1), they are skipped. Spent. |
| 10 | Unit is weakened by the frost curse | May use it; all strikes at 70 %; consumes one weakened throw. |
| 11 | Unit dies while holding pips | Pips vanish. Used count stays. The side may still use its other ultimates. |
| 12 | Two ready units on one side in the same round | Only the first to act may use it (rule 4 of the gate). The other keeps its pips. |
| 13 | Both sides fire in the same round | Allowed: the limit is per side. |
| 14 | Side has used 2 | Pips stop counting and are hidden; no entry, no ring. |
| 15 | Last enemy unit is alive and the ultimate is a multi-unit one | Works with the targets it has; extra follow-ups are lost, not redirected. |
| 16 | Match ends mid-ultimate | Normal win rule; remaining strikes are cut. |
| 17 | `resetGame` | Pips, used counts and arming reset (the built reset already clears `energy` and `ultUsed`). |
| 18 | Agent sends `ultimate: true` while not ready | Rejected with `ultimate_not_ready`; the turn is not used. |
| 19 | Human clicks a pip | Nothing happens. |
| 20 | Early game (rounds 1 to 3) | No rule needed: pips cannot reach 3 yet. |

## 5. Owner questions (one word each, my recommendation first)

1. Is the ultimate spent when it misses or is blocked? **Spent.** (Alternative: refund.)
2. Does the ultimate throw itself give a pip? **No.** (The built cat code gives 1.)
3. One ultimate per side per round in 4 v 4? **Yes.**
4. Pips per unit (what is drawn above the head), with the cap of 2 per side? **Yes.** This depends on log section 4, item 3, which is still open.
5. May a frost-cursed unit use it (at 70 %)? **Yes.**

## 6. Work for the main line (none done here)

| Step | Work | Size (my estimate) |
|---|---|---|
| 1 | Per-unit `pips` and `ultReady`; keep counting rules; ultimate throw gives 0 | S |
| 2 | Armed flag, gold menu entry, cancel paths, disarm on Move, Defend, Attack, heavy | S |
| 3 | Remove the automatic cat branch in `executeThrow`; fire it only when armed | S |
| 4 | Used-count runes in the top plate; armed look; ready ring | M |
| 5 | Public fields and `ultimate` argument, six rejection reasons, tool tests including rejected calls | M |
| 6 | AI rule list in `triggerAITurn` / `aiAttackNow` | S |
| 7 | Property tests: pips 0 to 3, at most 2 per side, same seed same result, damage never negative | M |

## 7. What I could not verify

- Nothing was run: no game, no tests. All of this is a design read from the code and the documents.
- Whether the three pips are drawn at all in this checkout (no drawing code found), and how the menu looks with a fourth entry.
- Whether the old skill buttons (double, heavy, heal) stay (log question 6), which changes the heavy and double rows.
- How a human feels about spending a whole turn's throw on a possible miss. Question 1 is a feel decision that needs a playtest.
- The AI thresholds (60 px, 3 turns) are guesses.
