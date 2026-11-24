# Kiro task 53 — the reaper as the fire thrower

NAME CHANGE (owner 2026-11-09): this class is now the NECROMANCER (死靈法師). The internal id stays `reaper` in code and files; only player-facing names change. Same black-robed hooded skull figure, no scythe.

Read: (not published) (newest rows last; the 'Reaper redesign' row is the rule), docs/class_stats_v2.md, docs/ultimate_rules.md, docs/kiro_51_recommendations.md, (not published)

Owner rules (2026-11-09): the black-robed reaper's normal attack THROWS FIRE (the scythe attack was called boring). Three ghost fires circle behind its back, one per lit energy pip (green normally, purple while the ultimate is armed); with the ultimate they fly out. Everything has to stay fair-information (what a human sees).

Design with numbers:
1. Normal attack: one flame shot at one unit. Weapon name, damage (keep the class band of class_stats_v2), arc and wind behaviour (compare the wizard's cannonball), hit box, what it looks like when it lands (burning ground chance?).
2. Make it DIFFERENT from the wizard, whose attacks are already a pumpkin cannon plus molotov / burning ground. Give the reaper a distinct niche (for example a burn status that ticks and spreads to the next hit, ghost fire that ignores the wind, or low arc fast flame). Recommend one with reasons and numbers; say what stays with the wizard.
3. Status: burn damage per tick and ticks, stacking rule (refresh, do not stack, like poison and bleed), interaction with the head crit and stun, with the green heal rain (does healing clear burn?).
4. Ultimate (OWNER RULE): the reaper's hand turns EMPTY with fingers pointing forward and the three ghost fires behind the back change colour and fly out; it is NOT a hand-held flame throw. The three ghost fires fly out. Is it one attack with three flames (like the skeleton's triple javelin, +5 percent per hit) or three separate seeking flames? Damage 1.5 x normal in total as for the other classes, once per own turn when armed, max 2 per match, no hidden information. Does it replace the old three scythe slashes? (The owner called the scythe boring: assume yes, say so.)
5. HP (provisional 105), movement, and the effect on the 8 to 12 round match length; run `node scripts/sim_balance.js` if it supports adding a class, otherwise give a hand model.
6. Art list for Colab (one-head idle comes first; the owner has not picked one yet): flame projectile sprite, throwing hand poses without scythe (wind-up, release, hit), portrait, burning ground patch, impact flash; style per (not published)

Write (not published) Do not edit index.html. Use `python3 -B` / `node` for any scripts.
