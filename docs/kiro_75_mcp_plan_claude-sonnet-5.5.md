# Kiro 75: MCP plan (claude-sonnet-5.5, 2026-11-10)

Nothing here was run. I read files only. "READ" = seen in a file (path:line). "ASSUMED" = not checked.
Built on `docs/owner_decisions_20261110_agents_headless.md` (every player brings an agent, headless in principle, modular, 4v4, per-seat public view). Owner log rules are not reopened.

## 0. Short version

- The existing MCP server is a good base for a single agent side. It is not yet fair under the new decisions: it shows both teams' shields and shield path ids, shows agent aim to everyone, has one shared notes field, and has no seats.
- A stdio MCP server serves one client per process. "Every player brings an agent" needs one shared match host on localhost and a small per-seat MCP proxy.
- The real game (statuses, ultimates, items) exists only in `index.html`. The Python engine is a subset. An agent can play the real game only if the page is the authority and talks to the host through an adapter.
- Build order: fix fairness and add seats in Python first (works without touching `index.html`), then the page adapter, then replay and stats. Cut order if time is short is in section 4.

## 1. Current state

### 1.1 Server and tools
| Statement | Source |
|---|---|
| Standard MCP over stdio, newline-delimited JSON-RPC 2.0. Methods: initialize, ping, tools/list, tools/call. Subclasses the engine, does not edit it. | READ `scripts/mcp_stdio_server.py:1-20`, `_dispatch` |
| Six tools: `get_public_state` (582), `get_history` (590), `submit_action` (607), `end_turn` (660), `set_notes` (674), `get_notes` (after it). | READ `mcp_stdio_server.py:580-700` |
| `submit_action` takes unit + `throw {angle 25-80, power 0-100}`, `move {direction}` (engine rolls the die, 36 px per pip), `defend {path1, path2}` (knight only, two of the last 4 enemy throw ids). Only path1 places the shield; path2 is recorded. | READ `mcp_stdio_server.py:_do_throw/_do_move/_do_defend (514)`; owner decision 10a in `.kiro/specs/mcp-standard/tasks.md:12` |
| Phases are `human`, then `agent` (12 s timeout checked lazily at the next call, injectable clock), then `over`. Units that did not act idle. | READ `mcp_stdio_server.py:Session._begin_round`, `tick (345)` |
| `get_public_state` returns: round, phase, seconds left, exact wind, wall, shields (both teams, with `path_ids`), units (x, y, hp, class, controller, `acted`, `moved`), `remembered_enemy_paths` for both teams, ultimates remaining, last timeout. | READ `mcp_stdio_server.py:376-408` |
| `get_history` returns throws with `wind_at_throw`, landing, `hit_type`, damage, sampled path (every 6th step, 50 max). Human angle/power are removed; agent angle/power are shown to everyone. | READ `mcp_stdio_server.py:158-170`, `HISTORY_MAX = 50` at line 67 |
| Hidden by design: RNG seed, dice stream, pending (unsubmitted) actions, human aim. The engine's own `get_public_state` has `landing_history` with human angle/power (`mcp_game_server.py:198`); the stdio server rebuilds its own state and drops it. | READ |
| No simulator tool. Notes are one string per match, max 2000 chars. | READ `mcp_stdio_server.py:66, 292` |
| Optional staging to disk only with `--memory-dir`/`PK_MEMORY_DIR`; atomic writes; no seed in `meta.json`; `(not published)` is git-ignored (`.gitignore:9`). The docstring at `mcp_stdio_server.py:19` still says it is not ignored (stale). | READ |
| `serve()` reads lines with no size limit and there is no rate limit. | READ `mcp_stdio_server.py:781-783` |
| `mcp_game_server.py` also holds an old non-standard JSON-RPC handler and a module-level `GAME_INSTANCE` (447). Not used by the stdio server. | READ |

### 1.2 Registration and tests
| Statement | Source |
|---|---|
| `.kiro/settings/mcp.json` registers one server `pumpkin-killer`: `python3 -B scripts/mcp_stdio_server.py` (relative path, so it needs the repo root as working directory: ASSUMED for Kiro). Auto-approved: `get_public_state`, `get_history`, `get_notes`. `submit_action`, `end_turn`, `set_notes` need a click each. | READ `.kiro/settings/mcp.json:3-9` |
| `scripts/test_mcp_stdio.py`: 23 tests (13 protocol/subprocess, 10 session/in-process; I counted them). Forbidden-key check covers `seed, rng, dice, pending_throw, pending_action, last_throw` only. | READ `test_mcp_stdio.py:25` (key list), tests from line 117 on |
| `scripts/test_mcp_game.py`: one example-based function `test_modes` (line 15). No property test of the engine (also `tech.md`). | READ |
| `scripts/eval_agent_learning.py`: history-only ridge-regression agent; exits 1 if second-half error is not lower than first-half. Not a `test_*` runner. | READ `eval_agent_learning.py:16-20` |
| `.kiro/specs/mcp-standard/tasks.md` items 9 and 10b are still unticked; 10b is done in fact (`.gitignore:9`). Item 9 (reviewer runs the tests) has no recorded result. | READ |
| No test covers: opponent shield secrecy, per-seat views, rate limits, network use, writes outside the scratch folder. | READ (absence in the test file) |

