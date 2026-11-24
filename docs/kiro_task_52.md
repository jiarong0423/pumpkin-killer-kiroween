# Kiro task 52 — sky target that heals the hitter's whole side

Read: (not published) (newest rows last), docs/kiro_51_recommendations.md, docs/class_stats_v2.md, (not published)

Owner rule (2026-11-09): targets appear in the sky; a projectile that hits one heals ALL allied units of the shooter's side.

Design the rule with numbers. Defaults to confirm or change with data:
1. Spawn: OWNER SAYS IT APPEARS AT RANDOM, so not one per round on a schedule: give a per-round spawn chance (and whether a target can appear mid-round), keep the average presence low enough that the heal does not break the 8 to 12 round length. HEIGHT with LIMITS (owner: always higher than the fence, random inside a limited range): the lowest allowed height is above the fence top (fence 250 px tall) plus a margin and the highest is limited so both sides can reach it with a normal throw; Kiro sets both limits from the 54 degree path data and the screen height (about 300 to 550 px above the ground is a starting guess to check). Height and a random x inside the 160 to 1760 range outside the fence, drifts with the wind (wind units to px/s), vanishes after 3 rounds unhit; never two at once.
1a. OWNER RULE: when the target appears a die is rolled to decide which side shoots at it first. Specify: the die (reuse the dice from the move step, docs or index.html stepDice), whether that first shot is the unit's normal attack for the turn or an extra one, what the other side does after a miss, a tie, what happens if both miss (target stays until the 3 round limit or vanishes), and whether the AI's first shot at the target is allowed to ignore the enemy unit. Keep the fairness: 50/50 by the die, no hidden information.
1b. OWNER RULE (CONFIRMED, reading A; ignore reading B): the unit that takes the first shot is one teammate picked at random from the winning side (1v1: the only unit). Give both readings with numbers: (A) random shooter, whole side healed; (B) whole-side shooter choice but the heal goes to ONE random teammate. Recommend one.
2. Hit box size and hit rule (centre inside the box, any projectile, ultimates multi-hit once only), how it interacts with the unit hit (a shot that passes through the target and then hits a unit counts both?), the fence and the shield.
3. Heal amount per unit (flat or percent of max HP), cap at max HP, no heal for the dead, no effect on poison or bleed (or clears them, recommend one). Must keep the match length at 8 to 12 rounds (see kiro_51 section 2); give the effect on win rate with the model used there.
4. Fair information: a human sees the target and the wind. The AI may choose to shoot at it only through the same noisy view (150 px position noise, no ballistic simulator). Give a rule for when the AI prefers the target to the unit (public information only).
5. Energy: does a target hit count as a successful hit for the three-hit ultimate energy? Recommend one answer.
6a. Owner effect: when the target is hit, a GREEN healing rain falls on every healed unit. Specify the particle preset (count, fall speed, duration about 1.2 s, green palette that matches the existing heal effect), the float text and the sound event to reuse from (not published)
6. Art list for Colab (sprite, hit flash, heal effect), in the style of (not published)

Write docs/kiro_52_recommendations.md with numbers and reasoning. Do not edit index.html. If you run scripts use `python3 -B` or `node`.
