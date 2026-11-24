# Production efficiency: what cost time today, and the fixes (2026-11-09)

Source: this session's own record (no outside research). Times are estimates from the tool timestamps; not a measured benchmark.

## Where time was lost

| # | Loss | Evidence today | Fix |
|---|---|---|---|
| 1 | Colab batch run with an untested prompt style | Hunchback poses: 4 images, about 8 minutes, all identical to the idle picture. Reaper r8 had two heads (one run lost), r9 needed a third run | Smoke test: ONE image first with the new prompt style, look at it, then queue the batch. Prompt style that works: an edit instruction ("Edit this image: remove X, change the pose to Y"), not a description of a new picture |
| 2 | Model reloaded for every run | Each run starts with about 1 minute of loading (7 runs today) | Keep `pipe` in memory: add a second small cell that only sets ONLY / TAG / jobs and calls the same loop; reload only when the model changes |
| 3 | The page and Colab both need the foreground tab | The 12-match run stalled when the Colab tab was fronted; the Colab session dropped twice | Run balance and AI checks in Node (scripts/sim_ai_nosim.js style), keep the browser for visual checks only; never front Colab while a browser test runs |
| 4 | Building before the owner confirmed | Skeleton and wizard ultimates written, then removed (one round lost); three ghost-fire colour changes | Rule: owner fragments go straight into (not published); code starts only on a clear 'do it' or when the reading is unambiguous; ask ONE question when two readings exist |
| 5 | Kiro outputs not merged | Tasks 46, 47, 50, 52, 54, 55 are finished in their worktrees and not yet integrated | A weekly integration block: read, re-run tests, merge one Kiro result at a time, commit; never start a seventh task before merging |
| 6 | Kiro throttling | Task 53 failed ('high traffic') | Retry once, then switch model; keep at most 3 tasks running at once |
| 7 | Polling | Many screenshot and wait calls | One long wait, then one check; the harness result is read from window state, not screenshots |

## Capacity plan to 2026-12-04 (25 days)

Order by value for the judges, smallest first:
1. Finish what is half done: necromancer art (9 new pictures to review), unit art wiring for hunchback and necromancer, sky target (Kiro 52), strength retune (Kiro 55).
2. Ultimates one class at a time after the rules are confirmed (skeleton, wizard, then knight A-B-C, necromancer).
3. Scenes (bell tower, pumpkin field) and terrain only if the first two are done by 11-27.
4. Freeze 11-27: README, run instructions, asset provenance, demo recording.

Per class, the repeatable pipeline: rule row in the log, Kiro numbers, Colab art (smoke test first), code, Node check, browser check, commit.
