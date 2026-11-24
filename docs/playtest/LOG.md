# Playtest log 2026-11-08 (scripted match, desktop build at commit 8233fe3)

Frames are the GAME CANVAS only (1280x720 JPEG). The bottom dock buttons, the skill bar and the first-run tutorial box are HTML elements that are NOT part of
the canvas, so they are missing from these frames (on the real page a tutorial box sits in the middle of the sky and the dock sits at the bottom).
Wind +2.4, player = skeleton (left), AI = skeleton (right), then the player switches to the Pumpkin Guard for the shield frames.

| Frame | What happened |
|---|---|
| f01_start | Round 1, player turn, idle. Timer 12 s running. |
| f02_charging | Player holds to charge; power arc around the player. |
| f03_release_swing | Throw animation; the weapon leaves the hand. |
| f04_flight | Projectile in flight (no path line is kept on screen: owner decision). |
| f05_after_impact | Impact finished; enemy turn about to start. |
| f06_ai_turn | AI turn (it may pick another hero class each turn). |
| f07_next_round | Back to the player; the AI turned out to be a Pumpkin Guard this round. |
| f08_defend_mode | Player is the Pumpkin Guard, defend mode: shield preview (dashed), remembered enemy path glowing. |
| f09_shield_locked | Shield locked (this used the turn: a defending unit cannot attack). |
| f10_move_choose | Move action: choose forward / backward plates. |
| f11_dice_rolling | The die is tumbling above the unit. |
| f12_after_move | Moved; the unit can still attack this turn. |
| f13_game_over | Game over banner. |

Known facts the reviewer should keep in mind: art is placeholder (final art is being generated); 4 vs 4 is not built yet (the mockup in docs/ref/concept_mockup.png shows it);
characters were deliberately made small and weapons/effects large by the owner; the game is meant to be playable on desktop first and on a phone later (landscape full screen).
