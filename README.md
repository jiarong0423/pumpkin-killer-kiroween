# Pumpkin Killer

**A Flash-era artillery duel, resurrected for the modern browser — phone, computer, and AI agents at one table.** Up to three heroes per side throw across a haunted fence while wind and weather shift every shot. Built for **Kiroween 2026 (Resurrection)** with Kiro specs, steering, hooks, custom agents, a Kiro Power (`play` skill), and a standard MCP server (`.kiro/`).

**Play now:** https://pumpkin.jace0423.com (phone in landscape, or any desktop browser).

- **8 heroes** (Skeleton Spearman, Pumpkin Wizard, Bat-cat Assassin, Necromancer, Silver Cross Sister, Ghost Bride, Bell Tower Hunchback, Heavy Pumpkin Guard), each with a distinct weapon arc, status effects, and ultimate.
- **4 battlefields** and **5 weather states** (clear, rain, storm, snow, fog) with shifting wind every round.
- **1 v 1, 2 v 2, and 3 v 3** team matches across desktop browsers, mobile phones (landscape PWA), built-in AI, and external MCP agents.

---

## System Architecture

Every device and the Python engine run the exact same deterministic rules from the same match seed. The relay never simulates a match — it only manages rooms, seats, and ordered action forwarding, while per-round state hashes (`round_hash`) verify that every client stays in lockstep.

```mermaid
flowchart TB
  subgraph Clients["Players & Agents"]
    PH["Phone Browser (PWA, landscape)"]
    PC["Desktop Browser"]
    AG["External AI Agent (Kiro / Claude / MCP client)"]
  end

  subgraph Edge["Single Container (Docker / Coolify) — nginx :80"]
    NG["nginx Reverse Proxy\nStatic files | /relay | /mcp | /ai"]
    RL["WebSocket Relay\nscripts/pk_relay.py (:8765)\nRooms, seats, seed, ordered log"]
    MH["MCP HTTP Gateway\nscripts/pk_mcp_http.py (:8767)\nStreamable HTTP /mcp"]
    AI["Optional AI Gateway\nscripts/pk_ai_gateway.py (:8766)\nCapped text opponent"]
  end

  subgraph Engine["Shared Deterministic Core (JS + Python)"]
    JS["Browser Engine\nindex.html + js/ (1920x1080 Canvas, 1/60s physics)"]
    PY["Python Rule Engine\nscripts/mcp_game_server.py + scripts/*_py.py"]
    SH["Single Source of Truth\nshared/*.json (constants, heroes, golden vectors)"]
  end

  PH & PC -- "HTTPS static" --> NG
  PH & PC -- "WebSocket /relay (actions + round_hash)" --> NG --> RL
  AG -- "Streamable HTTP /mcp (public view only)" --> NG --> MH
  AG -. "or local stdio (scripts/mcp_stdio_server.py)" .-> PY
  MH --> PY
  MH -- "WebSocket (gateway token)" --> RL
  NG -. "optional /ai" .-> AI
  SH --> JS
  SH --> PY
```

Full architecture diagrams, match sequence flows, deployment details, and known limits: [`docs/ARCHITECTURE_FULL_20261124.md`](docs/ARCHITECTURE_FULL_20261124.md).

---

## Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Game Client** | Vanilla HTML5 Canvas, ES JavaScript, CSS3, PWA | Zero frontend framework; `1920x1080` canvas with fixed `1/60 s` physics, offline cache (`sw.js`, `manifest.webmanifest`), QR invites (`js/qr_code.js`), i18n (`js/i18n.js`). |
| **Backend & Relay** | Python 3.12, `websockets==15.0.1` | Minimal runtime footprint (one third-party dependency in `requirements.txt`); in-memory WebSocket relay (`scripts/pk_relay.py`) with 6-char room codes, reconnect grace, and rate/size guards. |
| **AI Agent Interface** | Model Context Protocol (MCP) — stdio & Streamable HTTP | 7 game tools + 3 room tools (`scripts/mcp_stdio_server.py`, `scripts/pk_mcp_http.py`); strict public-information isolation (`public_throw()`), full-team or partial-unit `claim`. |
| **Cross-Runtime Determinism** | Shared JSON + Node.js & Python parity | Shared constants, hit masks, and golden vectors (`shared/*.json`) verified identically in JS (`js/determinism.js`) and Python (`scripts/determinism_py.py`), checked live via `round_hash`. |
| **Testing & Simulation** | Node.js, Python `unittest`, Headless Chrome | 184 `test_*` scripts (`97 JS + 1 MJS + 86 Python`), seeded property-based tests (`scripts/test_properties.js`), headless team simulator (`scripts/sim_team_headless.py`). |
| **Deployment** | Docker (`python:3.12-alpine` + `nginx`), Coolify | Single-container image (`deploy/Dockerfile.coolify`); Nginx on port 80 proxies loopback-only Python services with container healthchecks. |

---

## Play & Quick Start

