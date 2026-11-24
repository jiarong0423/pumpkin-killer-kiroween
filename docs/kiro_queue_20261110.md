# Kiro work queue (planned 2026-11-10 night; replaces the first 6-step list)

Rules: everything except picture generation is Kiro's by default (owner 2026-11-10); the main line orchestrates, re-runs every check, merges. At most 3 Kiro tasks at the same time (6 terminal tabs, Terra throttles). One writer per file: tasks that edit index.html run one after another, each in its own git worktree, merged by the main line. Models: Terra (`--route codex` or `design`) writes code, scripts, tests and art prompts; Sonnet (`--route flow`) writes plans, specs, docs, the write-up.  Deadline: submission closes Dec 5 06:00 Taiwan; freeze plan Nov 27.

## Wave A: start now, independent of each other (any 3 at once)
| id | task | model | edits | why it matters | done when (main line runs it) |
|---|---|---|---|---|---|
| A1 | task 81: start screen + name input wired into the page | Terra | index.html (worktree) | Design score, finishes finished-but-unwired module ((not published), 48 tests) | `node (not published)` and all node tests; screenshot of the start screen |
| A2 | Property-based tests for the rules and the engine (properties: same seed + same actions = same result; HP never negative; damage never above the cap; a unit never leaves its zone; the wall never goes below 0) in `scripts/test_properties.js` and `(not published)` with a small seeded generator | Terra | scripts/ only | Technological Implementation names property-based testing; the spec .kiro/specs/physics-pbt exists but no such test does | both scripts pass; a deliberately broken rule makes one fail (the main line checks that) |
| A3 | Kiro-native evidence: create `.kiro/agents/daily-logger.json`; fix the no-op hook (test-rig-on-save points at files that do not exist) and the stale text of the constants hook; add two useful hooks (run test_properties on save of js/*.js; run make_kiro_ledger on a new docs/kiro_*_result file); add one steering file `.kiro/steering/prompt_engineering.md` from docs/PROMPT_LOG.md; write `docs/kiro_evidence/README.md` explaining how to produce hook logs | Sonnet | .kiro/, docs/kiro_evidence/ | hooks, agents, steering are write-up topics; Kiro 83 found most of them unevidenced | `ls .kiro/agents .kiro/hooks`; JSON/hook files parse; the owner then saves a file in Kiro once and the main line keeps the output (needs the owner, 5 minutes) |
| A4 | Coin toss module `(not published)`: caller picks heads (人頭) or tails (字), the seed is created after the call, flip result from a seeded RNG, golden-vector tests; no DOM | Terra | js/, scripts/ | opening rule decided today; pure module, testable | `node (not published)`; same call and seed give the same result in node and in the browser console |

## Multiplayer MCP is Kiro's (owner 2026-11-10: "the multiplayer MCP should be given to him, shouldn't it?")
Yes. The multiplayer chain is entirely Kiro's: B2 relay (moved up: it depends on nothing, start it in wave A when a slot is free), B3 MCP channel with seats and the fairness / cannot-bypass tests, and C4 the lobby. Sonnet writes the MCP channel spec now (protocol of the messages: join_room, call_coin, submit_action, end_turn, get_public_view, your_turn notification; seat tokens; rate limits) so that Terra can build B2 and B3 in parallel with the rules core B1; the main line only verifies and merges. This is also the part judges can see as "MCP": a real multiplayer use, not a demo.

## Random rooms (owner 2026-11-10: "later there is also MCP random rooms")
Besides invitation codes, a player or an agent can join a RANDOM room: A5 relay gets `quick_match` (an open room waiting for a second seat, matched in order of arrival, in memory, expiry after a few minutes), B3 MCP channel gets the tool `join_random_room` next to `join_room(code)`, and C4 lobby gets a "random match" button. Rules to keep: a seat is an agent or a human chosen by whoever sits there; the coin toss and seed handshake are the same as for invitation rooms; no matchmaking beyond arrival order (no concurrency concern, decision 12). Sonnet's MCP channel spec must list both.

## Wave B: the architecture (after wave A is merged)
| id | task | model | edits | depends on | done when |
|---|---|---|---|---|---|
| B1 | Deterministic rules core `(not published)` (state, turn flow with coin toss, damage with overlap order, splash bands, statuses, seeded RNG) following docs/kiro_76_4v4_plan_*.md (OWNER CORRECTIONS and KIRO 76 ANSWERS first) and docs/owner_decisions_20261110_agents_headless.md; no DOM; golden vectors from the plan's worked examples (3 units in a line; 4 enemies at 60, 140, 220, 300 px) | Terra (Sonnet reviews the diff against the plan) | js/, scripts/ | A2, A4 | `node (not published)` reproduces the plan's numbers; a replay of 300 random matches is identical twice |
| B2 | Relay server `relay/server.js` (Node `ws`): random 6-character invitation codes, in-memory rooms, ordered action broadcast, call/seed handshake, message-size and rate limits, room expiry, `/health`, Dockerfile for Coolify, env-var config, no secrets | Terra | relay/ | none | its tests pass (two clients, 50 ordered messages, flood and oversize refused); `docker build` if Docker exists, else the Dockerfile is reviewed only |
| B3 | MCP channel for the new design: a thin per-device adapter that exposes only a seat's public view and accepts seat actions, talking to rules_core; the fairness and "cannot bypass the rules" tests from docs/kiro_75_mcp_plan_* | Sonnet spec, Terra code | scripts/, js/ | B1 | new tests pass; the existing 23 stdio tests still pass |

## Wave C: the game body (sequential, each in a worktree; index.html has one writer at a time)
| id | task | model | depends on |
|---|---|---|---|
| C1 | Pose animation `(not published)` (356 lines, test passes in ../pumpkin-killer_kiro67) wired into the pose drawing | Terra | A1 merged |
| C2 | Kiro 58/60 remaining patches: exit from move/defend, touch targets 44 px, HUD font sizes, power meter on the thrower, help text, reset confirm; phone layout (landscape) | Terra | C1 |
| C3 | 4v4 step S1 of the plan (units array with aliases, behaviour unchanged), then S2 to S7 one per task | Terra, Sonnet reviews | B1 |
| C4 | Lobby page (create room, show code, join by code, choose seat controller, coin toss with the pumpkin coin animation) | Terra | B2, B1, coin art from the main line |
| C5 | Sounds for the missing events (frost, stun, bleed, ultimates, new classes; three missing files): synthesised by a script or CC0 files listed in assets/audio/CREDITS.md | Terra | none (can run in wave A if a slot is free) |

## Wave D: the submission package (Sonnet writes, the owner publishes)
| id | task | model | needs the owner |
|---|---|---|---|
| D1 | English README, Devpost text description, and the Kiro-usage write-up with the 8 topics of the rules (IDE/CLI/Web/Crew, agents, hooks, specs vs vibe coding, steering, MCP, PBT, powers), each claim with a file path, built from docs/KIRO_LEDGER.md and docs/kiro_evidence_20261110.md after the main line verifies it | Sonnet | review for honesty (who wrote what) |
| D2 | 3-minute video script and shot list (outline in .kiro/specs/judging-fit): result first, live match, bring-your-own-agent, Kiro evidence, close; no copyrighted music | Sonnet | recording and YouTube upload |
| D3 | Blog post draft (public, says it is for Kiroween 2026) and the social post (starts with #KiroweenHackathon26) | Sonnet | publishing |
| D4 | Pre-submit checklist run against (not published) and the live rules page | Sonnet | final decision |

## Wave E: detail polish and optimisation (owner 2026-11-10: "fonts are his too, tomorrow he adjusts many details and optimises")
Fonts are Kiro's (tasks 48 and 49: scripts/build_fonts.py, css/fonts.css, assets/fonts: Cinzel Decorative Bold unmodified, Noto Sans TC 400 and 700 subsets as "PK Body" about 316 KB each, Noto Serif TC 900 subset as "PK Display CJK"; all SIL OFL with licence files). Facts the next task must start from: the font files, build_info.json, charset.txt and README under assets/fonts are MODIFIED AND UNCOMMITTED in git today (rebuilt by someone, not reviewed); the subsets cannot draw an arbitrary Chinese player name from the new name input.
| id | task | model | edits | done when (main line runs it) |
|---|---|---|---|---|
| E1 | Fonts pass: rebuild the subsets from a charset that is generated from every string in index.html, js/*.js and the new lobby/start-screen text; fix the name-input case (what a typed name uses when a glyph is missing: a consistent fallback and a test); wait for `document.fonts.ready` before the first canvas draw; add the two body fonts to the preload block (scripts/make_preload_links.py); size budget under 1.2 MB total; keep licences | Terra | assets/fonts, css/fonts.css, scripts/build_fonts.py, scripts/make_preload_links.py | `python3 -B scripts/build_fonts.py` reproducible; every glyph used in the game renders (a test that scans the strings against charset.txt); page loads with no console error |
| E2 | Detail pass on the HUD and dock from the existing reviews (docs/kiro_70_review_*, docs/kiro_58_recommendations.md, (not published)): small labels and diamonds about 25 percent larger, padding between round/timer/banner content, supply slots readable, dock right end used, HUD font size tiers for phone width, text contrast; list each change with before/after screenshots | Terra | index.html, css/*.css (worktree, after A1 and C1) | overlap check of canvas and DOM rectangles at 3 widths (new script), screenshots reviewed by the main line |
| E3 | Optimisation pass: frame-time budget with a measurement script; cache static layers (background plus fixed coffins) in an offscreen canvas; cap devicePixelRatio; extend the tint cache; particle budget from the 4v4 plan section 11; measure before and after | Terra | index.html, scripts/ | a browser or headless measurement reports average and 95th percentile frame time for 1v1 and 8 units; no visual change (screenshot diff) |
| E4 | Framework pass (owner: "fonts or the whole framework"): split index.html into modules along the plan (rules, state, rendering, input, agents, data) keeping behaviour identical; each step a worktree, the replay test from B1 as the safety net | Terra, Sonnet reviews | index.html, js/ | after B1; every step keeps all node tests and the 1v1 replay identical |
Order: E1 first (the start screen and lobby add text), then E2 and E3 after the page work of wave C settles; each edit of index.html in its own worktree, one at a time.

## Evidence layer additions (after the Kiro 83 check, 2026-11-10 night)
Kiro 83's file is accurate (every spot check true) and itself says what is missing. The judges only see what is pushed: origin/main is ea39931 and the local main is 192 commits ahead; 66 kiro/* branches and all evidence docs are local. So:
| id | task | model | note |
|---|---|---|---|
| A6 | Judge's guide at the repo root (`JUDGES.md`): one page, ordered by the eight write-up topics of the rules, each with the path to the evidence and the command that reproduces it | Sonnet | after A3 |
| A7 | Raw evidence: save the REAL output (not a summary) of each check under `docs/kiro_evidence/raw/` (test runs from `scripts/end_of_day.py --apply`, hook run output, agents rules-reviewer and asset-inventory output, an MCP session transcript, `git worktree list`) | Sonnet writes the script/steps, the main line and the owner run them | needs the owner for the Kiro IDE hook run |
| A8 | Commit convention for Kiro work: a trailer line `Kiro-Task: NN (model, brief, result file)` in each commit message (NOT a Co-Authored-By trailer: the owner's rule for public repos); a short script that lists commits by that trailer into `(not published)` | Terra | owner decides when to push |

## Fresh public repository: who does what (owner 2026-11-10)
- Task 84 (Sonnet, running): the release design (manifest, privacy gate, history strategy, layout, owner-only steps).
- Task 85 (Terra, after 84): `(not published)`, `(not published)`, the commit messages with `Kiro-Task:` trailers (true attribution only, no Co-Authored-By), the final-commit checklist.
- Limits stated plainly: Kiro CLI runs have had no shell, so the main line executes every `git` command; Kiro writes the scripts and messages and the main line verifies them; pushing and creating the repository are the owner's steps.

## Found in the official Kiro docs (2026-11-10, (not published))
| id | task | model | note |
|---|---|---|---|
| A3 (updated) | Keep the three IDE-format hooks and ADD v1 JSON hooks (`(not published)`, trigger PostFileSave, matcher regex, action command) so the CLI can fire them; run one from the Kiro CLI and save the output under docs/kiro_evidence/raw/ | Sonnet writes, main line runs | our `.kiro.hook` files are the older IDE format, which CLI runs do not read (CLI loading of the v1 files is UNVERIFIED) |
| A9 | A Kiro power `pumpkin-killer-seat` (plugin.json with activation keywords, mcp.json for our MCP channel, skills/play/SKILL.md for how an agent joins and plays fairly); install it from the local folder and use it once in a real session | Sonnet spec, Terra files | after the MCP channel spec; evidence for the "powers" and "MCP" topics |
| A10 | Optional custom agent `committer` with permissions allow `git status*`, `git diff*`, `git add *`, `git commit *`, `git log*` and deny `git push *`, `git remote *`, `git config *`, `rm -rf *`, `sudo *`, limited to the release folder | Terra | only if the owner authorises it |

## Configured on 2026-11-10 night (owner: "set up what should be set; I think we did not set it up well")
Files created or changed in the project (all local, nothing run through the Kiro CLI yet, so loading by the CLI is UNVERIFIED):
- `.kiro/agents/daily-logger.json` (task 78 asked for it): may write only docs/daily/ and docs/PROGRESS_TABLE.md, may run only (not published)
- `.kiro/agents/committer.json` (queue A10): local git only (status, diff, add, commit, log, show); push, remote, config, reset, checkout, clean, rm -rf, sudo, network are denied. NOT to be used until the owner authorises it.
- `(not published)` (v1 schema, three PostFileSave hooks): preload block fresh on index.html save; constants sync on engine or constants save; ledger on a saved Kiro result file. Each appends to (not published) One command was dry-run by hand: it works and it caught a real stale block (the new wind picture made the preload list 22, the block had 21); fixed with `make_preload_links.py --apply`.
- `.kiro/steering/prompt_engineering.md` (fileMatch steering from docs/PROMPT_LOG.md).
- `.kiro/powers/pumpkin-killer-seat/` (plugin.json, mcp.json, skills/play/SKILL.md): a DRAFT power; the room tools come with queue B3.
Account-level settings that only the owner can change in the Kiro app (not files): Model fallback, Tool approval, Memory, Cloud config, installing marketplace powers.

## Kiro Web with GitHub (found by the owner, 2026-11-10; owner decisions needed before use)
| id | task | who | note |
|---|---|---|---|
| A11 | After the fresh public repository exists: install the Kiro Agent GitHub app on that repository only, create issues for chosen tasks (for example A1 start screen, C2 patches, E1 fonts, D1 README draft) with the `kiro` label, let the Kiro Web agent open PRs; the main line reviews each PR (diff, tests) and the owner merges | owner (installs the app, merges), Kiro Web (code), main line (review) | gives real Kiro commits, PRs and issue threads as evidence for the "IDE/CLI/Web/Crew" and "custom agents" topics |
| A12 | One autonomous-mode task on a well-defined, low-risk job (for example "write property tests for (not published)") to document how Web autonomous mode differs from the CLI | Kiro Web | keep the PR and the task view as evidence |
Decisions for the owner: (a) accept Kiro's automatic co-author trailers in THIS repository (the Kiroween rules do not ask for a sole creator; the earlier no-co-author rule came from another contest), (b) grant the Kiro Agent GitHub app access to the new repository only, (c) credits budget for Web tasks. **DECIDED 2026-11-10 (owner, revised): Kiro's automatic co-author commits ARE accepted (the contest is about showing Kiro usage). Keep `Kiro-Task:` trailers for CLI work (tasks 84, 85); Claude Code adds NO Co-Authored-By in this repository. A11/A12 are active once the owner connects the Kiro Agent GitHub app to the new public repository only (owner click).**

## Tomorrow (2026-11-11): research Kiro powers / plugins (owner request)
- Read (not published) and kiro_features_20261110.md first.
- Open Kiro Web > Agent Config > Powers marketplace; for each candidate (Context7, Local Long-Term Memory, Build a Power, Nova Act, Postman, others) write: what it does, free or paid, needs an account or key, what it adds for Pumpkin Killer, risk. Owner decides what to install; install nothing without a yes.
- Check whether the CLI loads `.kiro/powers/pumpkin-killer-seat/` and `(not published)` (docs/kiro_evidence/raw/hook_runs.log).
- Output: (not published), then one plain-Chinese summary.

## Not Kiro's
Picture generation (Colab/Qwen, run by the main line); merging into the main project; git commits; anything that touches the cloud, deploys or pushes (owner only).

## Suggested order for the next days
Day 1: A1, A2, A3 (3 at once); the MCP channel spec (Sonnet) and B2 relay (Terra) as soon as a slot is free. Day 2: A4, C5, then merge and start C1. Days 3 to 5: B1 with B2 in parallel, then B3. Days 5 to 9: C2, C3 steps, C4. By Nov 27: freeze; D1 to D4 drafted from Nov 20 so the video can be recorded.
