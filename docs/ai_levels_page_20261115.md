# Page AI levels — 2026-11-15

`node scripts/sweep_page_ai_levels.js` uses 4,000 seeded throws per level over seeds 101, 202, 303, 404, 505, 606, 707 and 808. Wilson intervals are 95%.

| level | view position noise | view wind noise | aim error | hits / throws | hit rate | Wilson interval | throws 1-3 | throws 4-8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| easy | 350 px | 3.2 | 36 | 461 / 4000 | 11.5% | 10.6%-12.6% | 11.8% | 11.3% |
| normal | 150 px | 1.2 | 14 | 1085 / 4000 | 27.1% | 25.8%-28.5% | 27.5% | 26.9% |
| hard | 65 px | 0.5 | 5 | 2138 / 4000 | 53.4% | 51.9%-55.0% | 54.0% | 53.1% |

The initial page-normal knobs (150, 1.2, 6) measured 42.9% (41.4%-44.5%), outside the 25%-30% target. The final normal row keeps its existing perception values and raises only aim error to 14.

`scripts/agent_levels.py` wraps the MCP history learner and has five controls, including memory and wind fitting. The page table controls the separate page rule of thumb and calibration loop, so it is measured by `scripts/sweep_page_ai_levels.js` instead.

Task 123: call `AiLevelsPage.knobsFor(level)` at the start of every computer turn and use the three numbers instead of the constants.
