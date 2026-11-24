# Kiro task 104 result — gpt-5.6-terra

## Changed
- `scripts/agent_levels.py`: `LEVELS`, `PublicToolClient`, `LevelAgent`, and `choose_action` add seeded, public-tool-only difficulty wrappers around `eval_agent_learning.HistoryLearner`.
- `scripts/sweep_agent_levels.py`: `play_match`, `run_sweep`, Wilson intervals, ordered-rate exit, and the markdown report writer.
- `scripts/test_agent_levels.py`: deterministic, knob-only, ordering, public-tool, and report-output tests.
- `docs/ai_levels_sweep_20261115.md`: generated default sweep table. Normal aim error was tuned from 3.0 to 6.0; no other mechanism was added.

## Verification run
`python3 -B scripts/test_agent_levels.py`
```
Ran 5 tests in 0.106s

OK
```
`python3 -B scripts/sweep_agent_levels.py`
```
| easy | 200 | 27 | 13.5% | 373.3 px | 361.5 px | 9.4%–18.9% |
| normal | 200 | 54 | 27.0% | 260.3 px | 120.8 px | 21.3%–33.5% |
| hard | 200 | 119 | 59.5% | 247.0 px | 51.2 px | 52.6%–66.1% |
PASS: hit-rate order easy < normal < hard
```

The normal level reaches the requested 25–30% range. I did not run browser-game tests or main-line verification.
