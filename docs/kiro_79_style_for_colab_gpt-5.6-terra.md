# Kiro 79 — style conditioning for Qwen-Image-Edit

## Evidence and diagnosis

Reviewed: `docs/colab_pipeline_excerpt.md`, `docs/game_style_brief.md`,
`docs/pose_spec.md`, `docs/art_style_guide.md`, the failed ghost jobs and
`(not published)`; the current ghost, pose, coffin,
background, weapon, portrait, UI, and ghost-fire images named below.
`docs/kiro_69_art_optimization.md` could not open: it is absent from this
workspace. `(not published)` could not open: no file matches that glob.

The five failed jobs give Qwen a HUD bar (`ref: "bar"`), then explicitly say to
ignore its layout. That leaves no visual evidence of either the ghost or the
project's line treatment. “The SAME ghost” cannot preserve an identity that was
never supplied. Their style field also asks for “painterly” art and soft luminous
edges. That conflicts with the established flat three-tone cel shading, near-black
contour, and orange outer contour. The text has no face-lock rule, no anti-gradient
rule, and no instruction that a glow must sit outside a solid outlined form.

The failed idle image shows the predictable result: a broad cyan bloom, smooth
soft contours, and a simplified unrelated face. In contrast,
`assets/env/ghost_lantern.png`, `assets/poses/skeleton_idle1.png`, and
`assets/poses/bat_idle1.png` show the desired readable silhouette, dark contour,
cel-separated planes, and warm orange external rim. Text must reinforce those
pictures, not replace them.

## Reusable style blocks

Use one block in each job's `style` field. Put subject and action only in
`prompt`; do not repeat the whole style in both fields.

**English (under 90 words)**

> Dark-fantasy 2D cartoon game art. Thick clean near-black contour, then a thin warm-orange outer glow. Flat three-tone cel shading and soft highlights; no airbrush or realistic material rendering. Faces, if present: chibi, large expressive eyes, simple mouth, stable proportions; change only expression. Isolated sprite: solid #FF00FF background, no ground or cast shadow, 10–12% margin. Do not use photorealism, 3D/plastic, painterly gradients, thin linework, text, watermarks, extra figures, or magenta/pink inside the subject.

**中文對照（少於 90 詞）**

> 暗黑奇幻 2D 卡通遊戲美術。粗淨近黑主輪廓，外加細暖橘色外緣光。平面三階賽璐珞陰影與柔和高光，不用噴槍或寫實材質。若有人臉：Q版、大而有表情的眼睛、簡單嘴形、比例固定，只改表情。獨立精靈圖：純 #FF00FF 背景，無地面或投影，四周留 10–12% 空白。不要照片感、3D 或塑膠、繪畫漸層、細線、文字、水印、額外角色，或主體內洋紅／粉色。

Use this `negative` default unless a job needs a narrower addition:

```text
realistic, photo, 3D render, plastic shine, painterly, airbrushed gradient,
thin line art, soft outline, text, letters, watermark, ground, cast shadow,
extra character, duplicate subject, magenta or pink inside the subject
```

## Reference strategy

Stage each named project file in Drive and add a descriptive key to
`spec["refs"]`. Pass at most two references. Their list order is deliberate:
**style first, identity second**. The prompt must call them “first reference” and
“second reference”, because the pipeline supplies images without role metadata.
If one approved picture establishes both roles, pass it once rather than giving
Qwen duplicate evidence.

| Job kind | `refs` order: exact source files | Use and reason |
|---|---|---|
| Ghost idle / wind faces | `assets/poses/skeleton_idle1.png`, `assets/env/ghost_lantern.png` | The first locks the universal contour/cel/orange-rim language. The second is the only existing friendly ghost identity; prompt tells Qwen to keep its upper ghost only and omit lantern, rope, and chain. For later ghost frames, replace the second file with the owner-selected idle output. |
| Gust / wind-only pictures | `assets/poses/skeleton_idle1.png`, `assets/fx/sprites/fx_ghostfire.png` | The pose gives hard contour and orange rim; ghost-fire supplies the cool cyan emission family. A gust has no character identity, so the second image is colour/effect identity, not a shape to copy. |
| Chain and other props | `assets/poses/skeleton_idle1.png`, `assets/env/ghost_lantern.png` | Use the lantern image only for its dark iron, rope/chain, and cyan-lit material cues. State explicitly that the ghost and lantern must not appear. For an existing weapon, instead use its exact item as identity, for example `assets/weapons/shuriken.png` or `assets/weapons/small_shield.png`. |
| Coffin blue/purple twins | `assets/poses/skeleton_idle1.png`, `assets/env/platform_coffin_blue.png` for blue; first plus `assets/env/platform_coffin_purple.png` for purple | The first holds the shared cartoon line. The second preserves each coffin's silhouette, wood/iron construction, and its team colour without blending both variants into one object. `assets/ui/shield_slab_blue.png` is an acceptable identity only for a thin UI slab, not a platform. |
| Backgrounds | `(not published)`, `assets/env/bg_graveyard.png` | The concept establishes the full game hierarchy and palette; the graveyard image gives the current scene rendering. Prompt the first as style and the second as a composition/scene reference. For a new scene with no intended variation, use only the concept to avoid cloning the graveyard. |
| Portraits | `assets/poses/skeleton_idle1.png`, the class identity: `assets/portraits/skeleton_front.png`, `assets/portraits/wizard_front.png`, `assets/portraits/knight_front.png`, `assets/portraits/bride_front.png`, `assets/portraits/hunchback_front.png`, or `assets/portraits/reaper_front.png` | The portrait is the identity source because it already has the desired crop. For a missing portrait, use the corresponding `(not published)` as identity. Use one class per request. |
| Poses | the class's `(not published)` alone, or `assets/poses/skeleton_idle1.png` first plus that class idle second | The approved idle carries face, outfit, hand, scale, baseline, and style. For skeleton, pass it once. Keep `docs/pose_spec.md` wording in `prompt`; an art-style ref cannot replace direction, hand, and empty-hand rules. |

