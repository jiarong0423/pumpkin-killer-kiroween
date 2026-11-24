# Kiro task 74: game flow and system plan (claude-sonnet-5.5)

Date: 2026-11-10. Written: this file only. No code, art, sound or other doc was edited. **Nothing was run**: no game, no test, no script. Every number marked *provisional* is a proposal for a playtest, not a measured value. I cannot hear audio or judge how anything looks.

**Read:** `docs/kiro_task_74.md`, `(not published)` (3, 4, 5), `(not published)` (whole, decided rows win), `docs/ultimate_rules.md`, `docs/ultimate_mapping.md`, `docs/class_stats_v2.md`, `docs/kiro_53_recommendations.md`, `docs/roster_design.md` (section 3), `js/class_stats.js`, `js/audio.js` (event map), `docs/audio_event_map.json`, `assets/audio/CREDITS.md`, and read-only greps/reads of `index.html` (HERO_PROFILES, ULT_BUILT, hit branch, status code, start screen, `snd`/`sfx` call sites) and `scripts/mcp_game_server.py`.
**Could not open:** the outputs of tasks 54, 55, 56, 57 (`../pumpkin-killer_kiro54 .. 57/docs`): the read request for that path failed before it ran, and `docs/` in this workspace holds only `kiro_51`, `kiro_52`, `kiro_53`, `kiro_58`. So the knight A-B-C rules below come from the log rows only, and wind layers (task 57, B5) are not planned here.

## 0. The brief's facts, checked against the code

| Brief says | Result |
|---|---|
| HERO_PROFILES has 4 classes | **Right** (`index.html` 486: skeleton, wizard, bat, knight). |
| `class_stats.js` has bride, hunchback, reaper, no necromancer | Right, but **reaper and necromancer are one class**: the log renames it (id stays `reaper`, player-facing 死靈法師). The `reaper` row in `class_stats.js` is stale (skull, execute x1.5, scythe slashes, HP 110, damage 22). So the brief's "reaper, then necromancer" is one job, not two. |
| `class_stats.js` new-class numbers | **Stale for all three.** `CLASSES` holds task-40 numbers (bride 75/27, hunchback 130/20/speed 0.8, reaper 110/22). The owner accepted v2 (`class_stats_v2.md`): bride 75/25, hunchback 110/21/speed 0.85/knockback 50, reaper 105/23 + burn. |
| `ULT_BUILT = ["bat","skeleton","wizard"]` | Right (`index.html` 537). Knight, bride, hunchback, reaper have none. |
| Statuses (bleed 2x2, poison 2x2, frost, slow, stun) | Right. Frost: `weak = 2`, -15% damage per throw, `FROST_SLOW = 1.6`. Stun: `STUN_SECONDS = 7`. `WALL_HIT_DMG = 8`. |
| Three sound files missing | Right: `move_step.ogg`, `item_pickup.ogg`, `ultimate_ready_chime.ogg` are not in `assets/audio/sfx/`. |
| Two scenes have no background | Right: only `assets/env/bg_graveyard.png` exists; the picker greys the other two ("製作中"). |

**Extra mismatches found (report only, nothing changed):**
1. `index.html` 1762: the wizard ultimate blast calls `applyBleed(vic, 2)`. The log gives bleed to hunchback, reaper and skeleton, not the wizard.
2. `index.html` 1706: bleed weapon list still has `proj_skull` and `proj_axe`. The skull is gone from the necromancer design (burn replaces it).
3. Stale comments: line 561 says no weapon applies poison (the wizard shell does, line 1709); line 1709 says "3 damage" while `POISON_DMG` is 2.
4. `scripts/mcp_game_server.py` `HERO_TEMPLATES` has the old 4 classes with other damage values (bat 16, wizard 26, skeleton 18, knight 20) and has no status at all. The browser does not use it, so this is not a bug today, but any claim that "MCP agents play the same rules" is false for statuses and the new classes.
5. `HERO_BLURB` is stale: wizard says damage 28 (code 24), bat says 5 shuriken at 8 each (the 5-shuriken scatter is now the ultimate; normal = 1 shuriken, 22).
6. `class_stats_v2.md` says all damages are unique; after the wizard cut to 24 it equals the skeleton's 24. Harmless.
7. `kiro_53` colours (ghost fire green, purple when armed) are superseded by log rows: normal circling fires use the violet sprite, armed uses the cold cyan one.

