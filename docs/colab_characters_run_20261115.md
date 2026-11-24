# Colab character-art run sheet, 2026-11-15

Queue: `colab/jobs_characters_20261115.json`. Eight Q3 jobs, one v1 picture each. Nothing was run when this was written.

1. Copy the queue to Drive without touching `jobs.json`:
   `PK_DRIVE_INPUTS_DIR=<folder> bash scripts/push_queue_to_drive.sh colab/jobs_characters_20261115.json jobs_queue_characters.json`
2. Put the seven reference files in the inputs folder, under the same paths: `assets/poses/skeleton_idle1.png`, `assets/units/unit_reaper_idle.png`, `assets/poses/necro_idle.png`, `assets/poses/necro_windup.png`, `assets/fx/sprites/fx_ghostfire_purple.png`, `assets/portraits/bride_front.png`, `assets/portraits/hunchback_front.png`.
3. Run Cell 1, then Cell 2 with `jobs_queue_characters.json` as input, `TIERS = ["Q3"]`, `VARIANTS = 1` (same as `docs/colab_run_20261115.md`).
4. Expect 8 pictures named `<job-id>_v1_...png`. The earlier sheet gave about 7 minutes each, so plan about 56 minutes. I have not measured it.
5. Download the pictures. Keep only the ones that pass the checks below. Rerun a failed job with another seed, and do not edit a picture by code.

What to check on every picture: flat magenta background without noise; thick near-black outline with a thin orange rim; flat cel shading; no text; one figure; no magenta or pink inside the figure.

- `necro_front`: head and shoulders only; same hood, skull and purple flame eyes as the unit picture; no hands, flask or body.
- `necro_ult_point`: faces LEFT; one index finger forward and nothing burning in that hand; exactly three separate purple fires behind; same size as `necro_windup`; no pink sparkle stars.
- `necro_idle2`: nearly the same as `necro_idle`; same size and hand; only a small flame and hem change; not a copy.
- `necro_charge2`: faces LEFT; flame between the idle and the wind-up size; same hand; not a copy of either.
- `bride_front`, `hunchback_front`: head and shoulders only; black oval eyes, rose crown and veil kept; green skin, tusks and brows kept; no axe, hands or body.
- `hero_eighth_concept_a`, `_b`: do not judge for polish. Each is one idea; the owner reads the attack in the prompt and chooses. Check that the silhouette is clearly new (A: tall, wide hat; B: low, exactly eight legs).

Known issue: `necro_idle` faces right (three-quarter) but `necro_windup` and the rule in `docs/pose_spec.md` face LEFT. The new frames follow the wind-up. Tell the main line before the poses go into the page.

After approval: pose and portrait files need reviewed mappings first (see item 14 of `docs/colab_run_20261115.md`). Then run `python3 -B scripts/check_pose_set.py` and `scripts/pose_similarity.py`.
