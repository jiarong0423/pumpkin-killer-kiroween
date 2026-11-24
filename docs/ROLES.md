# Roles and work queue (decided 2026-11-08)

## Who does what
| Role | Does | Does NOT |
|---|---|---|
| **Main line (Claude Code)** | Orchestrates: writes the briefs, assigns work, integrates modules into `index.html`, re-runs every test itself, commits, reports to the owner in plain Chinese, drives the Colab browser UI, keeps this file current | Does not trust a sub-agent or Kiro summary as proof; no push/merge/cloud write without the owner |
| **Sub-agents (Claude Agent tool)** | Read-only helpers: heartbeat watchers of Kiro terminals (haiku), independent reviewers (rules vs diff, asset inventory), web research | No implementation, no edits, no git |
| **Kiro CLI** | **Owns the gameplay-experience DESIGN (owner decision 2026-11-09)**: turn flow, feedback and game feel, **particle and visual effects design (what plays when, how strong, the clean-screen budget)**, onboarding, pacing, per-class feel, demo moments; writes proposals in `docs/experience_design.md` + `.kiro/specs/gameplay-experience/`. Also implements code modules, specs, steering, hooks, custom agents, tests, i18n, responsive layout, MCP server (in its own worktree branch `kiro/<name>`) | No image generation, cannot run shell/tests, no git |
| **Colab (Qwen-Image-Edit)** | All image generation (weapons, poses, shield bar, portraits) | Nothing else |
| **Owner** | Rule decisions, approvals (merge, push, cloud sync, secrets), Drive uploads, final art choice | |

## Locks (one writer per file)
- `index.html`: one owner at a time. Order: Kiro i18n (08) -> Kiro responsive layout (09) -> main-line integrations (particles, rig, MCP wiring). The main line does not edit it while a Kiro task holds it.
- `scripts/mcp_game_server.py`: Kiro 07 only until merged.

## Queue (owner order, 2026-11-08: finish DESKTOP first, then the MOBILE landscape full-screen version)

### Phase A - desktop version (gate: "desktop done" checklist below)
1. [Main] touch pointer events - DONE (kept, harmless on desktop)
2. [Kiro 08] bilingual zh-TW / en mapping - RUNNING, holds `index.html`
3. [Kiro 06] particles module - RUNNING -> [Main] integrates after 08 is merged
4. [Kiro 07] standard MCP server + learning-curve eval - RUNNING -> [Main] verifies
5. [Colab] first tier of images (25 jobs) - RUNNING -> [Main] chroma-key, QA, integrate with the rig (Kiro 02)
6. [Main] desktop polish after 08 merges: remove the permanent tutorial box (3-step first-run hint), aim info (wind arrow, dashed arc, landing ring), attacker "big head" cut-in in the bottom bar, sounds (CC0)
7. [Kiro 10] 4 vs 4 mode - after the owner confirms the round flow (not needed for the first desktop gate)

Desktop done = bilingual, particles integrated, final art for weapons/poses/shield bar in, first-run hint, aim info, cut-in, MCP opponent mode works, all tests green, 10-minute playthrough without a stuck state.

### Phase B - mobile version (starts only after the desktop gate)
Landscape, full screen: canvas fills the whole viewport (no border/16:9 letterbox frame), Fullscreen API on first tap and `screen.orientation.lock("landscape")`
where supported (iOS Safari has no lock: show a "rotate your phone" hint in portrait), safe-area insets, HUD and dock scaled to the viewport height with >= 44 px
touch targets, thumb zones (charge/throw on the right, angle and actions on the left), hide the address bar (`viewport-fit=cover`, `100dvh`).
8. [Kiro 09] responsive landscape full-screen layout and touch UI - after the desktop gate
9. [Main] real-phone test (adb flow from the owner's phone notes) + fixes

- Later: [Kiro 11] agent memory storage (`(not published)`) after 07.

## Review loop for the design proposal (owner request)
1. [Kiro 13] writes `(not published)` + `(not published)` (RUNNING; it may not have seen the owner's later decisions).
2. [Main] when it finishes: verify the files exist, then write `(not published)` = the owner's confirmed rules since the task started
   (move step 36 px, airdrops into a single slot that replaces, per-class ultimate triggers, double-shot energy bar, hidden path lines) and mark which proposed mechanics conflict with them.
3. [Kiro 14] second pass: reviews the proposal against the decisions file and `docs/game_mode.md` -> `(not published)` (conflicts, feasibility, test strategy, what to cut, final recommended minimum set).
4. [Main] verifies, then summarises for the owner in plain Chinese with one-word questions.