## 1. Make a class playable

### 1a. Steps, in order (same for every class; files are in this repo)

| # | Step | Files |
|---|---|---|
| 1 | **Art gate.** Eight frames present and clean (idle x2, charge x3, release, empty, hit). File presence is not quality: the overnight run left hunchback frames that were copies of the idle and drifting faces. Task 73 (Terra) owns this. | `python3 -B scripts/check_pose_set.py --strict`; look at the frames by eye |
| 2 | **Numbers.** Set the `CLASSES` row to the v2 values (table 1b), rename/clean the reaper row, update the test and the simulator table. | `js/class_stats.js`, `scripts/test_class_stats.js`, `scripts/sim_balance.js` |
| 3 | **Art keys.** Add the unit picture and pose frames to `imgList`, add `POSE_SETS` and `UNARMED_ART` entries (today only skeleton and bat have poses), add `ART_FACES_RIGHT` entry. Check the facing by eye first (gap B7 is still unchecked). | `index.html` ~440, ~2093-2100 |
| 4 | **Profile.** Add the `HERO_PROFILES` entry (name, hp, weapon, imgKey, wLen, wThick, dmg, tipColor). Remove the class from `COMING_HEROES`, add `HERO_BLURB`, `DOCK_PORTRAIT`, `DOCK_GLYPH` (emoji shows until a portrait file exists). | `index.html` ~336, ~486, ~1516 |
| 5 | **AI pick list.** `aiClass` is drawn from a hard-coded 4-name array in two places; add the key. | `index.html` ~346 and `startMatch` |
| 6 | **Weapon.** Projectile picture, `THROW_SOUND` entry, hand offset (like `WIZARD_MUZZLE`). The client has **no per-class launch speed and no knockback** (grep: no `speedScale`, no `knockback`): bride 0.9 and hunchback 0.85 need a speed factor in `executeThrow`, which the AI power estimate must also use. | `index.html` `executeThrow`, `aiAttackNow` |
| 7 | **Hit effect.** Add the class's status/effect in the hit branch (~1700-1730). | `index.html` |
| 8 | **Reset and public state.** Add any new status to the reset line (~1357). | `index.html` |
| 9 | **Ultimate** stays out of `ULT_BUILT` until built; the button then says "still being made" (owner: do not hide it). | `index.html` 537 |
| 10 | **Engine (optional, parallel).** Add the class to `HERO_TEMPLATES` only if MCP agents must play it; needs the owner's word because engine and client already differ. | `scripts/mcp_game_server.py`, `scripts/test_mcp_*.py` |
| 11 | **Verify.** `node scripts/test_class_stats.js`, `node scripts/test_sim_balance.js`, `node scripts/sim_balance.js --matches 200 --seed 7`, `python3 -B scripts/check_pose_set.py --strict`, then a page run. | see section 6 |

### 1b. Per-class differences and stat proposal (v2 numbers; the owner agreed: no across-the-board nerfs)

| | Bride 鬼娃新娘 | Hunchback 鐘樓怪人 | Reaper = necromancer 死靈法師 |
|---|---|---|---|
| HP / normal damage | 75 / 25 at wave centre, 45% (11.25) at the 105 px edge, hits the ONE unit nearest the wave centre | 110 / 21 | 105 / 23 |
| Speed factor | 0.9 (needs client code) | 0.85 (needs client code) | 1.0 |
| Weapon | sound-wave rings (`proj_soundwave`; no file found in `assets/`) | giant axe, 2 spins/s (`fx_axe_thrown.png` exists; `proj_axe` does not) | purple flame (`fx_flame_comet.png` exists) |
| Status on hit | poison 2x2 | bleed 2x2, knockback 50 px | burn 2 x 3 (new), no bleed |
| New code | wave hit test (half-width 105, falloff); poison call | knockback; speed factor; two-handed throw frames | burn status; flame projectile rotated to flight; `ORBIT_FIRE_CLASSES` already lists `reaper` |
| Art state in repo | 8 pose files, idle, no portrait | 8 pose files (quality doubtful), idle, no portrait | 5 `necro_*` + 4 legacy `reaper_*` files; **5 of 8 frames** (log), 3 short |
| Stale pieces to remove | `proj_bouquet` splash row in `PROVISIONAL` | `proj_bell` | skull, execute, scythe slashes, `proj_skull` bleed branch |

