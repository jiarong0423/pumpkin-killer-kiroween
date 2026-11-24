# Kiro task 162 — record one MCP player match

Main line must run this task. Do not run it from this brief or ask the player agent to use shell, files, web, or any tool outside `pumpkin-killer`.

## Run from the repository root

The `pk-player` agent starts its own local stdio server from `.kiro/agents/pk-player.json`. That pinned server command includes `--seat white --opponent builtin:normal --transcript docs/kiro_evidence/raw/mcp_pk_player_match.jsonl`.

```sh
python3 -B scripts/kiro_route.py --brief docs/kiro_task_162_play_via_mcp.md --expect 'docs/kiro_162_result_*.md' --route gpt --agent pk-player
```

The main line must confirm that the transcript is saved at `docs/kiro_evidence/raw/mcp_pk_player_match.jsonl`. It must show at least one `submit_action` whose `is_error` is false. It must contain no hidden fields or values: `seed`, `rng`, `dice`, pending actions, opponent angle or power, tokens, notes, or a home path. The player must act only from `get_public_state`, `get_history`, and `get_notes`, and may record its own lessons with `set_notes`.

Save the agent's report as `(not published)` and retain the JSONL transcript at the evidence path above. If the CLI, MCP server, or tool approval prevents the run, record the actual failure and do not claim a recorded match.
