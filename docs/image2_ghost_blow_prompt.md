> **FINAL 2026-11-10 (owner): the wind ghost is 4 frames only (idle, puff, blow, blow_hard), NOT 8. This 8-cell file is obsolete.**

> **CORRECTION 2026-11-10: there is no image2 for us; images come only from Qwen (Colab or the 千問 chat). This 8-cell sheet prompt is NOT usable as is. Use the single-frame chain prompts from Kiro task 73/79 instead (frame 1 from the reference, then each frame from the previous one).**

# Wind ghost: continuous blowing sequence (owner 2026-11-10: "regenerate the blowing ghost as a continuous blowing picture")

Paste into ChatGPT image / Codex image2. Attach: assets/env/ghost_lantern.png OR the current wind ghost crop (same face), and a screenshot of the top HUD for scale.
Save the result as (not published) (the keying script cuts the cells; code then plays them in order).

PROMPT (English, one paste):

Create ONE sprite sheet of a cute friendly wind ghost blowing air, target canvas 2048 x 1024 pixels: 4 columns x 2 rows, eight equal 512 x 512 cells with 24 pixel solid magenta #FF00FF gutters, read left to right then top to bottom as ONE continuous animation of a single breath. The ghost faces RIGHT and blows toward the RIGHT in every cell. Attach the reference for the exact face: same round white ghost, same big dark eyes, same small tail, same proportions, same outline thickness, same position and size in every cell so the frames can be played as a loop.
Frame 1: calm, eyes half closed, mouth closed, body relaxed.
Frame 2: starts to inhale, body swells slightly, eyes open wide.
Frame 3: cheeks fully puffed, mouth pressed into a small round pout, body leaning back a little.
Frame 4: lips open into a small round O, first gust leaving, body starts to lean forward.
Frame 5: mouth open in a larger O, body leaning forward, eyes squeezed with effort, strong gust.
Frame 6: widest open mouth, strongest blow, body stretched forward and the tail trailing back.
Frame 7: mouth closing to a small O, body easing back, eyes opening.
Frame 8: relaxed again, same as frame 1 so the loop is seamless.
Style: thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, cold cyan rim light, same as the rest of the game UI. Leave clear empty space in front of the mouth in every cell (the game draws the mist and wind streaks itself). No wind lines, no mist, no arrows, no text, no labels, no numbers, no ground, no cast shadow, no watermark, no emoji, no extra characters, no photorealism, no 3D render, no painterly gradient. Flat solid magenta #FF00FF background in every cell.

AFTER IT ARRIVES (not done yet): key with scripts/ingest_queue.py (tight keying), cut 8 cells, and change the wind-ghost block in index.html drawTopHUD (frames ghost_idle/puff/blow/blow_hard) to play the 8 cells in order, with the cycle speed faster in a stronger wind; calm wind = frame 1 only. Kiro 67's (not published) can drive the playback.
