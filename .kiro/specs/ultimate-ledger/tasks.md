# Tasks: ultimate ledger

Kiro task 42 (all done):
- [x] 1. Read `docs/ultimate_rules.md`, `docs/ultimate_mapping.md`, `(not published)`, and the energy / `ultArmed` / `ultUsed` / `executeThrow` code in `index.html` (read only).
- [x] 2. Write this spec: requirements (23, each checkable), design.
- [x] 3. `js/ultimate.js`: `createLedger`, `registerHit`, `canArm`, `arm`, `cancel`, `consume`, `registerKO`, `getState`, `reset`, `splitDamage`, constants, reasons. (Req 1 to 20)
- [x] 4. `scripts/test_ultimate.js`: 24 tests including a 300-script shadow-model property. (Req 1 to 23)
- [x] 5. Run `node scripts/test_ultimate.js` and record the last line in `docs/implementation_report.md`.
- [x] 6. Write the wiring note for the main line in `docs/implementation_report.md`.

Handed to the main line (not part of task 42; `index.html` was not touched). See the wiring note in `docs/implementation_report.md`:
- Create one ledger per match and `reset()` it in `resetGame()`.
- Replace `energy`, `ultUsed`, `countedThrows`, `ultArmed` and `toggleUltimate()` by ledger calls.
- Menu entry `✨ 大招` from `canArm`; every disarm path calls `cancel`.
- MCP: map the reasons to rejection codes and the state to the public fields.
