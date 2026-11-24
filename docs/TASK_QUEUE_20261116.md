# Task queue, split small (2026-11-16 09:30; ACP route for Kiro, main line verifies every result)

Rules: one writer per file set; every task has its own brief, lock list, tests and result file; the main line re-runs the full test sweep after each result and commits only verified files (author is the owner, no Claude trailer). Supported team sizes are 1 to 3; the engine formerly accepted 4 per side. Run a task with `python3 -B scripts/kiro_acp_route.py --brief (not published) --expect (not published)` (live log `kiro_acp_<name>.log`, raw `kiro_acp_<name>.jsonl`).

| ID | Owner | Task | Locks (files) | Depends on | Status |
|---|---|---|---|---|---|
| 190 to 197, 202 | Kiro | phone fill, settings panel, usage doc, MCP 1 to 3, wiring+rooms, Gemini gateway, Smart seat, Shield Wall, meter sweep and hit report | many | | done, committed `beb21001` (202 has no result file: stopped after a failing loop, work verified by tests) |
| 199 (partly) | main | three regressions | | | done `d3029f6d` |
| hit radius | main | drawn projectile counts in the hit test | page, engine, sim | | done `b31c7e88` |
| 203 | Kiro | computer decides the side | index.html, css, i18n, determinism files | | queued now |
| 204 | Kiro | UI screenshots and ranked defect review (no page edits) | shoot script, (not published), ui_review | | queued now (parallel with 203, 206) |
| 206 | Kiro | QR encoder capacity, decode proof, site QR script | js/qr_code.js and tests | | queued now |
| 205 | Kiro | fix at most 8 cheap UI defects from 204 | index.html, css | 203, 204 | next |
| 207 | Kiro | QR lobby UI: large QR, copy link, hint | index.html, css, i18n | 205, 206 | next |
| 208 | Kiro | team step 1: unit state into teams, N=1 byte-identical | index.html | 207 | next |
| 209 | Kiro | team step 3b: items belong to their side, pity rule | index.html | 208 | next |
| 210 | Kiro | team N=2: rotation, ring, per-unit hp, hit test over enemy units, win rule | index.html, js/team_battle.js | 209 | next |
| 211 | Kiro | HUD for teams and start-screen N selector and per-unit hero picks | index.html, css, i18n | 210 | next |
| 212 | Kiro | the built-in AI plays N units | index.html | 211 | next |
| 213 | Kiro | N=3: spacing, draw order, phone readability | index.html, css | 212 | later (cut if not stable by 2026-11-25; last supported stage) |
| 214 | Kiro | relay and MCP carry unit ids on the page, round hash over all units | index.html, js/relay_client.js, engine | 212 | later |
| 215 | main | verify 195/196 with a fake gateway in the browser; Bedrock backend decision | gateway, index.html | owner's Bedrock choice | waiting for the owner |
| 216 | main | usage doc: IDE/CLI/Crew/ACP table, spec-vs-adhoc example, hook evidence, PBT seeds; re-measure the share | (not published) | after 214 | later |
| 217 | main | real-phone check of every UI change (adb) | | each UI task | ongoing |
| O1 | owner | privacy gate (PK_TERMS), clean export, private repo push go, Coolify app and tunnel route, domain | | | waiting |
| O2 | owner | video, English Devpost text, blog and social posts, image-model licence check, Bedrock or Gemini choice | | | waiting |
