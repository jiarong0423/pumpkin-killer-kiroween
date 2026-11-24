# Team battle (1 to 3 units per side): requirements (owner 2026-11-16: "change it to 3v3")

Scope: `index.html` unit state, turn flow, layout, HUD, start screen, AI; later the relay judge. Terms: **team** is a side (left or right); **unit** is one hero on the field; **active unit** is the unit that acts in the current turn; **N** is the number of units per side chosen on the start screen (1 to 3, the same for both sides in the first version).

Compatibility note: the engine formerly accepted 4 units per side; supported sizes are now 1, 2, and 3.

## R1 Choice and defaults
1. The start screen offers N = 1, 2, or 3; the default is 1 and 1 behaves exactly like today (every existing test stays green).
2. Each unit of a team has its own hero (picked on the start screen; duplicates allowed) and starts with its own hp, its own supply slot, its own one-use skills (heal, double, heavy) and its own energy for its own ultimate (max 2 ultimates per unit per match).
3. At least one human seat; no AI against AI (unchanged).

## R2 Turns
1. Teams alternate turns as today; inside a team the active unit rotates in a fixed order, skipping dead units (the Worms pattern); the active unit is marked by ONE steady YELLOW ring under its feet (#ffd32a, on the ground line, same size for every unit) and nothing else: no arrow, no glow, no blinking, no pulsing (owner 2026-11-16); the player cannot pick another unit in the first version.
2. The turn timer, aim, throw, move, defend, ultimate and skill rules apply to the active unit only. Statuses tick at the start of each team's turn for every unit of that team. The match ends when one team has no unit alive.
3. Wind and weather are per match as today.
4. FREEZE (owner 2026-11-16): when the turn passes to a unit, every other unit is frozen: idle pose, no animation, no timers, no pickups, not selectable; only the active unit acts. Status ticks still apply at the start of a team's turn.

## R3 Layout
1. Start positions come from the match seed (`Determinism.startX(seed, side, slot)`, slots 0 to N-1): units of a team are spaced at least 90 px apart inside their zone and drawn with a small vertical stagger (alternating 0 and 14 px) so sprites overlap less; the draw order is back to front.
2. The size of a character never changes with N (owner: character size and ratio are locked, `shared/size_frozen.json`).
3. The hit test checks every enemy unit; a projectile hits the first unit it meets; units of the same team never block own shots.

## R4 HUD
1. The top plate shows the ACTIVE unit of each team in full (avatar, name, hp, status chips); the other units of a team appear as a row of small avatars with a thin hp bar under the plate; a dead unit is greyed.
2. Each unit has its own supply slot, but a player's screen shows only the player's own slot contents; the other team's slots show a question mark or nothing (owner 2026-11-16).
3. Above each unit: a thin hp bar and, for the active unit, the energy pips; no number overlaps another unit's bar (bars are staggered with the unit).

## R4b Items belong to their owner (owner 2026-11-16: "each has its own item slot, with a guaranteed base")
1. Every unit has its own supply slot and its own baseline: the three one-use skills (heal, double, heavy) are guaranteed to each unit at the start and can never be taken, lost or shared.
2. A supply crate is assigned to one side when it is dropped and only units of that side can pick it up (today either side can walk to it); the side that has received fewer crates gets the next one (a pity rule: nobody goes more than 4 rounds without a crate while crates are dropping); a crate nobody takes expires after 3 rounds as today.
3. A picked item goes into the slot of the unit that picked it up; using it applies to that unit only.

## R5 AI and seats
1. The built-in AI plays its active unit with the same rules as a human (one throw per turn, skills with the same one-use limits).
2. A human seat controls the whole team; two humans on one screen use the curtain as today.

## R6 Networking (second phase)
1. The relay `start` message carries N and the hero list per team; the attacker sends the unit id with each action; the owner of the target unit judges the hit.
2. The round hash covers every unit (id, x, y, hp, alive, statuses).

## R7 Evidence
1. `scripts/test_team_battle.js` runs the pure helpers (rotation order, skipping dead units, win condition, spacing, seeded slots) for N = 1 to 3; `scripts/test_sim_balance.js` and every existing test stays green; a browser check lists 1 v 1, 2 v 2, and 3 v 3 screenshots in the result file.
