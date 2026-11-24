# Visual quality plan (Kiro task 49)

Owner words (2026-11-09): "Raise the screen quality." "Split every asset into parts." Earlier rules that still hold: art is made on Colab and never faked by code, the screen stays clean and readable, Halloween magic, a premium look. Fonts are task 48. Terrain is task 47.

Companion files: `js/scene_layers.js` (the layer renderer helper), `scripts/test_scene_layers.js`, `docs/scene_layers_integration.md` (which `index.html` lines to change), `colab/layered_job.py` (the Colab cell), `.kiro/specs/scene-layers/`.

## 0. What I read, what is missing, how to read the numbers

Read: `index.html` (`draw()` from line 1740, `drawFullArtCharacter` from 2166, `loop` from 2706, `windField` at 509, the canvas element at 183, `#game-container` at 45), `js/wind_fx.js`, `js/particles.js` and `js/particles_draw.js` (spec only), `docs/asset_mapping_table.md`, `docs/art_style_guide.md`, `docs/converge_scenes.md`, `docs/ui_reskin_plan.md`, `docs/ultimates_design.md` (the calm mode budget), `colab/pumpkin_assets_job.py`, `colab/audio_job.py`, `.kiro/steering/*`.

Not in this checkout, so not read:
- `(not published)` (task 46) does not exist. The only calm mode definition I found is in `docs/ultimates_design.md` section 1d ("Global effects budget": particles 500 to 250, wind items 64 to 32, full-screen overlays 1 to 0, shake off, flashes off; switch on `prefers-reduced-motion` or when the average frame time is over 24 ms for 2 s). I use that and add the layer rows it lacks.
- `(not published)` (task 47) does not exist. I used the task 47 brief (ground is an invisible collision profile, pits and slopes, ground strips per preset) and `docs/converge_scenes.md`. Section B5 must be checked against `terrain_design.md` when it lands.
- `assets/env/bg_belltower.png` and `(not published)` are listed in `SCENES` (line 331) but are not in `assets/env/`. Only the graveyard exists.

How to read the numbers:
- Every millisecond figure below is my estimate from counting draw calls and pixels. **Nothing was measured.** The main line measures with the method in section A3 and replaces my numbers.
- Memory figures are arithmetic: a decoded 1920 x 1080 RGBA image is 1920 x 1080 x 4 = 8.3 MB, 1536 x 864 is 5.3 MB, 1024 x 1024 is 4.2 MB.
- Thresholds marked INVENTED are my proposals, not owner decisions.

Facts from the code that shape the plan:
- The canvas is 1920 x 1080 (`index.html` line 183) shown in a container capped at 1400 CSS px (line 48). One canvas px is 0.729 CSS px. On a normal-density screen the picture is scaled down. On a 2x screen (2800 device px wide) the 1920 px backing store is scaled up 1.46x by the browser.
- The background `assets/env/bg_graveyard.png` is 1536 x 864 and `draw()` stretches it to 1920 x 1080 (line 1743), a 1.25x enlargement, then the browser scales again. This is the main source of the soft look.
- Units cast a flat black ellipse (`ctx.ellipse(0, -8, 54, 16)`, line 2173). The fence is code-drawn. Text on the canvas is plain `sans-serif`.
- The loop applies screen shake to the whole canvas with `Math.random` (line 2721). That is game feel and stays; layers sit under it and shake with everything else.
- `windField` already draws fog puffs, ghost dust and leaves (`js/wind_fx.js`, 64 items, budget 96).

## Part A. Quality lift

### A1. Ranking

Gain and effort are 1 to 5 (5 = biggest gain, 5 = most work). Score = gain / effort. Cost is the extra work per frame at the normal setting, an estimate (not measured): "GPU" means fill of full-canvas draws (1920 x 1080 = 2.1 Mpx each), "JS" means script time.

| Rank | Item | Gain | Effort | Score | Extra cost per frame (estimate) | Needs Colab art |
|---|---|---|---|---|---|---|
| 1 | Colour grade and soft vignette, cached once | 4 | 1 | 4.0 | one 1920x1080 draw, GPU about 0.3 to 0.8 ms; JS under 0.05 ms | no |
| 2 | Contact shadows from a cached sprite | 3 | 1 | 3.0 | 2 small draws, under 0.1 ms | no |
| 3 | Idle breathing of unit sprites | 2 | 1 | 2.0 | none (a scale factor) | no |
| 4 | Crisp background (native 1920x1080 or a 2x upscale) | 5 | 3 | 1.7 | none per frame; +3 MB decoded memory | yes |
| 5 | Hit feedback polish inside the effects budget | 3 | 2 | 1.5 | at most 40 particles per hit (inside the cap) | no |
| 6 | Ground fog bands that drift with the wind | 3 | 2 | 1.5 | wind items are already drawn; 1 tiled layer adds 2 draws, GPU about 0.2 ms | optional |
| 7 | Parallax layers (3 to 5 depth layers) with camera sway and wind sway | 5 | 5 | 1.0 | 5 to 8 draws, GPU about 1 to 4 ms worst case | yes |
| 8 | Moon glow and light bloom, additive, few sprites | 3 | 3 | 1.0 | 1 to 6 additive draws, GPU about 0.1 to 0.5 ms | glow sprite: yes |
| 9 | HUD sharpness (device pixel ratio) | 3 | 3 | 1.0 | cached HUD canvas redrawn only on change | no |
| 10 | Depth sorting of units, drops and layers | 1 | 1 | 1.0 | a sort of 2 to 8 items | no |
| 11 | Rim light on units | 2 | 3 | 0.7 | 1 extra draw per unit | only if the art lacks it |

