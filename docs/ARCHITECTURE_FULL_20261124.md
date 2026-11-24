# Pumpkin Killer: architecture, flows, technical details, and how Kiro was used

Written 2026-11-24 from the files and the code in this repository. Every number below was counted on that day with the command shown beside it or is dated where it was counted earlier. Where something is planned, partial, or untested it is marked **NOT DONE**, **PARTLY**, or **NOT VERIFIED**; nothing here is a claim that a feature works unless a test or a log named in the text shows it.

Older companion documents: `docs/architecture.md` (a read-only drawing of the page, from Kiro task 41), `docs/KIRO_USAGE_20261116.md` (the Kiro evidence record), `docs/relay_protocol_20261115.md`, `docs/mcp_agent_protocol.md`, `docs/ADR_unit_slot_fill_20261124.md`.

## 0. The opening card (the first seconds of the demo video)

Two strips fit in the first 8 seconds of the video and on the top of the README. Left: how a match is wired. Right: what Kiro did.

```mermaid
flowchart LR
  P["Phone page"] -- "WebSocket: actions only" --> R["Relay: rooms, seats, seed"]
  C["Computer page"] -- "WebSocket: actions only" --> R
  A["Outside AI agent via MCP"] -- "public view only" --> R
  R -- "same seed, same actions" --> P
  R -- "same seed, same actions" --> C
  R -- "same seed, same actions" --> A
```

```mermaid
flowchart LR
  B["Task brief + spec"] --> K["Kiro CLI writes code, tests, report"]
  K --> V["Main line re-runs the tests"]
  V --> L["Ledger: verified or rejected"]
  S["Steering + hooks on save"] -. "keep it honest" .-> K
```

One sentence for the narration: *every device runs the same rules from the same seed, so the relay only passes actions along and nobody has to trust anybody's screen.*

## 1. System architecture

```mermaid
flowchart TB
  subgraph Clients["Players"]
    PH["Phone browser"]
    PC["Computer browser"]
    AG["MCP client: Claude Code, Kiro, any MCP agent"]
    CS["Computer seat: headless Chrome + hybrid_seat_headless.js (local only)"]
  end

  subgraph Page["Game page (plain HTML, canvas, JavaScript, no framework)"]
    IDX["index.html: rules, input, 1/60 s physics, draw loop, lobby"]
    SH["shared/*.js: constants, flight, weather, determinism, round hash"]
    SW["sw.js: offline cache"]
  end

  subgraph Edge["One container (Coolify): nginx on port 80 is the only public door"]
    NG["nginx: static files, /relay, /mcp, /mcp/health, /ai"]
    RL["pk_relay.py on 127.0.0.1:8765: rooms, seats, seat tokens, seed, judging"]
    MH["pk_mcp_http.py on 127.0.0.1:8767: Streamable HTTP /mcp"]
    AI["pk_ai_gateway.py on 127.0.0.1:8766: optional text AI"]
  end

  subgraph Py["Python engine mirrors the page rules"]
    MG["mcp_game_server.py + mcp_stdio_server.py"]
    PYS["shared/*_py.py: same constants and vectors"]
  end

  PH --> NG
  PC --> NG
  NG -- "static" --> Page
  NG -- "WebSocket /relay" --> RL
  AG -- "HTTP /mcp" --> NG
  NG --> MH
  MH -- "WebSocket, gateway token + client address" --> RL
  MH --> MG
  MG --> PYS
  CS -- "WebSocket, local" --> RL
  NG -. "optional" .-> AI
```

