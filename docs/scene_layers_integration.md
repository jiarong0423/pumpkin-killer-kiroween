# Scene layers: integration into `index.html` (for the main line)

Companion of `docs/visual_quality_plan.md` (why and what art) and `js/scene_layers.js` (the helper). This note says which `index.html` places change, in which order, and how to check each step. `index.html` was not touched by task 49. Line numbers are from the checkout read for task 49 and will move; search for the quoted code.

Status of the art: no layer image exists yet. With no manifest the helper draws the single baked background, so every step below can land before any art does.

## 1. How the helper works (what the page must give it)

```js
const sceneLayers = SceneLayers.create({
  manifest,              // parsed assets/layers/<scene>/manifest.json, or null
  images: sceneImages,   // { bg: <fallback image>, <layerName>: <HTMLImageElement>, ... }, read live at draw time
  seed: 7,               // sway phases; any integer
  windMax: 4             // same as WindFx
});
sceneLayers.update(dt, wind, cameraX);   // once per fixed physics step
sceneLayers.draw(ctx, "back");           // before ground-less content, fence, units
sceneLayers.draw(ctx, "front");          // after the units
sceneLayers.getMode();                   // "layers" | "image" | "fill"
sceneLayers.reset();                     // time 0, as on the first frame
```

- `sceneImages` must be its own object. Layer names such as `ground` collide with `images.ground` (the existing ground strip, `imgList` line 411), so do not reuse `images`.
- `images.bg` is the fallback key. `startMatch` already replaces `images.bg` per scene (line 365); copy it: `sceneImages.bg = images.bg`.
- The wind value is the page's `wind` (the same one given to `windField.setWind`). The helper clamps it to +-`windMax`.
- `cameraX` is in canvas px and is clamped to the manifest `maxCamera` (24 by default).
- No randomness at run time. The same seed and calls give the same numbers, so a replay or a screenshot test repeats.

## 2. Steps, each with a pass condition

Do them in this order. Each step is small and can be reverted alone. A flag `const SCENE_LAYERS = true;` near the other constants (line 399 area) lets the owner switch to the old path; with the flag off the code in step 3 is skipped and the old lines run.

### Step 1. Load the script

Add after `<script src="js/wind_fx.js"></script>` (line 251):

```html
<script src="js/scene_layers.js"></script>
```

Pass: browser console `typeof SceneLayers === "object"`; `node scripts/test_scene_layers.js` prints `ALL 81 TESTS PASSED` (the count grows when tests are added).

### Step 2. Create the instance (fallback only)

Next to `const windField = ...` (line 509) add:

```js
const sceneImages = {};
let sceneLayers = SceneLayers.create({ manifest: null, images: sceneImages, seed: 7, windMax: 4 });
let camT = 0, cameraX = 0;
```

In `startMatch()` (line 363), after `images.bg = ...` (line 365):

```js
sceneImages.bg = images.bg;
sceneLayers = SceneLayers.create({ manifest: null, images: sceneImages, seed: 7, windMax: 4 });
```

Step 5 replaces the second line with `loadSceneLayers(sc.id);`, which creates the instance itself.

Pass: no change in behaviour yet (the instance is not drawn).

### Step 3. Draw the back plane

In `draw()` replace the background block (lines 1741 to 1747) with:

```js
sceneLayers.draw(ctx, "back");
```

and keep the ground-strip block (lines 1749 to 1755) but run it only when the helper is not drawing a ground layer:

```js
if (sceneLayers.getMode() !== "layers") {
  /* existing ground strip code: images.ground drawImage at GROUND_Y - 40, 260 high, or the flat fill */
}
```

Leave `if (windField) windField.draw(ctx);` (line 1756) and `drawAirdrop();` after it as they are. Resulting order: layers (sky ... ground, fog) then wind items, drops, fence.

Pass condition, in the fallback mode (no layers): a screenshot is the same picture as before except for resampling. The helper sets `imageSmoothingQuality = "high"`, which can differ from the browser default, so compare with a mean absolute pixel difference below 2/255 (INVENTED) rather than exactly zero. The flat colour behind a missing image is the old `#0a0514`.

### Step 4. Update with the fixed step

In `updatePhysics(dt)` (line 1475), next to `if (windField) { windField.setWind(wind); windField.update(dt); }`:

