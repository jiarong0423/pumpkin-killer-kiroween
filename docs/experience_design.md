# Pumpkin Killer: gameplay experience and effects design (Kiro task 17)

Author: Kiro, 2026-11-09. Status: PROPOSAL for the owner. The main line builds it only after approval and re-tests everything.

## 0. How to read this document

- I cannot play the game or open a browser. Anything that depends on seeing or hearing the running game is marked **(unverified)**.
- What I looked at: `docs/game_mode.md`, `docs/ROLES.md`, `(not published)`, `docs/mcp_agent_protocol.md`, `.kiro/steering/*.md`,
  the preset list and options in `js/particles.js`, `(not published)`, and four playtest frames (`f02_charging`, `f04_flight`, `f08_defend_mode`, `f11_dice_rolling`).
- `(not published)` does not exist in the repo, so nothing here builds on it. I did not read `index.html`, so "what is built" below comes only from the task brief and `particles.js`.
- Particle counts use the formula in `particles.js` (`round(base * sqrt(scale))`) at the game scale 1.25. I computed them by hand and did not run the code. The main line should confirm them with a test.
- Rules marked **RULE CHANGE** would alter confirmed behaviour and need an explicit owner "yes". Everything else is presentation only.

### Observations from the screenshots (approximate, 1280x720 JPEG)

| Frame | What I see | Design consequence |
|---|---|---|
| f02 charging | The power ring sits on the skeleton's head and body, with a "0%" label inside it. The ring hides the character and is hard to read at low power. | Move the gauge off the body (section c, "charge gauge"). |
| f04 flight | Grey dust puffs at the thrower's feet and a few cyan dots upper left. I cannot see the weapon in flight or in the hand. I cannot tell whether the frame was taken before the weapon appears or whether the weapon is too small. | Flight needs a clearly readable projectile (glow head and short ribbon). Unverified why it is not visible here. |
| f08 defend | The instruction line is thin cyan text over cloud, low contrast. The shield bar, dashed path and four pips are readable. | Instruction text needs a dark plate behind it. |
| f11 dice | The yellow instruction line at the top is low contrast. A second label overlaps the unit's own name and HP bar on the left. I cannot see the die in this frame. | Keep one instruction line, on a plate, and keep labels out of the unit's name and HP zone. |
| HUD (all) | Top strip text is about 10-12 px tall at 1280 wide. Unit name labels are tiny. | Size and contrast are part of "clean screen": see the readability rules in section c. |
| Mockup | Ghosts carrying crates, floating platforms, numbered markers, dashed yellow aim arc, golden landing rings, bottom control bar. | The mockup's landing rings and ghost-fire palette are the visual target. |

HP in the frames drops 100 to 78 to 54 (22 and 24 per hit), so a 100 HP unit dies in 5 hits (unverified: three data points from a scripted match).

---

## a. Turn flow as the player lives it

Assumption: the first desktop version is 1 unit per side. In 4 vs 4 the same beats run per unit, with one shared 12 s planning timer (the 4 vs 4 flow is not confirmed yet).
Times are targets, not measurements.

