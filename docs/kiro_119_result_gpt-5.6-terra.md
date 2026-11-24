# Task 119 result

Changed `js/ai_levels_page.js` (`knobsFor`, `levelName`), `scripts/sweep_page_ai_levels.js` (seeded page-math sweep), `scripts/test_ai_levels_page.js`, and `docs/ai_levels_page_20261115.md`.

| tried knobs: easy / normal / hard | 4,000-throw rates: easy / normal / hard |
|---|---|
| 240, 2.0, 10 / 150, 1.2, 6 / 65, 0.5, 3 | 29.1% / 42.9% / 59.5% |
| 300, 2.8, 26 / 150, 1.2, 18 / 65, 0.5, 5 | 15.8% / 22.4% / 53.4% |
| 350, 3.2, 32 / 150, 1.2, 14 / 65, 0.5, 5 | 12.8% / 27.1% / 53.4% |
| 350, 3.2, 36 / 150, 1.2, 14 / 65, 0.5, 5 | 11.5% / 27.1% / 53.4% |

Final Wilson intervals: easy 10.6%-12.6%; normal 25.8%-28.5%; hard 51.9%-55.0%.

`node scripts/test_ai_levels_page.js` → `PASS: page AI level table is deterministic, safe, and ordered`
`node scripts/sweep_page_ai_levels.js` → `PASS: ordered, non-overlapping level rates`
`python3 -B scripts/test_constants_sync.py` → `OK: shared/constants.json matches index.html for all 11 constants and adaptive-level tables.`
`python3 -B scripts/test_agent_levels.py` → `Ran 6 tests in 0.237s` / `OK`

Not run: browser wiring, which task 123 owns. One exploratory inline Node command was permission-denied; the required small sweep was rerun as `node scripts/sweep_page_ai_levels.js --throws 1000` and passed.
