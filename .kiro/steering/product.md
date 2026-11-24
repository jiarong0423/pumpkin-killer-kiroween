# Product

> *Historical snapshot (early November 2026): the project later evolved to 1v1–3v3 team battles, mobile landscape PWA support, and the Kiroween **Resurrection** category; see `JUDGES.md` and `docs/ARCHITECTURE_FULL_20261124.md` for the final shipped build.*

Pumpkin Killer is a short-turn Halloween artillery game for up to four humans
versus four sub-agents.

## Principles

- Feel first: angle, hold to charge, release, see the result, correct. No
  preview or confirm step before a throw.
- One rules engine. Humans and sub-agents both act through MCP tools. Nothing
  in the UI changes game state directly.
- Fair agents. Sub-agents get public information only, one decision per round,
  and the same published aim error as everyone else. They are not made weaker
  on purpose.
- Humans versus AI is the showcase. The AI cannot cheat: no trajectory
  simulator, no trial throws, no hidden state. It only gets the public wind
  value and a record of past landings, and must learn from that record the way
  a human does. The match should show both sides getting better round by round.
- Costume Contest bar: a polished haunted UI (graveyard, ghosts, candlelight)
  that helps readability, not decoration only.

## Non-goals

- Real-money features, accounts, or cloud persistence.
- Mobile layout in the first version.