Reasoning against the existing four (index.html now: skeleton 100/24, wizard 85/24, bat 90/22, knight 120/30 total, typical hit about 20):
- HP ladder 75 / 85 / 90 / 100 / 105 / 110 / 120: all different. The two glass classes (bride 75, wizard 85) are the ones with the best reach (wave width, cannon arc); the three heavy ones (hunchback 110, knight 120, necro 105) pay with slower speed or low direct damage.
- Hits to kill from direct damage only (my arithmetic, ceil(HP / typical hit); knight 20, bride 20.75; not run):

| attacker \ target HP | sk 100 | wiz 85 | bat 90 | kn 120 | bri 75 | hun 110 | nec 105 |
|---|---|---|---|---|---|---|---|
| skeleton / wizard (24) | 5 | 4 | 4 | 5 | 4 | 5 | 5 |
| bat (22) | 5 | 4 | 5 | 6 | 4 | 5 | 5 |
| knight (20) | 5 | 5 | 5 | 6 | 4 | 6 | 6 |
| bride (20.75) | 5 | 5 | 5 | 6 | 4 | 6 | 6 |
| hunchback (21) | 5 | 5 | 5 | 6 | 4 | 6 | 5 |
| necromancer (23) | 5 | 4 | 4 | 6 | 4 | 5 | 5 |

  Every cell is 4 to 6, inside the band in `class_stats.js` (typical 4-6, hard 3-8). Status ticks (up to 4-6 HP) shave one hit off some cells.
- `kiro_53` hand model with ticks (A = 150): necromancer +2.3% of the 7-class mean power; hunchback +13%, bat -14%, knight -13% (outside the +-12% v2 band). That is a hand estimate; the simulator has no status ticks yet. **Do not change any number from it.** Add ticks to `sim_balance.js`, run 200 matches, and adjust one class only if a pairing leaves 40-60% or a class average leaves 45-55% (levers already named in `class_stats_v2.md`: bride half-width 105 to 95, necro burn 3 to 2 turns, hunchback bleed 2 to 1 turn).

## 2. Ultimate rules (only gaps; decided rows are quoted from the log and not changed)

Shared, decided: 3 lit pips, own turn, armed first, max 2 per match, one per side per round, each unit hit takes 1.5 x the class's normal attack (bride swarm 1.3 x), the trigger hit is a normal hit and not part of the multiplier, the ultimate throw gives 0 pips, spent at release even on a miss (`ultimate_rules.md`).

