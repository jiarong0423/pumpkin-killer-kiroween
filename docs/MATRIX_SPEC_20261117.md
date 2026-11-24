# Front-versus-back match matrix (spec, 2026-11-17)

Owner orders: every one of the 8 heroes, in each of 3 match sizes (1v1, 2v2, 3v3), played at least 10 times = 8 x 3 x 10 = 240 matches, on the FRONT end (the real page code) and on the BACK end (the Python engine), then a comparison report. Opponent strength is RANDOM and HIDDEN (never shown on screen, only written into the result files).

## Cell and seeds
- Hero list order (index 0 to 7): `skeleton, wizard, bat, knight, bride, hunchback, reaper, hag`.
- Cell = (hero H, size N in 1..3). Play k = 0..9. `seed = 7000 + 100 * heroIndex + 10 * N + k` for k = 0..9; for a larger run (k >= 10, up to 20,000 matches) `seed = 100000 + (3 * heroIndex + N - 1) * 100000 + k`, so no two cells share a seed.
- Left side (the player side): hero H is unit 0; the other units are the next heroes in the `HEROES` order (wrapping), so no hero twice in a team (owner 2026-11-17: each unit has its own hero, a hero picked in the team is locked). Right side: first hero `HEROES[(seed * 7 + 3) % 8]` (may equal H), then the next heroes in the same order. One unit per side: just the hero. (Matrices run before 2026-11-17 evening used one hero for the whole team; their files are kept as `*_oldsingle.json` and are not compared.)
- Strength: a seeded PRNG (mulberry32 over `seed ^ 0x5eed`) draws, in this order, the left tier then the right tier, each uniformly from `[hard, normal, easy]` (index `floor(u * 3)`). Tier to engine aim noise (power error sd): hard 7.5, normal 14, easy 36 (since 2026-11-17; the 20,016-match engine run before this change used 1.6 / 5 / 9). Page: the built-in AI level of the same name (`js/ai_levels_page.js`; the left side AI plays through the page's left AI seat). The tiers are stored in the result, never drawn on screen.
- Team rules as built: `shared/team_tuning.json`, `shared/comeback.json` (team matches only); one unit per side is the plain duel.
- Both sides computer-controlled; a match ends at a winner or at the round cap (team) or at 60 rounds (duel, guard).

## Result record (one JSON object per match, same keys on both ends)
`{ end: "page"|"engine", hero, hero_right, size, seed, tier_left, tier_right, winner: "left"|"right"|"cap_left"|"cap_right"|"none", rounds, hp_share_left, hp_share_right, units_left_alive, units_right_alive, throws, direct_hits, near_misses, pity_triggers, comeback_hits, ultimates_left, ultimates_right, errors: [..] }` (counters the end cannot measure are null). A file: `{ end, started, matches: [...] }`.

## Outputs
- Page, no browser (Node vm harness): `(not published)`
- Page, real Chrome (desktop) and phone Chrome by CDP: `(not published)`, `(not published)`
- Engine: `(not published)`
- Comparison: `docs/FRONT_BACK_COMPARE_20261117.md` (per cell and per size: rounds mean, win share of the left side, hits per throw, comeback and pity counts, errors; flag a cell when page and engine differ by more than 25 percent in rounds or 20 points in win share; list every error with its seed).
