# Gameplay experience: requirements

Source of truth for the reasoning: `docs/experience_design.md`. Status: proposal, pending owner approval.
Items tagged **[RULE CHANGE]** need an explicit owner "yes" before anyone builds them.
Items tagged **[unverified]** depend on seeing or hearing the game and need a human check.

Terms: **director** is the DOM-free module that turns game events into effect plans. **Plan** is the list of preset calls plus screen reactions for one event.
**Live count** is `system.particles.length`. **Soft budget** is the number the director enforces. **Hard cap** is the existing `maxParticles` of 500.
Scale is 1.25 unless stated.

## R1 Budget numbers

1. While the match is in normal play, the live count shall not exceed 300.
2. While an ultimate is playing, the live count shall not exceed 450.
3. The director shall never rely on the hard cap of 500 to meet R1.1 or R1.2.
4. The director shall start at most 8 one-shot effects in any rolling 1000 ms. Per-frame trails and ambient effects do not count.
5. The sum of particles emitted by one event shall not exceed 90.
6. Each projectile shall emit at most 3 trail particles per frame.
7. Where no ultimate is playing, at most 1 projectile trail shall be active. The skeleton and cat ultimates may have 3, started 250 ms apart.
8. The ambient particles (face glow, wind motes, turn marker, ultimate pulse) shall not exceed 40 live in total and 8 per unit.

## R2 Screen reactions

1. Hit-stop shall not exceed 80 ms. A new hit-stop shall replace a running one, not add to it.
2. Shake amplitude shall not exceed 8 px at a canvas width of 1280, scaled linearly with width, and its duration shall not exceed 250 ms. Overlapping shakes shall use the larger, not the sum.
3. A full-screen flash shall not exceed alpha 0.20 or 120 ms, and at most 3 flashes shall start in any rolling 1000 ms.
4. Slow motion shall be used only for a KO, at 0.6x for at most 400 ms.
5. An ultimate shall take at most 2500 ms from its first effect to its last impact.
6. Where "reduced effects" is on, the director shall set shake and flash to 0, hit-stop to 0, and halve all particle counts (rounded up, minimum 1).

## R3 Event mapping

For each event the director shall return a plan with the presets, positions, options and delays given in `docs/experience_design.md` section c.

1. When a throw is released, the plan shall contain the rune halo at the hand, or for the wizard the muzzle flash and smoke puff.
2. When a projectile is in flight, the plan shall give the trail preset of its weapon: spear, shuriken, cannon or shield.
3. When a projectile hits a unit, the plan shall contain `impact_burst`, `hit_sparks`, a damage number and a shock ring, with hit-stop 60 ms, shake 4 px for 160 ms, and flash alpha 0.12 for 70 ms.
4. When a projectile is blocked by the sky shield, the plan shall contain `shield_ricochet_sparks`, a cyan shock ring and the text "BLOCKED", with hit-stop 40 ms and shake 2 px for 100 ms, and no flash.
5. When a projectile lands on the ground, the plan shall contain `landing_ring_dust` and a landing pillar, and shall contain no shake, flash or hit-stop.
6. When a unit reaches 0 HP, the plan shall contain `ko_wisps`, a shock ring and `ash_fall`, with hit-stop 80 ms, shake 7 px for 240 ms, flash alpha 0.18 for 110 ms, and slow motion per R2.4.
7. When poison is applied, the plan shall contain `poison_cloud` with duration 5 s and an `impact_burst`.
8. While a unit is poisoned, the director shall request `poison_drip` for that unit every 250 ms.
9. When the sky shield is placed, the plan shall contain `shield_materialize_ripple`.
10. When a unit's hit counter reaches its class threshold, the plan shall contain `weapon_rune_halo`, an `ultimate_ready_pulse` burst, and a flash of alpha 0.10 for 100 ms. While the ultimate stays unused, the director shall add a 6-particle pulse every 1500 ms.
11. When a hit counts toward an ultimate, the plan shall contain `pip_pop` with 4 particles.
12. When a round starts, the plan shall contain `banner_embers`.
13. A miss shall not start any shake, flash or hit-stop.