| # | Beat | Time | Player sees | Player hears | Player decides |
|---|---|---|---|---|---|
| 1 | **Round start** | 0-700 ms | "Round N" banner rises from the ground like a ghost-fire sign. The wind arrow swings to the new value. Wind motes (a few drifting sparks) change direction. | Low church-bell note, soft wind change. | Reads the wind. Nothing to press. |
| 2 | **My turn begins** | 700-1000 ms | A ghost-fire ring lights under my active unit. The 12 s timer ring starts at the top. The other side dims about 15%. | Short rising chime. | Nothing yet. |
| 3 | **Optional: move** | 1.2-1.6 s if used | Press Move: forward / backward plates. A die tumbles above the unit, then the unit walks 36 px per pip with a dust puff per step. Moving does not use the turn. | Die clatter, small footsteps. | Direction (the die decides distance). One move per turn. |
| 4 | **Optional: guard defends** | player paced | Guard only: the shield leaves his hand. Pick Path 1, Path 2 from the glowing remembered enemy paths (last 4). A translucent bar slides along the paths, then Lock. | Spell shimmer on the shield, glass tick on each path pick. | Where to block. This uses the turn (no attack). |
| 5 | **Aim** | player paced | The unit turns toward the pointer. The angle (25-80 degrees) clamps with a soft stop at both ends. A short angle stub (about 60 px) shows the direction. No full trajectory (see open question 1). | Faint tick each 5 degrees. A softer thud at the clamp ends. | Angle, by moving the pointer. |
| 6 | **Charge** | 0 to about 1.8 s per full back-and-forth | Press anywhere: charge starts at once. Gauge fills 0 to 100 and ping-pongs. The weapon glows and a rune halo opens at 100%. The unit winds up. | A hum whose pitch follows the power, so the player can hear 60% vs 90%. | When to release. |
| 7 | **Release** | 0-150 ms | Windup snaps to release. The weapon leaves the hand. Recoil on the wizard. The attacker's portrait (big head) shouts in the bottom bar. | Whoosh, class-specific (section b). | Nothing. Correction comes next throw. |
| 8 | **Flight** | about 0.8-2 s (unverified) | The weapon crosses the fence with its trail. Wind motes lean with the wind. A new weapon fades into the hand after 0.55 s. | Whoosh pitch drops as it falls. | Watches. Starts forming the next correction. |
| 9 | **Result** | 300-900 ms | Hit, block, or ground (section b). A number floats up, the HP bar drains with a pale "ghost" bar that follows 300 ms later. A ghost-fire pillar marks the landing and stays (see below). A small tag says "short 120" or "long 80". | Impact sound on the exact impact frame. | Reads the correction: short, long, wind. |
| 10 | **Handover** | 400 ms | Dim shifts to my side. A single "enemy turn" line. | Soft card-flip sound. | Nothing. |
| 11 | **Enemy turn** | agent pace, 600-900 ms "thinking", then a fixed windup | A pale ghost-fire swirl above the enemy head while it decides. Then the same throw animation as mine. The charge gauge is not shown for the agent. | Candle flutter while thinking, then the same sounds as mine. | Watches. If I hold a shield, my defend shows its effect here. |
| 12 | **Round end** | 600 ms | Ultimate pips update, poison ticks, tally. The ghost-fire landing pillars of the last 4 landings stay on the ground, newest brightest. | Page-turn sound. | Starts the next plan with 4 landing marks as memory. |

**Landing pillars.** The game already remembers the last 4 enemy paths for the guard. I propose the same memory is visible for everyone: a thin ghost-fire pillar on each of the last 4 landing points (human and agent), fading with age (alpha 1.0, 0.7, 0.45, 0.25). This is the "record of past landings" the product principles give both sides, so a human learns the way the agent does. It is public data only.

**Charge gauge placement.** Replace the ring on the unit's body with a short arc 36 px above and in front of the unit's head, plus a digit above 20% only (the "0%" label is noise). The unit's body and face stay visible. (unverified in game: I only have the f02 frame.)

---

## b. Feedback table (game feel)

Rules for the table:
- **Hit-stop** freezes unit and weapon animation only. Particles and the HUD keep running, so the screen never looks frozen. Maximum 80 ms.
- **Shake** amplitudes are in px at 1280 px canvas width and scale with canvas width. Direction is along the projectile travel, decaying linearly.
- **Flash** is a full-screen additive overlay. Maximum alpha 0.20 and 120 ms, at most 3 flashes in any 1000 ms (photosensitivity). A "reduced effects" toggle sets flash and shake to 0 and halves particle counts.
- Sounds are ideas, to be picked from CC0 libraries (ROLES queue item 6). Sound starts after the first press (browser autoplay rule). **All sound ideas are unverified**; I cannot hear them.