### 1.3 The built-in AI in `index.html` (read only)
- Sees the target through a random view: position off by up to 150 px then snapped to 36 px, wind off by up to 1.2 (READ `index.html:547-548, 1246-1247`).
- No exact simulator in the aim: `2.32*sqrt(gap)*aiCal + 4*seenWind` plus random error 6 (READ 1249-1256). `aiCal` is learned from its own previous landing (READ 1751). `simulateLandingX` and `estimatePowerForTarget` are still defined (1207, 1225) but I found no caller outside each other (ASSUMED: dead code; a static "no simulator in AI code" test would fail on mere presence).
- Its aim state is written to a page global `window.__aiLog` (power, seen x, seen wind, class) (READ `index.html:1258`). Anything running in the page can read it.
- The built-in AI's shield is not drawn for the human and is revealed 1.4 s on block (READ `index.html:1672, 1888`). That is the owner rule (`owner_feedback_log.md:89-90`).
- The browser does not call the MCP server (`tech.md`). Network use in the page: only `fetch` for audio files (READ `index.html:296`).

### 1.4 Findings that break the new fairness rules (report only, nothing changed)
1. Both teams' shields, `active`, x, y and `path_ids` are public (`mcp_stdio_server.py:385-389`). The owner says the shield and its path are invisible to the opponent.
2. `remembered_enemy_paths` is given for both teams (406). A seat needs only its own.
3. Agent throws show angle and power to every caller (`mcp_stdio_server.py:158-170`). A human cannot read an opponent's aim. The test `test_full_round_history_and_notes` asserts this behaviour and must change with the fix.
4. One shared notes string, no seat, no caller identity. Any caller can submit for any unit of the current phase.
5. `acted`/`moved` of enemy units is visible. A human cannot see that either.
6. Engine drift that also affects MCP matches: units are re-placed at random every round (`mcp_game_server.py:414-418`) while the client moves units only with the die (`index.html:1342`); wall damage 20 (`mcp_game_server.py:336`) vs `WALL_HIT_DMG = 8` (`index.html:412`); wind is a constant push (67.5) vs acceleration (72), approximate by design (`mcp_stdio_server.py:57`). `tech.md` still lists 48/45 and is stale. Per `tech.md` I do not fix these without an owner answer (Q2).

## 2. Goal and candidates

Goal: each seat is driven by its owner's agent through MCP with only that seat's public view. The built-in AI stays as the practice opponent. A human can still play a seat in the page.

### 2.0 Module boundaries (decision 3) and migration
| Module | Job | Knows nothing about | Test |
|---|---|---|---|
| `rules` (pure state step: apply action, resolve round) | authority for the match | drawing, input, MCP | node/py unit + golden vectors |
| `view` (`publicViewFor(seat)`) | the only function that builds what a seat may see | how the seat is controlled | non-interference test (3.3) |
| `seats` (seat id, team, units, controller kind agent/human/builtin, token) | who may act | physics | seat tests |
| `host` (localhost relay, holds the match, enforces rate/size/phase) | one match, many seats | rendering | protocol tests |
| `mcp proxy` (stdio, `--seat`, forwards to host) | MCP face for one agent | rules | existing protocol tests |
| `page adapter` (in `index.html`, later `js/`) | page sends `view`, accepts actions | MCP | manual + bridge test |
| `store` (scratch folder, replay data) | public history only | rules | atomic-write tests |
Migration: (1) add `view` and `seats` inside the Python server, no page change; (2) split the server file into `rules/view/seats/host/proxy`; (3) when the 4v4 plan (task 76) produces a units array, write the page adapter against `view`; (4) move page rules into a pure module only if time allows (decision 2 target, not required for the freeze).

