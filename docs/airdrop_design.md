# Ghost airdrop (supply drop) system: rules, items, balance (Kiro task 31)

Status: **design only.** I read `index.html`, `docs/game_mode.md`, `(not published)`, `docs/sound_mapping.md`, `docs/audio_event_map.json`, `shared/constants.json`, `scripts/mcp_game_server.py` and `scripts/mcp_stdio_server.py`. I ran nothing and heard nothing. `docs/experience_design.md` does not exist. Anything about how a thing looks, sounds or feels is **unverified**. All numbers below are first guesses for a playtest unless they are arithmetic on the code constants, and those I did by hand (not run).

Owner decisions this design keeps: ghosts carry the crates; the crate comes down on a parachute; there is one supply slot; the slot holds ONE item and a new pickup REPLACES the old one; no ultimate item.

## 0. Facts from the prototype that drive every number

| Fact | Value | Where |
|---|---|---|
| Canvas, ground | 1920 x 1080, `GROUND_Y` 860, a landed crate rests at y 840 | `index.html` |
| Fence | x 895..1025 (`FENCE_X` 960, `FENCE_W` 130), 250 px tall | `shared/constants.json` |
| Move | one d6 per turn, 36 px per pip, so 36..216 px, direction chosen by the unit, does not use the throw | `DICE_STEP_PX`, `startDiceRoll` |
| Move limits (browser) | player 160..850, AI 1070..1760 | `stepDice` |
| Move limits (MCP server) | red 100..835, white 1085..1820 (fence edge -/+ 60) | `TEAM_X_LIMITS` in `mcp_stdio_server.py` |
| Pickup radius | 70 px; unit sprite is 220 px wide, crate sprite 96 px | `updateAirdrop` |
| Gap between the two sides | closest possible distance between a player unit and an AI unit is 1070 - 850 = 220 px | limits above |
| Ghost | y about 170 (+/- 18), 330 px/s, always left to right | `updateAirdrop` |
| Crate fall | starts at about y 230, 150 px/s, so 610 px takes 4.07 s | `updateAirdrop` |
| Turn | 12 s timer, humans first, then the AI (which waits 1 s) | `TURN_SECONDS`, `triggerAITurn` |
| Damage per hit | 20..28 in the browser (`HERO_PROFILES`), 16..26 in the MCP engine | both files |
| Existing heal skill | +35 HP, 2 uses | `selectSkill` |

### Defects I found by reading the prototype (these shape the rules below)

| # | What happens | Why (code) | Effect |
|---|---|---|---|
| D1 | A crate can land on the fence or on the enemy side | `base = player.targetX + 140` plus an offset up to 159, clamped only to 300..1620; the player can stand at 850, so the crate x can reach 1149 (fence is 895..1025). Mirror case for the AI side | Crate hidden behind the fence, or nearer to the other side |
| D2 | The far end of the offset range is out of reach | Distance from the unit is 140..299 px; the best single move reaches 6 x 36 + 70 = 286 px | Offsets above 146 (about 8% of drops) cannot be taken in one turn even with a 6 |
| D3 | Chance to reach in one turn is low | With distance D uniform in 140..299, the average one-turn chance is about 39% (table in section 1a) | Most crates sit for several rounds |
| D4 | The first drop goes to the AI side | `dropSide` starts at 1, the first call flips it to -1, and -1 means the AI side | The human's first airdrop is the second one |
| D5 | The two sides get different timing | Ghost always flies left to right: a player-side release at x 500 happens at 2.0 s, an AI-side release at x 1500 at 5.0 s; landing about 4 s later, so AI-side crates land after most human turns | Not fair by construction in time |
| D6 | One unreachable crate stops all drops forever | `scheduleAirdrop` returns while `drops.length > 0`, and a crate never expires | The feature silently turns off |
| D7 | The AI ignores the item and the slot rule | `SUPPLY_ITEMS.heal.use(ai)` runs for any crate, even a heavy-shot crate, even at full HP; the AI has no slot, so "replace" does not apply to it. The AI also only moves in 25% of rounds, so it rarely picks a crate up | Not the same rules as the human |
| D8 | Movement limits differ between browser and MCP server | 850 / 1070 vs 835 / 1085 | A crate placement valid in one may be wrong in the other. My rules use the stricter pair (835 / 1085) |
| D9 | Pickup text is a sentence | "拿到物資：補血 +30" | Owner wants short messages |