| Event | Effect | Sound idea | Screen reaction | Duration |
|---|---|---|---|---|
| **Charge** | Weapon aura grows with power. Pumpkin face glow / skeleton eye flame brightens. Rune halo opens at 100%. | Hum rising in pitch with power. Tick at 100%. | None. A 2% brightness lift on the active side only. | While held. Halo 450 ms. |
| **Release** | Weapon leaves the hand. Class windup finishes. Rune halo at the hand (wizard: muzzle flash). | Class whoosh (rune hiss, flick, cannon thump, spin whir). | Wizard: shake 5 px. Others: none. No hit-stop. | Windup-to-release 120-160 ms. Shake 140 ms. |
| **Flight** | Weapon trail (1-2 particles per frame), glowing head, wind motes lean. | Whoosh with pitch falling as the weapon drops. | None. Camera stays still so the player can judge distance. | Flight time (unverified, about 0.8-2 s). |
| **Hit** | Impact burst, hit sparks, shock ring, damage number, target flashes white and nudges back 6 px. | Wet-wood or bone thud plus a bright accent, pitched by damage. | Hit-stop 60 ms. Shake 4 px. Flash alpha 0.12. | Hit-stop 60 ms. Shake 160 ms. Flash 70 ms. Nudge 120 ms. Number 1100 ms. |
| **Block** | Ricochet sparks off the sky shield, cyan shock ring on the bar, "BLOCKED" text. The bar flickers once. | Glass ping plus soft bell. | Hit-stop 40 ms. Shake 2 px. No flash. | Hit-stop 40 ms. Shake 100 ms. Text 900 ms. |
| **Miss / ground** | Landing ring and dust. Short "short 120" / "long 80" tag. A ghost-fire pillar stays. | Dull thud, fabric-like dust. No fanfare. | None. A miss must be quiet so it reads as information, not punishment. | Ring 500 ms. Tag 1200 ms. Pillar stays 4 landings. |
| **Fence hit** | Wood splinters (existing impact debris), fence flashes once. | Wood crack. | Shake 3 px. | Shake 120 ms. |
| **KO** | Unit's glow goes out, ghost-fire wisps rise, cyan-violet ring, unit crumbles to ash / drops its weapon. | Low gong, then a short sigh of wind. | Hit-stop 80 ms. Shake 7 px. Flash alpha 0.18. Slow motion to 0.6x for 400 ms. | Hit-stop 80 ms. Shake 240 ms. Flash 110 ms. Wisps 1800 ms. |
| **Poison (applied)** | Green cloud at the blast, unit tints green. | Bubbling hiss. | As Hit. | Cloud 5000 ms. Tint while poisoned. |
| **Poison (tick)** | Green drip from the unit every 250 ms and a small green damage number. | Soft drop plop. | None. | Tick effect 600 ms. |
| **Shield placed** | Shield materializes as a thin glossy bar with expanding cyan rings. | Spell shimmer, rising. | None. | Ripple 800 ms. |
| **Shield expires** | The bar dissolves into rising motes. | Reverse shimmer. | None. | 500 ms. |
| **Ultimate ready** | Gold-violet stardust column and rune halo on the unit. The portrait and the ultimate button get a pulsing gold edge. A pip pops. | Choir-like rising chord, 1 s. | Flash alpha 0.10. No shake. | Burst 600 ms, then a 6-particle pulse every 1500 ms until used. |
| **Ultimate used** | Class-specific anticipation (500 ms), then impact (section f). Total at most 2.5 s (from `vfx_reference_hearthstone.md`). | Big whoosh plus low rumble. | Hit-stop 80 ms per impact. Shake up to 8 px. Flash alpha 0.20. | At most 2500 ms in total. |
| **Pip gained** (successful hit counted) | Small ring and 3 sparks at the pip. | Soft tick. | None. | 350 ms. |
| **Turn timer low** (last 3 s) | The timer ring pulses red-violet. No particles. | Soft heartbeat tick once per second. | None. | 3000 ms. |
| **Round start** | Banner rises, wind arrow swings, wind motes retarget. | Church bell. | None. | 700 ms. |
| **Round end** | Pips and tally update. The oldest landing pillar fades. | Page turn. | None. | 600 ms. |
| **Move (die)** | Die tumble, then dust per step. | Dice clatter, footsteps. | None. | 1200-1600 ms. |
| **Game over** | Winner side lights up, loser side ash. Recap overlay (section g). | Short fanfare or a sad bell. | Flash alpha 0.15. | 1500 ms, then the recap. |

