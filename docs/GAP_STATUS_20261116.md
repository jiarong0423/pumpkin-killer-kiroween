# Gap status, 2026-11-16 (rewritten after the all-hero wiring; facts re-run today, replaces the 00:35 version)

## Done and verified today
- All 8 heroes (skeleton, wizard, bat, knight, necromancer, bride, hunchback, nun) are playable with wind-up, release and hit frames (`python3 -B scripts/pose_audit.py`: nothing missing in the page).
- Every hero has its own ultimate in the page; the knight's is the three free-chosen hidden coffin points (3 enemy rounds, no turn cost).
- Weather (rain, storm, snow, fog), wind (head 84, tail 56, every position still hits every target), no constant trembling, one-shot hit recoil with a short screen jolt.
- Tests re-run 2026-11-16: 26 node tests pass; python 31 of 36 pass. The 5 failures: 2 are stale fixtures, 3 need a socket/network the sandbox blocks (see Open 8). Fonts: rebuilt, 25 missing characters fixed (commit a569259).
- Local commits only; NOTHING pushed.

## New owner requirement 2026-11-16 (not built): free seat assignment
- Each of the two sides can be assigned freely to a human player, a sub-agent (MCP) or the built-in opponent, and both sides may be players (human vs human, agent vs agent, human vs agent). The page today has only "you against the built-in opponent" (no seat concept in index.html); the MCP engine has `--seat white|red` and `--opponent builtin:*`; the relay draft has seat choice. To do: a seat setting on the start screen (side 1 and side 2: human / agent / built-in), the second human side mirrors the same controls on its own turn (same-screen hot-seat first, the relay later), agent seats go through the existing MCP server.

