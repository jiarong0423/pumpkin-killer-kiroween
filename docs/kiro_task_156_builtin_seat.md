# Kiro task 156 — K2: built-in practice seat and a headless match runner (from the Opus review)

Owner answers 2026-11-15 (end of `(not published)`) keep: agents see public information only; the adaptive level is public; the built-in AI is only the practice opponent. K1 (seats) and task 150 (turn safety, coarse path, timers) are done and verified: do not weaken their tests.

Read: `docs/mcp_architecture_opus_20261115.md` (sections 2, 5, 6 K2), `scripts/mcp_stdio_server.py`, `scripts/mcp_game_server.py`, `scripts/agent_levels.py`, `scripts/sweep_agent_levels.py`, `js/adaptive_level.js` and `scripts/test_adaptive_level.py` (levels), `scripts/eval_agent_learning.py`, `scripts/test_mcp_stdio.py`, `scripts/test_mcp_seats.py`, `scripts/test_mcp_turns.py`.

Do, saving after each, one shell command per call:
1. `scripts/mcp_stdio_server.py`: `--opponent builtin:<level>` (levels `easy`, `normal`, `hard`, `adaptive`, taken from `agent_levels.py`) drives the OTHER seat in-process through the same six-tool client path that a real agent uses (no private access to the engine's hidden state); `get_public_state` gains the public fields `ai_level`, `ai_reason` and `engine` (`"py-practice"`).
2. A server-side public transcript (JSONL, `--transcript PATH`, off by default): only public fields, one line per tool call and result; never the seed, never a seat's own hidden aim for the other seat, never a token or a local path.
3. `scripts/pk_headless_match.py`: runs a whole match between the in-process built-in seat and a scripted stand-in agent (a simple function that uses only `get_public_state` and `get_history`), prints the winner and the rounds, and writes the transcript; seeded and deterministic.
4. `scripts/test_pk_headless_match.py` (`unittest`): two runs with the same seed give identical transcripts; the transcript contains no seed digits, no hidden aim, no home path; the built-in seat cannot read what a real seat cannot (a test that its view equals `view_for(seat)`); the match ends. Run it with the existing MCP tests and paste the last lines. If a command is refused, say so; never invent output.

Touch only `scripts/mcp_stdio_server.py`, `scripts/pk_headless_match.py`, `scripts/test_pk_headless_match.py`, and the result file exactly named `docs/kiro_156_result_gpt-5.6-terra.md` (max 15 lines). Never `index.html`, never the relay files, never the sync kit files of task 155. No network, no git.