---

## c. Particle and visual effects design

### Palette (Halloween magic, wizard-school)

| Role | Colours |
|---|---|
| Ghost fire (cold magic, turn markers, KO, shield) | cyan `#7df9ff`, `#a5f3ff`, ice white `#e0fbff`, mint `#9dffd0` |
| Violet (agent side, runes) | `#b388ff`, `#d9b8ff`, deep `#3a1c71` |
| Gold stardust (enchant, ultimates, UI accents) | `#ffe9a3`, `#ffd27a`, `#b45309` |
| Pumpkin glow (warm, player side, impacts) | `#ffb347`, `#fff0b8`, ember `#c2410c`, `#8f2d12` |
| Poison (only for poison) | `#3fbf3f`, `#4ade4a`, bubbles `#9dff7a`. Poison stays yellow-green so it cannot be confused with mint ghost fire. |

Team reading: player impacts use warm gold/orange, agent impacts use violet (this is already `TEAM_PALETTE` in `particles.js`). A player can tell who hit whom without looking at the HUD.

### Making effects "have texture" (owner feedback)

Each large effect uses four layers, as in `vfx_reference_hearthstone.md`: back glow (big, low alpha, additive), core (small, hot, additive), sparks (streaks and spinning squares, additive, with cooling colour from `colorEnd`), and soft smoke or dust (normal blending, alpha at most 0.5). Never use one uniform circle size. Random lifetimes vary by at least 40%. Optional: ask Colab for one 128 px grain/smoke sprite to replace the soft circle for smoke. Not required for the first pass. **(unverified: texture quality can only be judged by eye.)**

### Weapon effects vs face / body micro-motions

| Kind | What | Particle cost |
|---|---|---|
| **Weapon effects** (spear, shuriken, cannonball, thrown shield) | trail, glowing head, charge aura, rune halo, stardust, impact, ricochet | counted in the budget below |
| **Face micro-motions** | jack-o'-lantern glow flicker (`face_glow_pumpkin`), skeleton eye flame (`face_glow_skeleton`), eye glow brightens on charge, hit squint (sprite swap or 80 ms tint), KO eyes go out | tiny, "ambient" budget |
| **Body micro-motions** | breathing bob 1.5 px over 2.2 s, cape sway, cat tail flick, hit nudge 6 px over 120 ms, white hit tint 80 ms, green poison tint | zero particles (sprite transforms) |

### Per-event preset map

Counts are particles per call at scale 1.25, computed from `particles.js` (check with a test).
"NEW" means a preset that does not exist yet.

