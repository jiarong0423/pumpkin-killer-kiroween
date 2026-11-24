# Page UI settings inventory — 2026-11-16

Source: read from `index.html`, `css/dock.css`, `assets/i18n/*.json`, and `js/i18n.js` on 2026-11-16. “Saved” means persisted across a page reload by page code, not merely retained while the page stays open. Phone assessment is against the current 392 CSS-pixel-high landscape layout.

## Current controls and settings

| Control or setting | Where it lives | Saved across reloads | i18n keys | Works at 392 px-high landscape | Gap |
|---|---|---:|---|---|---|
| Language | `#start-lang` and `#lang-btn`; `toggleLang()` calls `I18N.toggle()` then `I18N.apply()` | Yes, `js/i18n.js` stores the language choice in `localStorage` defensively | `lang.title`, `lang.label` | Yes. The in-match button becomes a 44 px target under `(hover: none)` | It is separate from other preferences and has no settings summary. |
| Sound and music mute | `#sound-btn`; `toggleSound()` toggles `soundMuted`, `gameAudio.mute()` and `ambientSfx.setMuted()` | No | `dock.soundTitle`, `dock.soundTip` | Yes. 44 px target under `(hover: none)` | One switch combines effects, music and ambience. Its state is not restored after reload. |
| Restart | `#reset-btn`; `resetPressed()` and `resetAllowed()` permit it only through round 2 | No | `dock.resetAria`, `dock.resetTip`, `dock.resetTitle`, `dock.resetLockedTitle`, `toast.resetLocked` | Yes. 44 px target under `(hover: none)` | The action returns to hero selection without an explicit confirmation. |
| Help panel | `#help-btn`, `#instruction-pill`; `toggleHelp()` and H key | No | `dock.helpTitle`, `dock.helpAria`, `help.*` | Yes. 44 px target under `(hover: none)` | The panel has no visible close control; toggling, Escape, or a game action closes it. |
| Hero pick | `#pick-heroes`; `buildStartScreen()` renders cards and card click sets `pickedHero` | No | `hero.*`, `role.*`, `stat.*`, `tag.*`, `start.inProduction` | Yes. Start screen can scroll; cards are compact. | Current pick is reset on reload. Unavailable avatar cards are disabled after image-load failure. |
| Scene pick | `#pick-scenes`; `buildStartScreen()` and `requestScene()` | No | `scene.*`, `start.inProduction` | Yes. Start screen can scroll. | Current pick is reset on reload. |
| Seat assignment | `#seat-picker`; `buildSeatRows()` creates Human, Built-in AI, and relay Agent choices | No | `seat.left`, `seat.right`, `seat.playerOne`, `seat.open`, `seat.ai`, `seat.agent` | Yes. `.seat-choice` is 44 px high. | No preference persistence. The no-AI-versus-AI validity rule applies. |
| Built-in AI level | `.seat-level` buttons in `buildSeatRows()` set `seats.level[side]`; `levelFor()` affects `levelKnobs()` and `skillChanceFor()` | No | `level.easy`, `level.normal`, `level.hard` | **No.** Existing target height is 32 px, below the phone rule. | No persistence; level controls are embedded in seat rows rather than a single settings sheet. |
| Room create / join | `#room-picker`, `buildRoomControls()`, `connectRelay()`, `renderRoomDetails()` | No | `room.create`, `room.join`, `seat.noRoom`, `seat.waitingAgent` | Conditional on `?relay=`. The buttons are 44 px high. | Join only uses the `room` query parameter or the current room code. There is no typed join-code field. |
| Join code, link, QR | `#room-code`, `#room-link`, `#room-qr`; `renderRoomDetails()` and `joinLink()` | No | None for the generated code or link; `seat.noRoom` for the no-room state | Conditional on relay. QR is 112 px square and can force start-screen scrolling. | No copy-code action or i18n label for the generated code/link. |
| Agent turn QR | `#agent-wait`, `#agent-room-code`, `#agent-room-qr`; `showAgentWaiting()` | No | `seat.waitingAgent`, `seat.noRoom` | Conditional on agent seat. The overlay is usable but not a preference. | No room-state persistence. |
| Coin toss skip | `#coin-toss-skip`; `showCoinToss()` | No | `coin.leftFirst`, `coin.rightFirst`, `coin.skip` | Yes. 44 px target. | Not a retained setting. |
| Portrait rotate hint | `#rotate-hint` CSS at portrait widths below 900 px | Not applicable | `toast.rotatePhone` | Yes. It is deliberately hidden in landscape. | None for the current landscape-only game flow. |
| Install prompt / iOS hint | `#install-btn`, `#install-ios`; `beforeinstallprompt`, `appinstalled`, and iOS user-agent branch | Browser-managed | `ui.installApp`, `ui.installIosHint` | Yes when shown. | Availability varies by browser; no persistent dismissal state is kept. |
| First-play hint | `#first-hint`; `showFirstHint()` and `hideFirstHint()` | Yes, `pk_hint_seen` in guarded `localStorage` calls | `hint.goal`, `hint.step1`, `hint.step2`, `hint.step3` | Yes. | No way to re-open it after dismissal except clearing storage. |
| Aura detail | J key and `toggleAura()`; `auraSimple` changes `drawUltRing()` | Yes, `pk_aura_simple` in guarded `localStorage` calls | `toast.auraSimple`, `toast.auraFull` | Keyboard-only, so not usable as a phone control. | This is an existing visual preference with no visible settings control. |
| Angle | Pointer aiming, arrow/W/S keys, `activeAngle()` and `setActiveAngle()` | No | `hud.angle`, `dock.angle` | Pointer aiming works. The on-canvas angle plates are disabled (`SHOW_ANGLE_PLATES = false`). | No dedicated phone stepper. |
| Charge / throw | Canvas pointer, Space; `startCharging()` and `releaseAndThrow()` | No | `toast.tapCancel`, `hint.*` | Yes, but it is gameplay input rather than a retained setting. | None inventoried; scope excludes mechanics changes. |
| Action menu | Canvas character tap; `actionMenuItems()` and `chooseMenuItem()` | No | `menu.move`, `menu.attack`, `menu.defend`, related `toast.*` | Canvas hit targets are logical-world targets, not DOM 44 px controls. | Not a preference. |
| Move direction | Canvas / arrow/A/D; `moveWithDice()` and `chooseMoveDir()` | No | `move.*`, `toast.move*` | Pointer controls are present; keyboard alternatives do not apply to touch. | Not a preference. |
| Skills / ultimate / shield | Dock buttons; `selectSkill()`, `toggleUltimate()`, `toggleShieldDefend()` | No | `skill.*`, `ult.*`, `shield.*`, `knightUlt.*` | Yes. Dock controls have 44 px dimensions in the short-landscape rule. | Not a preference. |
| Supply use | `#supply-slot`; `useSupply()` | No | `supply.*`, `toast.pickup` | The slot is 52 px square. | Not a preference. |
| Path-trail visibility | T key toggles `showPathLines` | No | None | Keyboard-only. | Internal/debug-style display toggle has no discoverable phone control. |
| Art flip | F key changes `flipAllArt` | No | `toast.flip`, `toast.flipOn`, `toast.flipOff` | Keyboard-only. | Frozen orientation rules mean this should not be promoted as a setting. |