## 1. The rules

### a. Frequency and timing

**Recommendation: replace "every 2nd round" with a cooldown rule that depends on what happened to the last crate.**

1. First drop at round 3 or later. Reason: rounds 1 and 2 are where players read the wind (product principle: show both sides improving round by round).
2. At most one ghost or crate exists at a time (already true). A new drop may start at a round start when the previous crate was taken or expired **at least one full round earlier**. Reason: prevents back-to-back drops and keeps the screen clean. In practice: drop in round N, taken in N+1, next drop in N+3, about one drop per 3 rounds. Unverified: I do not know how many rounds a match lasts; if matches are short, lower the first round to 2.
3. **Pickup opens at the start of the next round** (round N+1), even though the crate lands in round N. Reason: ghost flight time depends on x and on the player's own pace, so tying pickup to landing time makes one side wait longer. A round-based gate is the same for both sides. The crate is picked up in the Move step of a unit's turn.
4. **The crate lives 3 turns**: available in rounds N+1, N+2, N+3, removed at the start of round N+4. Reason: fixes D6 and gives a hard guarantee (section 1b).
5. Match cap of 6 drops. Reason: stops a long, stalled match from turning into a supply fight. Unverified.
6. **Anti-snowball, three small rules:**
   - Side of the drop: the first drop goes to the human side (a new player sees the feature working for them first; fixes D4), then sides alternate. If one team's HP is lower by 30 or more percentage points of total max HP, the next drop goes to the trailing team, but never the same team three times in a row. Reason: the loser gets a small chance back, the leader never gets a second gift.
   - `candy_heal` has weight 0 unless a favoured unit is missing at least 20 HP (public information). Reason: no dead heal crate for a unit at full HP.
   - Every item is smaller than one hit in value (table in 1c). Reason: a crate helps but cannot decide a match.
7. Ghost entrance is delayed to 3.0 s after the round starts. Reason: `docs/sound_mapping.md` rule 8 keeps creature sounds off for 3 s after the `round_start` bell, and the ghost's laugh should not fight it. The delay costs nothing because of rule 3.

### b. Landing zones

Drawn zones (x only; the crate always lands on the ground, y 840):

| Zone | x range | Reason |
|---|---|---|
| Player side | 200 .. 835 | 835 is the MCP limit for red, which is also the fence edge (895) minus 60. 200 keeps the 96 px crate and its parachute on screen with margin |
| AI side | 1085 .. 1720 | Mirror of the above (1920 - 835 = 1085, 1920 - 200 = 1720) |
| Forbidden | 835 .. 1085 | Fence (895..1025) plus 60 px margin each side. **Never on the fence.** |
| Off screen | x < 100 or x > 1820 | **Never off screen** (the zones above already guarantee this) |

**Fair-side rule:** the side is chosen as in 1a(6). The crate is placed relative to that team's **reference unit**, which is its living unit nearest the fence. (In 1 vs 1 that is just the unit. The 4 vs 4 flow is still open, so this is a placeholder.)