| Event | Preset(s) | Count | Look |
|---|---|---|---|
| Charge | `weapon_charge_aura` | 2 per call, every 100 ms | Motes drawn into the weapon, team colour. |
| Charge at 100% | `weapon_rune_halo` | 11 once | Violet and gold ring opens around the weapon, 8 sparks drift out. |
| Release (spear, shuriken, shield) | `weapon_rune_halo` | 11 once | Same rune halo at the hand. |
| Release (cannon) | `muzzle_flash` plus `smoke_puff` | 13 plus 10 | Hot flash, streaks, grey smoke rising. |
| Flight, spear | `weapon_trail_spear` plus `weapon_enchant_stardust` | 1-2 plus 2 per frame | Pale blue streak, gold-violet stars falling. Glowing spearhead (already built). |
| Flight, shuriken | **NEW** `weapon_trail_shuriken` | 1-2 per frame | Cyan-violet motes plus small spinning squares. Replaces `weapon_trail_dart` (its orange tail suits a dart, not a shuriken). |
| Flight, cannonball | `weapon_trail_cannon` | 2 per frame | Dark smoke plus orange embers. |
| Flight, thrown shield | `weapon_trail_shield` | 1 per frame, a spark 25% of frames | Cyan rings and rare glass shards. |
| Hit | `impact_burst` plus `hit_sparks` plus `damage_number` plus **NEW** `shock_ring` | 38 plus 19 plus 1 plus 1 | Flash, ring, embers, debris, dust (already tuned). |
| Block | `shield_ricochet_sparks` plus `shock_ring` (cyan) plus `damage_number` text "BLOCKED" | 17 plus 1 plus 1 | Cyan-white sparks off the bar. |
| Miss / ground | `landing_ring_dust` plus **NEW** `landing_pillar` | 15 plus 6 | Rings and dust, then a thin ghost-fire pillar (`landing_pillar` is a vector line, 6 motes at emit, then a per-frame 0 cost glow). |
| Fence hit | `impact_burst` at scale 0.7 | 25 | Wood debris. |
| KO | `ko_wisps` plus **NEW** `shock_ring` plus **NEW** `ash_fall` | 14 plus 1 plus 10 | Cyan-violet wisps up, grey-violet ash drifts down. |
| Poison applied | `poison_cloud` (duration 5 s, not `rounds * secondsPerRound`) plus `impact_burst` | 51 plus 38 | Lingering mist. This changes the intent of task 15 in the `particles` spec: the mist is cosmetic and lasts 5 s. Poison on the unit is shown by tint and drip. A 3-round cloud would cost about 50 particles for about a minute. |
| Poison tick | `poison_drip` every 250 ms | 5 per call | Drops. At 250 ms the live count is about 14 per poisoned unit. |
| Shield placed | `shield_materialize_ripple` | 17 once | Three cyan rings, flash along the bar, rising motes. |
| Shield expires | **NEW** `shield_dissolve` | 8 | Bar breaks into rising cyan motes. |
| Ultimate ready | `weapon_rune_halo` plus **NEW** `ultimate_ready_pulse` | 11 once, then 6 per 1500 ms | Gold-violet column pulse. |
| Pip gained | **NEW** `pip_pop` | 4 | One ring and 3 sparks at the HUD pip. Drawn over the HUD by design, but only inside the pip's 24 px circle. |
| Wind | **NEW** `wind_motes` | 1 per 250 ms, 12 live at most | Faint dust and spark motes drift with the wind and speed up with its strength. Gives the wind a feel without reading numbers. |
| Turn marker | **NEW** `turn_marker_wisp` | 1 per 300 ms, 6 live at most | A small cyan flame circling the active unit's feet. |
| Face glow | `face_glow_pumpkin` / `face_glow_skeleton` | 1 per call, every 150 ms | Unchanged. Double rate while charging. |
| Round start | **NEW** `banner_embers` | 10 once | Embers rise off the banner. |
| Game over | `ko_wisps` on the loser, `weapon_enchant_stardust` on the winner | 14, 20 once | Winner gold, loser cold ash. |

### Clean-screen budget (numbers a test can check)

| # | Budget | Value |
|---|---|---|
| B1 | Live particles, normal play | at most **300** |
| B2 | Live particles during an ultimate | at most **450** |
| B3 | Hard cap (existing, unchanged) | **500**. It is a safety net. The budget above must hold without relying on the oldest-first drop. |
| B4 | One-shot effects started per rolling 1000 ms (not counting per-frame trails and ambient) | at most **8** |
| B5 | Trail particles per frame per projectile | at most **3** (stardust and trail together) |
| B6 | Projectile trails alive at once | **1**, except the skeleton ultimate (3, started 250 ms apart) and the cat volley (3) |
| B7 | Ambient live particles (face glow, wind motes, turn marker, ultimate pulse) | at most **40** in total, at most **8** per unit |
| B8 | One event's own emission (sum of all presets started by that event, at scale 1.25) | at most **90**. Largest cases: poison applied 89 (51 + 38), hit 59 (38 + 19 + 1 + 1), cannon release 23 |
| B9 | Full-screen flash | alpha at most **0.20**, at most **120 ms**, at most **3 per 1000 ms** |
| B10 | Shake | at most **8 px** (at 1280 wide), at most **250 ms**, never two shakes added together: take the larger |
| B11 | Hit-stop | at most **80 ms**, never overlapping (the new one replaces the old one) |
| B12 | Slow motion | only on KO, 0.6x for at most 400 ms |
| B13 | Ultimate total length | at most **2500 ms** |
| B14 | HUD rectangles (top bar, bottom dock, unit name and HP bars) | **no particle spawns inside them**, and the canvas draws HP bars and labels after particles so no effect covers them. Exceptions: `pip_pop` inside the 24 px pip circle |
| B15 | Characters | the character's face (head box) is never inside a full-alpha additive glow larger than 40 px radius for more than 150 ms. Weapon effects may overlap the body during release only. |
| B16 | Text readability | instruction and label text always has a dark plate with at least 70% opacity behind it |

