# Scene layers: requirements

Scope: `js/scene_layers.js` (the helper), `scripts/test_scene_layers.js` (tests), `colab/layered_job.py` (art job), the manifest format, and the notes in `docs/visual_quality_plan.md` and `docs/scene_layers_integration.md`. Wiring into `index.html` is out of scope for this spec.

Terms: **scene** is one battlefield (`graveyard`, `belltower`, `pumpkin`). **Layer** is one image of a scene with a depth, a parallax factor and optional wind sway. **Manifest** is the JSON file that lists a scene's layers. **Instance** is the object returned by `SceneLayers.create`. **Play plane** is the plane of the units, the fence and the ground; its parallax is 1. **Fallback** is the single baked background image `images.bg`. **Back plane** is drawn before the wind items, the fence and the units. **Front plane** is drawn after the units.

## R1 Module shape

1. The module shall not reference `window`, `document`, `Image`, `Math.random`, `Date`, `performance` or any timer.
2. When loaded by Node, the module shall export its API through `module.exports`.
3. When loaded by a browser script tag, the module shall expose its API as the global `SceneLayers`.
4. `draw` shall use only these members of the context passed to it: `save`, `restore`, `drawImage`, `fillRect`, `transform`, `globalAlpha`, `globalCompositeOperation`, `fillStyle`, `imageSmoothingEnabled`, `imageSmoothingQuality`.
5. `draw` shall leave `save` and `restore` balanced and shall leave `globalAlpha` and `globalCompositeOperation` as it found them.

## R2 Instance API

1. `SceneLayers.create({manifest, images, seed, width, height, windMax, fallbackKey, fallbackColor})` shall return an object with `update`, `draw`, `reset`, `getMode`, `getState`, `getViolations`, `width`, `height` and `layerCount`.
2. Where `width` or `height` is absent or invalid, the instance shall use 1920 and 1080.
3. The instance shall read `images` at draw time, not copy it, so images that load later and a replaced `images.bg` take effect.
4. `create` shall not throw for any value of `manifest`, including `null`, a string or a malformed object.

## R3 Manifest validation

1. `validateManifest(manifest, {width, height})` shall return a list of strings, one per violation; an empty list means valid.
2. The validator shall reject a manifest that is not an object, whose `version` is not 1, whose `scene` does not match `[a-z0-9_]+`, or whose `layers` is not an array.
3. The validator shall reject more than 8 layers.
4. For every layer the validator shall require a unique `name` matching `[a-z0-9_]+`, a `file` of the form `(not published)` whose folder is the manifest `scene` and whose name part equals `name`, a `depth` of 0 to 100 and a `parallax` of 0 to 1.5.
5. The validator shall reject `sway` outside 0 to 32 px, `swayHz` outside 0.05 to 2, `pivotY` outside 0 to the canvas height, `alpha` outside 0 to 1, `pulse` outside 0 to 0.5, `drift` beyond +-400 px/s, `calmDrift` beyond +-30 px/s, a `blend` other than `source-over`, `lighter`, `screen` or `multiply`, a `plane` other than `back` or `front`, and a malformed `rect`.
6. If a layer has `drift` or `calmDrift`, then the validator shall require `tileX` to be true.
7. If a layer uses a blend other than `source-over` and has no `rect`, then the validator shall require `alpha` of 0.5 or less, and shall reject more than 2 such layers per scene.
8. The validator shall reject a non-tiled layer whose camera shift (`maxCamera` times the absolute value of 1 minus `parallax`) plus `sway` exceeds 40 px.
9. The empty manifest (`version` 1, a valid `scene`, `layers` empty) shall be valid.

## R4 Fallback

1. If the manifest is missing, malformed, invalid or empty, then the instance shall have no layers and `draw` shall paint `images[fallbackKey]` (default `bg`) over the whole canvas.
2. If the fallback image is not loaded, then `draw` shall fill the canvas with `fallbackColor` (default `#0a0514`).
3. If any layer with `required` not false has no loaded image, then `getMode()` shall return `image` (or `fill`) and `draw` shall paint the fallback, not a partial scene.
4. If an optional layer has no loaded image, then `draw` shall skip that layer and paint the others.
5. An image counts as loaded only if it is an object, its `complete` is not false, and its width and height are greater than 0.
6. When the instance is in fallback mode, `draw(ctx, "front")` shall draw nothing.

## R5 Offsets

1. `update(dt, wind, cameraX)` shall compute, for every layer, a horizontal offset `dx`, a shear `shear`, an alpha, and `reach`, the largest horizontal displacement of any pixel.
2. The camera term shall be `cameraX * (1 - parallax)` with `cameraX` clamped to +-`maxCamera` (default 24); a layer with parallax 1 shall not move with the camera.
3. The wind sway shall be at most `sway` px in absolute value for any wind and any time, shall lean toward the wind direction on average, and shall be larger for stronger wind.
4. For every non-tiled layer, `reach` shall not exceed `offsetBound(layer)`, which is `maxCamera * |1 - parallax| + sway`.
5. Where a layer has `pivotY`, the layer shall be sheared so that the pivot row does not move and no row moves more than `sway`; content below the pivot swings its bottom toward the wind, content above it leans its top toward the wind.
6. Where a layer has `tileX`, its `dx` shall stay in 0 to the canvas width, shall advance at `calmDrift + wind * drift` px/s, and shall wrap.
7. A full-width layer shall be drawn wider than the canvas by its overscan margin on both sides so that a shifted edge never shows.
8. The wind shall be eased toward its target with a time constant of 0.6 s.
9. If `dt` is not a positive finite number, then `update` shall not advance time; if `dt` is above 0.1 s, then `update` shall use 0.1 s.
10. If `wind` or `cameraX` is not a finite number, then `update` shall treat it as 0.

## R6 Determinism

1. The per-layer sway phases shall come from a mulberry32 generator seeded by `seed`, used only inside `create`.
2. When two instances have the same seed and receive the same sequence of `update` calls, they shall return identical `getState()` values.
3. `reset()` shall return time, wind, camera and drift to their start values, so that the same calls then reproduce the first run exactly.

## R7 Drawing

1. `draw(ctx, which)` shall paint layers in ascending `depth` (ties in manifest order); `which` is `back`, `front` or `all` (default).
2. `draw` shall set the layer's blend mode and alpha for each layer and shall turn on `imageSmoothingQuality = "high"`.
3. A `tileX` layer shall be drawn as two copies side by side that overlap by 1 px, using only the rows of its `rect` when it has one.
4. `draw(null)` shall do nothing and shall not throw.
