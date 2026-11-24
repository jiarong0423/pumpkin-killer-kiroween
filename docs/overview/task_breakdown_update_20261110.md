# Task breakdown update (main line review of Kiro 77, 2026-11-10)

Kiro 77 was written before several owner decisions of the same day. Where this file and docs/overview/task_breakdown.md disagree, THIS FILE WINS. Sources: docs/owner_decisions_20261110_agents_headless.md (items 1 to 12), (not published) section 零.

## Rows to change
| row | change | why |
|---|---|---|
| R03 | The rules module must be DETERMINISTIC (seeded RNG, fixed step, no Math.random/Date in rules), runs under node, and is the ONLY rules authority; the same module runs in every browser and in an agent's local process | decisions 9 and 10 |
| R04 | Same, plus first-side coin toss with call (heads 人頭 / tails 字) drawn from a seed the relay creates AFTER the call | coin decision |
| R14 to R17 | Controllers per unit stay; the MCP server is a THIN per-device channel (observations out, actions in) that talks to the local rules module, not a shared match host and not a rules authority | decision 10 |
| R16 | Rename: "MCP channel serves the seat's public view and accepts seat actions"; the Python engine is one fixed headless mode kept aligned with the page (wall 8 and positions done by Kiro 80) | decisions 10, 11 |
| R18 | Keep (hidden fields, rate limit, writes only to scratch, no secrets) and add the "agents operate like humans, cannot bypass the rules" tests (illegal action, out of turn, hidden-state read, other seat's unit) | decision 8 Q3 |
| R20 | Wind ghost = FOUR frames of ONE continuous motion by chain generation (each frame edited from the previous one); the 8-cell loop is cancelled | owner |
| R21 | Chain picture stays | owner |
| R23 | CANCELLED: both coffins use the purple art; the left is colour-turned | owner |
| R24 | Not needed: Kiro 73 found the three fence states clearly different; check by eye once | Kiro 73 |
| R25 | Only the bat front portrait now; necromancer portrait deferred | cut |
| R26 | DEFERRED until the class is playable | cut |
| R27 | DEFERRED (the picker shows both scenes greyed as "in the making") | cut |
| R28 | Keep: knight empty hands, wizard release, skeleton charge MID | cut |
| R30 to R32, R34 | DEFERRED to after the four-class 4v4 works; teams are exactly skeleton, wizard, bat, knight (each class once per team) | owner Q4 |
| R33 | Keep (knight A-B-C), plain Defend stays | owner |
| R38 | Keep, plus "units do not die too fast": hits-to-kill 4 to 6, hit-rate target 25 to 30 percent | owner Q5, Q7 |
| every task naming image2 or ChatGPT/Codex | read as QWEN (Colab single pictures, or the owner pasting into the Qwen chat) | owner |

## Rows to add
| id | task | owner role | size | done-when |
|---|---|---|---|---|
| R41 | Tiny relay server (one Node file, `ws`): random 6-character invitation codes, in-memory rooms, forwards ordered action messages and the call/seed handshake, message-size and rate limits, room expiry, `/health` | MAIN-integrate (spec by SONNET-flow) | M | new test: two clients join by code and exchange 50 messages in order; oversize and flood are refused |
| R42 | Lobby page: create a room, show the code, join by code, choose seat controller (human / my sub-agent / built-in AI), choose dice or coin | MAIN-integrate * | M | manual run with two browser tabs |
| R43 | Coin toss: call heads or tails, relay creates the seed after the call, pumpkin coin flip animation (squash and swap of the two Qwen pictures) | MAIN-integrate * | M | both tabs show the same result; art pictures from gap A11 |
| R44 | Determinism tests: golden vectors (same seed + same actions = same HP and positions) across node and the browser, plus a replay test | MAIN-integrate | M | new test; a one-byte change in rules breaks it |
| R45 | Coolify packaging for Contabo: Dockerfile per service (static page, relay), env-var config, one port each, WebSocket through the proxy, `/health`; build and run locally only, NO deploy until the owner says | MAIN-integrate | S | `docker build` and local run pass (if Docker is available; otherwise the Dockerfile is reviewed only) |
| R46 | Phone layout and touch: controls at least 44 px, landscape layout, 8-unit crowding; test on a real phone | MAIN-integrate * | M | owner tests on the phone |
| R47 | Static preload and tint cache (DONE 2026-11-10: gate, 21 preload links, tint cache) | MAIN-integrate | — | `python3 -B scripts/test_preload_links.py` OK |
| R48 | Daily log and progress table by script and sub-agent (Kiro 78, running) | SONNET-flow | S | `python3 -B scripts/test_daily_log.py` OK, run by the main line |

## Standing workflow (owner 2026-11-10: "later, have him generate assets with reference pictures to extend")
For every new picture: pick the closest EXISTING picture(s) as references (style first, identity second, per docs/kiro_79_style_for_colab_gpt-5.6-terra.md), extend from them by chain generation, one picture per prompt, one variant first. The main line checks each result against the references before installing.

## Architecture diagram
docs/overview/architecture.mmd and the SVG still show the wind ghost as an 8-frame loop, the MCP server as the rules path (`T_MCPSTD --> T_MCPENG`) and have no relay, invitation codes, coin toss or deterministic rules node. They need one redraw after R03 and R41 are specified; until then read them with this file.