## Open, in the order I would do them
1. Sounds (owner action): `move_step`, `ultimate_ready_chime`, `item_pickup` return 404 in the page. Owner downloads the Kenney Interface Sounds zip (CC0) into `(not published)`; I extract, check the licence file, convert to ogg, add credits.
2. Wizard cannonball: in the scripted demo it landed about 90 px short (x 1363 for a target at 1450). In a full harness match (wizard vs skeleton, skill 1.0, 4 rounds) round 1 missed and rounds 2, 3, 4 hit (enemy HP 100, 78, 55, 33, then dead), so the damage path works; the first-shot miss is not explained yet (estimate versus launch, or the enemy moving).
3. Balance numbers need owner picks (from `docs/character_plan_review_20261116.json`): reaper hit width and HP, skeleton damage, nun damage and ultimate factor, whether bride and hunchback ultimates stay above 1.5x, two heroes sharing the same HP. Three-reviewer playtest result: section below.
4. Reaper burn status is not implemented (the owner's plan names it).
5. Hunchback has no clean throw/release frame (the generated ones were dirty); the empty-handed stance is the placeholder.
6. Owner's screen recording was unreadable (permission); owner was asked to put it in `(not published)`.
7. Stale tests: `test_apply_i18n_plan.py` (the plan is already applied, so it says SKIP and exits 1) needs its fixture refreshed.
8. Tests that need the owner's own terminal (socket or port): `test_mcp_connect.py`, `test_mcp_connect_weather.py`, `test_smoke_url.py`. Not a game defect.
9. Relay (rooms, invitation codes, WebSocket): protocol drafted in `docs/relay_protocol_20261115.md`; no server code yet; deploy only when the owner says.
10. PWA install button; MCP weather in the page round hash decision; English write-up, video and Devpost text (owner-only); push (owner permission); delete `refs/backup/pre-trailer-strip-20261116` when the owner confirms.

## Asset gaps (checked 2026-11-16 against the files: 138 asset paths named in index.html, js, css, sw.js and i18n; only 2 do not exist; 344 files in the Drive out folder; `scripts/make_gap_matrix.py` rerun: OK 115, queued 13, MISSING 8, its "queued" cells are stale because the pictures are already made)
**A. Named in the page but the file does not exist (404, sounds, 2):** `(not published)`, `(not published)` (`js/audio.js`; `move_step` falls back to an existing sound). Needs the CC0 download by the owner; no verified CC0 source yet for the chime.
**B. Art nobody has made (nothing on Drive, nothing installed):**
- skeleton charge2 pose; bat charge1, charge2 poses and bat front portrait (bat shows the other frames and the unit picture, so it plays; these only add polish).
- hunchback clean throw/release frame (placeholder: empty-handed stance); ui_poison_bubble (status icon); hand-breakdown frames 3 to 6 of the nun (not needed by the page).
- Class stats row for the nun is only in `index.html` (not in `js/class_stats.js`): a code gap, not art.
**C. Made on Colab, on Drive, looked at, NOT installed and no code in the page uses them (decide: wire or drop):**
- status icons: ui_frost_curse, ui_bleed_drop, ui_burn_flame, ui_cross_curse, ui_hallucination_mark (the page shows statuses with code-drawn effects and floating text; wiring means a small icon above the HP bar).
- ultimate art: ult_spectral_spear, ult_ricochet_shield, fx_shockwave_ring (the page draws its ultimates from `js/ultimate_fx.js` and particles, so these are optional upgrades); ult_pip_socket exists only as a particle preset.
- coin_pumpkin_head / coin_pumpkin_tail (no coin flip in the page uses them), ghoststar_blow / ghoststar_blow_hard (the page has its own `fx_ghost_blow` pictures).
- nun: fx_cross_rain and fx_cross_rain_heal (obsolete since the owner changed the nun ultimate to a spinning cross), fx_black_smoke (page draws smoke itself), hag_empty (not used), necro_front (reaper front portrait already installed).
- scenes: indoor variants bg_ruined_church_b, bg_abandoned_school_b (the page uses one picture per scene), pumpkin field (removed by the owner).
**D. Already done and installed (do not redo):** all 8 hero unit pictures and wind-up/release/hit sets, 7 front portraits, silver cross layer, knight unarmed, feet chain, 3 new scenes, fonts rebuilt today.
**Arbitration result for A to C (three asset arbiters, majority; each vote from the code; done = committed):**
| Item | Votes | Decision |
|---|---|---|
| Missing sounds | all three: use existing files, no download | DONE: `item_pickup` plays `chime_single.ogg` (CC0, BigSoundBank), `ultimate_ready` is synth-only (file null); `test_audio` 32/32; 404s now 0 |
| Status icons (frost, bleed, burn, cross, hallucination, poison) | WIRE-minimal / LATER / DROP | DROP as pictures: owner rule 2026-11-10 (nothing turns above the head except the stun stars; statuses show on the body: drops, bubbles, blue flash, feet chain). The HP-bar badge row has no code; a small code-drawn count beside the bar can be judged later |
| ult_spectral_spear, ult_ricochet_shield, fx_shockwave_ring | DROP / LATER / LATER | LATER (code and particles already make the ultimates) |
| Pumpkin coins | DROP / DROP / LATER | not wired now; revisit with the seat/lobby feature (owner 11-10 wanted a coin toss); pictures stay on Drive |
| ghoststar_blow(_hard), nun cross rain/heal, black smoke, hag_empty, necro_front, indoor scene variants | DROP | DROP (duplicates or obsolete; scene variants would also enter the preload list) |
| skeleton charge2, bat charge1/2/front, nun hand frames 3 to 6 | DROP / DROP / LATER | not made |
| Hunchback clean throw frame | MAKE / MAKE / LATER | MAKE (one Colab picture; the only new art approved) |
| Licence paperwork (arbiter 3) | | TO DO: `docs/ASSET_PROVENANCE.md` lacks portraits, fonts, new scenes, new heroes, ui and fx; 21 audio files have a CREDITS line but no licence file (ambient 13, bell_round, bones_rattle, chime_single, rock_break, step_leaf, 3 music); CREDITS author error for whoosh_spear and heartbeat (BigSoundBank, not Kenney); `(not published)` has an unknown source and must not ship |
**E. Needed for the new seat feature and the relay (not art yet):** a seat selector panel and a "waiting for the other side" screen need UI pictures or CSS only.

## Colab
- Round-9 queue finished; the notebook releases the A100 by design. New picture jobs only if a gap above needs one (hunchback release is the only candidate).
