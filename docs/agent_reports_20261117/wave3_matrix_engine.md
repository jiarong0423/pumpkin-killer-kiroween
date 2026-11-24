# Wave 3 report: back-end match matrix and front-versus-back comparison (2026-11-17)

## What exists
- `scripts/engine_matrix.py`: plays the 240 matches of `docs/MATRIX_SPEC_20261117.md` on the Python engine. Seeds `7000 + 100 x heroIndex + 10 x N + k`; right hero `HEROES[(seed*7+3)%8]`; hidden tiers from mulberry32 over `seed ^ 0x5eed` (left first, then right; checked equal to `js/weather_fx.js` mulberry32 in node); tier to power-error sd 1.6 / 5 / 9; both sides driven by the bot of `sim_team_headless.py` (`aim`, plus a random move on 35 percent of turns); team rules as built (hp scale, ramp, cap, comeback pack); 60-round guard for duels. Writes `(not published)` (spec record keys; extra top-level `params`). Its own knobs are CLI options (`--out --plays --sizes --heroes --move-rate`), no env, and the sim's repo log is not touched (log: `(not published)`).
- `scripts/compare_front_back.py`: reads the engine file and any of `matrix_page_vm.json`, `matrix_page_desktop.json`, `matrix_page_phone.json` (missing or unreadable files are listed, never an error); writes `docs/FRONT_BACK_COMPARE_20261117.md`: per size and per cell table, flags (rounds more than 25 percent, left win share more than 20 points), counters, every error with its seed, a seed-consistency check (hero, right hero, tiers must be identical per seed on every end), and a list of hypotheses derived from the numbers. Exit 0, or 2 when the engine file is missing.
- `scripts/test_compare_front_back.py` (9 tests, socket-free, fake files): flags, errors with seed, null counters, missing and corrupt files, exit codes, spec seeds, mulberry32 against node, a 2-cell engine run. Last lines: `Ran 9 tests ... OK`. Earlier suites (team rules 32, hash parity 6, stdio, seats, connect, relay, e2e) were green at the last code change; this task touched only new files.

## Engine run (`python3 -B scripts/engine_matrix.py`): 240 matches in 6 seconds, 0 errors, 0 caps, 0 guard stops
| size | rounds mean | left wins | hits per throw | near misses | pity triggers |
|---|---|---|---|---|---|
| 1v1 | 8.8 | 42% | 0.58 | 0 | 0 |
| 2v2 | 12.3 | 61% | 0.57 | 433 | 378 |
| 3v3 | 17.5 | 58% | 0.67 | 406 | 528 |
Per cell (n = 10, win share standard error about 15 points) rounds run 6.8 (wizard 1v1) to 20.1 (knight 3v3); the full 24-row table is in the output and in the comparison file. Counters not measurable on the engine are 0 (ultimates: the bot fires none; comeback hits = direct hits made while pity > 0 or behind in hp share).

## Owner runs the comparison after the page files exist
`cd <repo> && python3 -B scripts/engine_matrix.py && python3 -B scripts/compare_front_back.py` (the second reads whichever of `(not published)` exist and rewrites `docs/FRONT_BACK_COMPARE_20261117.md`; the committed copy is engine-only until then). Read first the "Seed consistency" section: if tiers or right heroes disagree, the page draw differs and the rest is not like for like.

## Limits to keep in mind
- Engine bot = plain throws only (no ultimates, skills, defend), so page ultimates and defends are the first suspects for any gap; hypotheses in the report are generated from thresholds and are guesses until checked.
- Left wins 42 percent in 1v1 on the engine (n = 80, about 5 points standard error): red may not be favoured by the engine's turn order; not investigated.
