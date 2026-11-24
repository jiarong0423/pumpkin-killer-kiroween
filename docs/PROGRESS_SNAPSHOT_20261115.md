# Progress snapshot — 2026-11-15

This is a file-and-listing inventory. “Built” means present in the current page or main-line verification record, not a claim that a browser test was run here.

## Hero readiness

| Hero | Playable in page | Ultimate built | Art complete; missing frame or asset | Stats row |
|---|---|---|---|---|
| Skeleton Spearman | Yes | Yes | Yes; eight pose states use three accepted `skel_*` legacy names | Yes |
| Pumpkin Wizard | Yes | Yes | No; `wizard_release` | Yes |
| Bat-cat Assassin | Yes | Yes | Yes; eight pose states present | Yes |
| Pumpkin Guard | Yes | No; module exists but page wiring is open | No; `unit_knight_unarmed` | Yes |
| Necromancer (`reaper`) | Yes | Yes; page lists `reaper` in `ULT_BUILT` | No; `necro_ult_point`, `necro_idle2`, `necro_charge2` | Yes |
| Ghost Bride | No | No | Yes; eight pose states, ring and swarm files present | Yes |
| Bell-tower Hunchback | No | No | Yes; eight pose states and axe sprite present | Yes |
| Apple Hag | No | No | No; `hag_idle1`, `hag_idle2`, `hag_charge1`, `hag_charge2`, `hag_charge3`, `hag_release`, `hag_empty`, `hag_hit` | No |

Sources: `index.html` `HERO_PROFILES`/`ULT_BUILT`/`COMING_HEROES`; `docs/character_gap_matrix_20261115.md`; `assets/poses/`, `assets/units/`, `assets/fx/sprites/` listings; `docs/hero_stats_table_20261115.md`. The page has five profiles and only Bride/Hunchback in `COMING_HEROES`; the Hag is not yet page data.

## Stage-1 contest requirements

| Requirement | Status | Blocking item |
|---|---|---|
| Public GitHub repository | Gap | B10 gate and B11 private push; owner must set Public |
| Working public URL | Gap | B03 owner ingress/deploy and live smoke test |
| Public video under 3 minutes | Gap | B16 begins after URL and freeze |
| English text/materials | Gap | B09 is unwired; page still has Chinese strings |
| New-project disclosure | Partly | B14 needs main-line review of pre-2026-10-30 items |
| MIT licence | Partly | `LICENSE` exists; B11 owner still checks GitHub About |
| `.kiro` present and not ignored | Partly | directory exists; B10 export recheck still required |

Sources: `docs/SCORING_ALIGNMENT_20261115.md`, `docs/WORK_QUEUE_20261115.md`, `docs/DISPATCH_BOARD_20261115.md`, `LICENSE` listing.

## Ranked open gaps

Stage 1 is pass/fail; the five Stage-2 criteria are 20% each (`docs/SCORING_ALIGNMENT_20261115.md`).

| Priority / judging effect | Gap and factual status | Owner | Block |
|---|---|---|---|
| 1, Stage 1 and Presentation | No public URL; deploy files and smoke test exist, but deployment is owner-held | owner-only, main line smoke | B03 |
| 2, Stage 1 | Export gate has 68 P13 blocks in newest log; re-export/gate and clean checkout remain | main line | B10, B11 |
| 3, Stage 1 and Presentation | No video; it depends on URL and range freeze | owner-only | B16 |
| 4, Stage 1 and Design | English page is not wired; main-line record says 153 mapped strings but page wiring is absent | Kiro CLI, then main line page writer | B09 |
| 5, Technology | IDE hook evidence exists but MCP panel attempt failed; Web/Crew evidence has not started | owner-only, main line | B01, B02, B12 |
| 6, Design and Innovation | Knight ultimate and page AI-level wiring remain open; modules/tests exist but are not page-wired | Kiro CLI, main line page writer | B04, B05 |
| 7, Design | Four literal picture references and three sound references are missing; Colab is held by owner | owner-only; Kiro CLI may drop sound refs | B07, B08 |
| 8, Design | Bride, Hunchback and Hag are not playable; one-page-writer lane is the constraint | Kiro CLI, main line page writer, owner art | B21 |
| 9, Innovation | 4 vs 4 is frozen and must not reopen before higher-priority blocks complete | no owner assigned | B19 |

Sources: `docs/DISPATCH_BOARD_20261115.md`, `docs/kiro_verified.json`, `(not published)`, `docs/character_gap_matrix_20261115.md`.

## Colab state

- `colab/jobs_queue_all_20261115.json` contains 14 queued definitions; the 2026-11-15 handoff says the Q3 runner waits for owner Drive-mount consent. Source: `colab/jobs_queue_all_20261115.json`, `(not published)`.
- Separate run sheets describe 8 character jobs, 14 Hag jobs, 8 missing-picture jobs, and 4 scene jobs. They are separate queues with overlapping/alternative work, so they must not be summed as one run. Sources: `docs/colab_*_run_20261115.md`.
- Installed outputs include Bride and Hunchback eight-frame pose sets; Necromancer legacy/new pose files and purple flame sprites; Bride ring/swarm; Hunchback axe sprite; and the graveyard scene. Sources: `assets/poses/`, `assets/fx/sprites/`, `assets/env/` listings.
- Missing page art remains `bg_belltower.png`, `bg_pumpkin_field.png`, `fx_feet_chain.png`, and `unit_knight_unarmed.png`. Missing character-job outputs include the Hag set and Necromancer pointing pose. Source: `docs/character_gap_matrix_20261115.md`.

## Do not touch

- B19 4 vs 4 is frozen. The live page is the 1 vs 1 prototype. Source: `docs/WORK_QUEUE_20261115.md`.
- `index.html` has one writer. Kiro tasks and IDE saves must not overlap with that lane. Source: `docs/DISPATCH_BOARD_20261115.md`.
- Only the owner may run Colab, deploy/ingress, set repository visibility, upload video, submit Devpost, redeem credits, or publish personal posts. Source: `.kiro/steering/team_plan.md`.
- Do not call external APIs, push, deploy, change remotes, generate pictures with code, or put private values, credit balances, or personal names in public files. Source: task 140 and `.kiro/steering/team_plan.md`.

## Spec and verification note

All available `.kiro/specs/*/tasks.md` files were read. `core-throw-loop/tasks.md` is absent. Their checkbox records are planning state only; `docs/kiro_verified.json` remains the main-line evidence source. The shell request to count every checkbox and detect Mermaid tooling was not granted, so no derived aggregate count is asserted here.
