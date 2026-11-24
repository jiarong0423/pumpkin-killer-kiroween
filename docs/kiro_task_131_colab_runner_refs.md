# Kiro task 131 — make the Colab runner accept an ordered list of reference images (work block B07)

Task 115 produced `colab/jobs_missing_20261115.json` (top-level keys `refs` and `jobs`; eight jobs) and `docs/colab_run_20261115.md`. Its step 7 says the checked-in runner reads ONE reference per job, but the new jobs use an ordered `refs` list (style image first, identity image second).

Read: `colab/jobs_missing_20261115.json` (the format), `colab/pumpkin_assets_job.py` (the runner code of Cell 2), `colab/layered_job.py`, `colab/cell_B_sdxl_ghost.py` (only to see style), `docs/colab_pipeline_excerpt.md`, `docs/kiro_79_style_for_colab_gpt-5.6-terra.md`, `docs/colab_run_20261115.md`. You cannot run Colab (no GPU, no network); the code is tested on a stub.

Do, saving after each:
1. Edit `colab/pumpkin_assets_job.py` so that a job may carry `refs` as a list of reference names (resolved through the top-level `refs` table of the queue file as in `jobs_missing_20261115.json`): the first reference is passed as the style image and the second as the identity image, in that order, to the Qwen-Image-Edit call (use the multi-image input form the existing code already uses for editing; if the pipeline call takes a list of images, pass the list; do not guess a new API: if the code does not show how to pass two images, write the open question in the result file and keep the one-reference path unchanged). A job with a single `ref` must behave exactly as today (byte-for-byte same call). Keep tier and variant handling unchanged.
2. Add a pure helper `resolve_refs(job, ref_table)` that returns the ordered list of file paths and raises a clear error for an unknown name, and put it in a small importable file `colab/job_refs.py` (stdlib only) that the runner imports; add `scripts/test_job_refs.py` (`unittest`): ordered list, single ref unchanged, unknown name error, all eight jobs of `colab/jobs_missing_20261115.json` resolve to names that exist in its `refs` table.
3. Update step 7 of `docs/colab_run_20261115.md` to say what changed (one or two lines).
4. Run `python3 -B scripts/test_job_refs.py` and `python3 -B -c "import ast,sys;ast.parse(open('colab/pumpkin_assets_job.py').read());print('syntax ok')"`; paste both. If a shell call is refused, say so; do not invent output.

Touch only `colab/pumpkin_assets_job.py`, `colab/job_refs.py`, `scripts/test_job_refs.py`, `docs/colab_run_20261115.md` (step 7 only) and the result file exactly named `docs/kiro_131_result_gpt-5.6-terra.md` (max 15 lines). No network, no git.
