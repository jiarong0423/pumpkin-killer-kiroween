---
inclusion: always
---
# How work is assigned to Kiro and how it is recorded (owner 2026-11-10: Kiro's work must be effectively recorded and assigned)

1. Before any task read, in this order: `(not published)`, `docs/WORK_QUEUE_20261115.md`, `docs/PLAN_20261115.md`, then `docs/KIRO_LEDGER.md` (every task so far: who, status, what is merged, what the main line verified), and the brief you were given (`(not published)`).
2. Division: Sonnet (route `flow`) = game flow, systems, MCP, planning, logs. GPT/Terra (routes `design`, `codex`, `gpt`) = art design, image prompts, scripts. Every picture is made by Qwen only; never draw art with code.
3. One writer per file: the main line edits `index.html`. You work in the worktree you were given or write only the files your brief lists. Never merge, push, deploy or write to the cloud.
4. Every result goes in ONE file named in the brief (`(not published)` or the file the brief names). Put at the top: what changed (file and function names, not line numbers), the exact commands to verify it, and what you could NOT verify. Do not claim a test passed unless you ran it and quote its last lines.
5. Never reopen a decided rule: they live in `(not published)` and `docs/owner_decisions_20261110_agents_headless.md`. If a brief conflicts with them, say so in the result file and follow the decisions file.
6. The main line re-runs every check and records its own result in `docs/kiro_verified.json`; the ledger is regenerated with `python3 -B scripts/make_kiro_ledger.py --apply`. Your report is never counted as verification.
7. DEFAULT OWNERSHIP (owner 2026-11-10: "except generating pictures, it is not his"): Kiro does the work by default (code in a worktree, scripts, tests, specs, plans, logs, wiring, merges prepared as patches). The ONLY thing Kiro does not do is generate pictures: the main line runs Colab/Qwen. The main line orchestrates, verifies every result itself and does the final merge into the main project.
8. PROMPT ENGINEERING IS A DELIVERABLE (owner 2026-11-10): every art prompt you write must state its goal, the exact reference pictures (style first, identity second), the settings you recommend, and 3 checks the main line can measure; the main line records the run and its verdict in `docs/PROMPT_LOG.md` (what was asked, what came out, what we changed). Reuse the rules at the bottom of that file.
