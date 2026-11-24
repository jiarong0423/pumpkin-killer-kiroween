# Kiro task 184 result

## What changed

- `index.html`
  - Added `seats`, `activeSide()`, `unitOf(side)`, `teamOf(side)`, `skillChargesOf(side)`, `isHumanTurn()`, and `seatOptionsValid(left, right)`.
  - Added `buildSeatRows()` to expose left and right seat choices. The default is left human and right built-in AI. The all-AI combination is disabled.
  - Added `showTurnCurtain()` and `advanceAfterAttack()` for the hand-off between two human seats, plus mirrored right-side pointer aiming in `aimFromPointer()`.
  - Made `startCharging()`, `releaseAndThrow()`, `selectSkill()`, `useSupply()`, `updateDock()`, and the timer use the active human seat. The dock reads the active unit and its skill charges.
  - Changed skill charges to one `double`, one `heavy`, and one `heal` charge for each side. The AI heals below 45 percent HP and has independent 20-percent heavy/double decisions when the opponent is in range.
  - Changed the heavy supply item to credit the side that collects it and changed `useSupply()` to render `T(it.labelKey)` through the pickup text.
  - Added side-named game-over text when both seats are human.
  - Added relay-controlled room controls, `?relay=` and `?room=` handling, `connectRelay()`, `renderRoomDetails()`, and QR rendering of the complete join URL. With no `relay` query parameter, the controls remain hidden and offline play retains its existing start flow.
  - Loads `js/relay_client.js` and the new QR module before the game script.
- `js/qr_code.js`
  - Added a dependency-free UMD QR encoder: UTF-8 byte mode, error-correction level L, QR versions 1 through 5, Reed-Solomon error correction, mask selection, and canvas drawing.
- `assets/i18n/en.json`, `assets/i18n/zh-TW.json`
  - Added the seat, curtain, room, and side-wins text keys used by the page.
- `assets/fonts/*`, `sw.js`
  - Rebuilt generated font subsets for the new Traditional Chinese text and refreshed the generated service-worker precache.
- `scripts/test_seats_items.js`
  - Added checks for seats, validity, active-side helpers, one-use per-side charges, supply attribution/text, AI thresholds, and successful parsing of the inline game script.
- `scripts/test_join_flow.js`
  - Added start-screen/relay/QR wiring checks and a fake-socket create-room plus join-room sequence check.
- `scripts/test_qr_code.js`
  - Added byte-mode capacity, the `HELLO WORLD` data-prefix vector, finder/timing matrix invariants, and capacity-rejection checks.
- `.kiro/specs/seats-and-items/tasks.md`, `.kiro/specs/cross-device/tasks.md`
  - Marked the scripted seats/item tasks and cross-device join task complete. The browser-only curtain task and the full-suite task remain unticked because I could not perform those checks.

## Commands run

```sh
node scripts/test_seats_items.js && node scripts/test_join_flow.js && node scripts/test_qr_code.js && node scripts/test_i18n.js && node scripts/test_relay_client.js && node scripts/test_sim_balance.js
```

Output tail:

```text
seats and symmetric one-use items: ok
join flow fake socket and QR wiring: ok
qr code byte-mode L vectors: ok
26 passed, 0 failed (225 keys per language)
relay client reconnect and hash checks: ok
test_sim_balance: all 28 tests passed
```

```sh
python3 -B scripts/test_fonts.py && python3 -B scripts/make_sw_precache.py --check && python3 -B scripts/test_constants_sync.py
```

Output tail:

```text
Ran 36 tests in 0.393s

OK
OK sw precache is up to date (61 files; 20 preload assets; pk-6d9a90c10b)
OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.
```

```sh
python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_mcp_stdio.py
```

Output tail:

```text
🎉 ALL NEW POSITION / WALL TESTS PASSED!

Ran 29 tests in 1.888s

OK
```

```sh
git diff --check
```

The command exited 0 with no output.

## Checks I could not complete

The task-required aggregate JavaScript loop did not run. The exact command was:

```sh
for f in scripts/test_*.js; do node "$f" || exit $?; done
```

The environment denied it before execution. Its only output was:

```text
The permission request failed before it was answered, so this call did not run; the user did not reject it.
```

I could not open a browser in this run. The QR test checks the published byte-mode `HELLO WORLD` payload prefix and QR structural invariants, but I did not independently compare the final masked matrix against an external QR-standard matrix in this environment.

## Browser checks for the main line

1. Select a human seat for both left and right. Start a match, finish the left throw, and confirm the opaque curtain hides the next player’s view until the right player taps **Right side, tap to start**. Confirm the 12-second timer begins after that tap and the right-side pointer aims toward the left.
2. Leave the default left human/right built-in AI seat pair. Confirm the normal offline match starts, the AI takes the right turn, and both sides show one charge for Heal, Double, and Heavy on their respective turns.
3. Open the page with `?relay=ws://host:port`. Confirm **Create room** and **Join with a code** appear. After room creation, confirm the relay-issued code, a scannable QR code, and a link containing `?room=<code>` appear.
4. Open that `?room=<code>` link with the same `relay` parameter on a second device. Confirm it joins the open right seat. Then return to an offline URL without `relay` and confirm room controls are hidden.
5. At a portrait phone viewport, confirm the existing rotate hint still covers the page and remains legible.