## Missing expected settings

| Missing setting | Decision | Reason |
|---|---|---|
| Effects sound on/off and volume | Do now | The current sound button combines effects, music and ambience. A player needs an independent effects volume or mute. |
| Music volume | Do now | Music is present through `GameAudio`, but has no independent control or retained level. |
| Reduce motion | Do now | The page includes screen shake, hit flashes and particle bursts. A preference can retain gameplay while simplifying visual effects. |
| Language in a settings sheet | Do now | Language already works and needs one consistent home with the retained settings. |
| Built-in AI level before a match | Do now | The setting exists but its 32 px buttons fail the phone target requirement and it is not retained. |
| Text size | Later | Canvas and DOM readability are already governed by the UI scale; adding a second scaling system risks HUD collisions. |
| Fullscreen button | Not needed | The manifest requests fullscreen/standalone presentation. Browser permission and platform UI make a custom in-game button unreliable. |
| Keep-screen-awake | Later | It needs a browser Wake Lock permission flow and lifecycle handling. It is not necessary for short prototype matches. |
| Left-hand layout | Later | Moving controls changes the currently measured HUD and dock geometry. It needs dedicated phone playtesting. |
| High-contrast theme | Later | The palette is frozen for the contest presentation. Contrast changes need a separate accessibility review. |
| Rebindable controls | Later | Desktop keyboard shortcuts are supplementary and the game’s main action is direct pointer input. |
| Account/cloud sync | Not needed | The product has no accounts or cloud persistence. |
