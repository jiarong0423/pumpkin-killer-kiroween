# Kiro task 137 (IDE) — character picture gaps for every hero, as one Colab run script (work block B07, B21)

Owner request (2026-11-15): list the missing character pictures and turn them into a script for Colab, together with the scene backgrounds (CLI task 136 writes `colab/jobs_scenes_20261115.json`; the Apple Hag jobs are in `colab/jobs_apple_hag_20261115.json` from task 134; the IDE's `colab/jobs_characters_20261115.json` already exists).

Read: `docs/pose_spec.md` (eight frames: idle1, idle2, charge1, charge2, charge3, release, empty, hit), `assets/poses/` and `assets/units/` (file names only), `docs/remaining_heroes_plan_20261115.md`, `docs/asset_inventory_drive_20261115.md`, `colab/jobs_characters_20261115.json`, `colab/jobs_apple_hag_20261115.json`, `docs/PROMPT_LOG.md`, `docs/colab_run_20261115.md`, and the `HERO_PROFILES` / `POSE_SETS` blocks of `index.html` (read only).

Do:
1. Write `docs/character_gap_matrix_20261115.md`: one row per hero (skeleton, wizard, bat, knight, necromancer `reaper`, ghost bride, bell-tower hunchback, Apple Hag `hag`), one column per frame of the pose spec plus portrait, projectile, ultimate effect and status icon; mark each cell present (file path), missing, or job exists (job id and file). Facts only from `ls`.
2. For every cell that is missing and has no job yet, add the job to `colab/jobs_characters_20261115.json` (same format and rules as the existing jobs there; do not duplicate jobs that exist in the hag or scenes files).
3. Write `colab/run_all_20261115.md` (max 25 lines): one run order across the three job files (`jobs_scenes_20261115.json`, `jobs_apple_hag_20261115.json`, `jobs_characters_20261115.json`), stage by stage, total picture count and time at about 7 minutes each, which stage needs the owner to pick a best picture first, and the single command or notebook cell line that loads each file.
4. Validate each job file with `python3 -c "import json;..."` (job count) and `ls` every reference path; paste the output. Do not invent output if a command is refused.

Touch only `docs/character_gap_matrix_20261115.md`, `colab/jobs_characters_20261115.json` (new jobs only), `colab/run_all_20261115.md` and `docs/kiro_137_result_gpt-5.6-terra.md` (max 12 lines). Do not edit `index.html`. No network, no git, no Drive, no Colab.
