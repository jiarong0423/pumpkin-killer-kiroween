# Kiro playtest review (build 8233fe3, scripted match of 2026-11-08)

Reviewer: Kiro CLI. Input: 13 canvas frames (`f01`..`f13`, 1280x720), `LOG.md`, `docs/game_mode.md`, `(not published)`, and a grep/skim of `index.html`.
I did not run the game. Everything below comes from the frames, the docs, or a line I found in `index.html`. Where I am unsure, I say so.

Frame facts I rely on: units are about 120 px tall on a 720 px frame (about 17%). Wind is +2.4 (f01), +1.7 (f07..f09), +2 (f10..f13). The player's HP is 100 (f01..f06), 78 (f07..f09), 54 (f10..f12), 0 (f13). The AI stays at 100 throughout.

## First impression (10 seconds)

- The backdrop is good: big moon, castle, bats, cyan ghost flames, candles, pumpkins. It reads as Halloween at once (f01).
- A judge sees two small skeletons at the far edges, a wooden gate between them, and a lot of empty blue. They will understand "two sides, something in the middle". They will not understand how to play, what the goal is, or whose turn it is.
- Confusing things in f01:
  - The top bar is small and dense: round, distance in px, "人類出招", wind, two HP bars, "浮空盾 [2/4] (防禦 2 輪)". The shield counter is shown to a skeleton who cannot use a shield.
  - Debug-style labels float over the units ("我方 (1號位: x=380)", "敵方 (2號位: x=1520)") and over the gate ("中央圍籬 (100%)").
  - No visible timer, angle, power, or "your turn" marker on the canvas. The code counts a 12 s timer (`turnTimer`) but I found nothing that draws it on the canvas.
- Both the HUD and the world text are Traditional Chinese. If the judges read English, most of the in-game instruction is lost. See Open questions in `RECORD.md`.

## Readability

- **Character size vs scene.** The size itself is not the problem. In the mockup the units are about 14% of the screen height, so f01's 17% is similar. The difference is that the mockup puts four units per side and fills the space around them. In f01 two units are 1140 px apart with nothing between them but a gate, so they look tiny and lonely.
- **Who is acting.** Not readable. In f01 and f07 the only cue is the text "人類出招" / "AI 思考" at 11 px in the top box. Teams differ only by a thin red or teal HP bar and the facing direction. Nothing marks the active unit (the mockup has a cyan ground ring under the active unit).
- **Team contrast.** In f07 the enemy Pumpkin Guard is black armor against dark tombstones and dark blue sky. His body is hard to separate from the background. The skeleton is easy to see because it is white.
- **What to do next.** f01 gives no prompt. Only the move and defend modes print a hint line (f08, f10). In f08 the cyan hint is thin, sits over the moon edge and bats, and is easy to miss.
- **Wind.** `風力: +2.4 m/s 東風 →` is about 11 px text next to a tiny cyan bar in the top box (f01). Wind is the main variable in this game and it is the hardest thing in the frame to see. The mockup gives it its own slot with an arrow.
- **Angle and power.** Angle is not shown in any frame. Power appears only in f02 as a dark ring with "0%" around the player's head. The ring is low contrast, overlaps the skull, and the "0%" is small.
- **HP.** Two places: big bars in the top corners (f01) and a tiny bar over each unit (about 75x6 px). The numbers are 11 px. Changes are hard to catch: the HP went from 100 to 78 between f06 and f07 and from 54 to 0 between f12 and f13, and no frame shows the damage happening. The viewer only sees the bar change afterwards.
- **Spear direction.** In f01 both skeletons hold the spear with the blade pointing away from the opponent. It may be a wind-up pose, but at first glance it looks backwards. I am not sure, please check in motion.

## Game feel

From frames only. I cannot judge timing or sound.