The order to build: 1, 2, 3 first (one afternoon, no art needed), then 4 (start the Colab request now, it is the longest), then 5, 6, then the layers (7) as the art arrives, 8 to 11 last.

Budget target (my proposal, INVENTED): the whole lift adds at most 3 ms of GPU time per frame in normal mode and at most 0.8 ms in calm mode on the owner's machine. If the 600-frame sample (A3) shows more, drop items from the bottom of the table first.

### A2. The items

For each item: technique, where, cost, calm fallback, how to verify.

**1. Colour grade and soft vignette (cached overlay)**
- Technique: build ONE offscreen canvas once (at scene start): a radial gradient from transparent in the middle to about 55 % dark blue-black at the corners, plus a very faint cool tint fill (about 6 % alpha, deep blue-violet) for the Halloween grade. Draw it every frame with one `drawImage` in `source-over`. Use `source-over` with alpha, not `multiply`: multiply costs more and gives nothing here. Because the gradient is smooth, the offscreen canvas can be 960 x 540 and be scaled up with no visible loss (2.1 MB instead of 8.3 MB).
- Where: new `buildGradeOverlay()` called from `startMatch()` (line 363) and a `drawGrade()` call in `draw()` after the front layers and particles, before `drawTopHUD()` (line 1740 area, step 11), so the HUD is not darkened.
- Safe areas: keep the vignette weaker over the top HUD (y 0..110) and the dock band (y 880..1080) so text contrast does not drop. Build the gradient centred slightly above the middle (y about 470).
- Calm fallback: bake the grade into the cached background composite (see item 7 calm fallback), so it costs nothing per frame. This is allowed by the calm table only if "full-screen overlays: 0" means no per-frame overlay draw. Say so when wiring.
- Verify: screenshot, read pixels with `getImageData`. The mean luminance of a 100 x 100 patch at each corner is 12 % to 30 % darker than the same patch with the grade off (INVENTED band), the centre patch differs by 2 % or less, the HUD bar patches differ by 5 % or less.

**2. Contact shadows from a cached sprite**
- Technique: at start-up draw one soft ellipse into a small canvas (for example 160 x 48) with a radial gradient scaled in y (`createRadialGradient` once, then `ctx.scale(1, 0.3)`), black at the centre with alpha 0.5 fading to 0. Each frame `drawImage` it under every unit. No `shadowBlur` and no `filter: blur` per frame (both are slow on canvas). Shadow width follows the unit's width; it shrinks and fades while the unit is knocked up or while it is the target of a high arc.
- Where: `drawFullArtCharacter` (line 2166), replace the `ctx.ellipse` block (lines 2170 to 2174). Shadow y must follow the ground: `Terrain.groundY(u.x)` when task 47 lands, else `GROUND_Y`.
- Cost: about 0.05 ms for two units. Calm fallback: keep (it is cheaper than the flat ellipse it replaces if the sprite is small).
- Verify: screenshot at 100 %, the shadow centre is within 4 px of the unit's feet x, it is visible on the ground strip (the shadow row is at least 20 % darker than the ground beside it) and it has no hard edge (the outermost 25 % of its width fades smoothly; check the line profile).

**3. Idle breathing**
- Technique: `computePose(u, team)` already returns `scx` and `scy` (used at the `ctx.scale(pose.scx, pose.scy)` call). Add for `animState === "idle"`: `scy *= 1 + 0.012 * sin(2*pi*0.45*t + phase)` and `scx *= 1 - 0.006 * sin(...)`, anchored at the feet (the code already translates to the feet before scaling). Phase per unit so the two do not breathe together. At most 1.2 % of height: about 2.5 px on a 220 px unit. It must stop during charge, throw and hit.
- Where: `computePose` and its caller at `drawFullArtCharacter`.
- Calm fallback: off (a motion effect).
- Verify: two screenshots 1 s apart at the same game state: the unit's top edge differs by 1 to 3 px, the feet row is identical.

**4. Crisp background**
- Cause: 1536 x 864 stretched to 1920 x 1080 (1.25x), then scaled again by the browser.
- Fix, no code: regenerate the scenes at 1920 x 1080 natively on Colab, or generate at the model's working size and upscale 2x with a real upscaler on Colab (job in `colab/layered_job.py`, `UPSCALE` switch; licence check in B6). A canvas-side resize is not a fix; do not "sharpen" with code.
- Targets: layer images are stored at their draw size (1920 wide for full-width layers). A 2x source (3840 wide) is not worth the memory: 33 MB decoded per full layer. On a 2x display the browser enlarges 1920 px by 1.46x, which is acceptable for a painted background (state this to the owner honestly: it will be slightly soft on a 5K display, crisp on a 1080p or 1440p one).
- Code that helps: draw with `imageSmoothingQuality = "high"` (the layer helper sets it) and avoid fractional destination coordinates for the single background.
- Verify: crop 400 x 300 around the moon edge at 100 % zoom from a screenshot at the owner's display size. Take a line profile across the moon edge: the 10 % to 90 % rise distance is 3 px or less on the canvas (INVENTED), against the current image for comparison.

