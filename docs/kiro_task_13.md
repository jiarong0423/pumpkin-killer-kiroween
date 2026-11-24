# Kiro task 13 — make the game deeper (design proposal, documents only)

The owner feels the current rules are too simple and wants a more complex, more strategic game. Read everything first:
`docs/game_mode.md` (CONFIRMED rules and owner wishes: do not contradict them without flagging), `docs/ROLES.md`, `(not published)`, `(not published)`,
`(not published)` (4 vs 4), `docs/object_inventory.md` and `docs/asset_gap_report.md` if present, `scripts/mcp_game_server.py`, and skim `index.html`.
Hackathon context: Kiroween 2026, Costume Contest (polished, memorable spooky UI), judged on impact, technical use of Kiro, design, innovation, presentation. 54 days left but the owner
wants a playable, polished desktop build soon, then a phone version. A sub-agent opponent that LEARNS from public history (via MCP) is the innovation core.

## Do exactly this (documents only)
1. Write `(not published)` in plain English with:
   - **Diagnosis**: what is shallow today (be specific: decisions per turn, dominant strategies, information the player lacks, why the AI is easy or too perfect).
   - **12-15 concrete mechanics**, each with: name, rules in 3-5 lines with numbers, what decision it creates, how a sub-agent can exploit/counter it, interaction with the existing rules
     (Move with die, Defend only for the Pumpkin Guard, one throw per turn, wind, fence, 4-hit ultimates twice per match, double-shot energy bar, floating shield with 2 paths), implementation cost S/M/L,
     test strategy (property tests where possible), and risk (confusion, balance, UI clutter). Cover at least: status effects (poison, burn, shock), terrain/fence states, wind events and gusts,
     class counters and synergies (4 classes), team composition for 4 vs 4, resource economy (energy bar sources and sinks), positional play (move die vs cover), fog/uncertainty that stays fair to agents,
     comeback mechanics, turn-order tactics, hidden-information-free bluffing through public history, round modifiers (cards of the round), and agent-learning-friendly structure.
   - **A recommended minimum set** (3-5 mechanics) that adds the most depth for the least UI clutter, in build order, with what to cut.
   - **Balance sheet**: a table of class stats (HP, damage, range feel, strengths, weakness) and the numbers you would start with, plus a way to check balance with a headless simulation (describe the script, do not write it).
   - **Open questions for the owner** (max 8), each answerable in one word.
2. Write `(not published)`: every place where a proposal changes or stretches a confirmed rule, one line each, so the owner can veto.
3. Do NOT edit any other file. No git commands. Do not invent assets that do not exist; mark art needs as "needs Colab art".
4. Finish with a 6-line summary: your recommended minimum set and the single biggest risk.
