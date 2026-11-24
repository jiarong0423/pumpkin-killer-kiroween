# Kiro task 58: details and controls, seen as a player

Author: Kiro, 2026-11-09. Only this file was written. `index.html` and `css/` were read, not edited.
Owner request: "look at the screenshot and say what Kiro finds, about the current game's details and the controls".

## 0. What I looked at

| Source | Opened? | Notes |
|---|---|---|
| `(not published)` (1672x941) | yes, I can view it | Banner with logo, PLAYERS diamonds, round and timer, wind arrow plus number "風 0", AGENTS diamonds. Unit bars carry numbers ("85/85") and markers 1-4 / A-D. Bottom bar has portrait, 投射/移動/防禦, angle, power segments, ammo, special slot, 鎖定. |
| `(not published)` (1920x1080) | yes, I can view it | Canvas only, one frame, round 1, player = pumpkin wizard, AI = pumpkin guard. It does not show the DOM dock or the "?" button. |
| `(not published)` | yes | Viewport 1078x826, 32 DOM elements, energy 3, wind 2.4, HP 85 / 120. DOM only: the click menu, move arrows, shield drag and the HUD are canvas drawings and are not in it. |
| `(not published)`, `docs/dock_design.md` | yes (all) | |
| `docs/experience_design.md` | partly | The read was cut at section h (open questions). Sections a to g were read. |
| `index.html`, `css/dock.css` | yes, the parts named below | Line numbers are from the file as it is now. |

I did not run the game. Everything below is from the pictures, the audit and the code. Items I could not confirm are marked **(unverified)**.

## 1. Controls that do nothing, surprise, or give no feedback

