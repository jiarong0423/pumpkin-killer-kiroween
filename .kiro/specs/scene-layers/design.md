# Scene layers: design

## Files

| File | Role |
|---|---|
| `js/scene_layers.js` | UMD module: manifest validator, offset maths, drawing, fallback. No DOM. |
| `scripts/test_scene_layers.js` | Node `assert` tests with a recording stub canvas. |
| `colab/layered_job.py` | Colab cell: Qwen-Image-Layered split, cleanup, optional upscale, quality report. Not run yet. |
| `docs/visual_quality_plan.md` | Why, the ranked quality items, the asset split tables, the manifest example (parsed by the tests). |
| `docs/scene_layers_integration.md` | Which `index.html` places change, in which order, with pass conditions. |

Plain JS in the style of `js/wind_fx.js` (ES5 syntax, `var`, one factory). No build step. It loads with a `<script>` tag.

## Data flow

```
manifest JSON --validateManifest--> violations? --yes--> no layers (fallback)
      |no                                              
      v
 normalizeLayers (defaults, seeded phases, overscan margin, pivot set-up, sort by depth)
      |
loop  update(dt, wind, cameraX) --> per layer: dx, shear, reach, alpha     (fixed 1/60 s step)
render draw(ctx, "back"|"front") --> drawImage per ready layer, or the single image, or a flat colour
```

## Offsets

- Parallax: `camOff = cameraX * (1 - parallax)`. The play plane (parallax 1) is the reference and never moves, so units, fence and ground stay registered. Parallax below 1 is behind it, above 1 in front of it. This is the physically correct sign for a camera that moves while the play plane is held still on screen.
- Wind sway: `swayX = sway * (0.5 * n + (0.1 + 0.4 * |n|) * sin(2 pi f t + phase))` with `n` the eased wind in [-1, 1]. The mean (0.5 n) leans with the wind, the swing grows with strength, and `|swayX| <= sway` for every n and t because 0.5|n| + 0.1 + 0.4|n| <= 1.
- Pivot (shear): `x' = x + c*y + e` with `c = side * swayX / far`, `e = -c * pivotY`. `far` is the distance from the pivot to the farthest drawn row, so no row moves more than `sway`. `side` is +1 when the pivot is in the upper half of the layer's rows (hanging: the bottom swings) and -1 otherwise (standing: the top leans).
- Fog (`tileX`): `driftPos` advances at `calmDrift + n * drift` px/s and wraps at the canvas width. The camera term is added before the wrap.
- Overscan: a non-tiled layer that spans the full width is drawn from `-margin` with width `W + 2 margin`, `margin = ceil(bound)`. At most 40 px (validator) means at most 4 % horizontal stretch at full camera and sway. A layer authored wider than the canvas avoids the stretch (art choice).
- Pulse: `alpha * (1 - pulse * (0.5 + 0.5 sin(...)))`, so alpha stays between `alpha * (1 - pulse)` and `alpha`.

## Fallback ladder

1. Valid manifest and every required image loaded: layers.
2. Otherwise the single baked image `images[fallbackKey]`, stretched to the canvas (what `draw()` does today).
3. Otherwise a flat colour.

All-or-nothing for required layers avoids a half-drawn scene with holes where the sky is missing. `required: false` (fog, glow, foreground) makes a layer optional.

## Why these choices

- Horizontal offsets only. Vertical motion of a background reads as the whole world bobbing and fights the ground line the units stand on.
- A sheared draw for trees. A rigid shift would slide the trunks' bases along the ground.
- `images` read at draw time. The page loads images asynchronously and swaps `images.bg` per scene; copying would freeze the first state.
- No random numbers at run time, for replay and for screenshot tests.
- Limits in the validator (8 layers, 2 full-canvas blend layers, 40 px shift) keep fill cost and stretch bounded without a profiler.
- Blend modes are an enum, not free strings, because `globalCompositeOperation` accepts any string silently.

## Not in this module

The vignette and colour grade, shadows, breathing, bloom and HUD canvas (plan items 1 to 3, 8, 9). They are small functions in `index.html` that need the DOM for an offscreen canvas. Character rigs (`(not published)`, planned in `tech.md`) and UI 9-slice. The terrain profile (task 47).

## Open points

- The numbers 24 px (max camera), 40 px (max bound), 0.1 s (max dt), 0.6 s (wind ease) are my choices (INVENTED). They are constants at the top of the file.
- The manifest `file` regex forces `(not published)`. Projectile, UI and character parts will need their own folders and validators.
- Whether the second and third scenes reuse the same slot names (they do in the plan) or get different ones is an art decision; the module does not care.