```js
camT += dt;
cameraX = 8 * Math.sin(2 * Math.PI * 0.07 * camT) + camKick;      // camKick: decaying hit impulse, 0 until used
sceneLayers.update(dt, wind, cameraX);
```

Optional lead toward the active unit: add `0.02 * (activeUnit.x - 960)` (at most about +-16 px). The helper clamps the sum to `maxCamera`.

`updatePhysics` runs at the fixed 1/60 s step (up to 6 per frame). Do not call `update` from `draw()`: the sway would depend on the frame rate.

Pass: with a test manifest (below) the numbers in `sceneLayers.getState()` change between frames and stay inside `bound`; a 600-frame sample (plan A3) shows no new cost in fallback mode.

### Step 5. Manifest and image loading (per scene, lazy)

```js
async function loadSceneLayers(id) {
  Object.keys(sceneImages).forEach(k => { if (k !== "bg") delete sceneImages[k]; });
  let manifest = null;
  try {
    const r = await fetch("assets/layers/" + id + "/manifest.json", { cache: "no-cache" });
    if (r.ok) manifest = await r.json();
  } catch (e) { /* file:// or offline: stay on the single image */ }
  const bad = SceneLayers.validateManifest(manifest, { width: CANVAS_W, height: CANVAS_H });
  if (bad.length) { if (manifest) console.warn("scene layers rejected:", bad); manifest = null; }
  sceneLayers = SceneLayers.create({ manifest, images: sceneImages, seed: 7, windMax: 4 });
  if (!manifest) return;
  manifest.layers.forEach(l => {
    const im = new Image();
    im.onload = () => { sceneImages[l.name] = im; };
    im.src = l.file;
  });
}
```

- Only the active scene's layers are loaded (about 30 MB decoded for a full set, see the plan). The other scenes keep their single images for the start screen (`initStartScreen`, line 373).
- Until every required image has loaded the helper stays in `"image"` mode, then switches to `"layers"` by itself (it checks at draw time). There is no half-drawn scene: a required layer that is missing keeps the whole scene on the single image.
- A page opened from `file://` cannot `fetch` the manifest in most browsers. The code above then stays on the single image. Serve the game over `http://localhost` to see layers.
- If an image fails to load (404) `sceneImages[l.name]` stays undefined; nothing throws. The console shows the 404.
- When the terrain presets arrive (task 47), after loading also load `40_ground_<preset>.png` for the active preset into `sceneImages.ground_<preset>` and set `sceneImages.ground = sceneImages.ground_<preset>` when present.

Pass: with no manifest: console has no error except the 404 of `manifest.json` (use `HEAD` first, or expect one 404 per scene); a broken manifest logs the violation list and the picture is the single image; with a valid test manifest (fixture below) `getMode()` becomes `"layers"` after the images load.

### Step 6. Draw the front plane

In `draw()` after the two `drawFullArtCharacter(...)` calls (step 6 of the draw, about line 1790) and before the power gauge (step 7):

```js
sceneLayers.draw(ctx, "front");
```

Projectiles, particles, floating text and the HUD stay above it, so a flying object is never hidden by grass. A front layer must keep clear of the units (art rule in the plan: nothing between y 700 and 1000).

Pass: screenshot with front layer on and off; the unit boxes differ by at most 8 % mean luminance (plan check 8).

### Step 7. Colour grade, shadows, breathing (plan items 1 to 3)

Not part of the helper, listed so the order is clear: `drawGrade()` after the floating texts and before `drawTopHUD()` (step 11 of `draw()`), the cached shadow sprite in `drawFullArtCharacter` (lines 2170 to 2174), the idle scale in `computePose`.

### Step 8. Calm mode

Calm mode (budget in `docs/ultimates_design.md` section 1d): bake the back plane once and draw it as one image.

```js
let sceneBake = null;
function bakeSceneLayers() {
  sceneLayers.reset();                                   // sway at its calm start value, camera 0
  sceneBake = sceneBake || document.createElement("canvas");
  sceneBake.width = CANVAS_W; sceneBake.height = CANVAS_H;
  sceneLayers.draw(sceneBake.getContext("2d"), "back");
}
```

In calm mode `draw()` does `ctx.drawImage(sceneBake, 0, 0)` instead of `sceneLayers.draw(ctx, "back")`, and skips `sceneLayers.update`. Re-bake when the scene changes or when the last layer image finishes loading (compare `getMode()` once per second). The grade overlay (plan item 1) can be drawn into the same bake. Pass: calm mode frame cost equals the single-background cost (plan check 10).

