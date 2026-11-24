# Kiro task 97 — make the Kiro IDE load our MCP server and hooks (IDE evidence for the judges)

What the main line saw in the Kiro IDE on 2026-11-15 (window "pumpkin-killer", folder trusted, saved `index.html` once):
- The hook `(not published)` DID fire on save (evidence: `docs/kiro_evidence/raw/ide_hook_run_20261115.txt` and `.jpg`).
- In the IDE side panel "Agent Hooks", the three `.kiro.hook` files show a "Migrate" button (the IDE treats the format as legacy), and the three hooks of `(not published)` are shown greyed out and did not write to `docs/kiro_evidence/raw/hook_runs.log` on that save.
- The side panel "MCP Servers" is EMPTY: the IDE chat said the tool catalogue has no pumpkin-killer tool (`docs/kiro_evidence/raw/ide_mcp_attempt_20261115.txt`). The same `.kiro/settings/mcp.json` is read by `kiro-cli mcp list` (server `pumpkin-killer` under the default agent).

Read: `(not published)` (Hooks and MCP sections), `(not published)`, `.kiro/hooks/*`, `.kiro/settings/mcp.json`, `.kiro/powers/pumpkin-killer-seat/`, the two evidence notes above. You may read the official pages only through those local copies (no network).

Deliver, saving each as soon as it is written:
1. `(not published)` (max 40 lines): your best-supported explanation of why the IDE shows no MCP server (for example the file location the IDE reads, a required field, a restart, the trust state, or the IDE reading user-level config only), and the same for the greyed `pk-checks.json` hooks. Mark each statement "from a local doc" (cite file and line) or "guess". Do not claim anything you did not read.
2. If a local doc supports it, a minimal change to `.kiro/settings/mcp.json` or a new equivalent file, and a conversion of the three `.kiro.hook` files and the three `pk-checks.json` hooks to the format the IDE's "Migrate" button expects (keep the same names, triggers, patterns and commands; keep a copy of each old file under `(not published)`). If no local doc says what the new format is, do NOT guess a format: write the open question in the findings file and stop.
3. After any change run `python3 -B scripts/test_mcp_stdio.py` and `python3 -B scripts/test_mcp_game.py` and paste the last lines.

Do not edit `index.html`. Do not install anything or change anything outside this repository (no edits under the home folder). No network, no git. Write the result file `(not published)` (max 20 lines): files changed, commands with last output lines, what you did not run.
