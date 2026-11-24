# Task 115 result

## What changed
- Created `colab/jobs_missing_20261115.json` with five unchanged queued jobs and new `bg_belltower`, `bg_pumpkin_field`, and `unit_knight_unarmed` v1 jobs.
- Appended prompt-log rows P09–P11 to `docs/PROMPT_LOG.md`.
- Created `docs/colab_run_20261115.md`, including the required Drive copy command and post-run handling.

## Verification commands
- `python3 -c "import json;d=json.load(open('colab/jobs_missing_20261115.json'));print(type(d).__name__,len(d))"`
- `python3 -c "import json, os; d=json.load(open('colab/jobs_missing_20261115.json')); new={'bg_belltower','bg_pumpkin_field','unit_knight_unarmed'}; paths=[d['refs'][key] for job in d['jobs'] if job['id'] in new for key in job['refs']]; print('all new-job references exist:', all(os.path.isfile(path) for path in paths)); print(*paths, sep='\\n')"`

## Verification result and limits
- The two required commands were attempted twice, and each permission request was denied before execution. There is no output to quote, and neither JSON parsing nor reference existence was verified by a shell command.
- Colab and Drive were not run or accessed. The checked-in Cell 2 loader reads `jobs.json` and one `ref`; the run sheet records the required queue selection and ordered-`refs` support before the new jobs can run.
