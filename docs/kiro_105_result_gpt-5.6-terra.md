# Kiro task 105 result — gpt-5.6-terra

## Changed
- `scripts/agent_levels.py` (`LEVELS`) and `scripts/sweep_agent_levels.py` now default to 400 throws per level across 8 seeds; `docs/ai_levels_sweep_20261115.md` records the final sweep.
- Added `scripts/adaptive_level.py` (`AdaptiveLevel.record_hit`, `public_state`), browser/Node `js/adaptive_level.js` (`recordHit`, `publicState`), and 12 shared cases in `scripts/adaptive_level_vectors.json`.
- Added `scripts/test_adaptive_level.py` and `scripts/test_adaptive_level.js`; `shared/constants.json` now has `ADAPTIVE_LEVEL`; `scripts/test_constants_sync.py` compares that table across Python, JavaScript, and JSON.

## Tuning tried (target/wind/power/memory/fit-wind)
| trial | easy | normal | hard | hit rates (easy/normal/hard) |
|---|---|---|---|---|
| baseline | 180/1.8/10/3/F | 80/.8/6/12/T | 20/.2/.5/50/T | 13.0/29.2/61.8% |
| trial 2 | 180/1.8/12/3/F | 80/.8/6/12/T | 20/.2/3/50/T | 12.5/29.2/52.2% |
| final | 180/1.8/13/3/F | 80/.8/6/12/T | 20/.2/3/50/T | 11.2/29.2/52.2% |

## Final sweep (400 throws per level; 8 seeds)
- easy: 45 hits, 11.2%, 95% CI 8.5%–14.7%; normal: 117, 29.2%, 25.0%–33.9%; hard: 209, 52.2%, 47.4%–57.1%. The intervals do not overlap.
- The successful sweep completed within the 180-second execution limit (under three minutes).

## Verification
`python3 -B scripts/test_agent_levels.py && python3 -B scripts/test_adaptive_level.py && node scripts/test_adaptive_level.js && python3 -B scripts/test_constants_sync.py && python3 -B scripts/sweep_agent_levels.py`
Last lines: `Ran 5 tests in 0.100s` / `OK`; `Ran 3 tests in 0.000s` / `OK`; `OK: 12 shared adaptive-level vectors passed.`
`OK: shared/constants.json matches index.html for all 11 constants and adaptive-level tables.`; final sweep: `| hard | 400 | 209 | 52.2% | ... | 47.4%–57.1% |` / `PASS: hit-rate order easy < normal < hard`.

I did not run browser-game integration or main-line verification. An optional `/usr/bin/time -p` sweep retry was permission-denied before execution; no timing output was used.
