# Pumpkin Killer — game mode (confirmed by the owner, 2026-11-08)

Kiroween 2026, Costume Contest. A turn-based artillery-style throwing game: players and sub-agents
throw weapons over a fence in a haunted graveyard. Concept mockup: `(not published)`
(4 players vs 4 agents, floating platforms, ghosts carrying crates, landing rings, bottom control bar).

## Confirmed rules (do not change without asking)

- Turn based. Hold to charge (power meter ping-pongs 0..100), release to throw. Aim angle 25..80 degrees
  (default 54). Wind pushes the projectile as a horizontal acceleration (range about +/-4, shown top centre).
  A fence stands in the middle and can be destroyed.
- Each unit gets ONE throw per turn. Turn timer: 12 s in the prototype (the mockup shows 8 s: undecided).
  If the timer ends the turn is forfeited. HP 0 ends the game.
- Order inside a round: human phase, then agent (AI) phase.
- The thrown weapon really leaves the hand and a new one is re-supplied automatically shortly after
  (0.55 s). The wizard fires a cannonball from the cannon muzzle (flash, smoke, recoil).
- Characters are small, weapons and effects are large and readable.
- One horizontal-mirror rule for every character (like classic sprites): the art is drawn once, facing LEFT,
  and mirrored for the other team. Everyone must face the enemy.
- AI aiming accounts for wind (it simulates with the same integrator the projectiles use).
- Sub-agents only see public information (positions, wind, past landing points). No hidden state, no
  ballistic simulator handed to them.

## Heroes (class: HP, weapon)

| Class | HP | Thrown weapon | Notes |
|---|---|---|---|
| Bat-cat assassin | 90 | throwing darts from a belt bag (owner 2026-11-09; was: silver dagger) | fastest |
| Pumpkin wizard gunner | 85 | cannonball from a shoulder cannon | recoil, camera shake |
| Skeleton spearman | 100 | long wooden spear (javelin throw) | arm arcs over the shoulder |
| Pumpkin heavy shield knight | 120 | small shield, thrown (owner: the knight attacks by throwing a flying shield; no pumpkin ball) | the ONLY class that controls the floating shield |

## Floating shield (Pumpkin Guard only) — updated 2026-11-08

- The Pumpkin Guard's attack is a small thrown shield (NOT a pumpkin ball). If the shield is in hand, he can throw it.
- If he chooses Defend, the shield in his hand disappears and a shield appears in the sky as a blocking effect
  (a thin glossy horizontal bar that materialises like a spell effect, not a solid prop). With the shield in the sky
  his hand is empty, so he cannot attack that turn. Giving up the attack to place/move the sky shield is his choice;
  no other class can choose Defend.
- Defend flow: the shield covers TWO areas. Pick Path 1, pick Path 2 (each snaps onto one of the remembered enemy
  flight paths; the last 4 enemy paths are remembered), then press Confirm. Each path blocks once (2 blocks total).
