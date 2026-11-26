---
inclusion: always
rewritten-by: Kiro, 2026-11-08
updated-by: Kiro task 18, to match docs/game_mode.md and the repo today
---

# Game rules (constraints)

> **Historical note (2026-11-08 baseline):** The `4 vs 4` draft below was later cut by the owner; the shipped **Resurrection** build supports **1v1, 2v2, and 3v3** with eight heroes, lobby invites, and `PageJudgeRelay`. See `README.md`, `JUDGES.md`, and `shared/heroes.json` for current shipped rules.

Restated from `docs/game_mode.md` (confirmed by the owner, 2026-11-08). Do not
change any of these without asking the owner first. If code disagrees with a
rule, report it; do not change the rule to match the code.

## Turn and throw

- Turn based. Hold to charge, release to throw. The power meter ping-pongs 0..100.
- Aim angle is 25..80 degrees, default 54.
- Wind is a horizontal acceleration on the projectile, range about +/-4, shown at
  top centre.
- A fence stands in the middle and can be destroyed.
- Each unit gets ONE throw per turn.
- Turn timer is 12 s in the prototype. The mockup shows 8 s; this is undecided.
  If the timer ends, the turn is forfeited.
- HP 0 ends the game.
- Round order: human phase first, then agent (AI) phase. The opposing side
  attacks one unit after another, not all at once.
- The thrown weapon really leaves the hand. A new one is supplied automatically
  0.55 s later.

## Characters

- Characters are small; weapons and effects are large and readable.
- One horizontal-mirror rule for all characters: art is drawn once facing LEFT and
  mirrored for the other team. Everyone faces the enemy.

| Class | HP | Thrown weapon |
|---|---|---|
| Bat-cat assassin | 90 | throwing darts (shuriken) from a belt bag (owner 2026-11-09; was a silver dagger). Fastest. |
| Pumpkin wizard gunner | 85 | cannonball from the shoulder cannon (muzzle flash, smoke, recoil, camera shake) |
| Skeleton spearman | 100 | long wooden spear, javelin throw, arm arcs over the shoulder |
| Pumpkin heavy shield knight | 120 | small thrown shield |

## Floating shield (Pumpkin Guard only)

- Only the Pumpkin Guard can choose Defend. No other class can.
- His attack is a small thrown shield, not a pumpkin ball. If the shield is in his
  hand he can throw it.
- Defend removes the shield from his hand and places a shield in the sky: a thin
  glossy horizontal bar that materialises like a spell effect, not a solid prop.
  With the shield in the sky his hand is empty, so he cannot attack that turn.
- Defend flow: the shield covers TWO areas. Pick Path 1, pick Path 2 (each snaps to
  one of the remembered enemy flight paths; the last 4 enemy paths are
  remembered), then press Confirm. Each path blocks once (2 blocks total).
- The bar slides left and right only; its height follows the remembered path at
  that x. It lasts 2 rounds.
- Re-placing the shield costs the unit's turn (the earlier "1 placement + 3 moves"
  idea is kept for re-placing).

## Move action

- The player picks forward or backward, then a die (1-6) sets the distance at 36 px
  per pip (36..216 px). The owner asked for bigger steps than the first 16 px version.
- Moving does NOT use the turn: the unit can still attack after moving. One move
  per turn.

## Decided, not built (owner decisions in `docs/game_mode.md`)

- Airdrop items go into ONE slot per unit. Picking up a new crate replaces the old item.
- Each class gets its own ultimate trigger: Skeleton 3 hits; Bat 3 hits or 3 dodged
  shots; Wizard 4 hits; Knight 3 sky-shield blocks (or 2 blocks + 1 hit).
- Ultimates in general, the double-shot energy bar and crate contents are NOT
  confirmed. Do not invent damage, radius or cooldown values.

## Agents (fairness)

- Sub-agents see only public information: positions, wind, past landing points.
- No hidden state. No ballistic simulator is handed to agents.
- AI aiming accounts for wind by simulating with the same integrator the
  projectiles use.

## Throw drama

- On a throw, a large portrait of the ATTACKER ("big head") shows in the bottom
  bar and reacts: charging face, shout at release, smirk or hit face. It sits
  together with the arm arc, muzzle and impact effects, and camera shake.

## Target mode: 4 vs 4 (mockup only, flow unconfirmed)

- Per round every unit picks one action (Throw, Move or Defend), then presses Lock.
  Humans resolve first, then agents. A unit that defends cannot throw that round.
- Bottom bar: selected unit portrait and HP, three action buttons, angle selector,
  power bar, ammo slot, special weapon slot, Lock button. Top bar: 4 PLAYERS,
  round and timer, wind, 4 AGENTS.
- Per-unit HP bar with a marker (1-4 for players, A-D for agents), landing rings,
  dashed aim arc.
- Do not build this flow until the owner confirms it.

## Known mismatches with the current prototype

Report these; do not resolve them by editing the rules.

- `index.html` still implements the Defend flow as dragging the shield, with a
  counter of 4 (1 placement + 3 moves) on the shield button, not Path 1 / Path 2 /
  Confirm. The MCP server (`scripts/mcp_stdio_server.py`) takes `path1` and `path2`
  but enforces only path1 for now (owner decision, see
  `.kiro/specs/mcp-standard/tasks.md` task 10a).
- The prototype is 1 vs 1, not 4 vs 4.
- The Pumpkin Guard now throws a small shield (`HERO_PROFILES.knight.weapon` is
  `proj_shield`) and the Bat throws darts (`proj_dart`). Those two earlier
  mismatches are closed.