| # | What happens | Evidence |
|---|---|---|
| C1 | **Clicking outside the open action menu starts a charge.** The code says "a click anywhere else just closes the menu", but it then falls through to `startCharging()`. Letting go throws. | `index.html:1078` sets `actionMenu = false` with no `return`; `1102` then charges. |
| C2 | **The menu cannot be closed by clicking the character.** The first block closes it, then `1100` toggles it open again. | `1078` then `1100`. |
| C3 | **No mouse or touch way out of Move or Defend.** In move mode every press is swallowed (`1081-1091`), and defend mode ignores presses off the shield. Only Esc cancels (`1166`). If the player does not roll or lock within 12 s the whole turn is forfeited (`1542-1550`). | A misclicked menu item costs a turn on touch. |
| C4 | **Space is not safe.** `keydown` Space calls `startCharging()` with no `preventDefault` and no `matchStarted` check (`1163-1165`, `1182`). (a) On the start screen, Space starts and releases a throw behind the overlay, and the AI answers; the match opens already one round in. (b) After a click on a dock button the button keeps focus **(unverified)**, so releasing Space also "clicks" it: 回血 heals again, 重置 restarts, 聲音 toggles. | |
| C5 | **Right and middle click charge a throw.** `pointerdown` never checks `e.button` (`1060`), and there is no `contextmenu` handler. Whether the context menu then swallows `pointerup` and leaves the meter running (the turn timer is paused while charging, `1542`) **(unverified)**. | |
| C6 | **回血 (heal) skips every check.** `selectSkill('heal')` (`780-792`) has no turn, game-over or full-HP test. It works during the AI turn, spends a charge at full HP, and after "你輸了" it refills the HP bar. It also looks like a shot-select button but fires instantly. | |
| C7 | **Empty or inert slots look like buttons and say nothing.** The ammo slot has no handler and no title. The supply slot with no crate, or on the AI turn, returns silently (`1415-1417`). The audit marks both "click reaches it: true", so "reaches" is not "does something". | |
| C8 | **A press on the dock plate itself starts a throw.** The inline `#bottom-dock { pointer-events: none }` (`index.html:75`) comes after `dock.css` and beats its `pointer-events: auto` (`dock.css:93`). Only the listed buttons and slots take clicks, so a miss between buttons aims at 25 degrees and charges. This is by cascade order, not seen in a browser. | |
| C9 | **The result panel disappears on the next press.** `pointerdown` while `gameOver` calls `resetGame(); showStartScreen()` at once (`1067`), with no delay. A press that was already coming (the player clicking to aim while the AI's last shot lands) skips "你贏了 / 你輸了" unread. | |
| C10 | **重置 (reset) ends the match in one click, no confirm.** It sits 10 px from 聲音 (audit x 958 vs 898+50). | `index.html:248`. |
| C11 | **The menu item 攻擊 only shows a toast** ("move the cursor to aim, hold to charge") and closes the menu (`711`). It looks like a mode switch but is not. | |
| C12 | **No cue on the enemy turn.** Presses are ignored without a message, and the timer (`2784`) only draws on the player's turn. A search for "對手回合" or "輪到" finds nothing. | |
| C13 | **Keyboard and mouse fight over the angle.** W/S and arrows change it (`1177-1180`), but any mouse movement sets it again from the pointer (`1108`). | |
| C14 | **Debug keys are live.** `F` mirrors all art, `T` toggles path lines (`1172-1176`). A player who hits F sees mirrored characters and no way to know why. | |
| C15 | **Power resets to 0 on release** (`1513`), so the player never sees what power the throw used. That is the number they need for the next correction. | |
| C16 | **Holding forever stalls the game.** The turn timer pauses while charging (`1542`), and a missed `pointerup` or `keyup` (alt-tab) keeps the meter running **(unverified)**. | |

## 2. What a first-time player cannot discover

The help text (`index.html:195-203`) is hidden behind a 30 px "?" and lists no keys, no move, no shield lock.

| Thing | Why it is hidden | One-line hint (zh-TW) |
|---|---|---|
| Aiming | The angle follows the pointer's direction from the hand, not its position. The pointer is not the target and distance does nothing. | 「游標指向哪個方向就往哪丟；按住越久越用力」 |
| Power meter | The only gauge is in the dock at the bottom edge (`chargePower` is drawn nowhere else). The eye is on the thrower. | 「按住蓄力，條來回跑，放開出手」 and a ring or bar at the thrower (`experience_design.md` section c proposed this). |
| Move dice | Reached only through click character, then 移動, then drag. The hint toast is a long sentence at top centre (`index.html:723`). | 「往左或往右拖，放開擲骰；每點走 36 px，移動後還能攻擊」 |
| Ultimate | The three pips above the head are 16 px canvas circles with no label (`2343-2352`). The 大招 button only shows once they are lit, with its explanation in a `title` tooltip (touch cannot read it). | 「打中 3 次，頭上 3 顆全亮，按右下『✨大招』再出手」 |
| Shield lock | The Lock button appears only in defend mode. The toast says "再按一次🛡️鎖定" (`821`), but that shield button is hidden (`dock-hidden`). | 「拖盾到亮線上，按右下『鎖定』確認（這回合不能攻擊，Esc 取消）」 |
| Sky shield rule | The help line "盾衛：點 A、B、C 預判三發" (`202`) describes a flow that is not built; the game still uses drag plus lock. | Remove the line until A-B-C exists. |
| Wind | The gauge has five chevrons but wind is limited to +/-4 and rounds to whole steps (`2645`). One step is about 120 px of landing (`AI_WIND_K`), but the label hides tenths. | 「箭頭方向＝風吹的方向；越多越強」 and show the number. |
| Fence label | "中央圍籬 (100%)" (`2395`) never says the fence can be destroyed. | 「圍籬可被打壞」 |
| Supply slot, head crit | The slot is labelled 物資 with no use text; the head crit only appears in the help list. | 「撿到的箱子在這裡，點一下使用」 |

## 3. Text that is cut, overlapping, wrong or inconsistent

| # | Finding | Evidence |
|---|---|---|
| T1 | **"風 有風" is not a rendering bug.** The code prints `風 ${word}` (`2655`) and `word` is one of 無風, 微風, 有風, 強風 (`2646`), so every state shows 風 twice. Wind 2.4 gives 有風, which is the owner's screenshot. The mockup shows "風" plus an arrow plus a number. | |
| T2 | **"角度 54°" is drawn under the energy pips.** The text is at `y = player.y - 232` (`2787`) and the pips are at `cy = -232` (`2345`), same row, same centre. In the screenshot the cyan text is hidden behind the three lit yellow circles above the wizard. | Screenshot, wizard. |
| T3 | **The top-plate shield counter "2/4" shows for every class.** It prints `sh.charges/4` (`2629`). In the screenshot the wizard, who cannot defend, shows "2/4". "4" is the move count (`sp.actions`, the hidden `#badge-shield`), "2" is the block count: two different numbers under one fraction. It also sits on the plate's rune strip, which makes it hard to read. | `2629`, screenshot. |
| T4 | **Low HP is invisible for the player.** The bar is `#ff6b6b` and the low-HP colour is `#ff4757` (`2624`), nearly the same red. The in-field bar is always `#ff5252` (`2333`). The AI side turns red from teal, so only the AI shows danger. | |
| T5 | **Canvas text is tiny once scaled.** Top HUD fonts are 12 to 15 px on a 1920 canvas (`2617`, `2626`, `2628`, centre panel). At the 1400 px cap that is 8.7 to 10.9 px; at the audit's 1078 px viewport it is 6.7 to 8.4 px. In-field HP bars are 110x9 canvas px (about 80x6.5 CSS px at 1400). The HP number on the plate is 12 px. | |
| T6 | **HP bars over the units have no numbers** (the mockup has "85/85"), and the plate shows "85" without the maximum. | `2331-2333`, screenshot. |
| T7 | **"距離 1044" has no unit.** The player thinks in 36 px dice steps. | `2640`. |
| T8 | **Timer sits outside the centre panel** (y 108, below the gold frame, `2784`) and appears only on the player's turn, so the HUD changes shape each turn. | Screenshot. |
| T9 | **The "?" button likely covers the AI portrait corner.** `top: 40px; right: 10px; 30x30` (`index.html:164-166`) maps to canvas x about 1849-1903, y 71-125 at 1078 px; the AI portrait is x 1819-1877, y 32-90. Computed, not seen. | |
| T10 | **聲音 icon and label disagree.** The audit shows 🔇 at the first frame while the markup default is 🔊 (`index.html:247`); I do not know whether the audit muted it. Icon = state, label = noun, so it is unclear whether a click turns sound on or off. | |
| T11 | **Defend toast names a hidden button** (`821`, see section 2). | |

## 4. Touch and small screen

| Item | Size (CSS px) | Verdict |
|---|---|---|
| Container scale | 1400 px cap gives 0.726 canvas-to-CSS; the audit viewport 1078 px gives 0.558 | 44 CSS px = 61 canvas px (1400) or 79 (1078) |
| Click-menu items (108x52 canvas, `701-706`) | 78x38 at 1400; 60x29 at 1078 | **fail** (height) |
| Move arrows (drawn 104x48, hit area 112x68, `1082-1083`) | hit 81x49 at 1400; 62x38 at 1078 | pass at 1400, fail at 1078 |
| "?" help button | 30x30 | **fail** |
| Dock skill buttons / sound / reset / ultimate (audit) | 56x68 / 50x50 / 50x50 / 96x56 | pass; tier S forces 44 |
| Ammo and supply slots | 58x74 | pass (ammo is inert) |
| Energy pips | 16 canvas px = 12 CSS px | display only |

Other problems:
- No page-fit rule: `#game-container` is `width:100%; max-width:1400px; aspect-ratio:16/9` inside a `100vh` flex body with `overflow:hidden` (`index.html:34-57`). On any window shorter than width x 9/16 (a 1366x768 laptop with browser bars is about 650 px tall for a 1366 px wide container, which is 768 px tall) the container is either clipped (dock and top plate lost) or squashed by flex-shrink. I could not tell which without a browser.
- Mouse only: the angle plates are off (`SHOW_ANGLE_PLATES = false`, `1033`; `touchInput` is set but never used). Touch aiming works by dragging while charging, with the finger on the view. There is no cancel (C3), no ultimate key (the button works), and `title` tooltips are unreadable on touch.
- Pinch zoom is disabled (`user-scalable=no`, `index.html:5`). That is a low-vision problem, not a mobile-layout one. Mobile layout is a stated non-goal for the first version, so touch items are P1 or P2 only.
- Start-screen cards are `div`s with `onclick` and no `tabindex`: a keyboard cannot choose a class or scene.

## 5. Ranked list

Format: **rank, ID, file:line, one-line fix.** None of these edit rules; rule conflicts are in section 6.

### P0 (blocks play)

| ID | File:line | Fix |
|---|---|---|
| P0-1 Page does not fit short windows (section 4) | `index.html:46-57` (`#game-container`) | `width: min(100%, 1400px, calc(100vh * 16 / 9))` and drop the flex-shrink (`flex: none`), then re-check the dock tiers in `dock.css:723,758`. |

### P1 (confusing or breaks a turn)

| ID | File:line | Fix |
|---|---|---|
| P1-1 C1/C2 menu fall-through | `index.html:1078`, `1100` | After closing the menu `return`; let a press on the character toggle it only when it was closed. |
| P1-2 C3 no exit from Move/Defend | `index.html:1081-1091`, `1166`, `821` | Draw a small ✕ cancel plate beside the die and the shield; on the first press outside both, cancel. |
| P1-3 C4 Space | `index.html:1162-1165`, `1182` | `if (!matchStarted) return`, `e.preventDefault()` for Space, and `document.activeElement.blur()` after a dock click. |
| P1-4 C6 heal | `index.html:780-792` | Return unless `turn === "player" && !gameOver && matchStarted && hp < maxHp`, and say why. |
| P1-5 T1 wind label | `index.html:2646`, `2655` | Print `風 ${wind.toFixed(1)}` (mockup style) or the word alone; never both. |
| P1-6 T2 angle under pips | `index.html:2787` vs `2345` | Move the angle text to `player.y - 262`, or fold it into the pips row only while aiming. |
| P1-7 T3 shield counter | `index.html:2629` | Draw it only for `canControlShield()` classes and show one number (blocks left). |
| P1-8 T5 tiny HUD text | `index.html:2617`, `2626`, `2628`, centre panel | Raise HUD fonts to at least 20 canvas px (about 14 CSS px at 1400) and the plate HP number to 18. |
| P1-9 C9 result panel | `index.html:1067` | Ignore presses for 0.8 s after `gameOver`, and show 「點一下重新開始」 only after that. |
| P1-10 C8 dock plate presses | `index.html:75` | Give `.dock-readouts` and `.dock-sep` `pointer-events:auto` (or set the dock plate to `auto` in `dock.css` and drop the inline rule). |
| P1-11 C5 mouse buttons | `index.html:1060` | `if (e.button !== 0) return;` and `canvas.oncontextmenu = e => e.preventDefault()`. |
| P1-12 Power not on the thrower | `index.html:2326-2352` (unit overlay) | Draw a short arc or bar 36 px above the head while charging, as `experience_design.md` section c asks. |
| P1-13 Help text wrong | `index.html:202` | Delete the A-B-C line; add 「Space 蓄力、W/S 調角度、Esc 取消、U 大招、M 聲音」. |
| P1-14 T4 low HP colour | `index.html:2624`, `2333` | Use an amber then white-flash state below 30 percent, not a second red. |

### P2 (polish)

| ID | File:line | Fix |
|---|---|---|
| P2-1 C10 reset confirm | `index.html:248` | Press-and-hold 0.6 s, or move it away from 聲音 (at least 24 px). |
| P2-2 C7 inert slots | `index.html:241-242`, `1415-1417` | Add titles, dim the ammo slot, and toast 「沒有物資」 / 「對手回合」 on a blocked press. |
| P2-3 C11 攻擊 item | `index.html:707-712` | Make it set an "aiming" state that highlights the field, or drop the item. |
| P2-4 C12 turn cue | `index.html:2784` | Show 「對手回合…」 in the same spot as the timer. |
| P2-5 C14 debug keys | `index.html:1172-1176` | Guard F and T behind `?debug`. |
| P2-6 C15 last power | `index.html:1513` | Keep the last throw's power in the dock until the next press. |
| P2-7 T7 distance | `index.html:2640` | 「距離 29 步」 (px / 36) or hide it. |
| P2-8 T9 help button | `index.html:164-166` | Move it to `top: 124px` or inside the dock. |
| P2-9 T10 sound icon | `index.html:247` | Label 「開 / 關」 and read the icon state at load. |
| P2-10 C13 angle | `index.html:1108`, `1178` | Pause pointer aiming for 1 s after a W/S press. |
| P2-11 C16 blur | `index.html:1182` | `window.addEventListener("blur", releaseAndThrow)` or cancel the charge. |
| P2-12 T6 numbers | `index.html:2331-2333` | Add `hp/max` above the bar; use the 1-4 / A-D markers from the mockup when 4 v 4 arrives. |
| P2-13 Touch sizes (section 4) | `index.html:701-706`, `1082-1083` | Menu item height 76 canvas px, hit area 88, "?" 44x44. |
| P2-14 Start cards | `index.html:356` | Add `tabindex="0"` and Enter/Space handling. |

## 6. Rule conflicts to report (not fixed here)

Reported per `rules.md`: I did not change a rule to match the code.
- `rules.md` says one throw per turn. The 雙發 shot fires a second projectile 260 ms later (`index.html:907`). The double-shot is listed as not confirmed.
- 回血 (+35 HP, 2 charges) and 重彈 (1.5x) are not in `rules.md`.
- The Defend flow is still drag plus one lock; Path 1 / Path 2 / Confirm and the owner's A-B-C are not built (already listed as a known mismatch).

## 7. What I could not verify

- Anything that needs a running page: focus after a dock click (C4b), right-click behaviour (C5), the page-fit result (P0-1), the dock-plate click-through (C8), hover, animation, sound and the real look of any emoji.
- The owner's "風 有風" screenshot. I did not have it; the cause is read from `index.html:2646,2655`.
- The audit has one viewport, one hero and DOM only. It says nothing about canvas-drawn controls, touch, or the dock at other tiers.
- The screenshot is canvas only, so the dock, the "?" button and the help panel were not seen. Overlap T9 and the dock arithmetic are computed.
- 4 v 4, the Colab art for the pending top HUD, and the hunchback / necromancer / bride cards (all "製作中") were not judged.
- `docs/experience_design.md` was read to section h only.
