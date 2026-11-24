# Seats and items: requirements

Scope: `index.html` turn and input code, the start screen, `assets/i18n/*.json`. Terms: **side** is `left` (today `player`) or `right` (today `ai`); **seat** is who controls a side: `human`, `ai` (the built-in opponent) or later `agent`; **active side** is the side whose turn it is.

## R1 Seats
1. The start screen shall offer two seat rows, one per side, each with `Human` and `Built-in AI` (default: left Human, right Built-in AI). A match shall have at least one human seat; both seats `ai` is not offered (owner 2026-11-16: no AI against AI in the product).
2. With two human seats the game shall run on one screen: all input (aim, charge, throw, move, defend, ultimate, skills, items) shall act on the active side's unit; the dock, the ultimate button and the power meter shall show the active side's hero.
3. Between two human turns a curtain shall hide both aim lines and the knight's stored points until the next human taps it ("Right side, tap to start"); the 12 s timer starts after the tap.
4. The right side aims mirrored: the throw direction is toward the left, the pointer origin is the right unit.
5. Win, lose and result texts shall name the sides ("Left wins") when both seats are human.

## R2 Symmetric items
1. OWNER 2026-11-16: ONE use each. The skills heal (35 hp, once), double shot (once) and heavy shot (once, 1.5 x damage) shall exist per side with the same counts and rules (the free-action rule of heal does not change); the built-in opponent shall use them (heal when under 45 percent hp and a charge is left; heavy and double with a 20 percent chance each when a charge is left and the target is in range).
2. The supply item "heavy" shall add a heavy charge to the side that picks it up (today it adds to the left side whoever picks it up).
3. Using a skill shall not depend on the side being `player`: no code path shall test `isPlayer` to decide whether a skill exists.

## R3 Evidence
1. `scripts/test_seats_items.js` shall check R1.1, R2.1 and R2.2 by reading the code or running the pure helpers (`skillChargesOf(side)`, `seatOptionsValid(left, right)`).
