---
inclusion: always
rewritten-by: Kiro, 2026-11-08
updated-by: Kiro task 18, to match the repo today
---

# Structure

## Where things live

| Path | Purpose |
|---|---|
| `index.html` | The playable game: markup, styles and the client JS (rules, input, AI opponent, drawing). |
| `js/particles.js`, `js/particles_draw.js` | Seeded particle system and its canvas drawing. Loaded by `index.html`. |
| `shared/constants.json` | Ten numbers shared by the client and the engine. |
| `scripts/mcp_game_server.py` | Python rule engine. |
| `scripts/mcp_stdio_server.py` | Standard MCP server over stdio. Wraps the engine. |
| `scripts/test_mcp_game.py`, `test_mcp_stdio.py`, `test_constants_sync.py`, `test_particles.js` | The tests. Run commands are in `tech.md`. |
| `scripts/eval_agent_learning.py` | Learning-curve check for a history-only agent. Not a `test_*` runner. |
| `scripts/bake_*.py`, `make_*.py` | One-off asset and gif generators. Not runtime. |
| `scripts/key_magenta_items.py`, `key_skeleton_poses.py` | Key the magenta background out of Colab images. |
| `scripts/playtest_receiver.py` | Temporary local receiver for playtest frames, writes only into `(not published)`. Not runtime. |
| `assets/units/` | Character art, 1024 px, facing left (`unit_*.png`, `*_raw.png`, `*_unarmed.png`). |
| `assets/poses/` | Colab skeleton pose images (keyed). |
| `assets/weapons/` | Colab item images: small shield, dart, dart bag, spear (keyed). |
| `assets/ui/` | Colab shield slab images (keyed). |
| `assets/env/` | Background, ground, platforms, projectiles, fx images. |
| `assets/sprites/`, `assets/fx/` | Baked sprite sets and effect sheets (from `bake_*.py`). |
| `(not published)`, `colab/` | Inputs and jobs for Colab art generation. |
| `docs/game_mode.md` | Source of truth for confirmed rules. |
| `docs/mcp_agent_protocol.md` | MCP tools and fairness rules. |
| `docs/ASSET_PROVENANCE.md` | Where each art folder came from, and what is unknown. |
| `docs/ROLES.md` | Who does what, file locks, work queue. |
| `(not published)` | Notes for the contest write-up and video. |
| `docs/kiro_task_*.md` | Task briefs given to Kiro. |
| `.kiro/steering/` | Steering: product, tech, structure, rules. |
| `.kiro/specs/` | Specs: `asset-candidates`, `core-throw-loop`, `judging-fit`, `mcp-standard`, `particles`, `shared-constants`. |
| `.kiro/hooks/` | Save hooks that run the test scripts. |
| `.kiro/agents/` | Custom agents: `tester` (can write files and run test scripts), `rules-reviewer` and `asset-inventory` (read-only). |
| `.kiro/settings/mcp.json` | MCP client config for the `pumpkin-killer` server. |
| `HANDOFF*.md` | Session handoff notes from earlier work. |

Planned, not present yet: `(not published)`, `(not published)`, `(not published)`, `(not published)`,
`docs/object_inventory.md` (the `asset-inventory` agent stops if it is missing), `(not published)`.

## Branches and worktrees

- One branch per task, named `kiro/<name>` (for example `kiro/shared-constants`).
- One git worktree per branch, so parallel tasks do not share a working tree.
- Do not commit to `main` directly for feature work. Merge only after the tests for the touched area pass.

## Editing boundaries

- A task brief names the files it may touch. Stay inside that list.
- `docs/game_mode.md` and `.kiro/steering/rules.md` change only on the owner's instruction.
- Generated art in `assets/` is not edited by hand. Regenerate it with the scripts or the Colab job.
- `(not published)` is git-ignored; local agent-memory output goes there.