- The bar slides left-right only; its height follows the remembered path at that x. Lasts 2 rounds.
- Moves: the earlier "1 placement + 3 moves" idea is kept for re-placing the shield (cost: the unit's turn).

## Move action (confirmed)

- The player picks forward or backward, then a die (1-6) decides the distance: 36 px per pip (36..216 px). Owner asked for bigger steps than the first 16 px version.
- Moving does NOT use the turn: after moving the unit can still attack. One move per turn.

## Turn order (confirmed)

- The opposing side attacks in sequence, one unit after another (not all at once).

## Target mode: 4 vs 4 (mockup; not built yet, needs owner confirmation of the flow)

- Per round every unit picks one action: Throw, Move or Defend, then presses Lock. Human units resolve first,
  then the agents. A unit that defends cannot throw that round.
- Bottom bar: selected unit portrait and HP, three action buttons, angle selector, power bar, ammo slot,
  special weapon slot, Lock button. Top bar: 4 PLAYERS / round + timer / wind / 4 AGENTS.
- Per-unit HP bar with a number marker (1-4 for players, A-D for agents), landing rings, dashed aim arc.

## Throw drama (owner request)

- A throw should feel dramatic: when a unit throws, a large portrait of the ATTACKER ("big head") shows in the
  bottom bar (the mockup's portrait panel) and reacts (charging face, shout at release, smirk/hit face), together
  with the arm arc, muzzle/impact effects and camera shake already built.

## Double shot needs an energy bar (owner request, details open)

- The double-shot skill must have an ENERGY BAR (visible meter that fills and is spent), instead of a fixed use count.
- Open questions: what fills it (successful hits? time? per round?), its size, and whether it is the same meter as the ultimate (4 successful hits).

## Ultimate move (owner mention, NOT confirmed - waiting for the owner's reference screen)

> **2026-11-09 owner: "I have not designed the ultimates yet."** Everything below is a draft from earlier chats. Any ultimate effect, sound or animation proposed by Kiro or the main line is a DRAFT: do not build it until the owner designs and confirms each class's ultimate.

- Unlike a traditional single-point throw, the ultimate turns the normal dart/spear throw into an AREA throw
  ("range darts"): one throw covers a zone instead of a single landing point.
- **Unlock rule (owner, final 2026-11-09): the ultimate energy bar fills after FOUR successful hits** (briefly said three, then confirmed four); at most 2 ultimates per match.
  **Owner 2026-11-09: each player counts their own hits** (not shared by the team). Still open: does a block / miss count (assumed: only hits count), does it reset after the ultimate (assumed: yes), and in 4 vs 4 whether "player" means each human / agent controller or each unit. Everything else about the ultimates is still undesigned.
  Open questions: does the counter belong to a unit or the team, and does a blocked or missed throw count as unsuccessful (assumed: only hits count)?
- Skeleton: the javelin ultimate becomes THREE consecutive throws.
- Dart-like weapons (bat dagger; owner said "similar to raining darts"): a volley that rains down over an area
  (assumed for the bat; confirm).
- Wizard: the pumpkin cannonball becomes a POISON shell: bigger blast area, poisons everyone it hits, damage over time for
  3 rounds, and a poisoned character turns GREEN while poisoned.
- Knight: the thrown small shield becomes a RICOCHET: it bounces on collision, and a die roll decides how many
  collisions it makes; each collision hits a character. (Open: bounce targets, damage per hit, does a 6 mean six hits.)
- The owner said this was discussed before, but no record of that discussion was found in the repo docs or past
  sessions. Details (damage, radius, cooldown, which classes, the cut-in screen) are unknown: do not invent them.

## Airdrops (owner idea, details open)

- Ghosts carry supply crates (see the mockup) and drop them onto the field. A unit picks a crate up by moving onto it (the Move die) or by
  other means to be decided; the crate fills an ITEM / SPECIAL-WEAPON SLOT (the slot in the mockup's bottom bar).
- Dropped items go into ONE slot (a single item slot per unit, as in the mockup's bottom bar): a unit holds at most one item at a time.
  DECIDED (owner): if the slot is already full, picking up a new crate REPLACES the old item.
- Open: what is inside (heal, ammo, poison shell, shield repair, extra die, energy), how often and where they land (random, seeded for tests), who may take a crate, and
  whether agents see crates in the public state (they should: it is visible to humans too).

## Ultimate trigger per class (owner direction, supersedes the single global rule where it conflicts)

- Every class gets its OWN trigger condition, for example "after three successful hits". The global default is 4 successful hits to fill the energy bar (owner 2026-11-09, final), max 2 per match, until each class is defined.
- DECIDED (owner confirmed the proposal): Skeleton = 3 hits; Bat = 3 hits or 3 dodged shots; Wizard = 4 hits (strong area ultimate); Knight = 3 blocks with the sky shield (or 2 blocks + 1 hit). Open detail: what exactly counts as a 'dodged shot' for the bat, and whether the counter resets after the ultimate.

## Art status (owner decision, 2026-11-08)

- Decision: use PLACEHOLDER art first (Kiro credits were approved on 2026-11-04 per the Devpost email; the art was made earlier)
  (the original four unit images, the baked sprites, programmatic effects) and replace it later.
- Final art is being generated on Colab (Qwen-Image-Edit-2509, `colab/jobs.json`, 41 jobs); until it lands the game keeps the
  placeholder look (`USE_LAYERED_HANDS = false` in `index.html`) and the write-up must say the art is placeholder / AI generated.

## Bat-cat darts and bag (owner, 2026-11-09 - confirmed by the owner's own words)

- The cat THROWS SHURIKEN (owner 2026-11-09: "change the dart to shuriken"; first it was darts) and carries a BAG (pouch) on its belt, and moves like an ASSASSIN (low crouch, quick flick, cape trailing). The action: the cat takes a shuriken out of the bag and flicks it out.
- Art plan: bag and dart are separate item sprites (`bat_shuriken_bag`, `bat_shuriken_item` in the Colab jobs, tier P1g) attached by the rig;
  the existing bat poses are reused, so the bag/dart are not redrawn into every pose. A pull-from-bag pose (hand to bag) may be needed.
- Open: does the bag show a dart count (ammo)? does the ultimate stay a rain of darts over an area (assumed yes)?
- The silver dagger art (`bat_dagger_item`) is kept as an unused spare.

## Technical facts (prototype)

- `index.html` (plain canvas) is the playable version; `scripts/mcp_game_server.py` is the MCP rule engine;
  shared numbers live in `shared/constants.json` (branch `kiro/shared-constants`).
- Physics: fixed 1/60 s step, gravity 980, launch speed = power * 13.8, wind acceleration = wind * 48.
- Art: `(not published)` (1024 px, facing left). New layered art is being
  generated on Colab (Qwen-Image-Edit) and will land in `(not published)`.