### 1. Run Locally (Desktop)
```sh
pip install -r requirements.txt
python3 -B scripts/dev_server.py 8080 --with-relay
```
Open `http://127.0.0.1:8080/`. The `--with-relay` flag starts the local WebSocket room relay (requires `websockets`); without it, single-player mode works out of the box.

### 2. Play on Phone or Against a Friend
- **Phone**: Open the hosted URL from the Devpost page in landscape (`16:9` recommended) and optionally install it to your home screen as a full-screen PWA.
- **Multiplayer Room**: Choose **1 v 1**, **2 v 2**, or **3 v 3** on the start screen and press **Play with friends**. After a one-time name, a lobby opens with a 6-character room code, copy-link button and QR code; friends join by link, QR, or **Join code**. Players take places on the red or white team, lock their heroes (no hero twice on one team), and the host presses **Start**; a 3-second countdown begins once every place is locked. After the match everyone returns to the same lobby for a rematch.

### 3. Play with AI or Bring Your Own Agent (MCP)
- **Built-in Computer Opponent**: In single-player matches, empty seats are played by the built-in AI (**Easy**, **Normal**, **Hard**, or **Smart (online)** when the server AI gateway is enabled).
- **Lobby AI Fill (Multiplayer)**: With **Computer fills open places** ticked, the host's **Start** fills every empty place with a computer seat that runs in the host's browser at zero server cost (or fill from the terminal with `python3 -B scripts/fill_room.py`).
- **External AI Agent (MCP)**: Set a seat to **Agent (MCP)** on the start screen to display the room code, QR code, and join command (`python3 -B scripts/make_agent_join_config.py`; full walkthrough in [`docs/HOST_AGENT_HOWTO.md`](docs/HOST_AGENT_HOWTO.md)).
  - Runs on the player's own machine with their own model account (zero LLM cost to the game host).
  - Supports joining as a whole team or claiming a subset of units (`join_room(..., claim=1..units)` or `python3 -B scripts/mcp_stdio_server.py --connect <relay> --code <code>`).
  - Sees only public player information through **7 game tools** (`get_public_state`, `get_roster`, `get_history`, `submit_action`, `end_turn`, `set_notes`, `get_notes`) and **4 room tools** (`join_room`, `lock_hero`, `leave_room`, `wait_for_turn`). With **Allow agents** ticked, any seated player can **Invite an agent**: a one-use ticket seats it on the inviter's team with a briefing, and it picks its hero and plays on its own.

### 4. How a Turn Works
A coin toss decides who goes first. On each unit's turn: pick a skill or item, set your angle (`25°–80°`), read the wind, hold to charge power, and release to throw — or spend your turn rolling a die to move. Direct hits charge your ultimate meter, and breaking the center fence opens lower trajectories.

---

## Built with Kiro

The entire `.kiro/` workspace is committed to this repository. Rather than treating AI output as automatically correct, every Kiro task followed a spec-driven, independently verified loop:

```mermaid
flowchart LR
  SP[".kiro/specs/ & .kiro/steering/"] --> TB["Structured Task Brief\ndocs/kiro_task_*.md"]
  TB --> K["Kiro CLI / ACP\nWrites code, tests & report"]
  K --> HK[".kiro/hooks/\nPostFileSave checks"]
  K --> V["Main-Line Independent Re-run\nTests & golden vectors"]
  V --> LG["Audit Ledger\ndocs/kiro_verified.json"]
```

### Kiro Features & Skills Used

| Kiro Feature | What Was Built & Used | Location |
|---|---|---|
| **Specs** | 32 spec folders (91 files) with `requirements.md`, `design.md`, and `tasks.md` covering physics PBT, shared constants, MCP standard, team battle, balance sim, i18n, and UI polish | `.kiro/specs/` |
| **Steering** | 11 steering docs defining product scope, architecture, coding rules, single-writer constraints (`index.html`), art pipeline, and UI aesthetics | `.kiro/steering/` |
| **Hooks** | 7 `PostFileSave` hooks automating engine tests, constants sync, preload block freshness (176 recorded save runs), picture orientation freeze, and ledger checks | `.kiro/hooks/` |
| **Custom Agents** | 8 scoped agents (`builder`, `tester`, `researcher`, `rules-reviewer`, `asset-inventory`, `daily-logger`, `committer`, `pk-player`); `pk-player` is restricted to public MCP tools | `.kiro/agents/` |
| **Kiro Power & Skill** | Custom Kiro Power (`pumpkin-killer-seat`) bundling an MCP server config and the **`play` skill** (`.kiro/powers/pumpkin-killer-seat/skills/play/SKILL.md`) for fair agent seat play | `.kiro/powers/pumpkin-killer-seat/` |
| **MCP Integration** | Workspace MCP configuration connecting Kiro directly to the game's stdio MCP server | `.kiro/settings/mcp.json` |
| **Property-Based Testing** | Seeded property runner checking non-negative damage, determinism, round hashes, weather bounds, flight termination, and hero balance bands | `scripts/test_properties.js` |
| **Kiro Surfaces** | **Kiro CLI** (`kiro-cli chat` via `scripts/kiro_route.py` and ACP via `scripts/kiro_acp_route.py`) wrote the Python engine, initial relay, MCP server, and early tests; **Kiro IDE** ran a save-triggered hook; **Kiro Crew 0.12.2** ran a read-only doc audit (`docs/crew_audit_usage_doc_result.md`) | `scripts/kiro_route.py`, `scripts/kiro_acp_route.py` |