### 2.1 Candidates
| # | Tool(s) and arguments | Purpose | Hidden | Called by | Cost | Risk | Build before 12-04? |
|---|---|---|---|---|---|---|---|
| C1 | Seat-scoped `get_public_state`, `get_history`, `submit_action`, `end_turn`, `get_notes`, `set_notes`. No `seat` argument: the seat comes from the proxy's `--seat` and token. | The opponent mode | Other seats' pending actions, shields, shield paths, agent aim, `acted`/`moved`, seed, dice, AI noise draws | Each player's agent | M (seats, host, proxy) | Seat spoofing; stdio is one client per process | YES, core |
| C2 | `get_rules` (no args): angle range, power range, turn seconds, 36 px per pip, class HP/weapon, hits-to-kill table | Agents need the printed rules, as a human reads the help | `GRAVITY`, `V0_PER_POWER`, wind constant (they would be a simulator) | Each agent at start | S | Leaking constants by accident | YES |
| C3 | `get_match_status` (no args): match id, round, phase, seat list with controller kind, server version, constants hash | Read-only status for judges and the demo screen | Everything not already public | Judges, Kiro, main line | S | None | YES (small) |
| C4 | `list_matches {limit}`, `get_replay {match_id}` | Replay of finished matches from staged public history; also feeds a viewer that animates the sampled paths | Same public rules as live; only finished matches | Judges, Kiro, viewer page | M tool, M-L viewer | Path traversal on `match_id` (validate against `index.jsonl`) | Tool YES; viewer only if time |
| C5 | `get_match_stats {match_id}`: hit rate by round per seat, from `result.json` | Show both sides improving (product.md) | Same | Judges, main line | S | Counts must exclude status damage (kiro_51 found this error) | YES |
| C6 | `run_measure` (run N matches, return AI hit rate) | Measure the AI | n/a | main line | M | A tool that spawns processes and runs long loops is a risk surface | NO. Keep it a command: `node scripts/sim_ai_nosim.js` (ASSUMED to measure the AI; file not read) and `eval_agent_learning.py`. Report the results in C5 format. |
| C7 | `get_asset_inventory` (no args) reading `docs/asset_inventory.json` (exists, generated 2026-11-09 19:06, READ `asset_inventory.json:2`) | Shows MCP in the dev loop for judges | n/a | Kiro, main line | S | Must live in a separate dev server so game agents never get repo access; fixed file, no path argument | Only if spare time, after C1-C5 |
| C8 | Human orders to own agent (`owner_message` field) | Decision 1 says the human may give orders | Other seats' orders | Human via page | S | Prompt injection into the agent; agent must treat it as data from its owner | NO before the freeze (Q5) |

## 3. Fairness and safety rules

### 3.1 The agent may never see
- RNG seed, dice stream, any unsubmitted action of any seat, future wind.
- The built-in AI's noise draws (seen x, seen wind), its `aiCal`, its aim, and `window.__aiLog`.
- Any opponent shield: position, existence, path ids, A-B-C points, until the shield blocks (then only the block event and the point that fired, as the page does at 1.4 s).
- Opponent angle and power (human or agent). Landing points and flight paths are public.
- Whether an enemy unit has acted or moved this turn.
- Physics constants that rebuild a simulator (`GRAVITY`, `V0_PER_POWER`, wind constant).
- Wind precision: no finer than the HUD shows (Q3).
Own seat sees: its own units, shields and paths, its own throw aim, its own notes.

### 3.2 Safety limits
- Host and relay bind `127.0.0.1` only; reject any `Host` header that is not `127.0.0.1:<port>` or `localhost:<port>` (DNS rebinding). No outbound sockets in server code.
- Per-match random token per seat, passed to the proxy by environment variable, never written to disk or logs, never returned by a tool.
- Rate limit per seat: 10 calls per second, burst 20; request line at most 16 KB; notes 2000 chars (exists); history 50 (exists). Over limit returns `isError` and counts nothing.
- Writes only under the scratch folder (`(not published)`, git-ignored). The proxy and host open no other file for writing. Replay and inventory tools read fixed locations only.
- No secrets in code, tool output, notes, or staged files. Tool output and notes are data; the server never executes them.
- Turn timeout 12 s per seat stays (`TURN_SECONDS`); a timeout is a forfeit, not an error.