Suggested calibration keys: `style_skeleton_idle1` ->
`assets/poses/skeleton_idle1.png`; `identity_ghost_lantern` ->
`assets/env/ghost_lantern.png`; `identity_skeleton_idle1` -> the same skeleton
file; and, after chain frame 1 is selected, `identity_calib_chain_frame1` -> the
selected output copied to Drive inputs as `ref_calib_chain_frame1.png`.

## Job format and notebook change

Keep `ref` for backward compatibility. Add `refs` as an ordered list of keys.
The calibration JSON follows this format. Defaults are a job-level `style` using
the English block and the shared `negative` above.

Replace the current one-reference load and `image=[ref]` call in the job loop with:

```python
keys = job.get("refs") or [job["ref"]]
refs = [fit(Image.open(f"{IN_DIR}/{spec['refs'][key]}")) for key in keys]
res = pipe(image=refs,
           prompt=f"{job['prompt']} {job.get('style', spec['style'])}",
           negative_prompt=job.get("negative", " "),
           num_inference_steps=STEPS, true_cfg_scale=TRUE_CFG,
           generator=seeded).images[0]
```

This preserves old jobs. Run `calib_chain_frame1` first, select one result without
editing it, stage that selected file under `identity_calib_chain_frame1`, then run
`calib_chain_frame2`. This makes frame 2 a real image edit of frame 1 rather than
a new unconnected chain.

## Calibration batch and measurable acceptance

`colab/jobs_style_calib_20261110.json` contains six jobs: three controlled versions
of the same idle ghost, one skeleton pose that exercises identity metrics, and a
two-frame chain continuity test. It requests outputs; it does not assert that any
output exists.

For each output, first run the existing magenta key/crop check by calling
`key_magenta_items.key_and_crop`; it must not raise “nothing left after keying”.
Use `scripts/pose_similarity.py`'s `compare()` directly for the named pairs; it
works on magenta-keyed source images as well as RGBA images. The checks below make
the comparison purpose explicit.

| Job | Acceptance check and response when it fails |
|---|---|
| `calib_ghost_a_text_control` | Key/crop must succeed. This is a negative control, never a production candidate. Record its palette/scale values against `assets/poses/skeleton_idle1.png` and `assets/env/ghost_lantern.png`; it establishes the text-only baseline. |
| `calib_ghost_b_style_only` | Key/crop must succeed. Its palette similarity to `assets/poses/skeleton_idle1.png` must be at least the control's, and it must visibly have a near-black contour, orange rim, and three planes. If not, shorten the subject prompt and retain the explicit style block. |
| `calib_ghost_c_style_identity` | Meet B's check and contain no lantern, rope, or chain. Compare its palette/scale with `assets/env/ghost_lantern.png`; record the result beside A/B for the owner. If a prop leaks in, drop the lantern identity and use the selected B output as the next identity reference. |
| `calib_pose_skeleton_charge1` | No `FACE`, `PALETTE`, `SCALE`, `DIRECTION?`, or `COPY` from `compare(skeleton_idle1, output, "charge1")`: palette >= 0.55, scale 0.80–1.25, face similarity >= 0.50 or ORB >= 10, and pose difference >= 0.06. After selection and placement in `assets/poses/`, `check_pose_set.py --strict` must also pass: 1024-square RGBA, transparency, baseline rows 990–1010, and no height over 112% of idle. FACE failure needs a stronger face lock; PALETTE failure needs fewer competing refs; SCALE/direction failure needs the baseline/LEFT rule; COPY failure needs a concrete action. |
| `calib_chain_frame1` | Key/crop must succeed. Count exactly five links with one consistent dark-iron material, no ghost/lantern/rope. Record palette and scale against frame 2 later. On a count/material failure, make “exactly five” and “one material” the first prompt clause. |
| `calib_chain_frame2` | Key/crop must succeed. `compare(frame1, frame2)` must give palette >= 0.55, scale 0.80–1.25, and pose difference >= 0.06. It must retain five links and no extra prop. If palette/scale fails, retry with frame 1 as the only identity reference. If it is a copy, name the displaced links and direction; if it changes count/material, add “EXACT same chain, no new links/material”. |

The ghost comparison is a controlled ranking, not a false face comparison between
different ghost expressions. If A outperforms both B and C on the stated visual
criteria, the style block is not discriminating enough. Keep B/C's hard style
language, reduce the subject wording, and rerun the comparison.