| Part | File | What it does | State |
|---|---|---|---|
| Game page | `index.html`, `js/`, `css/`, `shared/` | Whole game on a 1920x1080 canvas; fixed 1/60 s physics; start screen with the room lobby | built, tested |
| Relay | `scripts/pk_relay.py` | Creates rooms with a random 6-character code, assigns seats, sends the same seed to every seat, forwards only allowlisted actions, checks size (16 KiB), rate (10 messages per second), seat and phase, keeps a numbered log for replay | built, tested |
| MCP stdio bridge | `scripts/mcp_stdio_server.py` | 7 game tools and 3 room tools for one agent on the same machine | built, tested with scripted clients |
| MCP over HTTP | `scripts/pk_mcp_http.py` | The same tools at `/mcp` for remote agents; Origin allowlist, locked to the local relay, per-client session cap | built, tested; **NOT deployed, NOT VERIFIED with Claude Code or Kiro** |
| Computer seat | `scripts/hybrid_seat_headless.js`, `scripts/fill_room.py`, `scripts/run_slot_room.py`, `scripts/host_room.py`, lobby `#slot-fill-ai` | Host-browser AI fills open slots directly from the lobby (`#slot-fill-ai`, zero server cost); headless Chrome scripts also work from a terminal | built, tested (updated 2026-11-25) |
| AI gateway | `scripts/pk_ai_gateway.py` | Optional text generation backend | built; copied into the image since 2026-11-24; whether it is switched on for the contest build is the owner's decision |
| Deploy | `deploy/Dockerfile.coolify`, `deploy/entrypoint.sh`, `deploy/nginx.conf` | One container: nginx plus the Python processes | built; see section 9 |

State lives in memory: restarting the container ends every room.

## 2. A match from room to result

```mermaid
sequenceDiagram
  participant H as Host page
  participant R as Relay
  participant G as Guest page
  participant A as MCP agent
  H->>R: create_room (team size, seat)
  R-->>H: room_state (code, seat_token)
  Note over H: lobby shows code, link, QR code
  G->>R: join (code, side, units)
  R-->>G: room_state + replay of the log
  A->>R: join_room tool (link or code)
  H->>R: ready
  G->>R: ready
  A->>R: ready
  R-->>H: start (seed, first team)
  R-->>G: start (seed, first team)
  R-->>A: start (seed, first team)
  loop each turn of the team that is up
    H->>R: action (angle, power, skill)
    R-->>G: action, numbered
    R-->>A: action, numbered
    Note over H,A: every client simulates the same flight from the same seed
    H->>R: round_hash
    G->>R: round_hash
    R-->>H: mismatch report only if the hashes differ
  end
  R-->>H: result
```

- **Invite**: the lobby shows the room code, a link and a QR code. The link carries `choose=1`, so a friend sees a red or white card first and joins after choosing. An older link without it joins straight in.
- **Started room**: a new red or white seat in a room whose match has started is refused with `room_started` (2026-11-24, `scripts/test_relay_late_join.py`, `scripts/test_late_join_page.js`); before that fix the seat was created and the page stayed silent. Spectators and a `resume` of an existing seat are unchanged.
- **Reconnect**: each seat has a secret `seat_token`. A dropped connection is held for 60 seconds and `resume` replays the missed numbered messages. After 60 seconds the seat is removed and the other seats are told.
- **Seat leaves**: a seat that leaves a started match makes its team lose (a decision the owner may overturn). A seat whose units are all dead is ignored (red-team R2A-F1).

## 3. Why the relay is thin: determinism and fairness

The page and the Python engine run the same rules from the same inputs, so the relay does not simulate anything and cannot cheat.

```mermaid
flowchart LR
  SEED["seed from the relay"] --> W["wind, weather, first team, dice: one pseudo-random stream"]
  W --> F["flight(angle, power, wind): fixed 1/60 s steps"]
  F --> H["hit mask: 70x190 hit box with a binary mask"]
  H --> D["damage, status, energy"]
  D --> HASH["round hash of the state"]
  HASH --> CMP{"all seats equal?"}
  CMP -- "yes" --> NEXT["next turn"]
  CMP -- "no" --> REP["relay reports the mismatch; the room is flagged"]
```