- **Throw.** f02 shows a charge ring. f03 shows a swing pose. In f04 I cannot see the projectile at all; I see only a few teal dots and a faint text near the feet (the code's "泥土偏斜" ground-miss label). Either the capture missed the weapon or it is too small and blends into the background. The owner wants weapons large and readable, so check this.
- **Hit and block.** No frame shows an impact. The code has a hit-stop, an impact burst, a floating "直擊 -N" and a blocked-by-shield label with cyan sparks (`index.html` around lines 1085 to 1130), but none of it appears in the frames. A first viewer would not see damage cause and effect.
- **Move and dice.** f10 to f12 show the hint line, then "5：前進 80 px" in faint small text left of the unit (f12), and the unit has moved from x=380 to x=459. I cannot see a die in f11. The dice is a drama moment and currently looks like a text line.
- **Sound.** The code has five synthesized tones (charge, throw, block, hit, heal). I found none for move, dice, game over or a UI click, and no music or ambience. Cannot judge from frames.
- **Shake and slow motion.** The code sets screen shake on the wizard cannon (line 692) and a hit-stop on a hero hit. I did not find shake on other hits. There is no slow motion on the final blow.
- **AI class change.** Between f05 and f06 the AI skeleton becomes a Pumpkin Guard with no transition or label. It reads as a glitch.
- **Game over.** f13 shows HP 0/100, an empty HP bar, the skeleton still in its normal pose, and the header still saying "人類出招". The banner I found in the code (dim overlay and "💀 子代理獲勝", around line 1900) is not in the frame. Either the capture was one frame early or the overlay is not drawn. Please check. Also nothing shows that the unit died.
- **What feels missing:** a visible projectile with a trail, landing mark, damage numbers that stay for about a second, bar drain animation, a death animation, shake on every hit, slow motion on the last hit, and a win or lose screen that names the winner.

## Rules clarity

Without reading text, a new player cannot tell these things from the frames.

- **Move.** f10 shows a long yellow sentence only. Nothing marks the forward and backward plates on the ground, so "choose forward/backward" is not visible in the canvas (the plates may be HTML or small). After the move (f12) nothing says "you can still throw". The only cue is the faint text in f11 "(移動完還可以攻擊)".
- **Defend.** f08 says (in text) "this turn cannot attack". It is not shown visually; the unit has no empty-hand cue. The HUD shield counter "[2/4]" is cryptic.
- **One throw per turn.** No frame shows a "throw used" state. After f03 the header changes to "AI 思考" while the throw animation is still playing (f03, f04), which is the only sign.
- **Shield valid paths.** f08 shows one remembered enemy path as a cyan dashed arc, and one short shield bar at the upper left with the label "左右拖曳，沿著路徑滑動". `docs/game_mode.md` says the shield covers two paths (Path 1, Path 2, Confirm) and the last four enemy paths are remembered. The frame shows a single bar and a single arc. Either the two-path flow is not in this build or the other paths are not drawn.
- **Shield locked on an invalid spot.** In f09 the shield sits above the gate at about (600, 290), nowhere near the dashed arc from f08. The faded text under the hint line matches the code's not-snapped message "已鎖定（不在記憶路徑上），剩 3 次移動" (line 563). So the player used the turn and the shield is probably not on a valid path. The frame gives no strong visual difference between a snapped and an unsnapped shield, and the dashed path disappears after locking, so nobody can verify the placement. This is the biggest rules-clarity gap.
- **Shield after class switch.** In f10 the player is a skeleton again but the shield stays ("浮空盾持續防禦中 (剩餘 1 輪)"). That is probably intended but looks odd.
- **Shield look.** `game_mode.md` asks for a thin glossy spell-like bar. The bar in f09 looks like a solid wooden bar with arrows.

## Against the mockup

The eight largest visual gaps. Size: S under half a day, M about one to two days, L more than two days.

1. **4 vs 4 roster with number and letter badges (1 to 4, A to D).** The frames have 1 vs 1 only. L, needs the owner to confirm the flow first (`game_mode.md`: not built, flow unconfirmed).
2. **Floating platforms** (the two tilted glowing slabs and two wooden platforms with candles and ghost wisps). None in the frames. M.
3. **Ghosts carrying crates** (the airdrop). None. The sky between the units is empty. M (art from Colab, plus drop logic).
4. **Bottom bar** with unit portrait, HP, Throw/Move/Defend buttons, angle, power, ammo, special slot and Lock. Not in the canvas frames (the real page has an HTML dock; see "Things I could not judge"). M.
5. **Landing rings and dashed aim arc.** The mockup has glowing yellow rings on the ground and a dashed arc. The frames have none after impact. S. Note: the owner chose no path line during flight; a ring that marks only the landing point does not conflict with that and supports the "learn from past landings" idea in `steering/product.md`.
6. **Top bar** with large "4 PLAYERS" and "4 AGENTS" pills, round number with a big timer (08), a wind arrow with a value, and a logo. The frames have a thin strip with 11 px text and no logo. S.
7. **Lighting and palette.** The mockup is dark purple with warm candle light and a vignette, and foreground gravestones and pumpkins. The frames are saturated bright blue and flat. The mockup's characters have warm rim light; ours do not. M, mostly art.
8. **Per-unit HP bars with badges and the active-unit ring.** The mockup shows large numbers (90/90) above each unit and a cyan ring under the active one. The frames show tiny bars and debug labels. S.

## Empty space and composition

- The eye goes first to the moon and castle at upper right (brightest, most detail), then to the gate at the center, then to the HUD. The units, which matter most, are third.
- The middle band, from the top bar to about y=380, is empty except for bats and branches. That is where every throw happens (f08 shows the arc crossing it). It should hold the action: wind indicator, landing marks, platforms, ghosts with crates.
- The two bottom corners hold pumpkins and candles but the center of the stone slab is blank.
- Cyan flames sit directly behind each unit (x about 320 and 1100). They compete with the units' cyan eyes and make a bright blob behind the head. Move them back or dim them.
- **Add:** a turn banner or ring on the active unit, a clear wind widget near top center, ground rings for landings, and the platforms and ghosts from the mockup.
- **Remove:** the x/px debug text, the "雙方距離" value in the top bar, and the shield counter when the unit is not a Pumpkin Guard.
- **Tone down:** saturation of the sky.

## Top 10 improvements

Ranked by impact over effort.

1. Remove debug labels (x=380, 雙方距離) and raise HUD text to at least 20 px at 1280 wide. Owner: main line.
2. Show a landing ring at each throw's impact point and keep it for one round. Owner: main line.
3. Show damage numbers and an animated HP bar drain on every hit, held for about a second, so f06 to f07 is visible. Owner: main line.
4. Draw the turn timer, angle and power number on the canvas next to the active unit. Owner: main line.
5. Add an active-unit ground ring and a short "YOUR TURN" or "AI TURN" banner. Owner: main line.
6. Check the game-over banner (missing in f13); add a death animation and a winner line. Owner: main line.
7. Shield: draw all remembered paths while placing, color the bar green when snapped and red when not, and keep the chosen path visible after lock. Owner: main line, Kiro can review the flow against `game_mode.md`.
8. Label the AI's class and add a short swap effect when it changes (f05 to f06). Owner: main line.
9. Add shake on every hit and a short slow motion on the final blow; add sounds for dice, move and game over. Owner: main line.
10. Add the platforms and ghosts with crates from the mockup, and warm the palette. Owner: Colab art for the assets, main line to place them.

## Things I could not judge

- **HTML dock and skill bar.** Missing from the canvas frames, so I cannot say whether Throw/Move/Defend, Lock and the angle control are clear. Record the full browser page.
- **First-run tutorial box.** `LOG.md` says it sits in the middle of the sky, which is exactly the empty area. I cannot judge whether it helps or blocks the view.
- **Timer display.** I found no canvas drawing of the 12 s timer; it may be in the HTML. Record it counting down and expiring.
- **Motion and sound.** Throw timing, hit-stop length, shake strength, tone quality. Needs a video with audio.
- **Projectile look.** No weapon visible in f04. Needs a frame sequence of 10 or more frames around release and impact.
- **Real first-time use.** Whether a new player finds the hold-to-charge control without help.
- **What recording would help:** a full-page screen recording at 1280x720 and 1920x1080 with audio, covering one throw, one hit, one block, one move with dice, one timeout, and the game-over screen, plus a think-aloud session with one person who has not seen the game.
