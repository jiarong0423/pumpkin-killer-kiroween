# Design: judging fit

## Output

One document, `(not published)`, with these parts: problems to fix first, criteria table, Kiro usage map, Costume Contest fit,
3-minute video outline, Devpost skeleton, pre-submit checklist, and a list of what could not be verified.

## Method

- Read the local docs, steering, spec folder names and agent file. Check `.gitignore` and `LICENSE`.
- Run only existing project test scripts (`node scripts/test_particles.js`, `python3 -B scripts/test_mcp_stdio.py`) to confirm test counts.
- Use outside facts (judging criteria, submission rules, dates) only as given in `(not published)`.
- Where two repo files disagree, list both and do not pick a side.

## Decisions

- Evidence is a file path. A claim without a path is not made.
- Hooks and powers are marked missing. The sheet recommends one cheap hook (run the two test scripts) and does not create it, since the task did not ask for it.
- The video is ordered by the owner's brief: gameplay first, then architecture, pain point, Kiro evidence, close. The hook beat is conditional.
- Measured numbers in the skeleton are marked "re-run before publishing".

## Out of scope

Changing `index.html`, `assets/`, `scripts/`, `js/`; creating images; git operations; editing steering or README (listed as fixes, not done here).