**5. Hit feedback polish (inside the effects budget)**
- Existing: hit-stop 0.075 s, white flash, `screenShake` 0.18 s, particles. Budget from `docs/ultimates_design.md`: 500 particles alive, 14 sprite particles, 6 floating numbers, shake peak +-10 x / +-6 y px for 0.30 s, no more than 2 flashes per second, no flash above alpha 0.25 over more than 40 % of the screen.
- Add, all inside that budget: (a) a camera kick instead of random jitter for the first 3 frames of a hit (a decaying `cameraX` impulse of 6 px, shared with the layers so the background reacts with parallax, which reads as impact); (b) a short red edge pulse by changing the vignette overlay alpha for 0.15 s (no new draw); (c) damage numbers pop in at 130 % and settle to 100 % in 0.12 s; (d) reuse the per-unit flash canvas instead of resizing it every frame (the white flash and the poison tint in `drawFullArtCharacter` set `flashCv.width = dw; flashCv.height = u.h` at about lines 2214 and 2226; assigning the size clears and may reallocate the buffer). Resize only when the size changes.
- Calm fallback: kick and pulse off, numbers without the pop, shake off (from the calm table).
- Verify: record the particle count and the longest frame during 20 consecutive hits (A3). Pass: particle count never above the cap, no frame above 25 ms (INVENTED), no HUD pixel changed more than 5 % (check C10 of `docs/ultimates_design.md`).

**6. Ground fog bands drifting with the wind**
- Technique, no art: raise the fog share of `windField` per scene theme (`docs/converge_scenes.md` section 5: graveyard 6, bell tower 3, pumpkin field 8 puffs) and make them a little denser (alpha 0.05 now; 0.08 is still faint). They already drift with the wind (`WIND_SPEED.fog = 90 px/s` at full wind) and keep out of the HUD.
- Technique, with art: one tileable fog band layer (`fog`, `tileX`, `drift` 120 px/s at full wind, `calmDrift` 6) drawn behind the units, front of the tombstones. `SceneLayers` moves it with the same wind value, so both agree.
- Where: `windField` creation (line 509) takes a `theme`; layer manifest for the band.
- Cost: about 0.2 ms for the band. Calm fallback: wind items 64 to 32 (fog share unchanged), the band becomes static (no drift).
- Verify: screenshots at wind -4, 0, +4: fog moves downwind, no fog puff covers a unit's face or the HUD (mean luminance of the unit's bounding box differs by 8 % or less between fog on and off, INVENTED).

**7. Parallax layers, camera sway, wind sway**
- Technique: `SceneLayers` (this task). 3 to 5 depth layers is the first target (sky, far, mid, ground, front); the full 8 slots are in B2. Camera: a slow sway `cameraX = 8 * sin(2*pi*0.07*t)` plus a lead of 2 % toward the active unit and the hit kick, clamped to +-24 px. Layers far behind the play plane move up to 24 px against it, layers in front move the other way, the play plane (units, fence, ground) does not move. Wind sway: trees lean in the wind direction with a sheared draw (pivot at the ground), banners and hanging things swing from a top pivot. Amplitudes: trees 14 px, banners 10 px, foreground grass 6 px at full wind, about 10 % of that in calm air.
- Where: new `js/scene_layers.js` loaded after `wind_fx.js`; `draw()` step 1 and 2, `updatePhysics` (line 1475), `startMatch` (line 363). Exact lines in `docs/scene_layers_integration.md`.
- Cost: with 5 full-canvas layers about 10 Mpx fill, GPU about 1.5 to 4 ms on an integrated GPU (estimate); rect layers (ground, fog, tombstones) cost a third. Memory about 30 MB decoded for a full scene (B2).
- Calm fallback: draw the layers ONCE into an offscreen canvas after `scene.reset()` (sway at its tiny calm value, camera 0) and draw that single canvas each frame. Cost then equals the current single background. If a layer image is missing or `manifest` is empty the helper already falls back to `images.bg`.
- Verify: see checks 5, 6, 7 in A4.

**8. Moon glow and light bloom**
- Technique: a soft glow sprite (`moon_glow`, about 700 x 700) drawn with `lighter` at alpha 0.4 to 0.7 and a slow pulse (`pulse` 0.2, `pulseHz` 0.15 means the alpha swings by at most 20 % every 6.7 s). Bloom on a few bright sprites only: fire projectiles, the muzzle flash, candle flames, ultimates. Make one pre-blurred copy of each such sprite at load time (blur once with an offscreen canvas `filter = "blur(8px)"`, never per frame), then draw it again with `lighter` at 1.4x scale and alpha 0.35. Limit: 6 additive draws per frame (the layer validator already allows at most 2 full-canvas blend layers; a rect layer is not counted).
- Where: layer manifest for the moon glow; `drawProjectile` and the fx draw loop (step 8b of `draw()`) for the bloom copies.
- Cost: 0.1 to 0.5 ms. Calm fallback: off, except the static moon glow baked into the cached composite.
- Verify: count additive draws per frame (wrap `ctx.globalCompositeOperation` in a test build), at most 8. Count pixels at 255/255/255 in a screenshot: at most 0.5 % of the frame (INVENTED), so nothing is blown out.

