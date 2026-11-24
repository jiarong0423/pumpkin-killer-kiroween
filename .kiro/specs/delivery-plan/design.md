# Design: delivery plan (round 1)

## Overview

`docs/plan_v1.md` is the first plan for the remaining 18 working days. It was built from the work-breakdown outward: lanes, then work packages, then dates, then checkpoints. Only afterwards was it compared with `(not published)` and the build order in `docs/review_reconcile.md`. Round 2 (task 43b) is the main line's correction pass.

## Model

| Part | Rule |
|---|---|
| Calendar | Day 0 = 11-09. Working days 11-10 to 11-27 (18). 11-28 and 11-29 are submission days. 11-30 to 12-03 are unplanned reserve until the owner confirms the deadline. |
| Work package | One row, one owner, one verification. Effort S (up to 2 h), M (3 to 6 h), L (7 h or more). Owner can be several actors; main-line hours are counted separately. |
| Dependencies | Finish-to-start; same-day start allowed. The Colab queue is a chain: Run n+1 depends on Run n. |
| Critical path | Longest dependency chain by dates: WP06, WP12, WP17, WP22 and WP23, WP30, WP38, WP44, WP50, WP55, WP57, WP59, WP62. The art chain WP03, WP05, WP09, WP10 has 2 days of float. |
| Load | Main-line hours of each WP are spread evenly over its days. The daily sum is compared with an assumed 8 h/day. Peak 10.8 h on 11-18. |
| Cutline | MVP must ship. STRETCH goes first. The cut ladder (4 steps, 34.5 h) lists the next cuts. |
| Art cost | Images x 2 min + 5 min per run. 2 variants per job, 3 for backgrounds. 18-image rerun budget. |
| Gates | Owner windows OW1 to OW8 hold one-word questions. "cross" means an independent sub-agent check or a second pass. |

## Decisions made in the plan

| Decision | Reason |
|---|---|
| 1 v 1 with 7 classes; 2 v 2 behind a gate; no 4 v 4 | 4 v 4 adds about 44 h (hand estimate) to a plan that is already 8.2 h/day |
| Per-class HP table | `rules.md` lists 90, 85, 100, 120 for four classes; "all 100" would change a confirmed rule |
| AI landing-ledger learner | `product.md` forbids a simulator for the AI; the fix is about 20 lines per `docs/playtest_fixes.md` |
| Idle art first, one class per Colab run | Pose jobs use the approved idle as reference; the reaper is the cheapest class to integrate |
| i18n late but MVP | Judges read English; strings stay in flux until 11-22 |
| MCP parity early, agent demo 11-22 to 11-24 | Wind drift is the one known client/engine difference; the demo is the main Kiro-depth evidence |

## Open points for round 2

Main-line capacity per day; whether NEW1 images exist; the real deadline; the output of tasks 41 and 42; who presses Run on Colab.

## How to check the plan itself

1. Count rows: `grep -c '^| WP' docs/plan_v1.md` should give 62 table rows plus any rows quoted in text; the diagram must hold 62 `WPnn[` nodes.
2. For each row, the end date of every dependency must be on or before the row's start date.
3. Sum the main-line hours of the MVP rows (147.7) and compare with the load table.
4. Sum the Colab minutes of runs 1 to 6 (242) and of runs 7 to 9 (131).

These checks are manual; no script exists for them yet.
