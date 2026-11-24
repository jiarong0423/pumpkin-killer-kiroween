# Web research: scaling, hit shapes, turn netcode, turn flow, mobile (2026-11-17)
Public pages only, about 14 reads. "UNSOURCED" = could not confirm.

## 1. Scaling and coordinates
- Phaser FIT keeps aspect and letterboxes; ENVELOP covers and crops; gameSize (logical) is separate from displaySize (CSS). No safe-area advice there. https://docs.phaser.io/phaser/concepts/scale-manager
- Godot base size is a design size; stretch canvas_items for non-pixel art; aspect keep = bars, expand = use extra screen on tall phones. 20:9 not named. https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html
- Unity Canvas Scaler "Scale With Screen Size" = reference resolution plus match width/height. Confirms the one-logical-resolution pattern. https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-CanvasScaler.html
- Notch/safe area: env(safe-area-inset-*) plus viewport-fit=cover; apply left/right in landscape. https://developer.mozilla.org/en-US/docs/Web/CSS/env
- Collision vs art: the engine docs above do not say (Godot page explicitly silent). GDQuest treats hit/hurt shapes as dedicated shapes tuned apart from art. https://gdquest.com/library/hitbox_hurtbox_godot4
- Late art resize: no source found (UNSOURCED); only inference from GDQuest that independent shapes need no change.

## 2. Hit shapes and tuning
- Hurtbox size is a design choice; player hurtbox smaller than sprite for fairness, enemy larger for easy hits. https://gdquest.com/library/hitbox_hurtbox_godot4
- Near-miss logic: a slightly smaller hurtbox makes near misses read as misses. https://bugnet.io/blog/how-to-build-a-hitbox-and-hurtbox-system
- Typical ratio: only forum-level figure (enemy about 80% of sprite, player much smaller, shmups). Treat as folklore. https://critpoints.net/2015/05/20/why-shouldnt-hitboxes-match-perfectly/
- Tunnelling: test the path, not the endpoint; ray/shape cast from previous to new position, first hit wins. https://www.gdquest.com/library/glossary/tunneling
- Swept CCD vs speculative contacts in engine docs. https://docs.rs/crate/avian3d/0.6.1/source/src/dynamics/ccd/mod.rs
- Worms: damage by per-weapon explosion fields; worm collision mask is what an explosion must reach; no pixel sizes found (UNSOURCED). https://worms2d.info/Project_X/Weapon_file_block
- Hedgewars / tank clones hit ranges: UNSOURCED. "First body met among several targets": only the ray-cast first-hit pattern above.

## 3. Turn-based networking
- Lockstep sends inputs, not state; needs bit-identical sim, same dt, same inputs; float differences across compiler/OS/arch break it. https://gafferongames.com/post/deterministic_lockstep/
- Seed sharing: Hedgewars engine takes one seed string (eseed, 1-249 chars) for setup; part before "|" makes terrain. https://hedgewars.org/kb/EngineProtocol (page has no netplay or desync section)
- Desync check: OpenTTD server sends periodic checksum of RNG state; detects, does not locate. https://sources.debian.org/src/openttd/15.1-1/docs/desync.md
- Spring RTS compares checksums to the majority; suggests casting floats to ints before hashing. https://springrts.com/wiki/Debugging_sync_errors
- Authoritative alternative: Nakama server validates, stores, broadcasts; leave handler can hold a seat for reconnect; turn-based uses low tick. https://heroiclabs.com/docs/nakama/concepts/multiplayer/authoritative/
- Relayed matches respond instantly but are not validated. https://forum.heroiclabs.com/t/handling-package-drop-caused-by-bad-connections-in-turn-based-game/4987 (forum)
- Photon async: disconnect flags player inactive, rooms can be saved/loaded. https://doc.photonengine.com/realtime/current/tutorials/async-and-turnbased
- Hedgewars lockstep/reconnect, Colyseus docs: UNSOURCED.

## 4. Turn flow with teams
- Worms: team order is random or fixed; one worm per turn; Select Worm follows the team rotation, skipping dead. https://worms2d.info/Select_Worm (via search snippet; page itself blocked)
- Scheme option WormSelect: 0 in order, 1 user picks, 2 random. https://worms2d.info/Worms_Armageddon_mission_file
- Sudden Death removes the ability to pick the next worm. https://en.wikipedia.org/wiki/Worms_Armageddon
- Retreat time after firing (0/3/5/10 s, 5 typical) lets the active unit move before the turn ends. https://worms.fandom.com/wiki/Retreat_Time
- Turn timer: Nakama-style projects keep deadline on server, client only shows countdown. https://forum.heroiclabs.com/t/handling-package-drop-caused-by-bad-connections-in-turn-based-game/4987 (forum)
- Readability: team colour, name plus health number above each worm, team energy bar bottom centre, colour-blind alliance palette. https://worms2d.info/WkFlamingHealthBars and https://worms.fandom.com/wiki/Energy
- Active-unit arrow marker, time bank, Advance Wars cues: UNSOURCED.

## 5. Mobile and web
- Touch target about 48 dp (about 9 mm), 8 px spacing. https://web.dev/articles/accessible-tap-targets
- 44 px figure (Apple HIG): UNSOURCED here, not fetched.
- Address bar: 100vh includes bars; use dvh/svh with vh fallback; dvh ignores virtual keyboard. https://web.dev/blog/viewport-units
- Fullscreen API on iPhone Safari: UNSOURCED.
- Canvas cost: pre-render to offscreen, integer coordinates, no scaling in drawImage, avoid shadowBlur, layer canvases, alpha:false. https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas
- Hi-DPI: bitmap = CSS size x devicePixelRatio, ctx.scale(dpr). Cap value (2) is UNSOURCED. Same MDN page.
- Scale with CSS transform; smaller canvas scaled up beats larger scaled down. Same MDN page.

## What this means for us
1. One world: keep 1920x1080 as the only logical space; draw via one transform (FIT + letterbox). Q1.
2. Sides: use ENVELOP-like extra width only for background; keep HUD inside safe-area insets (viewport-fit=cover). Q1.
3. One number: define unit body radius R in world units (code constant, not from art). Q1, Q2.
4. Hurtbox = k * R with k about 0.8 of the drawn radius (folklore, tune by play). Derive crate, icon and projectile radius as fixed ratios of R. Q2.
5. Hit test is a swept segment (prev to new position) vs circle of R_unit + R_proj; pick the earliest t among all bodies. Q2.
6. Sim shared by both clients: send seed plus inputs only, integer or fixed-step math, hash (RNG state + positions rounded to int) every round; on mismatch stop and resync. Q3.
7. Turn: fixed rotation per team, skip dead, optional pick; show active arrow, team colour, name+HP tag; server-side deadline, short retreat time. Q4.
8. Phone: buttons at least 48 CSS px and 8 px apart after scaling (check against scale factor); dvh; cap DPR at 2; pre-render terrain offscreen. Q5.