**9. HUD sharpness (device pixel ratio)**
- Cause: HUD text is drawn into the 1920 x 1080 canvas (`drawTopHUD`, `drawRuleOverlay`, unit tags, floating texts). The browser scales it by 0.729 (or 1.46 on a 2x display), so the text is soft. `window.devicePixelRatio` is not read anywhere in `index.html` (a search found no use).
- Options: (A) a second, transparent HUD canvas stacked on top, sized to the displayed width times `min(devicePixelRatio, 2)`, drawn with `ctx.scale(k, k)` and redrawn only when a HUD value changes (round, timer second, HP, wind, shield count), at most 10 times per second. Cost per frame is then one cached canvas, which the browser composites for free. (B) raise the main canvas backing store to the displayed size: costs 2x to 4x fill for everything. Recommended: A. Fonts are task 48, so do A after the font swap.
- Calm fallback: keep A (it is cheaper than redrawing the HUD every frame).
- Verify: screenshot of the top plate at 100 %: the glyph stems are 1 device px crisp, no halo; the same frame with the old path for comparison.

**10. Depth sorting**
- Technique: draw units, drops and the fence in order of base y (then x). Today the player is always drawn before the AI and the airdrop before the fence. With 1 v 1 and equal `GROUND_Y` this is invisible; with terrain slopes (task 47) and the 4 v 4 mockup it matters. Front-plane layers (foreground grass, hanging chains) go after the units and before particles.
- Where: `draw()` steps 3 to 6: build a small array of `{y, x, fn}` and sort. About 8 entries.
- Calm fallback: none needed. Verify: put the two units at different y in a test scene, the lower one is drawn on top.

**11. Rim light on units**
- First check whether the art already has it. `docs/art_style_guide.md` says objects have a "cool cyan rim light" and characters a warm orange outer outline, both painted. If so, skip this item.
- If still wanted: one cached tinted copy per sprite (made once at load with `source-atop`), drawn with 2 px offset away from the moon at alpha 0.25, `lighter`. It is a lighting effect on the sprite's own silhouette. It must not repaint the character.
- Calm fallback: off. Verify: side-by-side screenshot, the rim is 2 px wide on the moon-facing side only.

### A3. How the main line measures (replaces my estimates)

JS time per frame (does not include GPU time, which a script cannot read; say so in the report):

```js
// Paste in the browser console while a match runs. Wrap draw() once, sample 600 frames.
(function () {
  const orig = window.draw; const t = []; let n = 0;
  window.draw = function () { const a = performance.now(); orig(); t.push(performance.now() - a); if (++n === 600) { window.draw = orig; t.sort((x, y) => x - y); console.log('draw() JS ms: median', t[300].toFixed(2), 'p95', t[570].toFixed(2), 'max', t[599].toFixed(2)); } };
})();
```

(`draw` is a top-level function declaration, so it is `window.draw`. If the game script is wrapped in a module later, adapt.) For GPU cost use the browser Performance panel and compare the frame time with each item switched off. Run each time: the baseline, then one item on, then the full set, then calm mode. Record median, p95, max, and `performance.memory` (Chrome) for decoded memory.

Rule of thumb: a frame at 60 Hz has 16.7 ms. The existing loop already caps physics at 6 steps per frame.

### A4. Screenshot checklist (10 checks)

Take every screenshot at the displayed size and at native 1920 x 1080 if the browser allows it. Pass criteria with INVENTED numbers are marked "(I)".