### 3.3 Checks the main line can run (all new unless named)
| Check | How | Proves |
|---|---|---|
| Non-interference test | Two matches with the same visible inputs for seat A but different hidden values for seat B (shield points, AI noise draws, B's aim). Every tool output for seat A must be byte-identical. | Section 3.1 for any field, not only listed keys |
| Forbidden-value scan | Fuzz 200 random legal games; collect all strings/numbers in all outputs; none equals the seed, a dice value, a hidden shield coordinate or a constant from 3.1 | No indirect leak |
| `get_rules` scan | Output contains none of the physics constants | C2 is not a simulator |
| Static import check | `grep -nE "import (socket\|urllib\|http\.client\|requests\|ftplib\|smtplib)" scripts/mcp_*.py` empty; only the host may import `http.server` | No network beyond localhost |
| Bind check | Start the host; assert the listening address is `127.0.0.1`; a request with `Host: evil.example` gets 403 | Localhost only |
| Write check | Hash the repo tree (excluding `(not published)`) before and after a full 30-round match; equal | No writes outside scratch |
| Seat test | Seat A's proxy tries other seat's unit: rejected; wrong token: rejected | Seat isolation |
| Rate test | 100 calls in one second: first ~20 pass, rest `isError`; state unchanged | Rate limit |
| Existing | `python3 -B scripts/test_mcp_stdio.py` (23 tests, one to be updated), `python3 -B scripts/test_mcp_game.py`, `python3 -B scripts/test_constants_sync.py`, `python3 -B scripts/eval_agent_learning.py` | No regression |
| Page check | After the adapter: `grep -n "__aiLog" index.html` returns nothing unless behind a debug flag; adapter sends only `publicViewFor` output | Page does not leak |

## 4. Schedule (today 11-10; freeze 11-27 provisional; deadline 12-04)

Owner of `scripts/mcp_*.py` work: Kiro in a branch `kiro/mcp-seats`. Main line re-runs every command itself. `index.html` is edited by the main line only (lock in `ROLES.md`).
| # | Step | Size | Depends on | Needs owner | Verify |
|---|---|---|---|---|---|
| 1 | Answer Q1-Q6 | S | none | YES | owner reply |
| 2 | Write the fairness tests first (3.3 non-interference, scan, rate, write). They fail on today's code. | M | none | no | `python3 -B (not published)` fails on the current server (proves the test can fail) |
| 3 | Add `view` per seat: hide opponent shields/paths/aim/`acted`; per-seat notes and `remembered_paths`; update the one old test | M | 2, Q4 | Q4 | `python3 -B scripts/test_mcp_stdio.py` and the new file pass |
| 4 | Seats and controller kinds (agent/human/builtin) in the Python session; phases per team, not "human/agent" | M | 3, task 76 seat definition | no | same two commands + seat test |
| 5 | Host on `127.0.0.1` + per-seat stdio proxy (`--seat`, token env), rate and size limits, Host check | M | 4 | no | bind, Host, rate, seat tests |
| 6 | `get_rules`, `get_match_status`, update `docs/mcp_agent_protocol.md`, `.kiro/settings/mcp.json` (second entry per seat, `autoApprove` stays read-only) | S | 5 | no | `tools/list` test lists the new tools; scan test |
| 7 | Agent-vs-agent demo and learning curve through the proxies | S | 5 | no | `python3 -B scripts/eval_agent_learning.py`; copy the real numbers into the write-up |
| 8 | Engine drift fix (positions, wall 8; wind stays approximate) | S | Q2 | YES | `test_mcp_game.py`, `test_constants_sync.py`, new golden-vector test |
| 9 | Page adapter in `index.html`: `publicViewFor`, apply action, connect to host; gate or remove `window.__aiLog`; controller choice per seat | L | 4 seats in the page (task 76), 5 | Q1 | page check, bridge test, one manual match: Kiro plays the white seat |
| 10 | `list_matches`, `get_replay`, `get_match_stats` | M | 5 | no | tests on a staged fixture; path-traversal test |
| 11 | Demo script, README "Run it" lines, video | M | 7, 9 | YES (video) | owner watches the match |
| 12 | Replay viewer page (animates sampled paths) | M-L | 10 | no | manual |
| 13 | Dev server with `get_asset_inventory` | S | 5 | Q4b | `tools/list` of the dev server; read-only test |

Cut order if behind: 13, 12, 10 (keep `get_match_stats`), 9. Steps 2-7 alone give a fair, tested MCP opponent mode in headless matches and a Kiro-played demo against the Python engine. Without step 9 the real page cannot be played by an agent; say so honestly in the write-up. Target: steps 2-7 by 11-17, step 9 by 11-24, step 11 on 11-25 to 11-27.

## 5. Open owner decisions (recommendation first)

1. Q1. Should the page's rules be the single authority for human-vs-agent matches, with the Python engine kept as a labelled headless practice engine? Recommend yes: the engine lacks statuses, ultimates, items and the 8-point wall, so an agent on it plays a different game.
2. Q2. May I (Kiro) align the Python engine with the client on position changes and wall damage only? Recommend yes; leave the wind model approximate and update the stale 48/45 row in `tech.md`.
3. Q3. Should the agent see wind exactly as the HUD shows it (no finer)? Recommend yes; the main line confirms what the HUD displays (whole steps or tenths) and one function feeds both.
4. Q4. Should a seat's agent aim (angle, power) be hidden from other seats? Recommend yes; a human cannot read it. Q4b: build the asset-inventory dev tool at all? Recommend no before the freeze.
5. Q5. Should a human be able to send short orders to their own agent? Recommend no before the freeze; decide after the demo works.
6. Q6. May the README ask judges to run a local relay (`python3 -B (not published)`) to try an agent seat, with the built-in AI as the default experience? Recommend yes; a hosted page cannot reach a judge's local relay (ASSUMED: judges mostly watch the video and open the hosted game).
