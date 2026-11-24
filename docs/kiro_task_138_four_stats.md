# Kiro task 138 — every hero has four stats: HP, defense, attack range, attack points (work block B21, balance)

Owner decisions (2026-11-15): lower the necromancer's total attack now and tune balance values later; every hero is described by four stats: HP (血量), defense (防禦), attack range (攻擊範圍) and attack points (攻擊點數). The numbers are provisional and will be tuned later, so the structure must make that a one-line change.

Read: `js/class_stats.js` (all class rows, `REAPER_FLAME_CONSTANTS`, `hitsToKill`, band checks), `scripts/test_class_stats.js`, `scripts/sim_balance.js`, `scripts/test_sim_balance.js`, `docs/balance_eight_20261115.md`, `js/ultimate_fx.js` (`NECRO_VOLLEY_SCALE` = 0.5 provisional), and in `index.html` (read only) `HERO_PROFILES` and the damage code at the hero hit (`dmgNow`).

Do, saving after each:
1. In `js/class_stats.js` give every class row four explicit named fields: `hp` (exists), `attack` (the existing normal damage, alias of `dmg`), `defense` (a damage-reduction fraction from 0 to 0.5, default 0 for every class so nothing changes yet; PROVISIONAL marker next to each) and `range` (a number: the typical landing distance in px at full power, computed from `speedScale` and the existing flight model; document the formula in a comment). `hitsToKill` must apply `defense` as `damage * (1 - defense)` before rounding, so a later non-zero value works; add `statsOf(key)` returning the four fields.
2. `scripts/test_class_stats.js`: tests that every class has the four fields in range, that defense 0 leaves every existing hits-to-kill number unchanged, that a defense of 0.2 raises hits to kill for a hand-checked case, and that range is positive and monotone in `speedScale`. Existing tests must still pass.
3. Write `docs/hero_stats_table_20261115.md` (max 40 lines): one row per hero (8 rows incl. Apple Hag as `hag`, bride and hunchback as already in the table, from the code, not invented), the four stats, the ultimate total at the current scale (necromancer 1.1/1.3/1.5 x 0.5 x N), and a column "tune here" naming the constant. State plainly which values are invented placeholders.
4. Do not wire defense into `index.html` (a separate task after the owner picks values).
5. Run `node scripts/test_class_stats.js`, `node scripts/test_sim_balance.js`, `node scripts/test_ultimate_fx.js`; paste the last lines. If a shell call is refused, say so; do not invent output.

Touch only `js/class_stats.js`, `scripts/test_class_stats.js`, `scripts/sim_balance.js` and `scripts/test_sim_balance.js` (only if needed), `docs/hero_stats_table_20261115.md` and `docs/kiro_138_result_gpt-5.6-terra.md` (max 12 lines). Do not edit `index.html`. No network, no git.