**Placement algorithm (deterministic with the injected seeded RNG, draw order fixed: side tie-break, distance, direction fallback, item):**
1. Draw D = 110 + floor(rng x 69), so D is 110..178 px.
2. Put the crate D px in front of the reference unit (toward the fence). If that x is outside the zone, put it D px behind instead. If neither fits (cannot happen when the unit is inside its move limits and the zone is 635 px wide), clamp to the zone edge.
3. **Shield clearance** (the parachute passes through the sky shield's height, about y 430, and the shield bar is 210 px wide): if the x is within 200 px of an active sky shield's x, draw D again, up to 3 times. If still blocked, accept it: the crate never collides with the shield (visual overlap only). Reason: "never inside a shield" is met for the ground crate by definition, and the clearance keeps the falling canopy out from behind the bar when possible.
4. The crate never interacts with projectiles or the fence once placed.

**Reachable-in-one-turn guarantee for the favoured side.** One move reaches a crate at distance D if the die shows at least k = ceil((D - 70) / 36) (and the unit picks the right direction). Chance this turn = (7 - k) / 6.

| Distance D (px) | Pips needed k | Chance in one turn |
|---|---|---|
| up to 106 | 1 | 100% |
| 107 .. 142 | 2 | 83% |
| 143 .. 178 | 3 | 67% |
| 179 .. 214 | 4 | 50% |
| 215 .. 250 | 5 | 33% |
| 251 .. 286 | 6 | 17% |
| above 286 | none | 0% (the prototype's D2) |

- A literal 100% in one turn exists only for D up to 106, a crate the unit almost stands on. I recommend **not** doing that: the pickup would need no decision. Instead I recommend D = 110..178, which gives **67% to 83% on the first turn** and **100% by the third turn**, because a forward move is at least 36 px per turn: after T turns the unit certainly reaches D up to 70 + 36 x T, and for T = 3 that is 178. The crate lives exactly 3 turns, so the guarantee matches the lifetime. The move limits (835 / 1085, 160 / 100) never block this because the zones are inside them.
- It is **always possible in one turn** (D is never above 286).
- **The other side cannot reach it.** A crate in the player zone is at x 835 or less; the AI cannot stand left of 1085, so its best reach is 1085 - 70 = 1015, and the crate is more than 180 px away. Mirror for the AI zone. With the radius at 70 and the minimum gap at 220, two units are never both in range.
- Real cost of the pickup (this is the decision): a unit that moves loses the aim it has learned from its landing record. Unverified, but it is the reason the crate is worth thinking about instead of free.

### c. Item table

Six items. Each item is smaller than one hit (16..28 damage). Chinese labels are for the dock and are 2 characters. Emoji are fallbacks until the Colab icons exist (`docs/airdrop_asset_requests.md`).

| id (label) | Icon idea (fallback) | Effect | Who may take / use | Duration | Counter-play | Engine support |
|---|---|---|---|---|---|---|
| `candy_heal` (糖果) | Glass jar of green candy (🍬; prototype used 🧪) | +25 HP, never above max HP. Use is **rejected at full HP** and the item stays in the slot | Any unit may carry it. Only the holder uses it, on its own turn, before or after its throw. Free action, one item use per turn | Instant | Opponent sees the slot and can kill the target first; 25 is about one hit | **Works now** in the browser (`SUPPLY_ITEMS.heal`, +30, change to +25 and add the full-HP rejection). MCP engine needs `use_item` |
| `heavy_shell` (重彈) | Black bomb with a lit fuse (💣) | +1 charge of the existing heavy shot, at most 3 held | Any unit; the next throw uses the heavy shot as before | Until used | Fence and sky shield still stop it; it still has to hit | **Works now** in the browser (`skillCharges.heavy++`). The MCP engine has no heavy shot, so agents need that first (unverified how large a change) |
| `second_die` (雙骰) | Two ivory dice (🎲) | The next Move rolls two dice and keeps the higher. Direction is still chosen. Same move limits | Any unit | Next Move, or 3 rounds, whichever comes first | Pure positioning, no damage. Fence and edges still limit it | **New:** move rule needs a "roll two" status |
| `shield_patch` (修盾) | Cyan hammer on a coffin-lid slab (🔧) | +1 block charge on your sky shield, maximum 2. Rejected if the shield is not active or already full | Only a unit that controls a sky shield (the Knight). The drop pool includes it only when the favoured team has a living Knight | Instant | It does not change the shield position, width, duration or number of paths. A throw that misses the bar still lands. **Does not make anything ignore the shield** | **New:** engine must add to `charges` with a cap |
| `calm_wind` (靜風) | Pale violet wisp with a crossed-out arrow (🍃) | Wind counts as 0 for the holder's next throw. The effective wind is written to the throw record (`wind_at_throw` = 0) so the landing history stays true | Any unit | Next throw, or 3 rounds | It removes only the wind term, not the damage or the fence. Visible as a status next to the unit. Does not touch anyone else's throw | **New:** per-throw wind override in the engine and in the browser physics (`p.vx += wind * ...`) |
| `bone_ward` (骨甲) | White bone breastplate (🦴) | The next hit this unit takes deals half damage, rounded up. Damage never goes below 0 | Any unit | Until hit, or 2 rounds | Visible status; the attacker can pick the other unit or wait. Does not stop a shot, so it is not a shield | **New:** status plus a damage hook |

Pool weights for the seeded draw: `candy_heal` 3 (only if a favoured unit is missing at least 20 HP), `heavy_shell` 2, `second_die` 2, `bone_ward` 2, `shield_patch` 1 (only with a living favoured Knight), `calm_wind` 1. Never the same item twice in a row. Unverified: all weights.

Balance checks I did by reading:
- Heal cap: `Math.min(maxHp, ...)` already caps; the rejection at full HP is new.
- No free kill: no item deals damage by itself. `heavy_shell` is a normal throw that can miss.
- No item ignores the shield: nothing here changes projectile collision with the sky shield.
- No ultimate item: none of the six touches the ultimate bar, hit counting or any ultimate effect.
- Which already work: `candy_heal` and `heavy_shell` in the browser only. The other four, and all six for agents, need engine support.

### d. Pickup rules

| Question | Recommendation | One-line reason |
|---|---|---|
| Stand-on radius | **70 px**, measured on the unit's **move path** (from the old x to the new x, both ends included), not on the animated x | The prototype already checks per frame on the sliding x, which is nearly the same; defining it on the target x makes it testable and stops a 6 from jumping over a crate and missing it |
| When is it checked | At the end of a unit's own Move, and once when the crate lands (for a unit already in range) | A unit acts to get it; nothing is stolen between turns |
| Both units in range | Cannot happen with the current limits (220 px gap vs 140 px of two radii). If a 4 vs 4 layout changes that: nearest unit wins; tie goes to the unit currently acting | One rule, no randomness |
| Who may take | Any living unit that is in range, including a unit of the other team | No special permission to remember; geometry already keeps the other team away |
| Slot full | **Replace** (owner). The old item is gone, no refund. Public record: `replaced_item` | Owner decision |
| Replace is a surprise | The item icon floats over the landed crate, so the holder sees what they will get before moving. No confirm dialog | "Feel first: no preview or confirm step", and it still avoids a blind swap |
| Can a thrown projectile destroy a crate | **No, in version 1.** Projectiles pass through | One throw per turn means a shot at a crate is a lost attack, and an ordinary miss would break crates by accident, which is messy. Worms lets explosions remove crates and Fortnite Creative offers a destructible balloon, so this can be added after a playtest. Unverified |
| Expiry | Removed at the start of round N+4 with a short fade | Avoids D6 |

### e. The agents (AI and sub-agent opponents)

**What must be public.** Humans see the ghost, crate, ring, landed icon and the opponent's pickups, so all of that goes into the public state. Humans also have to see the opponent's slot (small icon next to the HP bar); otherwise the AI would know something the player cannot, or the reverse. Recommendation: **every unit's slot and statuses are public to everyone.** Reason: counter-play (bone ward, calm wind) needs it, and it keeps "the AI cannot cheat" true in both directions.

**Hidden until it is visible:** the item inside a crate is hidden while the ghost flies and the crate falls, and appears at landing (as the icon does on screen). The RNG seed, the schedule of future drops and the dice stream stay hidden.

**Field names for `scripts/mcp_stdio_server.py` (names only, no code):**

| Where | Field |
|---|---|
| `get_public_state` | `airdrop` with: `state` (`none`, `ghost_flying`, `falling`, `landed`), `favoured_team`, `x`, `item` (null until `landed`), `pickup_open`, `drop_round`, `expires_after_round`, `pickup_radius` |
| `get_public_state`, per unit | `slot` (item id or null), `statuses` (for example `bone_ward` with rounds left, `calm_wind`, `second_die`), `item_used_this_turn` |
| `submit_action` result for `move` | `picked_up` (item id or null), `replaced_item` (item id or null) |
| New tool, as in the tech rule | `use_item` with argument `unit`; result: `item`, `effect`; it is rejected for an empty slot, a dead unit, another controller's unit, a second use in the same turn, or an item with no valid use (heal at full HP) |
| `get_history` | an `airdrop_events` list with `round`, `type` (`landed`, `picked_up`, `replaced`, `expired`), `unit`, `item`, `x` |
| `shared/constants.json` | `PICKUP_RADIUS`, `AIRDROP_FIRST_ROUND`, `AIRDROP_LIFETIME_TURNS`, `AIRDROP_MAX_PER_MATCH`, `AIRDROP_ZONE_PLAYER`, `AIRDROP_ZONE_AI`, `AIRDROP_DISTANCE_MIN`, `AIRDROP_DISTANCE_MAX` |

The `use_item` tool is named in `.kiro` tech rules but is not in the server's six tools yet (`get_public_state`, `get_history`, `submit_action`, `end_turn`, `set_notes`, `get_notes`). An alternative is a fourth `action.type` in `submit_action`; either works.

**How an AI decides to detour (public information only, no simulator, no trial throw, one decision per round):**
1. Ignore the crate unless `airdrop.state` is `landed`, `pickup_open` is true and the crate is on its own side.
2. Compute D from the crate x and its own x, then k = ceil((D - 70) / 36). The AI knows the die is random, so it knows only the odds, not the roll.
3. Value of the item, from the public `item`: `candy_heal` only if it is missing at least 20 HP; `shield_patch` only for a Knight with an active shield; the others have a fixed small value.
4. Cost: leaving the spot it has calibrated. If its last two landings (from its own record) were both within 60 px of the target, it is "dialled in" and detours only for a heal.
5. Detour if the item is worth it and k is 3 or less (67% or better this turn). Choose the direction toward the crate, then move, then throw with the correction re-based by its own new x.
6. It uses the slot by the same `use_item` rule as a human. It never reads `airdrop.item` before landing.

### f. Feel and feedback

Structure borrowed from the Hearthstone feedback article: a short **preparation**, one clear **emphasis**, and a short **aftermath**, with control returned to the player while the aftermath plays. The screen stays clean: one ghost, one crate, one ring, one floating text per event, no dialog.

| Moment | What the player sees (unverified) | Existing sound event to reuse | Note |
|---|---|---|---|
| Round start | Nothing about the drop yet | `round_start` (bell) | The bell finishes first |
| Ghost entrance (3.0 s after round start) | Ghost fades in at the screen edge nearest the favoured side and flies toward the release x | A short laugh: ambient kind `witch_cackle` (1.2 s, voice family, listed in `docs/sound_mapping.md`), played as a **scripted** cue, panned about -0.8 for the left edge and +0.8 for the right. Fallback: the existing synthesized `ghost` through `ambientSfx.trigger('ghost')` | I did not find `witch_cackle` in `KINDS` in `js/ambient_sfx.js` (it has crow, cat_meow, dog_bark, ghost_*, zombie_moan), so the main line must add the kind or use the fallback. Register the scripted cue as played so the random ambient layer does not add a second cackle (voice family gap 45 s) |
| Release | Ghost pauses for about 0.3 s, the canopy pops open, a **ring in the favoured team's colour** appears on the ground at the landing x (blue for the human side, purple for the agent side, same as the shields) | none | Silent on purpose to keep the mix clean |
| Descent (about 4 s) | Canopy sways about 14 px; it also **leans with the public wind**, in proportion to |wind| / 5. Landing x does not move | none | Gives the wind reaction the owner asked to see in the scene, for free. Cosmetic only |
| Landing | Light thump and a small dust burst, the canopy collapses over about 0.8 s, the item icon appears above the crate and bobs about 6 px (already built) | `impact_ground` at about half gain (not `impact_ground_heavy`); the existing `impact_burst` effect at scale 0.4 | Already in the prototype |
| Pickup | Icon arcs to the slot (0.4 s); slot border glows once (0.6 s, `.is-full` in `css/dock.css`); floating text is the icon and at most 4 characters | `item_pickup` (event exists in `docs/audio_event_map.json`; its file is missing, so it falls back to the synthesized recipe) | For the AI the icon arcs to its HP bar and the slot icon appears there |
| Replace | The old icon rises and fades as a grey wisp (0.4 s); two-character label 換新 | same `item_pickup` | Control stays live (Hearthstone aftermath) |
| Use | One floating text, for example "+25" | `candy_heal`: `heal`. `shield_patch` and `bone_ward` applied: `shield_place`. `bone_ward` absorbing a hit: `shield_block`. `second_die`: `dice_rattle` then `dice_result` at the Move (both already called in `startDiceRoll` / `stepDice`). `heavy_shell` and `calm_wind`: `ui_click` plus a badge pulse | `docs/sound_mapping.md` plans extra layers on `heal` and `shield_place`; check by ear that they still sit well together |
| Expiry | Crate and ring fade with a small puff over 0.6 s | none | |

Rules to keep it clean: the falling crate and canopy are drawn under projectiles, units and floating text; the ghost never touches or deflects a projectile; no sound for the sway; only one scripted ghost cue per drop. Unverified: whether the ghost at y about 170 overlaps the top bar in the 4 vs 4 layout.

### g. Test list the main line can automate

1. **Determinism:** same seed and the same round sequence give the same drop list (round, team, x, item) on two runs; changing the seed changes it in at least 19 of 20 seeds.
2. **Placement validity, 10,000 random cases:** unit positions inside the move limits, random shield positions. The crate x is always inside 200..835 or 1085..1720, never inside 835..1085, and D from the reference unit is 110..178 unless the documented fallback applied.
3. **Reach:** for every starting position and every die value, a forward move picks the crate up exactly when die >= ceil((D - 70) / 36); the observed one-turn rate matches (7 - k) / 6; a unit that moves toward the crate for 3 turns always gets it when D <= 178.
4. **Other side cannot take it:** for all positions inside the move limits, no unit of the unfavoured team can reach the crate in any number of turns.
5. **Replace rule:** slot holds A, pickup B: slot is B, `replaced_item` is A, no copy of A remains. Empty slot: `replaced_item` is null.
6. **Gate and expiry:** no pickup in the drop round; pickup works in N+1 to N+3; the crate is gone at N+4; the next drop is eligible after one full round; an untouched crate does not stop later drops.
7. **Fairness over 20 drops (equal HP):** sides alternate 10 and 10, starting with the human side; the mean D per side differs by under 5 px; both sides use the same item weights; ghost travel time to the release point is mirrored within 0.05 s.
8. **Catch-up:** with a 30 point HP gap the trailing team is favoured, never three times in a row.
9. **Property tests (fast-check):** HP never above max after any item; damage never negative with `bone_ward`; `candy_heal` at full HP is rejected and the item stays.
10. **Public state:** while `ghost_flying` or `falling`, `airdrop.item` is null; the state has no seed and no schedule; the agent view and the human view of the same unit match; slots of all units are visible to all.
11. **Items and the shield:** an active sky shield still blocks a `heavy_shell` shot; `calm_wind` writes `wind_at_throw` = 0; `use_item` rejects an empty slot, a dead unit, a unit of another controller, a second use in a turn, and `shield_patch` for a non-Knight.
12. **AI:** with `pickup_open` false the AI does not detour; with k <= 3 and a useful item it moves toward the crate; it never uses an item it does not hold.

## 2. Comparison with other games

Method: I searched, then opened pages where I could. **Could not open:** `https://worms.fandom.com/wiki/Crate`, `https://fortnite.fandom.com/wiki/Supply_Drop_(Battle_Royale)` and `https://pubg.fandom.com/wiki/Air_Drops` (all returned HTTP 403). Facts that come only from a search snippet are marked "snippet only". I did not watch any gameplay video, so how any of this *looks or sounds* in those games is not claimed.

| Game | What the drop does | How it is announced | How a player reaches it | Balance trick | What we copy | What we avoid |
|---|---|---|---|---|---|---|
| **Worms** (Armageddon and series) | Crate with a weapon, health (25 HP by default in later games, also cures poison), or a utility. [worms2d.info](https://worms2d.info/Crate_Probability), [Worms World Wiki](https://worms.miraheze.org/wiki/Crates) (both opened) | Crates fall from the sky between turns; contents are hidden (a utility reveals them) | Walk, jump or use the rope to the crate | Each crate type has a per-turn chance, so a crate does not appear every turn; at most 5 crates on the map by default; crates do not spawn near other objects; health crates stop in Sudden Death; booby-trapped crates were removed after players called them unfair | A crate **limit** (ours is 1) and a **chance-based cadence**. Spawn only on a valid spot. No traps | Heal with no cap (most Worms games). Hidden bad outcomes |
| **GunBound** (Powerball mode) | Powerballs fall from the sky; collecting one gives that ability (thunder, dual shot, gold, force, bomb). Effects can stack; the bomb ball hurts whoever it hits and stacks up to 4. [Wikipedia](https://en.wikipedia.org/wiki/Gunbound) (opened) | The article does not say | The article does not say | A short list of five named effects; in normal play, strong items cost two inventory slots, weak items one, and using items delays your next turn. In Solo mode, players who are out can drop random items or bombs from the sky | A **small fixed item list** with a name each. The idea that a dropped item has a tempo cost (our cost is the lost aim) | Stacking effects, and a harmful ball that can do 100 damage (it would be a free kill) |
| **Fortnite** (Battle Royale supply drop) | Crate under a balloon with high-quality loot. [Millenium guide](https://us.millenium.gg/guide/2742.html?page=3) (opened); Creative device settings: [Epic docs](https://dev.epicgames.com/documentation/fortnite/using-supply-drop-spawner-devices-in-fortnite-creative) (opened); random location inside the safe circle: snippet only | A characteristic sound, then blue smoke marks the landing spot; Creative also offers a flare, a reticle and a map icon | Run to it; the balloon can be shot to bring it down sooner (the guide gives 1250 HP, the Creative device default is 250, so the numbers differ by mode or era). Opening takes an action | Everyone contests it, so strength is paid for with risk. Creative can limit who may open it by team or class | One **marker at the landing spot** and one **distinct sound** so the player always knows where to look | A map-wide icon, an opening step, and free-for-all contest. Our crate is for one side |
| **PUBG** (airdrop) | Crate with the strongest weapons, gear and healing. [GuruGamer](https://gurugamer.com/mobile-games/pubg-mobile-best-strategies-to-loot-airdrops-safely-9594) (opened) | Plane sound and a red smoke trail; red smoke on landing also appears in a search snippet of the PUBG wiki (snippet only, page could not open) | Run there. The guide says the safe window is about 10 to 15 s after the drop, then the area fills with enemies | Loot is paid for with exposure: players camp the crate | **Smoke or ring as a landing mark**; a time window | Strong contested loot and ambush play. We do not want a kill zone |
| **Hearthstone** (Discover and feedback) | Discover lets a player choose one of three cards (snippet only, [wiki.gg](https://hearthstone.wiki.gg/wiki/Discover)). It is not a drop, so I used it for item feedback, not item rules | A readable feedback sequence, per the design article: [Boger, "Hearthstone Dramatic Signs & Feedbacks"](https://jboger.substack.com/p/hearthstone) (opened) | n/a | Not a balance trick; the lesson is that the effect has three beats (preparation, emphasis, aftermath), several layers (animation, sound, text), and that the player regains control while the animation ends | The **three beats**; a clear "replaced" mark when something is swapped out (the article describes this for the mulligan); control back during the aftermath | Long, blocking animations (a Blizzard forum thread title, snippet only, complains about losing games to animations) |
| **Cat vs Dog** (Doodle-style turn-based throwing; this listing is "tw.idv.ananshop.iCatDog") | **No supply crates on the page I opened.** It has four skills, combo scoring, physics gadgets drawn with angles and speeds, and a crow that flies over the wall from level 8 and knocks throws away. [Google Play](https://play.google.com/store/apps/details?id=tw.idv.ananshop.iCatDog) (opened) | The crow is simply visible on screen | n/a | Hazards are shown with their numbers, so the player learns from them | Show the physics (wind lean on the parachute) so the scene teaches | A flier that changes the outcome of a shot at random. Our ghost never touches a projectile |

### Where the prototype differs from the best practice, and what to change first

| Order | Difference | Best practice | Change |
|---|---|---|---|
| 1 | Crates can land on the fence, on the wrong side, or out of reach, and an unreachable one blocks all drops (D1, D2, D6) | Worms spawns only on a valid spot and caps the number of crates | Zones, distance band, 3-turn lifetime, expiry (sections 1a and 1b) |
| 2 | Only the ghost and the falling crate tell the player where it lands | Fortnite and PUBG mark the landing spot and use a distinct sound | Team-coloured ring at release, one scripted ghost cue |
| 3 | The AI gets its own rules (always heals, no slot, rarely moves) (D7) | The same rules for everyone; "the AI cannot cheat" is a product principle | Public slot for every unit, `use_item`, the detour rule in 1e |
| 4 | The two sides get different timing, and the first drop goes to the AI (D4, D5) | Fairness by a rule, not by luck | Next-round pickup gate, ghost enters from the nearer edge, first drop to the human |
| 5 | Two items only, one of them unused by the AI | A small fixed list (GunBound), each effect smaller than a kill | The six-item table; two work today |
| 6 | Pickup text is a sentence, no replace mark, no sequence | Hearthstone's three beats and a replace mark | Icon plus 4 characters, wisp for the replaced item |

### Compared with how the owner plays

| Owner trait (`(not published)`) | How the design answers it | Risk |
|---|---|---|
| Short messages, replies in fragments | Floating text is an icon plus at most 4 characters; labels are 2 Chinese characters; no dialog, no confirm | The 2-character labels may be too terse for a new player (unverified) |
| Nothing messy | One ghost, one crate, one ring at a time; no sound for the sway; crate drawn under projectiles | The ring and icon add two marks to a busy field. Remove the ring first if it feels busy |
| Readable screen | Team colours as for the shields; item icon visible after landing; the opponent's slot as one icon at its HP bar | Icons are only 34 px in the prototype. They need distinct silhouettes (see the asset request) |
| Wind should be visible in the scene | The canopy leans with the public wind | The lean could be mistaken for a changed landing x. Keep it small |
| Results, not long explanations | Section 1g is a checklist the main line can turn into automated checks | none |

## 3. Summary (6 lines)

1. Replace "every 2nd round" with: first drop at round 3, one crate at a time, pickup opens next round, crate lives 3 turns, one full round gap, human side first then alternate with a 30-point catch-up.
2. Land the crate 110..178 px in front of the favoured side's front unit, never in 835..1085; that gives 67 to 83% in one turn and 100% by turn 3, and the other side can never reach it.
3. Six items, each smaller than one hit: `candy_heal`, `heavy_shell` (both work today in the browser), `second_die`, `shield_patch`, `calm_wind`, `bone_ward` (need engine support); no ultimate item, nothing ignores the shield.
4. Slots and statuses are public for everyone; the item inside is hidden until landing; the AI uses the same `use_item` rule and a simple detour rule.
5. Feedback reuses `round_start`, `impact_ground`, `item_pickup`, `heal`, `shield_place`, `shield_block`, `dice_rattle`, `dice_result`, `ui_click`, plus a scripted `witch_cackle` (or the synthesized `ghost`) for the entrance.
6. The prototype has nine defects (section 0); fix zones, expiry and AI parity first.

## 4. What I could not verify

- Nothing was run or played. Reach odds and distances are arithmetic on the constants in `index.html`, done by hand.
- Whether a 3 to 4 s fall, a 3.0 s ghost delay, a 70 px radius, or the six weights feel right: guesses.
- Whether `witch_cackle` and `item_pickup` files exist (sound_mapping.md says the ambient folder is absent in this checkout), and how any sound reads.
- Whether a match lasts long enough for a drop every third round.
- How the 4 vs 4 flow, the "reference unit" and the dock slot for several units will work (owner question 4 in the feedback log is open).
- The three Fandom pages (Worms, Fortnite, PUBG) could not be opened; the Hearthstone Discover wiki, the Blizzard forum thread and the Fortnite random-location claim are snippet only. I saw no gameplay video, so I make no claim about how these games look or sound.
- The browser and MCP server use different move limits (D8). I assumed the stricter pair; the main line should confirm which one is correct.