B8 note: counts come from hand arithmetic on `particles.js` (for example `impact_burst` = 2 + round(20 x 1.118) + round(7 x 1.118) + round(5 x 1.118) = 38). The test should measure the real counts and compare them with this table.

Priority when the budget is full (drop in this order): ambient, wind motes, trail stardust, smoke and dust, shock rings. Never drop: impact core, damage number, KO wisps, the block flash. If a one-shot would break B1 or B2, it is emitted at half scale first.

---

## d. Onboarding: the first 60 seconds

Goal: a new player throws a first correct-looking shot within 20 seconds, without reading anything. The permanent tutorial box in the sky is removed.

**Three hints** (one line each, on a dark plate beside the player's unit, never in the middle of the sky). A hint appears only after the previous one is done:

1. **"Move the pointer to aim"**. Shown from second 3. Done when the angle has changed by at least 8 degrees. The angle stub pulses.
2. **"Press and hold to charge"**. Done when a press lasts at least 300 ms.
3. **"Release to throw"**. Done on the first release.

No timer starts before step 1 is done in round 1 (the 12 s timer starts after the first hint is shown and the player has moved the pointer, or after 8 s, whichever is first, so the first turn is not forfeited by reading). **RULE CHANGE (small):** round 1 timer grace. Open question 9.
After the first throw the hints never return (a `localStorage` flag; no account, no cloud). A "?" key brings them back.

**Taught by doing (no text):**
- Wind: the wind motes and the arrow lean. After the first miss the landing tag ("short 120") plus the pillar show the effect.
- Power: the hum pitch rises while charging.
- Correction: the landing pillar stays. The second throw is the lesson.
- Move: pressing Move shows plates, then the die. Self explanatory.
- Ultimate: pips fill. The ready burst plus gold edge is enough.
- The fence: the first fence hit shows debris.

**Never explained in text:** the ping-pong gauge, the die-to-distance rule, the 36 px per pip, why the AI is hard to fool, the remembered paths (the guard sees them glow when Defend opens), ultimate counters per class. A player who wants the rules opens the "?" panel.

| Time | What happens |
|---|---|
| 0-3 s | Scene fades in. Candles flicker, a ghost passes, banner "Round 1", wind arrow. |
| 3-10 s | Hints 1 to 3 as the player acts. |
| 10-20 s | First throw. Most first throws miss. The landing tag explains the miss. |
| 20-30 s | Handover. The AI thinks, then throws. Its landing pillar also appears. |
| 30-45 s | Second throw. The player uses the pillar as a reference. |
| 45-60 s | The AI's second throw. A closer second throw by either side is the first "I am learning" moment. |

Mobile: not in this phase. The later phone version replaces "move the pointer" with "press and drag to aim" and keeps the same three steps.

---

## e. Pacing and difficulty

**Round length.** Human turn up to 12 s (the owner has not decided between 12 s and the mockup's 8 s: I recommend keeping 12 s for the first round and testing 8 s later). A typical 1 vs 1 round: banner 0.7 s, human turn about 7 s, result 1.5 s, agent turn about 5 s, result 1.5 s, which is about **16-20 s**. Unverified: only a stopwatch in a real session can confirm.

**Match length.** Target **4-5 minutes**: 10-12 rounds in 1 vs 1 with the observed damage (about 22 per hit). In 4 vs 4 (not built), 6-7 rounds at about 35 s each (assumes each unit's resolution takes 1.5-2.5 s). The 3-minute video does not need a full match.

**How the agent gets harder without being weakened.** The agent plays fair (steering: "not made weaker on purpose"). Its strength comes only from what it has read:
- Round 1-2: the agent has no history. It makes a wide guess and usually misses. This is real, not staged.
- Round 3+: it uses `get_history` (wind at throw, landing_x/y, hit type) and its own notes. Its misses should shrink.
- A visible **learning ticker** (small line under the enemy name, from the agent's `set_notes` text): "Last: landed 140 short at wind +2.4. Next: more power." This is public text written by the agent. It makes the learning visible without leaking anything.
- The human also sees the pillars and tags, so both sides get the same information. That is the "both sides getting better" story from the steering file.
- "Veteran" mode: start the agent with saved notes (`--memory-dir`, off by default). Fresh agent = easy, veteran = harder. The labels are the only difficulty switch. **No hidden aim penalty, no aim bonus.**

**Comeback mechanics** (presentation first, rule changes marked):
1. *Ultimate catch-up is already built in*: ultimates unlock by hits, so the leader gets them first. That favours the winner. So:
2. **RULE CHANGE (recommended yes):** *Pity pip.* A side that has been hit twice in a row without landing a hit gets +1 ultimate pip (once per match). It keeps the max of 2 ultimates per match unchanged. Open question 6.
3. *Low-HP vignette* (presentation only): below 30% HP the screen edge gets a faint red-violet vignette at alpha at most 0.15, and a slow heartbeat sound. It builds tension and does not change rules.
4. *Airdrops* (owner idea, not built): crates should land nearer the trailing side. Only a suggestion. Details are open in `game_mode.md`.
5. *Last-stand cheer*: a unit that lands a hit while below 30% HP gets a bigger damage number and gold sparks (cosmetic).

---

## f. Per-class feel

**Skeleton javelin.** The satisfaction is the real hand: the skeleton's bony arm swings back, a clear windup lasting 90 ms, then the arm goes overhead and the spear leaves from the fingertips with a bright cold-blue glint on the spearhead (already built). In flight a thin pale ribbon follows, with gold-violet stardust dropping from the shaft. The impact is a bone-white spark, with a short rattle sound. The weapon is long and readable at a distance, which suits the owner's "weapons large, characters small". The ultimate is three javelins 250 ms apart; each leaves a ground crack and the third carries a bigger halo. Charging brightens the eye flame so the face tells the player "I am ready".

**Cat shuriken (assassin).** The satisfaction is speed. The cat crouches low (about 25% lower than idle), the hand dips to the belt bag, and a quick flick throws one shuriken. The cape trails once. The trail is thin cyan-violet, with the shuriken spinning. A small cheek-flash at release. Impact is short and sharp: small sparks, no big shake (shake 2 px), because the cat is the fast class, and the quick rhythm is its feel. The ultimate shows three shuriken fanned out, then a rain over an area (`dart_rain`, width about 300 px, 38 streaks), so the "rain" must be lit in cyan-white, not orange, to match the shuriken change. Open: the ultimate look depends on the final rule (confirm "rain" vs "fan").

**Pumpkin wizard (cannon).** The satisfaction is weight. The cannon lifts with a charge glow, then fires with a muzzle flash, smoke, and a recoil that pushes the wizard back 8 px over 120 ms and shakes the screen 5 px. The cannonball leaves a dark smoke trail with orange embers. The big impact has the largest ring of all classes. The pumpkin face glow flares at release. Ultimate: the poison shell. The barrel turns green and steams (anticipation 500 ms), the blast is green with a wide ring, a 5 s mist lingers, and hit units tint green and drip.

**Pumpkin guard (thrown shield, floating shield).** The satisfaction is two different moods. Attack: the guard throws a small shield that spins sideways like a saw, with cyan rings in the trail and a clear ringing "clang" when it hits. Defend: the shield leaves his hand and a glossy bar materializes in the sky with three cyan rings, like a spell cast. When an enemy throw hits it, the bar flickers, sparks fly, "BLOCKED" rises, and the guard's lit face smirks. The block works the way the guard's memory works, so the player feels clever for placing it on the remembered path. Ultimate: the ricochet, one spark ring per collision, number of bounces from the die (die tumbles first, visible).

---

## g. Demo moments (3-minute video)

1. **"The AI learns."** (5 s, about 0:50 in the video) Round 5 or later. On screen: both ghost-fire landing pillars (the last 4) clustering near the targets, the learning ticker line, the wind arrow, the round counter, the AI's throw landing close. Must show: the older pillars visibly farther away than the newest, so the viewer sees improvement. HUD and both characters fully visible. Needs the pillars and the ticker.
2. **Pumpkin guard blocks with the sky shield.** (5 s, about 1:30) On screen: the shield bar materializing earlier (or already placed), the enemy weapon arriving on the remembered path, the ricochet sparks, "BLOCKED", the guard's smirk, both HP bars unchanged. Must show the dashed or glowing remembered path in the lead-in so the viewer understands the idea.
3. **Wizard poison shell ultimate and KO.** (5 s, about 2:20) On screen: pips full and the gold edge on the ability, the green anticipation steam on the cannon, the big green blast, the mist, two units tinted green with drips, then the damage numbers and the KO wisps. HP bars and the round counter stay visible. Total effect within 2.5 s.

Optional closing frame (3 s): the **match recap overlay**, both sides' landing dots per round, big at first and shrinking toward the target. It is the clearest picture of the steering file's claim "both sides getting better round by round".

---

## h. Open questions for the owner (one word each)

| # | Question | My recommendation |
|---|---|---|
| 1 | Aim preview: show only a short angle stub, no trajectory and no landing prediction (matches "no simulator" and "no preview" in the steering file; the mockup's long dashed arc would give humans a simulator)? | **stub** |
| 2 | Add CC0 sounds (charge hum, whooshes, impacts) with a mute button? | **yes** |
| 3 | Hit-stop 60 ms on hits and 80 ms on KO? | **yes** |
| 4 | Show the last 4 landings of BOTH sides as ghost-fire pillars? | **yes** |
| 5 | Show the agent's learning ticker (its own notes) under its name? | **yes** |
| 6 | RULE CHANGE: pity pip (+1 ultimate pip once per match after being hit twice in a row without a hit)? | **yes** |
| 7 | Reduced-effects toggle (no flash, no shake, half particles)? | **yes** |
| 8 | Target match length? | **five** (minutes) |
| 9 | RULE CHANGE (small): the round-1 timer starts only after the player moves the pointer (or 8 s)? | **yes** |
| 10 | Turn timer: keep 12 s? | **twelve** |
| 11 | Poison mist lasts 5 s only (the status is shown by tint and drip)? | **yes** |
| 12 | Match recap overlay at game over? | **yes** |
| 13 | Keep effect scale 1.25 and particle cap 500? | **keep** |
| 14 | Cat ultimate colour: cyan-white rain (shuriken), not orange? | **cyan** |

---

## What I could not verify

- Anything visual or audible: texture quality, timing, how the effects look together, whether the budget numbers feel right. All durations and counts are first guesses for the main line to tune.
- Real flight time, real gauge ping-pong speed, the real timer behaviour, real HP and damage values (only three data points from the frames).
- Whether the particle counts in section c match the code at scale 1.25 (hand-computed).
- What `index.html` already does with the effects it calls "built" (I did not read it).
- 4 vs 4 pacing: not built and the flow is unconfirmed.
- Two shell commands I tried at the start (directory listing) did not run: the permission request failed before it was answered. I used the file tools instead, so nothing depended on them.