Additional AI coding assistants handled later page wiring, team-battle integration, lobby AI fill, hosted MCP, and red-team fixes under the owner's direction; the owner decided every game rule and public text. Kiro results were independently re-run before acceptance (`docs/kiro_verified.json` records 38 audited verdicts across 112 result reports). An external review by GLM-5.3 and DeepSeek V4 Pro (Nebius Token Factory) wrote break-it cases and review notes; every claim was checked in the code and re-run before any change ([`docs/llm/llm_findings_verdict_20261126.md`](docs/llm/llm_findings_verdict_20261126.md)).

- Full honest account (including what worked and what did not): [`docs/KIRO_USAGE_20261116.md`](docs/KIRO_USAGE_20261116.md)
- Reviewer & judge evidence index: [`JUDGES.md`](JUDGES.md)

---

## Checked, Not Just Claimed

| What | Result | Evidence / Command |
|---|---|---|
| **Hit judging** (center fence broken, full power range) | 425,861 flight steps, 0 false hits, 0 missed hits (14.7% are area or returning weapons, exempt from the false-hit check) | `docs/hit_coverage_20261119.svg` |
| **JS page vs Python engine flight parity** (both directions, wind & weather) | 67,456 shots each way, 0 mismatches | `docs/rear_rear_weather_wind_20261119.json` |
| **Team engine simulation** | 6,667 matches at each of 1, 2, and 3 units per side, 20 rule checks, 0 failures | `redteam/evidence/sim_team_full_run2_20261122_summary.txt` |
| **Built-in AI hit rates** (hits per throw) | Easy `0.141`, Normal `0.332`, Hard `0.462` | `node scripts/test_page_ai_hit_rates.js` |
| **Full test suite** | 184 `test_*` scripts (`97 JS + 1 MJS + 86 Python`) + `sim_team_headless.py`. `zsh scripts/run_full_suite.sh` passes with 0 failures (178 run in batch; 6 local-socket tests skipped there and verified separately alongside relay, MCP claim, MCP risk, and deploy checks) | `redteam/evidence/recheck_full_suite_v3_20261125.txt`, `redteam/evidence/recheck_socket_v3_20261125.txt` |
| **Deployed container E2E** | Built and verified locally: page, relay, MCP, and health checks respond through nginx; late join into a started room is refused; foreign origins are blocked | `redteam/evidence/prepush_docker_e2e_20261124.txt` |

Run the test suite:
```sh
zsh scripts/run_full_suite.sh
```
Or run JS and Python tests individually (`for t in scripts/test_*.js; do node "$t"; done` and `for t in scripts/test_*.py; do python3 -B "$t"; done`; relay, MCP, and smoke tests open local sockets).

---

## What Is Inside

| Part | Location |
|---|---|
| **Game client** (HTML5 canvas, `index.html`, modular JS, CSS, PWA) | `index.html`, `js/`, `css/`, `sw.js`, `manifest.webmanifest` |
| **Shared deterministic rules & golden vectors** (seeded starts, wind, dice, coin toss, `round_hash`) | `js/determinism.js`, `scripts/determinism_py.py`, `shared/` |
| **WebSocket room relay** (random codes, ordered replay log, reconnect, team rooms) | `scripts/pk_relay.py`, `js/relay_client.js`, `docs/relay_protocol_20261115.md` |
| **Python rule engine & MCP servers** (stdio + Streamable HTTP `/mcp`, 7 game + 3 room tools) | `scripts/mcp_game_server.py`, `scripts/mcp_stdio_server.py`, `scripts/pk_mcp_http.py`, `docs/mcp_agent_protocol.md` |
| **Balance simulators & property-based tests** | `scripts/sim_balance.js`, `scripts/sim_team_headless.py`, `scripts/test_properties.js` |
| **Optional smart-opponent gateway** (server-side, capped daily/budget limits; browser never sees a key) | `scripts/pk_ai_gateway.py`, `shared/ai_models.json` |
| **Container & Coolify deployment** | `deploy/` |

---

## Licence & Provenance

MIT Licence — see [`LICENSE`](LICENSE). Inspired by Flash-era artillery games; third-party licences, audio sources, and generated-art disclosures are documented in [`CREDITS.md`](CREDITS.md) and [`docs/ASSET_PROVENANCE.md`](docs/ASSET_PROVENANCE.md).
