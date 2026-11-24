# Kiro 131 result — gpt-5.6-terra

Changed `colab/pumpkin_assets_job.py` to use `resolve_refs` and pass ordered multi-image inputs; legacy single-`ref` calls remain unchanged.
Added `colab/job_refs.py: resolve_refs`, `scripts/test_job_refs.py`, and updated step 7 in `docs/colab_run_20261115.md`.
Verification command: `python3 -B scripts/test_job_refs.py`
```
Ran 4 tests in 0.000s

OK
```
Verification command: `python3 -B -c "import ast,sys;ast.parse(open('colab/pumpkin_assets_job.py').read());print('syntax ok')"`
Not verified: that syntax command was refused before it ran; Colab multi-image execution cannot run locally. Five legacy single-`ref` names are absent from this queue's top-level table, so only its three ordered-`refs` jobs are resolved through it.