## 3. Order of everything in `draw()` after the change

1. `sceneLayers.draw(ctx, "back")`: sky, glow, far shapes, mid trees, tombstones, ground, fog.
2. Ground strip (only when the helper is not in `"layers"` mode).
3. `windField.draw(ctx)`: fog puffs, dust, leaves.
4. `drawAirdrop()`.
5. `drawCentralWall()` (the fence; it stays on the play plane, parallax 1).
6. History trajectories, shields, tethers (unchanged).
7. Units, sorted by base y (plan item 10).
8. `sceneLayers.draw(ctx, "front")`.
9. Power gauge, thrown paths, projectiles, muzzle flashes, particles, floating text (unchanged).
10. `drawGrade()` (plan item 1), then `drawTopHUD()`.

The loop wraps `draw()` in the screen-shake translate (lines 2720 to 2724). Layers shake with everything else. Shake is a random shift of up to about 7 px; the layer overscan covers the camera and sway range, not the shake, so a thin strip of the container colour can show at an edge during a shake. Today's single background has the same property. Plan check 7 is taken on frames without shake.

## 4. The terrain interplay (task 47)

`(not published)` did not exist when this was written; this follows the task 47 brief.

- The terrain profile is invisible collision data. The `ground` layer is the picture of the floor and the only layer on the play plane (parallax 1). It is drawn in the back plane, before the fence and the units, exactly where `images.ground` is drawn today (top edge at `GROUND_Y - 40`).
- Pits and slopes need their own ground images (`40_ground_<preset>.png`, see plan B2). A missing one means the flat ground is drawn and the terrain debug line (task 47, e) still shows the real profile. The mismatch is visible in that case, which is the intended warning.
- What shows through a pit is the layers behind the ground. The plan requires the sky art to be dark soil in its bottom 220 px and no back layer to have a bottom edge in y 780 to 1080.
- No layer with a parallax other than 1 may carry a floor line (it would slide under the feet). The helper cannot check this; it is an art rule and plan check 5.
- Shadows and breathing anchors use `Terrain.groundY(u.x)` once `(not published)` is wired, else `GROUND_Y`.
- The terrain debug overlay is drawn after the front plane so it is never hidden.
- The headless engines (`scripts/sim_balance.js`, the MCP engine) do not draw and do not use layers. Layers never affect physics.

## 5. A fixture to try the steps without art

This is a test fixture, not game art. In the console, make solid-colour canvases with one distinct mark each and feed them in:

```js
const fx = (c, mark) => { const cv = document.createElement("canvas"); cv.width = 1920; cv.height = 1080;
  const g = cv.getContext("2d"); g.fillStyle = c; g.fillRect(0, 0, 1920, 1080); g.fillStyle = "#fff"; g.fillRect(mark, 400, 40, 400); return cv; };
sceneImages.sky = fx("#102", 300); sceneImages.castle = fx("rgba(0,0,0,0)", 700);   // etc.
```

then call `SceneLayers.create` with a manifest of the same names (any valid one, the files can be fake paths). A white bar per layer shows the parallax: with `cameraX` at +24 the `sky` bar moves 24 px, the `castle` bar 21.6 px (parallax 0.1).

## 6. What to check at the end (short)

- Fallback: remove one required file: one 404, the single background, no exception.
- Flag off (`SCENE_LAYERS = false`) or empty manifest: the old picture within the resampling tolerance of step 3.
- Plan checks 5, 6, 7, 9 and 10 in `docs/visual_quality_plan.md` section A4.
- `node scripts/test_scene_layers.js` still passes after any change to `js/scene_layers.js`.

## 7. Risks

| Risk | Handling |
|---|---|
| Decoded memory grows (about 30 MB per scene) | load the active scene only; remove the previous scene's layer images on scene change (the loader above does) |
| First frames show the single image, then the layers pop in | acceptable; or hold the start screen until `getMode() === "layers"` (owner choice) |
| A layer image has a different size from the manifest rect | the helper scales the image to the rect; check the stored size equals the rect size (`colab/layered_job.py` report) |
| The layer ground and the terrain profile disagree | terrain debug line; fall back to the flat ground variant |
| `fetch` blocked on `file://` | serve over localhost, or embed the manifest in a `<script type="application/json">` later |