Evidence (re-run commands in parentheses): shared constants and golden vectors in `shared/` are read by both the JavaScript and Python tests (`node scripts/test_determinism.js`, `python3 scripts/test_determinism_golden.py`, 66 flight vectors plus 500 cross-runtime cases); hit judging was replayed over 425,861 flight steps with 0 false hits and 0 missed hits, with the stated exemption for area and returning weapons (`docs/hit_coverage_20261119.svg`); 67,456 shots in each direction showed 0 mismatches between the page and the engine (`docs/rear_rear_weather_wind_20261119.json`).

## 4. MCP: how an outside agent sits at the table

```mermaid
flowchart LR
  subgraph Agent["Agent side"]
    T["tools/list"] --> J["join_room(link or code)"]
    J --> W["wait_for_turn"]
    W --> S["get_public_state"]
    S --> X["submit_action, end_turn"]
    X --> W
  end
  subgraph Gate["Gateway pk_mcp_http.py"]
    O["Origin allowlist"] --> Q["per-client session cap: 8"]
    Q --> U["relay address locked to the local relay"]
  end
  Agent --> Gate --> REL["Relay seat"]
```

- **Tools**: 7 game tools (`get_public_state`, `get_roster`, `get_history`, `submit_action`, `end_turn`, `set_notes`, `get_notes`) and 3 room tools (`join_room`, `leave_room`, `wait_for_turn`). There is deliberately no tool that creates a room: people open rooms, agents join them.
- **Public view only**: an agent sees what a player sees. The seed, the pending actions and the opponent's aim are not in the view (`public_throw()` in `scripts/mcp_stdio_server.py`).
- **Hosted limits**: the gateway reports the real client address to the relay only with a one-time random token (`PK_RELAY_GATEWAY_TOKEN`, made at container start and never written to a file), so the relay's per-address connection cap counts each remote client, not one proxy. Each client may hold 8 sessions (`PK_MCP_MAX_SESSIONS_PER_IP`); the ninth gets HTTP 429. Tests: `scripts/test_mcp_risk_ab.py`, `scripts/test_pk_mcp_http.py`, `scripts/test_mcp_room_tools.py`.
- **Full-team or partial-unit claim (updated 2026-11-25).** An MCP agent can join as a whole team or claim a subset of units on a shared team via `join_room(..., claim=1..units)` with 3-way `round_hash` parity (`scripts/test_mcp_claim.py`).
- **NOT VERIFIED**: no run with a real MCP client (Claude Code, Kiro) is recorded, and `/mcp` is not deployed yet. The recorded Kiro IDE attempt failed because that session had no Pumpkin Killer tool (`docs/kiro_evidence/raw/ide_mcp_attempt_20261115.txt`). A multi-client end-to-end run is the open task in `(not published)`.

## 5. Filling empty seats (unit slot fill)

```mermaid
flowchart TB
  ROOM["3 v 3 room, two human seats ready"] --> HOLD["fill_room.py joins placeholder seats so the match waits"]
  HOLD --> DEC{"filler"}
  DEC -- "computer" --> CPU["hybrid_seat_headless.js plays the empty units through a headless Chrome"]
  DEC -- "agent" --> AGT["join_room(..., claim=1..units) claims 1 or more open units on a team"]
  CPU --> REL["placeholders released, match starts"]
  AGT --> REL
  HOLD -- "failure" --> KEEP["placeholders kept; they expire after the 60 s grace and the room starts without a fill, and the log says so"]
```

