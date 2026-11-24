# Kiro task 85b — plan the release package as a Kiro spec, then drive it (spec-driven)

You own this release. Plan it the Kiro way: a spec first, then tasks executed one by one from that spec. Write the spec in your own words from the facts below; the earlier plan `docs/kiro_84_release_plan_claude-sonnet-5.5.md` is your input, not a script to copy. Everything you write must be true on the day you write it: use today's real date, never back-date, and do not claim work that no file or command output shows.

Read: `docs/kiro_task_85_release_delivery.md` (stages R1 to R6, fixed rules), `docs/kiro_84_release_plan_claude-sonnet-5.5.md` (sections 1 to 8), `(not published)`, and the existing spec layout `.kiro/specs/core-throw-loop/` for the file style.

Create `.kiro/specs/release-package/` with three files, in this order, saving each as soon as it is written:
1. `requirements.md` — user stories with acceptance criteria in EARS style ("WHEN ... THE SYSTEM SHALL ..."): a judge can run the project from a clean clone; the repository is public-ready (MIT, `.kiro` visible, no private data); history shows real dates and true Kiro attribution; the upload happens only after the gates pass. One requirement per fixed rule of the delivery document.
2. `design.md` — components (export tree, asset-reference check, privacy gate, history builder, root documents, clean-checkout script, upload step), data flow from `pumpkin-killer` to `(not published)` to the new remote, the gate order, failure handling, and what is verified by which command.
3. `tasks.md` — a checklist: T1 export tree (stage R1), T2 privacy gate (R2), T3 history build (R3), T4 root documents (R4), T5 clean checkout (R5), T6 upload (R6). Each task lists its files, its verify command and the requirement it satisfies. Tick a box only when a command output you saw proves it. Status now: T1 is in progress (task 85a started it; check which files under `scripts/release/` and `scripts/test_export_tree.py`, `scripts/test_check_asset_refs.py` really exist and mark only those).

Then write `(not published)` (max 40 lines): the three paths, and what you did not run. Do not start any task of the checklist in this run, and do not touch GitHub, git remotes, or files outside `.kiro/specs/release-package/` and the result file. No network.