| Class | Decided (log) | Gap I fill (all *provisional*) |
|---|---|---|
| **Knight 南瓜重裝盾衛** | Defend-mode ultimate. Three lit pips: place hidden shield points A, B, C. Each answers one of the enemy's next three attacks, in order. Shield and points are invisible to the opponent (shown 1.4 s when one blocks). Uses the defend turn, not a throw. Replaces "Shield Chain". | **Spent** at Lock (no release exists); pips to 0. **Placement:** three clicks in the sky band, numbered markers shown to the owner only; Lock needs all three. **Checking:** each enemy *throw* (a volley is one throw) is tested against the current point; the point is consumed by that throw, blocked or not; a point blocks at most one projectile (matches "each path blocks once"). **Expiry:** after 3 enemy throws or 4 rounds, whichever is first. **Not blockable:** follow-up strikes that are not the main throw (bride swarm, hunchback return). **Public state:** only `ult_kind` and the pip drop; the points appear in history after use ("private plan, public history"). **Cost:** the turn (no damage). Today's plain Defend (drag shield, `actions 4`, 2 charges) stays. Open for the owner: whether the plain Defend stays once A-B-C exists. |
| **Bride 鬼娃新娘** | Normal = sound wave, poisons. Ultimate: if the wave hits the FIRST unit precisely, a bat swarm is summoned. Swarm hits every ENEMY unit only (OWNER 2026-11-10: allies take no damage; the old 'enemies and allies' reading is dropped). Damage per unit = normal attack x 1.3 (bride only). | **Precise** = impact inside the 40 px full-damage zone (the wave's `fullWithin`). **First unit** = the living enemy nearest the bride by public x. **Swarm targets:** every living ENEMY unit, trigger unit included; allies are never touched (OWNER 2026-11-10). **Damage** 25 x 1.3 = **32.5** per unit. Allies take no damage at all; it may kill an enemy. **Poison:** none from the swarm (keeps the status count down). **Shield/fence:** not blockable (it is an area, not a projectile). **1 v 1:** hits the enemy once (trigger 25 + swarm 32.5 = 57.5 of 75-120 HP). **No trigger hit = no swarm.** The caster-excluded choice is mine: `kiro_44` addendum 10c's answer was not available to me. Arming label: "hits all enemies". |
| **Hunchback 鐘樓怪人** | Boomerang axe is the ultimate. The axe pierces the LAST unit and flies back to the FIRST with a guaranteed hit. It returns ONLY if it hits the last unit (spent either way). In 1 v 1 it must hit the only enemy. | **Trigger** = first hit, normal 21 + bleed + knockback 50 px. **Return** = 1.5 x 21 = **31.5**, no knockback (avoids ping-pong), refreshes bleed. **Flight back:** straight line at the unit's body height, constant speed (I suggest 1400 px/s), not blockable by the sky shield, not affected by wind. **1 v 1 total** 52.5 of 110 HP. **4 v 4:** units hit in order of x along the flight; "last" = the last hit; "first" = the first hit. Pierce does not consume sky-shield charges. |
| **Reaper = necromancer 死靈法師** | Confirmed ("all yes" to `kiro_53`): one volley of three flames from one aim, not seeking, replaces the scythe slashes and the 30% execute, circling fires ARE the pips (no pip dots), burn 2 x 3, no bleed. Numbers: `kiro_53` section 5 (fan +-1.2 power = about +-36 px, 11.5 per flame, 34.5 for three, burn once, no crit on flames). | Nothing new. Implementation notes only: (a) delete the `proj_skull` bleed branch and the execute row; (b) colours follow the log (violet normal, cyan armed), not `kiro_53`; (c) 4 v 4 stays single-target (a +-36 px fan cannot reach a unit 160 px away). |

Numbers I did not invent: no radius, cooldown or damage outside the owner's 1.3 / 1.5 rules. New *provisional* numbers: return speed 1400 px/s, knight expiry 4 rounds, "precise" = 40 px.

## 3. Status-effect system (one table, matches the log and `index.html`)

Common rules (code): ticks run at round start in the order poison, bleed (burn next); a tick never kills (leaves 1 HP); applying again refreshes with `max`, never stacks; nothing in the game clears a status except expiry or `resetGame` (potion, heal rain and crate heal do not clear: same ruling as `kiro_52`/`kiro_53`). A blocked projectile never reaches the hit branch, so the sky shield prevents the status. Extra projectiles of an ultimate go through the same hit branch.

| Status | Source | Duration | Damage | Visual | Sound | Stacking | Clears | Ultimate and shield |
|---|---|---|---|---|---|---|---|---|
| 暈眩 stun | Head hit (top quarter, within 35 px of centre); also skeleton triple javelin when all 3 hit | Unit's next turn lasts 7 s instead of 12 | none (head crit x1.25 is separate) | Stars circle the head; text "暈眩！只剩 7 秒" | **none** | Not applied if stunned last turn (`stunLast`) or the hit kills | After that one turn | Does not block arming (design call, *provisional*). AI aim error x1.6 while stunned. |
| 流血 bleed | Spear, axe (skull to be removed); (the wizard blast no longer applies bleed: removed by the OWNER 2026-11-10) | 2 round starts | 2 each | Occasional small drips, 2-4.5 s apart, staggered; text "流血" | **none** | Refresh | Expiry | Every javelin/axe hit refreshes; no extra damage. |
| 中毒 poison | Wizard cannon hit; bride wave (planned) | 2 round starts | 2 each (`POISON_DMG`) | Green pulse, bubbles, text | `poison_tick` (synth only) | Refresh | Expiry | Wizard ultimate shell hit poisons once. |
| 霜咒 frost (weak) | Spear hit | The unit's next 2 throws | -15% damage per throw; swing and hit reaction 1.6x slower | Blue blink | **none** | `weak = 2`, not additive | One throw uses one count, even a 3-javelin ultimate | Damage is cut before the ultimate branch, so the ultimate is also -15% (`ultimate_rules.md` 2f). |
| 減速 slow | Cat-bat shuriken hit | The unit cannot Move for 1 round; it can still attack | none | Feet chain (**picture missing, nothing shows**), text | **none** | Not re-applied while slowed | Next round after its turn | Bat ultimate sets it once. A slowed knight can still Defend. |
| 燃燒 burn (planned) | Necromancer flame | 3 round starts | 2 each | Ghost-fire tongues up the body, text "燃燒" | **none yet** | Refresh | Expiry | Ultimate applies it once on the first flame that hits. |

- Worst case at one round start: poison 2 + bleed 2 + burn 2 = 6 (`kiro_53`).
- Wall (not a status): `WALL_HIT_DMG = 8` per hit, 13 hits to break; provisional, unplayed.
- To do in code, when the main line builds the table: one `STATUS` definition table with `id, turns, dmg, tickOrder, visual, sound`, so the HUD, reset, MCP `statuses` field and the sim read the same data (today the logic is spread over `applyPoison`, `applyBleed`, `tickPoison`, `tickBleed`, and ad hoc fields `weak`, `slow`, `stun*`).

## 4. 4 v 4 / multi-unit (open owner decision B1)

**Facts.** The browser has two singleton units (`player`, `ai`) and per-side `energy`, `ultUsed`, `shields`, `supply`. The dock shows one hero. The top banners show **two diamonds = ultimates left**, but the mockup uses the diamonds for **units alive**: they cannot mean both. The engine (`mcp_game_server.py`) already has N units with `controller` and the MCP server already runs "human phase, then agent phase".

| | A. Sequential unit turns (`roster_design.md` section 3) | B. Plan, then Lock (the mockup flow) | C. Stay 1 v 1 in the browser, 4 v 4 only through the engine/MCP |
|---|---|---|---|
| Turn flow | In each side phase every living unit acts once, one after another; the human may pick the order; Move then Attack, or Defend (knight). 8 s per unit, 7-round cap. | Each unit picks Throw, Move or Defend, presses Lock; then humans resolve, then agents. | Browser unchanged. A 4 v 4 match runs as agents/scripts against the MCP server. |
| Time | Typical round 47.5 s, worst 61.5 s (estimate in that doc, unmeasured). | Shorter if the timer is per side (not specified). | n/a |
| HUD | Selected-unit dock plus click-to-select; diamonds = units alive (ultimates move to the pips above each head); markers 1-4 and A-D; per-unit HP bars. | Same HUD plus a per-unit action chip and Lock button. | None. |
| Fits "feel first" | Yes: hold, release, see, correct, for each unit. | **No**: power and angle must be set before anything resolves; it is the confirm step the product rules rule out. | Yes (unchanged). |
| AI impact | `aiAttackNow` and `aiCal` become per unit (or per side with shared calibration); four decisions per phase; each sees the earlier landings of the round. | Four decisions are made blind to each other's landings, so learning inside a round is weaker. | None in the browser; agents already work. |
| Code cost | **L**: replace `player`/`ai` singletons by unit arrays, per-unit energy/ultimates, spacing 160 px, death handling. | **L+**, plus a new UI state machine. | **S** (docs and a demo script). |
| Risk | Large refactor of one HTML file with no browser test. | Breaks the core feel. | The showcase ("humans vs AI, 4 v 4") is not playable in the page. |

**Recommendation: A, rolled out as 2 v 2 first, then 4 v 4 by changing a constant.** Build the N-unit data model once; ship 2 v 2 for the contest video; take 4 v 4 after the 200-match balance run. Fall back to C if the refactor does not fit the time left.

**Exact owner decision needed (one word each):**
1. Flow: **A**, B or C.
2. If A: does a "player" in the HUD mean each *unit* (my recommendation) or each *controller* (log section 4, question 3)?
3. If A: turn timer per unit 8 s (mockup) or 12 s (prototype)?
4. GAP_QUEUE B1 adds "change the parachute airdrop to a ghost carrying the crate". My reading: with several units on a side, a ghost that carries the crate to a chosen unit is easier to read than one parachute in the middle; **keep the parachute** is the cheaper answer. Owner chooses.

## 5. Sound event map

All sounds are unverified by ear. `snd(name)` plays the event named in `js/audio.js` / `docs/audio_event_map.json`; a missing file falls back to the synthesised recipe, so the three missing files are silent bugs only in the sense that the file never plays.

| Game event | Call in `index.html` | Event / file | State |
|---|---|---|---|
| Button click (skill buttons only) | document click | `ui_click` / `ui_click.ogg` | ok; the listener only covers `.skill-btn` and `.hero-tab` (no other `ui_click` call found by grep) |
| Round start | `resolveRound` | `round_start` / `bell_round.ogg` + synth | ok |
| Hold to charge, dice roll | `sfx.charge` | `charge` (synth hum) | ok |
| Throw (spear, shuriken, dart, cannon, shield) | `THROW_SOUND` | `throw_*` / files | ok; **any other weapon falls back to `throw_spear`** |
| Unit hit | `sfx.hit` | `impact_unit` (`punch_hit`) or `impact_unit_heavy` when damage >= 24 | ok |
| Fence hit / break, ground, airdrop landing | hit branch, airdrop | `impact_fence`, `impact_fence_break`, `impact_ground` | ok |
| Sky shield block / place | `sfx.block`, `lockShield` | `shield_block`, `shield_place` | ok |
| Dice result, step | `startDiceRoll`, dice apply | `dice_rattle`, `dice_result`, `move_step` | `move_step.ogg` **missing** (synth plays) |
| Crate pickup | supply code | `item_pickup` | `item_pickup.ogg` **missing** (synth plays) |
| Potion heal | `sfx.heal` | `heal` / `heal_harp.ogg` | ok; crate heal has no heal sound |
| Poison tick | `tickPoison` | `poison_tick` (synth) | ok |
| KO / low HP | hit branch, per-frame check | `ko`, `low_hp_heartbeat` (player only) | ok |
| Music mood, ghost on KO | `playMusic`, `ambientSfx` | `battle_calm`, `victory`, `defeat` | ok |
| **No call found by grep** | | `ultimate_ready`, `round_end`, `flight_*` (4), `impact_ground_heavy`, `ui_hover` | defined, never fired; `ultimate_ready_chime.ogg` also missing |

**Gaps and how to fill them** (rule: free only; CC0 files need a licence line in `CREDITS.md` with the page seen; Kiro verifies, main line downloads; no web search was done here):

| Gap (event) | Fill | Why |
|---|---|---|
| 霜咒 apply, 暈眩 apply, 減速 apply (chain clink), 流血 apply/tick, 燃燒 apply/tick | **Synthesised**, layered on existing credited files where useful (`chime_single` for frost, `metal_bing` pitched down for stun and chain, `thwack_wood` for a dull knock) | Short, tonal or percussive; no new licence work. Burn crackle is the one place a real fire recording would sound better: optional CC0 file later. |
| `ultimate_ready` (wire the call, flat arpeggio exists) | **Synthesised** (`arpeggio_up`); drop the file reference or leave the synth fallback | The missing Kenney sci-fi file is not worth a new licence row; the owner has not heard either. |
| `move_step` | Point `file` at the existing `step_leaf.ogg` (already CC0, credited) | One-line map change, test keeps the two maps in sync (`node scripts/test_audio.js`). |
| `item_pickup` | Pick a file from the **already credited** Kenney Interface Sounds pack, or keep the synth | Same pack licence as `ui_click` in `CREDITS.md`. |
| Ultimate fire, one event per class (shuriken rain, triple javelin, pumpkin blast, soulfire volley, boomerang, bat swarm, A-B-C shield) | **Reuse + synth layering**: `swish_throw` x5, `whoosh_spear` x3 staggered, `throw_cannon_boom` + `rock_break`, `spell_magic` + synth whoosh, `whoosh_spear` low pitch, `ambient_sfx` bat kind, `shield_place_spell` x3 | No new files; each is a timing recipe. |
| New attacks: `throw_soundwave`, `throw_axe`, `throw_flame` and their impacts | **Synthesised** for the soundwave ring and the flame hiss; **reuse** `whoosh_spear` (low) + `punch_heavy` for the axe | Matches the old plan in `ultimate_mapping.md` (stand-ins `spell_magic`, `ghost_real`). |
| `round_end`, `flight_*`, `ui_hover` | Leave unfired (owner wants a clean sound layer); decide at the volume pass | D3 (volume balance) needs the owner's ears first. |

CC0 files are worth a new download only for organic textures synthesis does badly (fire crackle, wet impact, a real chain). Everything else stays synthesised.

## 6. Schedule

Size: S under 1 h, M a few hours, L a day or more of main-line work (my estimate). Parallel steps run in separate worktrees and merge one at a time (same `index.html` regions).

| # | Step | Size | Needs | Owner? | Verify (main line can run) |
|---|---|---|---|---|---|
| 1 | Owner decisions: B1 flow, unit/controller, timer, airdrop (section 4); bride swarm caster; knight plain Defend stays? | S | none | **Yes** | Answers recorded as log rows |
| 2 | Sync `class_stats.js` to v2, retire `reaper` skull/execute, add burn, rename 死靈法師 | M | none | no | `node scripts/test_class_stats.js && node scripts/test_sim_balance.js` |
| 3 | Add status ticks to the simulator; run the 200-match balance pass (B3) | M | 2 | no | `node scripts/sim_balance.js --matches 200 --seed 7` exits 0 |
| 4 | `STATUS` table in `index.html`, fix mismatches 1-3, add burn, reset | M | 2 | (decided: wizard blast bleed REMOVED, already done in index.html) | Page run: apply each status, read HP after `resolveRound`, confirm HP never below 1 from ticks |
| 5 | Sound recipes for statuses, ultimates, new attacks; wire `ultimate_ready`; `move_step` file fix | M | none | no | `node scripts/test_audio.js && node scripts/test_ambient_sfx.js`; grep `index.html` for each new `snd("...")` |
| 6 | Optional CC0 downloads and `CREDITS.md` rows | S | 5 | no (rule: free only) | `ls assets/audio/sfx`; each new file has a `CREDITS.md` row with page and licence |
| 7 | Necromancer playable (art gate: 3 frames short) | M | 2, 4, art (task 73) | no | `check_pose_set.py --strict` for its frames; page run: throw, burn ticks, stars |
| 8 | Bride playable (wave hit test, speed factor, poison) | M | 2, art | no | `test_class_stats.js`; page run: wave hits only the nearest unit |
| 9 | Hunchback playable (knockback, speed factor, axe) | M | 2, art | no | Page run: a hit moves the target 50 px, stops at the 160 px / zone limits |
| 10 | Ultimates: necromancer volley, hunchback boomerang, bride swarm, knight A-B-C (in that order of effort) | L | 4, 7-9 | Bride/knight open points (step 1) | `node scripts/test_ultimate.js`; per-class page run; ULT_BUILT updated |
| 11 | N-unit refactor, 2 v 2 first (option A) | L | 1, 4 | **Yes** (step 1) | Page run with 2 units a side; diamonds = units alive; overlap check as before |
| 12 | Re-measure AI hit rate (B4, target about 25-30%) and the 12-match runs | M | 11 or 7-9 | no | The 300-throw method used for `(not published)` |
| 13 | MCP/engine parity (classes, statuses, `ult_*` fields, `HERO_TEMPLATES`) | L | 2, 4, 10 | Scope: yes | `python3 -B scripts/test_mcp_stdio.py && python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_constants_sync.py` |

**Parallel:** 2, 5 and 6 can start now; 3 and 4 follow 2; 7, 8, 9 can run side by side after 2, 4 and their art.
**Not mine / waiting on art:** the two scene backgrounds, bride and hunchback frame redo, portraits, feet chain, soundwave sprite, `proj_axe` (task 73).
**Not planned here:** layered wind (B5, task 57 unreadable), terrain, opening screen and naming (B6), HUD fixes (C1).