State (updated 2026-11-25): works both directly in the lobby (**Fill open slots (AI)** via `#slot-fill-ai`, running in the host's browser at zero server cost; verified E2E in 1 v 1, 2 v 2, and 3 v 3) and from a terminal (`python3 -B scripts/fill_room.py`, `scripts/run_slot_room.py`). External MCP agents can also claim partial units via `join_room(..., claim=1..units)`. Design choices are in `docs/ADR_unit_slot_fill_20261124.md`.

## 6. Deployment

```mermaid
flowchart LR
  USER["Player or agent"] -- "HTTPS" --> TR["Coolify proxy"] --> NG["nginx :80"]
  NG --> STATIC["static game files"]
  NG -- "/relay" --> RL["relay 127.0.0.1:8765"]
  NG -- "/mcp" --> MH["mcp http 127.0.0.1:8767"]
  NG -. "/ai" .-> AI["ai gateway 127.0.0.1:8766"]
  MH --> RL
```

`deploy/entrypoint.sh` starts the Python processes, then nginx, with a trap for stop signals. Only nginx faces outside. Environment variables the owner sets: `PK_ALLOWED_ORIGINS`, `PK_RELAY_TRUST_PROXY`, `PK_RELAY_MAX_PER_ADDR`; the gateway token is made at start. Without `PK_RELAY_TRUST_PROXY` every player behind the proxy looks like one address. Not deployed yet (nothing is live).

## 7. How Kiro was used

### 7.1 The loop

```mermaid
flowchart TB
  O["Owner decides rules and scope"] --> SP[".kiro/specs: requirements, design, tasks"]
  SP --> TB["docs/kiro_task_N.md: one small task brief"]
  ST[".kiro/steering: product, rules, tech, structure"] --> KR
  TB --> KR["scripts/kiro_route.py routes the brief to Kiro CLI, logs the model and the run"]
  KR --> KO["Kiro writes code, tests and docs/kiro_N_result*.md"]
  KO --> HK["Hooks on file save: engine tests, constants sync, preload block check"]
  KO --> MV["Main line re-runs the tests itself; a report is not proof"]
  MV --> LG["docs/KIRO_LEDGER.md and docs/kiro_verified.json record verified or rejected"]
  LG --> O
```

### 7.2 Kiro features, used or not (counted 2026-11-24)

| Kiro feature | Used? | Evidence |
|---|---|---|
| CLI | Yes, the main route | `scripts/kiro_route.py`; 197 task briefs `docs/kiro_task_*.md`; 112 result files `docs/kiro_*_result*.md` |
| Specs | Yes | 32 folders in `.kiro/specs/` (requirements, design, tasks) |
| Steering | Yes | 11 files in `.kiro/steering/` (for example `structure.md` makes `index.html` a one-writer file) |
| Custom agents | Defined, one recorded run | 8 files in `.kiro/agents/`; `pk-player` played one recorded match through the public tools (`docs/kiro_162_result_gpt-5.6-terra.md`, not counted as verified); the other agents have definitions only |
| Hooks | Yes | 7 files in `.kiro/hooks/`; `docs/kiro_evidence/raw/hook_runs.log` (git-ignored, so not in a public tree) held 176 save entries on 2026-11-16 |
| MCP | Yes | `.kiro/settings/mcp.json`; `scripts/mcp_stdio_server.py`; one CLI-routed match; the IDE attempt failed |
| Property-based testing | Yes | `scripts/test_properties.js`: six seeded properties; task 179 recorded four failures and task 181 corrected them |
| Powers | One written, not installed | `.kiro/powers/pumpkin-killer-seat/` |
| IDE | Once | one save-triggered hook run, `docs/kiro_evidence/raw/ide_hook_run_20261115.txt` |
| Crew (ACP) | Once, read-only audit | `docs/crew_audit_usage_doc_result.md` |
| Web | No | no record |

### 7.3 Spec-driven versus no spec (a real comparison from this project)

- With a spec and a test: Kiro task 225 wrote an end-to-end test with two MCP seats; it failed and showed a relay that silently skipped one team's turn from round 2; the fix was one function.
- Without a spec: a phone-layout test that pinned strings passed while the hero tiles had disappeared; only measuring the real page found it. Details: `docs/KIRO_USAGE_20261116.md`.

### 7.4 Who did what

- Kiro (CLI, ACP, Crew): task briefs, specs, scripts, tests, the Python engine, the relay and MCP server, result reports. On 2026-11-16, 109 of 333 development commits named a Kiro task (method in `docs/KIRO_USAGE_20261116.md`). Since 11-16, the development repo grew to 514+ commits (115 naming Kiro) as later work (team battles, lobby AI fill, partial-unit MCP `claim`, hosted MCP, red-team fixes, phone layout) was completed by the owner with additional assistants. Note: the public release repository is a privacy-cleaned single-commit snapshot, so all published task briefs and result files are preserved directly in `docs/` and `.kiro/`.
- A second AI coding assistant (Claude Code) under the owner's direction: page wiring, integration, independent verification, fixes.
- Gemini: the hosted MCP server and several red-team fixes on 2026-11-24, re-run by the main line.
- The owner: every rule, every public text, the art pipeline (Qwen-Image-Edit on Colab) and the decisions recorded in `(not published)`.

Rule that kept this honest: **a Kiro result is a report, not verification.** The main line re-runs the tests; `docs/kiro_verified.json` lists only tasks with a recorded verdict.

## 8. Tests and evidence (updated 2026-11-25)

| Item | Result | How to re-run |
|---|---|---|
| Whole suite | 184 `test_*` scripts (`97 JS + 1 MJS + 86 Python`) + `sim_team_headless.py`; `zsh scripts/run_full_suite.sh` passes with 0 failures (178 run in batch; 6 local-socket tests skipped there and verified separately alongside relay, MCP claim, MCP risk, and deploy checks) | `zsh scripts/run_full_suite.sh`, `redteam/evidence/recheck_full_suite_v3_20261125.txt`, `redteam/evidence/recheck_socket_v3_20261125.txt` |
| Room late join | relay 4 tests, page 17 checks, real Chrome 1 test; each failed before the fix | `python3 -B scripts/test_relay_late_join.py`, `node scripts/test_room_status.js`, `node scripts/test_late_join_page.js` |
| Phone landscape invite panel | 7 viewport sizes pass | `node scripts/test_invite_panel_fit.js` |
| MCP risk A and B | 10 tests | `python3 -B scripts/test_mcp_risk_ab.py` |

## 9. Known limits and open items

| Item | State |
|---|---|
| Hosted URL, hosted `/mcp` | NOT DONE (nothing deployed) |
| MCP with a real client (Claude Code, Kiro) | NOT VERIFIED |
| Lobby button for computer fill | DONE (2026-11-25): `#slot-fill-ai` in lobby fills all open red/white slots using host-browser AI (zero server cost); verified E2E in 1v1, 2v2, and 3v3 |
| AI (MCP) fill of part of a team | DONE (2026-11-25): `join_room(..., claim=1..units)` allows an MCP agent to claim 1 or more units on a shared team with 3-way `round_hash` parity (`scripts/test_mcp_claim.py`) |
| Container image | Fixed 2026-11-24 and checked in a real container: the AI gateway is copied, the nginx `types` block that real nginx rejected is repaired, a watcher stops the container if the relay or MCP process dies (`scripts/check_coolify_deploy.py`, `redteam/evidence/prepush_docker_*_20261124.txt`). Still open: the `/ai` origin check, `PK_RELAY_TRUST_PROXY`, the Coolify variables only the owner can set. Details: `(not published)` |
| Room state | in memory; a restart ends every room; one container, no horizontal scaling |
| Match where a seat leaves | that team loses (owner may overturn) |
| Portrait phone | a rotate hint covers the page by design |
| Real phone in full screen exit | an overflow was reported once and not reproduced (gap G3) |

## 10. Where to find things

| Question | Open |
|---|---|
| What are the rules and the engine? | `index.html`, `shared/`, `scripts/mcp_game_server.py` |
| How do rooms work on the wire? | `docs/relay_protocol_20261115.md`, `scripts/pk_relay.py` |
| How does an agent play? | `docs/mcp_agent_protocol.md`, `scripts/mcp_stdio_server.py` |
| How was Kiro used? | `docs/KIRO_USAGE_20261116.md`, `docs/KIRO_LEDGER.md`, `.kiro/` |
| What was found and fixed in red-team rounds? | `(not published)` |
| What is checked before publishing? | `scripts/release/README_gate.md`, `(not published)` |