| # | Check | How | Pass |
|---|---|---|---|
| 1 | Background sharpness | 400 x 300 crop at the moon edge, 100 % zoom, line profile | 10 to 90 % rise <= 3 px (I), better than the 1536 x 864 original |
| 2 | Vignette and grade | corner and centre 100 x 100 patches, grade on and off | corners 12 to 30 % darker (I), centre within 2 %, top HUD and dock within 5 % |
| 3 | HUD readability over the scene | top 110 px and bottom 200 px bands | text/background luminance ratio >= 3:1 (the threshold of `docs/converge_scenes.md` check 5) |
| 4 | Feet and shadows | crop 300 x 120 under each unit | shadow centre within 4 px of the feet x, soft edge, ground not covered |
| 5 | Parallax | two shots at `cameraX` -24 and +24, same game state | far layer moves 24 x (1 - p) px (match by template search, +-1 px), fence and units pixel-identical |
| 6 | Wind sway | wind -4, 0, +4, same time offset | tree tops lean with the wind; the pivot row (the ground line) does not move; calm air: <= 1.4 px sway |
| 7 | No edge strips | camera +-24, wind +-4, check the outer 40 px columns | no clear colour (#0a0514) or black strip at either edge |
| 8 | Fog and glow do not hide anything | unit bounding boxes and the HUD, fog and glow on vs off | luminance change <= 8 % on a unit (I), 0 on the HUD text; no pixel above 255/255/255 on more than 0.5 % of the frame (I) |
| 9 | Fallback | rename one required layer file, reload | the page shows the single baked background, no exception, one 404 in the console |
| 10 | Frame time and memory | A3 script, 600 frames, normal and calm | normal: p95 draw JS <= 6 ms and no frame above 25 ms (I); calm: <= 3 ms; decoded layer memory <= 40 MB per scene (I) |

### A5. What must NOT be done in code (it would be faking art)

Code may do light, depth and motion on art that already exists. Code may not make the art.

Do not:
- Draw trees, tombstones, castle, moon, hills, fog sprites or foreground silhouettes with canvas paths to stand in for a missing layer. When a layer is missing the answer is the single baked background, not a code drawing.
- Cut a layer out of the single baked background by colour threshold, flood fill or a hand-drawn polygon and "repair" the hole with blur or a clone. If a layer is needed, Colab makes it (decomposition or its own prompt).
- Recolour or tint characters per scene to fake a lighting change (`docs/converge_scenes.md`, row 10 of section 8, already decided: units do not change colour per scene).
- Claim a 2x image by resizing a smaller one in the browser or in a script. Only a real upscaler run on Colab, or a native re-generation, counts.
- Use code-made noise, "painterly" filters or sharpen filters to hide softness.

Fine to do in code: gradients for vignette, grade and glow (light is not an object), the cached ellipse shadow, additive copies of a sprite's own pixels for bloom, camera and sway transforms, shear for sway, particles that already exist, 9-slice geometry of UI frames, cropping rectangles from Colab images, recolouring EFFECT sprites from a palette (B5).

## Part B. Asset split

### B1. Principles

- A layer is one PNG with alpha. Full-width layers are stored 1920 px wide at their draw size. A layer that covers only a band (ground, fog, tombstones) is stored at the band size, and the manifest `rect` says where it goes. That is what keeps memory low.
- The game loads a manifest per scene. If anything is missing it falls back to the single baked image; nothing breaks. The single image stays in the repo as the safety net.
- Two ways to make layers: (1) **Decomposition**: Qwen-Image-Layered splits one finished picture into RGBA layers and inpaints what was hidden. Every layer is registered with the others because they come from one canvas. Best for characters and scenes where the parts must line up. (2) **Separate prompts**: Qwen-Image-Edit-2511 or the existing Edit job makes one element on flat magenta, keyed with `scripts/key_magenta_items.py`. Best for items and UI. Parts made this way do not register with each other, so do not use it for pieces of one character.
- Code only makes pure geometry: crops by rectangle, 9-slice cuts, tiling, row bands.

### B2. SCENES

Eight slots at most (`SceneLayers.MAX_LAYERS`). Order is the `depth` number, low = far.

| Depth | Slot (name) | Plane | Size stored / rect | Parallax | Sway (px at full wind) | Blend | Made by |
|---|---|---|---|---|---|---|---|
| 00 | `sky` (sky, moon, stars, clouds; the bottom 220 px is dark soil so a terrain pit shows earth, not sky) | back | 1920 x 1080, opaque | 0 | 0 | normal | Colab: native generation, or Layered layer 0 |
| 05 | `moon_glow` / `sun_glow` / `candle_glow` | back | about 700 x 700 RGBA, rect near the light | 0.02 | 0 | lighter, alpha 0.4 to 0.7, pulse 0.2 | Colab: separate prompt (a soft glow on black, keyed by luminance) or code radial gradient (light, allowed) |
| 10 | `castle` (far silhouettes) | back | 1920 x 600 RGBA, rect [0,260,1920,600] | 0.1 | 0 | normal | Colab: Layered |
| 20 | `trees` (mid trees, banners, hanging things) | back | 1920 x 820 RGBA, rect [0,80,1920,820] | 0.35 | 14 trees (pivot 860, standing); bell/banners 10 (pivot at the top, hanging) | normal | Colab: Layered |
| 30 | `tombs` (tombstones, gate, near props; none in the empty band) | back | 1920 x 360 RGBA, rect [0,540,1920,360] | 0.7 | 0 | normal | Colab: Layered or separate |
| 40 | `ground` (the strip the units stand on) | back | 1920 x 260 RGBA, rect [0,820,1920,260] | 1 | 0 | normal | Colab: separate prompt, as today's `ground_strip.png` |
| 50 | `fog` (low band, tileable left to right) | back | 1920 x 300 RGBA, rect [0,700,1920,300] | 0.9 | drift 120 px/s at full wind, 6 in calm air | normal, alpha 0.5 | Colab: separate prompt, must tile (left edge = right edge) |
| 90 | `foreground` (grass, stones, cobweb in the bottom corners and edges; nothing between y 700 and 1000) | front | 1920 x 220 RGBA, rect [0,860,1920,220] | 1.3 | 6 (pivot 1080) | normal | Colab: separate prompt |

Memory for the graveyard set: 8.3 (sky) + 4.6 (castle) + 6.3 (trees) + 2.8 (tombs) + 2.0 (ground) + 2.3 (fog) + 1.7 (foreground) + 2.0 (glow) = 30 MB decoded (arithmetic from the sizes above). Only the active scene's layers are loaded; the other two scenes stay as their single images for the start screen.

What each slot shows, per scene (from `docs/converge_scenes.md`; the rules there still hold: ground band y 780..1000 empty, centre column x 880..1040 empty from y 560 to 1000, HUD band y 0..110 and dock band y 880..1080 low contrast):

| Slot | Graveyard (`graveyard`) | Bell tower (`belltower`) | Pumpkin field (`pumpkin`) |
|---|---|---|---|
| `sky` | night sky, large moon, stars, thin clouds | dark stone back wall with the arched window and night sky | orange-to-violet dusk sky, low sun, clouds |
| glow | `moon_glow` | `candle_glow` (warm, two lamps) | `sun_glow` |
| `castle` | far chapel and mausoleum silhouettes | city rooftops seen through the window | low hills and a far leaning scarecrow (x < 300 or x > 1620) |
| `trees` | bare trees (sway) | bronze bell on its frame, y 150..420, away from x 880..1040 below y 560 (hanging sway from the top) | far corn stalks and distant jack-o'-lanterns, y < 760 |
| `tombs` | tombstones, iron gate pieces at the sides | stone pillars and gargoyles at x < 300 and x > 1620, y 250..600 | field rows, fence posts at the sides |
| `ground` | graveyard earth (exists as `ground_strip.png`) | stone slabs (`ground_strip_belltower` request) | dirt and short grass (`ground_strip_pumpkin` request) |
| `fog` | pale blue mist band | thin grey dust haze | warmer orange-violet mist (8 puffs by `windField` too) |
| `foreground` | grass blades, a cobweb in the top corners is NOT allowed (HUD band) | rubble and chain ends at the bottom corners | vines and pumpkins only at y > 1000 |

Terrain (task 47, brief only; `(not published)` was not available):
- The terrain profile is an invisible collision line. `ground` is the only layer on the play plane (parallax 1) and the only one whose upper edge must match that profile. All other layers have a bottom edge that ends above y 780 or is hidden behind `ground`.
- Terrain variants: extra ground images in the same folder, named `40_ground_<preset>.png` (for example `40_ground_central_pit.png`, `40_ground_hill_valley.png`). They are not manifest layers. The loader stores them as `images.ground_<preset>` and copies the active one to `images.ground`. A missing variant means the flat ground is used and the terrain debug line still shows the true profile.
- Pits cut the ground image. What shows through is whatever is behind it, so `sky` must be dark soil in its bottom 220 px, and no back layer may have a visible bottom edge in y 780..1080.
- Nothing with parallax other than 1 may carry a line that looks like the floor. A layer with parallax 0.7 shifts up to 7 px against the play plane, which is fine for tombstones but would make a floor line slide under the units' feet.
- The foreground layer must stay out of the pit and slope area, y 700..1000.

Manifest example (the game loads one file per scene; this one is checked by `scripts/test_scene_layers.js`, which parses the block below and runs the validator on it):

```json manifest-example
{
  "version": 1,
  "scene": "graveyard",
  "width": 1920,
  "height": 1080,
  "maxCamera": 24,
  "layers": [
    { "name": "sky", "file": "assets/layers/graveyard/00_sky.png", "depth": 0, "parallax": 0 },
    { "name": "moon_glow", "file": "assets/layers/graveyard/05_moon_glow.png", "depth": 5, "parallax": 0.02,
      "rect": [1220, 0, 700, 700], "blend": "lighter", "alpha": 0.7, "pulse": 0.2, "pulseHz": 0.15, "required": false },
    { "name": "castle", "file": "assets/layers/graveyard/10_castle.png", "depth": 10, "parallax": 0.1,
      "rect": [0, 260, 1920, 600] },
    { "name": "trees", "file": "assets/layers/graveyard/20_trees.png", "depth": 20, "parallax": 0.35,
      "rect": [0, 80, 1920, 820], "sway": 14, "swayHz": 0.3, "pivotY": 860 },
    { "name": "tombs", "file": "assets/layers/graveyard/30_tombs.png", "depth": 30, "parallax": 0.7,
      "rect": [0, 540, 1920, 360] },
    { "name": "ground", "file": "assets/layers/graveyard/40_ground.png", "depth": 40, "parallax": 1,
      "rect": [0, 820, 1920, 260] },
    { "name": "fog", "file": "assets/layers/graveyard/50_fog.png", "depth": 50, "parallax": 0.9,
      "rect": [0, 700, 1920, 300], "tileX": true, "drift": 120, "calmDrift": 6, "alpha": 0.5, "required": false },
    { "name": "foreground", "file": "assets/layers/graveyard/90_foreground.png", "depth": 90, "parallax": 1.3,
      "plane": "front", "rect": [0, 860, 1920, 220], "sway": 6, "pivotY": 1080, "required": false }
  ]
}
```

Manifest fields: `name`, `file` (`(not published)`, `<nn>` is the two-digit depth rank, `<name>` equals `name`), `depth` (draw order, 0 far to 100 near), `parallax` (0 far, 1 play plane, up to 1.5 in front), `sway` (px at full wind, 0 to 32), `swayHz`, `pivotY` (row that stays fixed: standing things lean their top, hanging things swing their bottom), `tileX`/`drift`/`calmDrift` (wrap-around fog), `blend` (`source-over`, `lighter`, `screen`, `multiply`), `alpha`, `pulse`/`pulseHz`, `rect` (`[x, y, w, h]`), `plane` (`back` before the ground and units, `front` after), `required` (default true: if a required image is missing the whole scene falls back to the single image). Limits the validator enforces: at most 8 layers, at most 2 full-canvas blend layers, camera shift plus sway at most 40 px per layer.

File naming: `(not published)`, manifest `(not published)`, terrain variants `40_ground_<preset>.png` beside them. Single fallback image: `(not published)` (unchanged).

Fallback when layers are missing: `SceneLayers.create` with a missing, empty or invalid manifest, or with a missing required image, draws `images.bg` stretched to the canvas exactly as `draw()` does today (line 1743), or the flat colour `#0a0514` if even that is not loaded. An optional layer that failed to load is skipped.

### B3. CHARACTERS

Today: one 1024 x 1024 image per hero facing left (`assets/units/unit_*.png`), an unarmed variant (`*_unarmed.png`) and the held weapon as its own layer (`USE_LAYERED_HANDS`, `HELD_WEAPON`), plus whole-body pose images (`assets/poses/`). Planned in `.kiro/steering/tech.md`: `(not published)`, `(not published)`, `(not published)`. The mirror rule is unchanged: parts are drawn once facing left, mirrored for the other team.

| Order | Part | Why separate | Made by |
|---|---|---|---|
| 0 | `shadow` | follows the ground and the terrain | code (cached ellipse, item A2.2) |
| 1 | `cape_back` / robe back / wing (behind the body) | sways with the wind like flame lean | Colab Layered |
| 2 | `arm_back` (off hand) | idle motion | Colab Layered |
| 3 | `body` (torso, legs, feet) | breathing, hit squash | Colab Layered |
| 4 | `head` | nod, hit snap, a pivot at the neck; also feeds the big-head portrait | Colab Layered |
| 5 | `emissive` (eye fire, pumpkin glow, cannon rim) | drawn additive, pulses | Colab Layered or a mask from the glowing pixels (decide on the first test) |
| 6 | `arm_front` (throwing arm and open hand) | rotates about the shoulder for windup and release, replacing pose swaps | Colab Layered |
| 7 | `weapon` (exists: `assets/weapons/*`) | leaves the hand on release | exists |

- Decomposition is the right tool because parts must register. Feed it the existing 1024 art. 8 layers is the target, 4 the fallback; the model decides how to split, so a human reviews the contact sheet and maps its layer indices to the part names (the job writes the sheet).
- Registration: all parts keep the original 1024 x 1024 coordinate frame and are cropped to their bounding box. A `rig.json` per hero stores each part's crop offset and pivots (neck, shoulder, wrist, cape top). Total decoded memory target: 6 MB per hero, 24 MB for four (arithmetic: parts cropped to roughly 1.4 Mpx in total).
- Naming: `(not published)` and `(not published)`. `SceneLayers` does not load these; `(not published)` is a later task.
- Fallback: if any part is missing the game keeps the single image plus the pose images it uses today.
- Not decided: whether the rig replaces the pose images (`skel_windup`, `skel_release`, `skel_hit`). It could save art requests but changes the look of throws, so it is an owner call.

### B4. PROJECTILES

| Part | Content | Made by | Naming |
|---|---|---|---|
| `art` | the flying object (spear, dart, shield, cannonball), facing left, 256 x 256 or smaller | exists (`assets/weapons/proj_*_colab.png`, `assets/env/proj_*.png`) | unchanged |
| `glow` | additive halo for fire and magic projectiles, 128 x 128 | code radial gradient (it is light), or a Colab glow | cached at load |
| `trail` | a horizontal streak texture, 256 x 64, tileable along the flight, white-grey so a palette colours it | Colab separate prompt, or the existing particle presets | `(not published)` |

The trail is a stretched quad along the velocity vector with `lighter`, alpha 0.5 fading with age. Fallback: the existing particle trail.

### B5. UI

| Part | Content | Made by |
|---|---|---|
| `frame` | the border: 9 pieces (4 corners, 4 edges, centre), corner size fixed, edges tile | Colab makes the whole frame once (exists: `ui_dock_frame`, `ui_top_plate_*`); code cuts the 9-slice by rectangles (geometry) |
| `plate` | button plates, normal and active, as two images | Colab separate prompts (exist) |
| `icon` | one 128 x 128 icon per skill, no frame | Colab separate prompts |
| `glow` | an additive rim for active and hover states | code gradient, or a Colab glow |
| `fill` | tileable stone or wood behind the frame | Colab (tileable prompt) |
| `text` | not art; fonts of task 48 | fonts |

Naming: `(not published)` with a manifest of the same shape when the UI is wired; `SceneLayers.validateManifest` only covers scenes today.

### B6. EFFECTS: sprite plus palette

- Split each effect into a **white or grey alpha sprite** (shape and brightness only) and a **palette** (a few colour stops in JSON). The code tints the sprite once at load (`source-atop` into a cached canvas per palette, at most 6 variants) and draws it additive. This lets one flash serve four classes without new art. Recolouring effects is allowed; recolouring characters or scenes is not (A5).
- Existing sheets: `(not published)` and `(not published)`. New ones follow `(not published)` plus a `palette` field in the manifest.
- Colab prompt rule for masks: "white and light grey glow effect on a flat black background, no colour" then key by luminance. Magenta keying is for coloured items.

### B7. Colab job design (`colab/layered_job.py`)

- Model: `Qwen/Qwen-Image-Layered`, `QwenImageLayeredPipeline` in diffusers (Apache 2.0 according to the task text; read the model card licence line on the day). Input: a scene picture from the Drive `PumpkinKiller/out/` folder, the output folder of the existing Edit job. Layers: 8 (4 as fallback). Working resolution 1024 (640 is the other supported bucket). Seeds: three per scene, pick the best.
- Two phases in one file because a human must map layers to names:
  1. `decompose`: writes the raw layers and a contact sheet (checkerboard background so alpha is visible) to `layers_raw/<scene>/`.
  2. `finish`: reads `layer_map_<scene>.json` (written by hand from the sheet: raw index to name, depth, opaque flag, rect, optional merge of several raw layers), then per layer: bleed colour into transparent pixels, optional 2x upscale (RGB by the upscaler, alpha by Lanczos), resize to the target size, crop to the rect, save `layers_out/<scene>/<nn>_<name>.png`, run the quality checks, write `report.json` and a draft `manifest.json`.
- Upscaler: Real-ESRGAN (`xinntao/Real-ESRGAN`, `RealESRGAN_x4plus`). From memory its code licence is BSD-3-Clause; I could not open the repository from here, so **the licence of the code and of the weights file is unchecked**. `LICENSE_ACK` in the job stays False until someone reads the repository `LICENSE` and the model release notes and the contest rules. It is also known (from memory) to fail on newer torchvision with an import error in `basicsr`; the job catches this and continues without the upscale. Swin2SR (Apache 2.0 from memory, via `transformers`) is the other candidate; same check applies. If neither is allowed, regenerate the scene natively at 1920 x 1080 instead.
- Sharpness: the model works at 640 or 1024, so a layer comes out at roughly that size and is resized to 1920 wide. With `UPSCALE = False` this is a plain Lanczos enlargement of about 1.9x and the layers will be soft. The first run logs the real output size (`seed ...: N layers, size ...`); decide from that whether the upscale step is needed.
- Nothing in the job was run, and the file was not syntax-checked by a Python parser (that shell command did not run in this session). Colab, GPU and model weights were not available. Run ONE scene first (`ONLY = ["graveyard"]`, `LAYERS = 8`), look at the sheet, then finish it.

### B8. Test plan for the first scene (graveyard)

1. Generate or pick the best 1920 x 1080 (or 1536 x 864 for a first try) graveyard picture. Put it in Drive `out/`.
2. Run `decompose` with 8 layers, seeds 777, 778, 779. Open the three contact sheets. Choose the seed whose layers separate sky, far shapes, trees, tombstones, ground best. Write `layer_map_graveyard.json`. If no seed separates cleanly, switch to separate prompts for `trees`, `tombs`, `foreground` and keep only the sky and ground from decomposition.
3. Run `finish` with `UPSCALE = False` first. Read `report.json`. Fix the map, repeat.
4. Copy `layers_out/graveyard/` to `(not published)` and the validated `manifest.json` beside it. Run `node scripts/test_scene_layers.js` (the doc example) and add a test that loads the real manifest (a later step; no real manifest exists yet).
5. Wire it (`docs/scene_layers_integration.md`), then run the 10 checks of A4 on the graveyard.
6. Only then request the bell tower and the pumpkin field, using what failed in the first run.

### B9. Layer quality checks

Automatic (in `finish`; thresholds INVENTED):

| Check | Pass |
|---|---|
| No magenta fringe | zero visible pixels (alpha > 16) with R > 200, B > 200, G < 90 |
| Alpha clean | `sky` (and any layer marked opaque) is 255 everywhere; other layers have at most 12 % semi-transparent pixels (16 < alpha < 240) among visible pixels, and no isolated specks |
| No empty or huge layer | visible coverage between 0.5 % and 95 % for non-opaque layers |
| No missing parts | recompositing all layers in depth order and resizing to the input gives PSNR >= 28 dB against the original picture |
| Size | the stored size equals the rect size (or 1920 x 1080 for full layers) |
| Seamless fog | the left and right columns of a `tileX` layer differ by a mean of 6/255 or less |

By eye (the contact sheet and a screenshot): no hole where a front object used to hide something (the inpainted part looks plausible), no halo of the old background colour around trees, no layer that contains two things that should move differently (a tree stuck to a tombstone), style matches `docs/art_style_guide.md`.

## Summary of decisions the owner or the main line must take

1. Native 1920 x 1080 scenes or a 2x upscale on Colab (and who checks the upscaler licence).
2. Whether the character rig replaces the pose images.
3. The calm mode switch wording: "full-screen overlays 0" is read here as "no per-frame overlay draw" so the grade stays baked in.
4. Whether HUD sharpness uses a second HUD canvas (recommended) after task 48 lands.