## R4 Clean screen

1. The director shall not place any emit point inside a HUD rectangle (top bar, bottom dock, unit name and HP bars), except `pip_pop` inside its own pip circle.
2. The drawing order shall be: world, particles, unit labels and HP bars, HUD. No particle shall be drawn over an HP bar or a label.
3. While a head box is covered by an additive glow larger than 40 px radius, that coverage shall last at most 150 ms, except during release.
4. When the live count would exceed the soft budget, the director shall drop effects in this order: ambient, wind motes, trail stardust, smoke and dust, shock rings. It shall not drop the impact core, damage number, KO wisps or block flash.
5. If dropping is not enough, then the director shall emit the one-shot at half scale before dropping it.
6. Instruction and label text shall be drawn on a plate with at least 70% opacity.

## R5 Determinism and fairness

1. The director shall use only the particle system's seeded generator and the event data it is given. It shall not use `Math.random`, `Date`, `window` or `document`.
2. When two directors receive the same sequence of events and the same seed, they shall return identical plans.
3. The director shall read only public state (positions, HP, wind, history, shield state). It shall not read the RNG seed, future wind or another side's unsubmitted action.
4. While the agent is deciding, the UI shall show a fixed "thinking" effect that does not depend on the angle or power the agent has chosen.
5. The agent's charge gauge shall not be shown.

## R6 Landing memory

1. When a throw lands, the UI shall record a landing mark from the public history (`landing_x`, `landing_y`, team).
2. The UI shall keep the last 4 landing marks for both sides and show them as pillars with alpha 1.0, 0.7, 0.45, 0.25 from newest to oldest.
3. When a fifth landing arrives, the oldest mark shall be removed.
4. When a throw lands, the UI shall show a tag "short N" or "long N" (N in px, distance to the enemy unit's x), for 1200 ms.

## R7 Onboarding

1. When a new player starts round 1, the UI shall show hint 1 ("move the pointer to aim") after 3 s.
2. When the angle has changed by at least 8 degrees, the UI shall replace hint 1 with hint 2 ("press and hold to charge").
3. When a press has lasted at least 300 ms, the UI shall replace hint 2 with hint 3 ("release to throw").
4. When the first throw is released, the UI shall hide all hints and store a local flag. After that the hints shall not appear again unless the player presses "?".
5. The hint shall be drawn next to the player's unit, not in the middle of the sky.
6. **[RULE CHANGE]** Where the match is in round 1 and the hints are not finished, the 12 s turn timer shall start when the pointer first moves or after 8 s, whichever is first.

## R8 Agent learning display

1. When the agent writes notes, the UI shall show the latest note line (at most 80 characters) under the enemy name.
2. The UI shall use only text the agent wrote through `set_notes`. It shall not add information the agent did not have.
3. At game over, the UI shall show a recap of the miss distance per round for both sides, from the public history.

## R9 Pacing

1. When a round has no pending action, the delay between the end of a result and the next turn shall be at most 400 ms.
2. The agent's "thinking" beat shall last between 600 and 900 ms.
3. The target match length is 4 to 5 minutes. [unverified]
4. **[RULE CHANGE]** Where a side has been hit twice in a row without landing a hit, and it has not used the pity pip in this match, that side shall gain 1 ultimate pip. The maximum of 2 ultimates per match shall stay unchanged.
5. While a unit has less than 30% HP, the UI shall show a vignette of alpha at most 0.15.

## R10 Sound

1. The sound system shall not start before the first press.
2. Where the player presses mute, the system shall play no sound.
3. While the charge gauge is above 0, the charge hum pitch shall be a monotonic increasing function of power.
4. The impact sound shall start on the frame where the impact effect starts. [unverified]
