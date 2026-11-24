# Phase 2 (started 2026-11-15): concept art first, then a Kiro spec, then Kiro builds

Real order of work, with real dates. Nothing here is back-dated and nothing replaces the earlier history.

## Scope (default; the owner may change it before step 1)
The opening flow of the game: (1) start screen with name entry, (2) coin-toss opening (pumpkin coin decides who goes first), (3) seat selection (agent / human / built-in AI).
Existing code for these parts is in `index.html` and `docs/kiro_queue_20261110.md` items A1 and the coin toss; Kiro decides in its spec what is kept and what is rebuilt.

## Step 1 — owner: concept images from Codex (real tool, real date)
Make 3 concept images, one per screen above, in the game's existing look (dark purple graveyard, pumpkin accents; see `docs/art_style_guide.md`). Save them in `(not published)`:
- `01_start_screen.png`
- `02_coin_toss.png`
- `03_seat_selection.png`
Then add one row per image to `docs/phase2/CONCEPTS.md`: file, tool name, date made, the prompt you used (paste it), and one sentence of what to keep. If a tool other than Codex was used, write that tool's name instead. Do not rename tools to look different.

## Step 2 — Kiro: write the spec from the concepts
Run task 91 (`docs/kiro_task_91_phase2_spec.md`). It stops if `(not published)` is empty. Output: `(not published)` (requirements, design, tasks).

## Step 3 — Kiro: build from the spec, one task at a time
Main line writes one narrow brief per spec task, runs it through `scripts/kiro_route.py`, reruns the tests, and records the result in `docs/kiro_verified.json`. Commits carry the real date and a `Kiro-Task:` trailer only for work Kiro really did.

## Not part of this phase
Changing or hiding the earlier history. The release package (spec `release-package`) continues in parallel; its privacy gate applies to this phase's files too.
