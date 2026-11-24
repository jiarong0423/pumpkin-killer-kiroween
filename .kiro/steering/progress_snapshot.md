---
inclusion: always
---
# Progress snapshot — 2026-11-15

Read `docs/PROGRESS_SNAPSHOT_20261115.md` before planning new work. It is the current file-based inventory. Read the diagrams below for system and delivery dependencies.

## Current state

The project is in **single-match game (current)**. The page has five playable profiles: Skeleton, Wizard, Bat, Pumpkin Guard, and Necromancer (`reaper`). The page marks Bat, Skeleton, Wizard, and Necromancer ultimate-built. Knight ultimate page wiring, AI-level page wiring, English page wiring, release gates, public URL, and video remain open.

## Ranked gaps

1. **Stage 1 and Presentation:** owner deployment and live smoke test, B03.
2. **Stage 1:** main-line export privacy gate, clean checkout, private push, and owner Public action, B10–B11.
3. **Stage 1 and Presentation:** owner video recording/upload, B16.
4. **Stage 1 and Design:** English UI is applied to `index.html` (106 edits, 26 i18n checks pass, 2026-11-15) but not yet viewed in a browser, and the English text is a machine draft that needs owner approval, B09. The main line owns `index.html` changes.
5. **Technology and Innovation:** MCP line (main line owns it, Kiro builds): the Opus review `docs/mcp_architecture_opus_20261115.md` found no seat identity, public enemy aim/shield/acted, unsafe `end_turn` retries. Build list K1 to K8, track diagram `docs/overview/mcp_track_20261115.mmd`; K1 (seats and per-seat views, task 145) is IN PROGRESS, K2 to K8 wait for K1 to be verified (all edit `scripts/mcp_stdio_server.py`: one writer at a time). IDE MCP evidence is incomplete; Web/Crew evidence has not started, B01–B02 and B12.
6. **Design and Innovation:** Knight ultimate and agent-level modules exist but need page wiring, B04–B05.
7. **Design:** four page image references and three audio references are missing; the Colab run (14 pictures, queue `colab/jobs_queue_all_20261115.json`) has produced nothing yet: the L4 ran out of RAM twice, the notebook was changed to the 4-step Lightning LoRA and a lower-memory load, and the run is on hold; the owner spot-checks the first pictures, B07–B08.
8. **Design:** Bride, Hunchback, and Apple Hag are not playable, B21. The one-writer `index.html` lane limits this work.

## Do not touch

- Do not reopen frozen B19 (4 vs 4).
- Do not overlap any `index.html` edit or IDE save with its single writer.
- Only the owner may run Colab, deploy, set repository visibility, upload video, submit Devpost, redeem credits, or publish personal posts.
- Do not call external APIs, push, deploy, change remotes, generate pictures with code, or place private values, credit balances, or personal names in public files.

## Pointers

- Inventory and sources: `docs/PROGRESS_SNAPSHOT_20261115.md`
- Architecture: `docs/overview/architecture_20261115.mmd`
- Delivery state machine: `docs/overview/state_20261115.mmd`
- Main-line evidence only: `docs/kiro_verified.json`

## Local MCP resources (read before any MCP or multiplayer task)
- `(not published)` holds copies of earlier local work so nothing starts from zero: reference-project rules and threat models, and `pumpkin-agents_prototype/` (an earlier fairness/engine/room prototype of this same game concept) and `shared-room_asymmetric/` (the earlier asymmetric multiplayer plan: up to four humans against four LLM subagents dispatched by a host, plus room and join code excerpts); read each folder's `_README_FOR_KIRO.md` first. The folder is git-ignored and never exported.
- The architecture review to follow: `docs/mcp_architecture_opus_20261115.md` (tasks K1 to K8).
