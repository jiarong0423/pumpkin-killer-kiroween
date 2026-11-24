# Kiro 84: release plan for the fresh public repository (claude-sonnet-5.5)

Plan only. Nothing here was run: this session had no shell and no git, so every size, count and command below is either read from a file (named) or marked UNVERIFIED. I did not push, create a repository, or edit any file except this one. I did not print any email address, username or secret value, and no hit list in this plan contains one.

Read: kiro_task_84.md, kiro_queue_20261110.md, (not published), KIRO_LEDGER.md, kiro_evidence_20261110.md, KIRO_IMPACT_INVENTORY_20261110.md, docs/official/* (both), docs/kiro_evidence/README.md, README.md, .gitignore, the directory listings of the repo root, docs/, .kiro/, colab/, assets/, and the first six lines of `.git/logs/HEAD`.

## 0. Four findings that change the plan
1. **The local reflog shows a personal (non-noreply) identity as COMMITTER** on the first six commits. The main line's fact says all 199 AUTHORS are the noreply address. Author and committer are separate fields. Check both (`%ae` and `%ce`, `%an` and `%cn`). The new repository avoids the question by setting both identities explicitly on every commit it creates (section 3).
2. **The first commit hash in the reflog is not the one in the brief.** The reflog lists 9b30d03 as `commit (initial)`; the brief and COMPLIANCE_CHECK say 6eaaa6e. One of them is stale, most likely because history was rewritten once (for example to change authors). Scripts must find the first commit with `git rev-list --max-parents=0 HEAD`, never a hard-coded hash. Its date is 1793386918 +0800, which is 2026-10-31 03:02 Taiwan time. In Pacific time that is about 12:00 on Oct 30, about three hours after the submission period opened (Oct 30 09:00 PT). The margin is small, so author dates must survive untouched.
3. **`*.log` is in .gitignore.** The 14 `kiro_route_kiro_task_*.log` files in the repo root, which are the only raw proof that Kiro CLI ran, are therefore untracked and would never reach a fresh export. `(not published)` and `(not published)` are also ignored. Route logs must be copied (renamed `.txt`) into `docs/kiro_evidence/raw/route_logs/` after the privacy gate (queue item A7). `(not published)` stays out (section 1, assets note).
4. **README.md overclaims.** It says up to four humans face four agents and that every player acts through the MCP server. tech.md says the browser game does not call the MCP server and the prototype is 1 vs 1. The new README must describe only what runs on the day of the push.

## 1. Export manifest
Rule for the table: INCLUDE = copy as is after the gate; TRANSFORM = copy with a listed edit, recorded in `docs/kiro_evidence/EXPORT_NOTES.md` (what changed and why, no private values); EXCLUDE = not copied. Sizes: only three totals are known (about 100 MB tracked, assets about 121 MB on disk, docs about 86 MB on disk with git-ignored (not published) inside it). Everything else is UNVERIFIED. One command fills the column: `du -sk .kiro assets colab css docs js scripts shared index.html LICENSE README.md .claude | sort -n`, then `du -sk assets/* docs/* | sort -n | tail -25`.

| Path | Decision | Reason | Size |
|---|---|---|---|
| `LICENSE` | INCLUDE | MIT, must show in About | tiny |
| `README.md` | TRANSFORM (rewrite) | finding 4; section 4 | tiny |
| `JUDGES.md`, `CREDITS.md` | NEW | section 4 | tiny |
| `.gitignore` | TRANSFORM | keep node_modules, .env, .DS_Store, pycache, build; drop `(not published)` and `(not published)` lines if the folders are not exported; never any `.kiro` line; no blanket `*.log` (see finding 3) | tiny |
| `index.html`, `css/`, `js/`, `shared/` | INCLUDE | the game; page must run from the repo alone | UNVERIFIED |
| `.kiro/` (agents, hooks, settings, specs, steering) | INCLUDE | rules require it at the root; 73 tracked files per COMPLIANCE_CHECK. TRANSFORM only `steering/kiro_assignment.md`: its references to `(not published)` and `(not published)` point at excluded files. Replace with "(not published)". Only that file; it is not part of the real first commit | small |
| `(not published)` | INCLUDE after gate | shows the Claude Code / Kiro split honestly | tiny |
| `(not published)`, `(not published)`, `(not published)` | EXCLUDE | tool state, unknown content | UNVERIFIED |
| `scripts/` | INCLUDE (tests, engine, MCP server, tools) | tests must pass from a clean checkout. Review `push_queue_to_drive.sh` (may name a Drive remote or folder) and `kiro_models.json` (credit-multiplier notes) before including; TRANSFORM if they hit the gate | UNVERIFIED |
| `colab/*.json`, `colab/*.py` | INCLUDE | prompt-engineering evidence (jobs files, cells) | small |
| `(not published)`, `(not published)`, `(not published)` | EXCLUDE until listed | contents unknown: may hold third-party reference pictures or private files. Run `unzip -l` (names only). INCLUDE only items that are our own art and named in PROMPT_LOG.md | UNVERIFIED |
| `assets/` referenced by the page | INCLUDE (mandatory) | load gate needs all of them; script `check_asset_refs.py` (section 5) lists them | most of 121 MB |
| `assets/` not referenced | EXCLUDE unless a kept bake script or PROMPT_LOG row names it as input | spares size; `*_raw.png` 1024 px sources are kept only if `bake_*.py` reads them | UNVERIFIED |
| `assets/audio/` incl. `_licenses`, `CREDITS.md` | INCLUDE | CC0 licence files must travel with the audio | UNVERIFIED |
| `assets/fonts/` incl. OFL licence files, README | INCLUDE after the E1 pass | files are modified and uncommitted today and not reviewed (queue wave E) | about 1 MB target |
| Art provenance | GATE | every top-level `assets/*` folder needs a line in `docs/ASSET_PROVENANCE.md`. `(not published)` and `(not published)` suggest some art or text came from tools other than Qwen. If any shipped picture came from them, the README disclosure must say so or the picture goes. Owner question 2 | n/a |
| `docs/` evidence | INCLUDE | `kiro_task_NN.md` briefs, `kiro_NN_*` results, `kiro_evidence/`, `kiro_evidence_20261110.md`, `KIRO_LEDGER.md`, `kiro_verified.json`, `KIRO_IMPACT_INVENTORY_20261110.md`, `PROMPT_LOG.md`, `ASSET_PROVENANCE.md`, `ROLES.md`, `daily/`, `PROGRESS_TABLE.md`. Briefs and results with an absolute path TRANSFORM it to `<project root>` (this brief, kiro_task_84.md, is one) | small (text) |
| `docs/` design and rules | INCLUDE | `game_mode.md`, `mcp_agent_protocol.md`, `architecture.*`, `workflow.*`, `overview/*.svg` and `.mmd`, the Kiro design docs (airdrop, dock, roster, wind, sound, ultimates, richness, ui_reskin, class_stats*), `art_style_guide.md`, `game_style_brief.md`, `plan_v1.md`, `codex_asset_prompts.md`, balance reports | small |
| `docs/kiro_queue_20261110.md` | TRANSFORM | delete the one sentence that states the remaining credits balance | tiny |
| `docs/owner_decisions_20261110_agents_headless.md` | INCLUDE after gate | design decisions the steering points to | tiny |
| `(not published)`, `(not published)`, `(not published)` | EXCLUDE | working notes; (not published) holds a credits balance and planning chatter | small |
| `(not published)`, `(not published)`, `(not published)`, `(not published)` | EXCLUDE | working notes; the first is a running log of the owner's remarks (risk of private content); `agent_memory_paths.md` has local paths and the AWS warning | small |
| `(not published)` | EXCLUDE | decision in section 4 | tiny |
| `(not published)`, `docs/playtest/*.md` | EXCLUDE frames, INCLUDE `LOG.md`, `RECORD.md`, `kiro_review.md` after gate | frames are many screenshots that may show a desktop | UNVERIFIED |
| `(not published)` (screen recording `.mov`, `concept_mockup.png`) | EXCLUDE | the recording is large and may show the owner's screen; the mockup has no provenance line | UNVERIFIED |
| `docs/gifs/` (28 gifs) | EXCLUDE all but `all_heroes_idle_quad.gif` and `svg_scene_gameplay_showcase.gif` | README can use two; the rest are working previews | UNVERIFIED |
| `(not published)` screenshots, `(not published)`, `docs/*.html` review pages (`attacks_only`, `character_gallery`, `dock_preview`, `fonts_sample`, `gameplay_mockup`) | EXCLUDE | large or working pages; SVG twins stay | UNVERIFIED |
| `(not published)`, `(not published)` | EXCLUDE | third-party tool traces; see Art provenance row | small |
| `(not published)` | EXCLUDE | refers to a third party game; low value for judges | tiny |
| `(not published)`, `match12*.json`, `playtest_data_*.json` | EXCLUDE; keep the `.md` reports | raw data; reports are the evidence | small |
| `(not published)` | EXCLUDE (git-ignored) | gate asserts it is absent | large |
| `kiro_route_kiro_task_*.log` (root) | TRANSFORM | gate, rename `.txt`, move to `docs/kiro_evidence/raw/route_logs/` | small |
| `.DS_Store`, `(not published)`, `(not published)`, `__pycache__/` | EXCLUDE | noise | n/a |
| 66 `kiro/*` branches, 67 worktrees | EXCLUDE | local; their useful content reaches the new repo only through the milestone snapshots. Worktree-only output (see kiro_evidence_20261110.md section 3) is NOT published unless merged first | n/a |

Do not ship a file the ledger calls a Kiro result when its content was never checked. Keep it, but its ledger row says "not checked".

## 2. Privacy gate
Run on the exported tree, then on every milestone commit of the rebuilt repo. **Rule: read hits as file and line only.** Every command below ends in `cut -d: -f1,2` or `-l`, so the matched text never reaches the screen. Nobody opens a flagged line to look at the value: the fix is to change or delete the line, then re-run. BLOCK = must be zero. REVIEW = a human decides per file:line and records it in an allowlist (`path|sha1-of-line`, so an edited line must be approved again).

Setup: `cd <export dir>; G="grep -rInE --exclude-dir=.git"`. Private terms (owner name, handles, NDA company and product names, the owner's other projects, family) go in a file OUTSIDE the tree: `export PK_TERMS=~/pk_privacy_terms.txt`, one term per line. It never enters the repo, and this plan does not contain its content.

| id | check (command) | class | a hit means / fix |
|---|---|---|---|
| P1 | `$G '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}' . \| grep -vE 'noreply\.github\.com\|@[0-9]x\.' \| cut -d: -f1,2` | BLOCK | an email address; delete the line or replace with `<email>`. Facts say two tracked files have one |
| P2 | `$G '<local path>\|/home/[a-z][^/ ]*/\|[A-Z]:\\\\Users' . \| cut -d: -f1,2` | BLOCK | absolute local path; replace with a relative path or `<project root>`. Facts say four tracked files; this brief is one |
| P3 | `$G '(AKIA[0-9A-Z]{16}\|ghp_[A-Za-z0-9]{20,}\|hf_[A-Za-z0-9]{20,}\|sk-[A-Za-z0-9]{20,}\|BEGIN [A-Z ]*PRIVATE KEY)' . \| cut -d: -f1,2` | BLOCK | a secret-shaped value. Remove it, then tell the owner to rotate it even if the repo was never public |
| P4 | `$G -i '(secret\|token\|passw(or)?d\|api[_-]?key)[A-Za-z_]*["'"'"' ]*[:=]["'"'"' ]*[A-Za-z0-9/+_-]{16,}' . \| cut -d: -f1,2` | BLOCK | a name followed by a long assigned string. Change the line to read an environment variable |
| P5 | `$G -il '(secret\|token\|passw(or)?d\|api[_-]?key)' . ` | REVIEW | name only (facts: 7 files). Fine if it is a variable name or a prose mention. Never open to read a value |
| P6 | `find . \( -name '.env*' -o -name '*.pem' -o -name '*.key' -o -name 'id_rsa*' -o -name '.netrc' -o -name '*.p12' -o -name '.DS_Store' \) -print` | BLOCK | credential or noise file in the tree; delete |
| P7 | `[ -s "$PK_TERMS" ] && grep -rIinFf "$PK_TERMS" --exclude-dir=.git . \| cut -d: -f1,2` and the same on filenames: `find . \| grep -iFf "$PK_TERMS"` | BLOCK | a private name or an NDA third-party name; rewrite or delete. The gate fails if the terms file is missing or empty (so it cannot pass by accident) |
| P8 | `$G -i '(credits? (left\|remaining\|balance)\|balance\|NT\$\|剩餘\|餘額\|已使用\|運算元\|compute units?)' . \| cut -d: -f1,2` | REVIEW | money or credit balance. "4,000 credits" from the public rules is fine; the owner's own balance is not. Known hits: (not published) (excluded), kiro_queue (transformed) |
| P9 | `$G '(drive\.google\.com\|/content/drive\|MyDrive\|rclone\|folder[_-]?id)' colab scripts docs .kiro \| cut -d: -f1,2` | REVIEW | Drive path or folder id in Colab jobs and scripts; replace with a placeholder such as `<DRIVE_DIR>` |
| P10 | `python3 scripts/release/privacy_gate.py --tree . --check cjk` lists files with Chinese characters outside `index.html`, `js/`, `css/`, `assets/fonts/charset.txt` | REVIEW | the rules want English. The Chinese notes are the main line's and the owner's; translate the file or exclude it |
| P11 | images and archives: `python3 scripts/release/privacy_gate.py --check png-text` reads PNG text chunks and EXIF (prompts, workflow JSON, local paths); `unzip -l` on every `.zip` (names only) | BLOCK | metadata with a path or email; strip with Pillow `save()` without `pnginfo` (this edits the file bytes: allowed for metadata only, never for art) |
| P12 | size: `find . -type f -size +20M` | BLOCK | GitHub warns at 50 MB and refuses 100 MB; no tracked file is over 20 MB today |
| P13 | dangling links: `python3 scripts/release/privacy_gate.py --check links` finds markdown links and backticked `(not published)` paths to files absent from the tree | BLOCK | steering and docs point at excluded notes; edit the text, do not restore the note |
| P14 | placeholders: `$G '(HOSTED_URL\|TODO_OWNER\|<PLACEHOLDER>)' README.md JUDGES.md CREDITS.md \| cut -d: -f1,2` | BLOCK on release day | the hosted URL must be real before the push to public |
| P15 | history (rebuilt repo): `git log --all --format='%an|%ae|%cn|%ce' \| sort -u` shows exactly one line, the noreply identity in all four fields; `git log --all --format=%B \| grep -ci '^co-authored-by'` prints 0; `git log --all --format='%an %ae %cn %ce %s%n%b' \| grep -ciFf "$PK_TERMS"` prints 0 | BLOCK | wrong identity or a trailer; rebuild |
| P16 | tracked-path rules: `git check-ignore -q .kiro && echo BAD`; `git ls-files .kiro \| wc -l` is 73 or more; `git ls-files (not published) \| wc -l` is 0 | BLOCK | `.kiro` ignored or leaked folder |

P1 to P4 and P6 to P7 run on the whole history too: `for c in $(git rev-list --all); do git grep -IlE "<pattern>" $c; done` prints commit:file only, never the line.

## 3. History strategy
| | (a) one commit | (b) 15 to 25 curated milestone commits | (c) full history, git filter-repo |
|---|---|---|---|
| Judges | simplest; no timeline; "new after Oct 30" is only a claim; every Kiro claim is a README sentence | readable timeline with real dates; Kiro task visible per commit | most detail (199 commits; 69 mention Kiro); noisy |
| Privacy | best: one tree, one identity | good: each snapshot passes the same gate; messages are written fresh | worst: every old blob and every message needs scrubbing; the old HANDOFF files with a credits balance, paths and emails sit in old blobs; one missed blob is public forever |
| Honesty risk | low | medium: wording can overclaim, so it needs the validator below | low for dates, high for leaks |
| Kiro evidence kept | files only (`.kiro`, ledger, logs) | files plus per-commit `Kiro-Task` trailers and true dates | files plus the original commit mentions |
| Cost | minutes | script plus about a day of review | a day or more, and a re-scan of all blobs |
| Owner's earlier rule | fits "fresh repo" | fits | does not fit (it carries the old history) |

**Recommendation: (b).** It keeps the real first day (licence, steering, first spec) and the real dates, and every commit message is new text that I can check against the ledger. Fallback if the build is not green by Nov 29: (a), with a dated "history" table in JUDGES.md that cites the ledger. Do not choose (c).

**Method for (b): snapshots, not slices.** Each milestone is the real source tree at a real end commit, passed through the same manifest rules. This avoids inventing a state that never existed. Author and committer date = the real author date of the end commit; author and committer identity = the noreply identity set explicitly (`GIT_AUTHOR_*`, `GIT_COMMITTER_*`, `--no-gpg-sign`, `-c core.hooksPath=/dev/null`). Order follows `git rev-list --first-parent --reverse`; an end commit that is not later than the previous one is an error.

Milestone file `(not published)`, tab separated: `id, end_rev, subject, kiro_tasks, kiro_part, mainline_part, evidence_level`. Evidence level: **V** = the task is in `docs/kiro_verified.json` as verified; **C** = a real commit message names Kiro and the brief (for example c8f18c1 "Kiro CLI, brief docs/kiro_task_06.md"); **L** = the ledger lists a brief and a log only. Only V and C may say "Kiro wrote". L may say "brief written; output not verified". Ledger status other than `ok` (tasks 62, 65, 72 and 83 as printed today) never gets a trailer that claims output; 83's file exists although the router logged `failed`, so its row says that.

Commit message shape:
```
<subject>

Kiro part: <what, with file names>.
Main line (Claude Code) part: <what, with file names>.
Kiro-Task: 06 (brief docs/kiro_task_06.md; evidence level C)
Kiro-Task: 07 (...)
```
No `Co-Authored-By`. A milestone with no Kiro work has no trailer and says "Main line (Claude Code) only."

Script `(not published) --source . --milestones (not published) --manifest scripts/release/export_manifest.json --out ../pk-release [--dry-run (default)] [--apply]`:
1. Dry run (default, writes nothing): for each milestone print end sha, date, file count, size, gate result P1 to P7 and P12 on that snapshot, and trailer validation. Exit 1 on any BLOCK.
2. `validate_trailers.py` checks each `Kiro-Task: NN` against the KIRO_LEDGER.md row and kiro_verified.json, and that every file named in "Kiro part" appears in the ledger, in KIRO_IMPACT_INVENTORY_20261110.md or in the real end commit's diff.
3. `--apply`: refuses a non-empty `--out`, runs `git init`, and per milestone: `git archive <end_rev>` into a temp dir, filter by manifest, `git add -A`, commit. It adds no remote and never pushes.
4. After the last commit: assert the new commit 1 tree hash equals the real first commit's tree hash (`git rev-parse <real1>^{tree}` against `git rev-parse <new1>^{tree}`). Equal means it is exactly the real first commit's content. If a gate fix had to change a file, the script stops and prints the file; the exception is written into EXPORT_NOTES.md, never hidden.

### Draft milestone list (22). Boundaries are UNVERIFIED: the main line fixes `end_rev` from `git log --reverse --format='%h %ad %s' --date=short`
| # | Milestone (real anchor) | Kiro part (trailer) | Main line (Claude Code) part |
|---|---|---|---|
| 1 | Initial skeleton: MIT licence, Kiro steering, core-throw-loop spec (real first commit, 2026-10-31) | steering and spec files are in Kiro format; who typed them is UNVERIFIED, no trailer until the owner answers (question 1) | the commit itself |
| 2 | Fairness principle in steering and spec (real second commit, 10 minutes later) | same as 1 | same |
| 3 | Art pipeline v0: sprite baking, placeholder units, team colours, environment assets (the next four real commits) | none | all (scripts, assets) |
| 4 | Shared constants and engine (task 01; constants.json; mcp_game_server.py base) | Kiro-Task 01 (level to be set) | index.html throw loop, physics |
| 5 | Standard MCP server (task 07; merge of kiro/mcp-standard) | Kiro-Task 07 | wiring, docs |
| 6 | Particle system with property tests (task 06; c8f18c1, merge 6d4101a) | Kiro-Task 06, level C | wiring in index.html |
| 7 | Asset candidates, object inventory, prompts (tasks 03, 15, 26) | Kiro-Task 03, 15, 26 | Colab runs, picture keying |
| 8 | Bilingual mapping module (task 08) | Kiro-Task 08 (module only; not wired; its test is red today) | none |
| 9 | Playtest, depth and design proposals (tasks 12, 13, 17, 18) | docs | playtest runs |
| 10 | Sound module and CC0 sources (task 20; c409781, merge 45d0b87; tasks 22, 23, 24, 30) | Kiro-Task 20, 22, 23, 24, 30 | downloads, licence hashes, extensions |
| 11 | Wind design and wind visuals (task 25; 7dcfc9c) | Kiro-Task 25 | wind in index.html |
| 12 | Bottom dock design and CSS (task 19; d009bea) | Kiro-Task 19 | wiring, HUD |
| 13 | Airdrop, roster, ultimates, richness designs (tasks 31 to 35, 38 to 40) | Kiro-Task 31 to 35, 38 to 40 (designs) | which rules were adopted |
| 14 | Balance simulator and class stats (tasks 42, 44; bf95661) | Kiro-Task 42, 44 | numbers adopted in the page |
| 15 | "Bring in Kiro tasks 41 to 44" bundle (real bundle commits) | Kiro-Task 41 to 44 | re-ran tests |
| 16 | Fonts pipeline and licences (tasks 48, 49) | Kiro-Task 48, 49 | wiring |
| 17 | Status effects, HUD, wind ghost, preload gate | none | all (index.html) |
| 18 | Game review and fixes (task 58: P0 and P1 fixes) | Kiro-Task 58 (review) | the fixes |
| 19 | Plans: flow, MCP, 4v4, architecture, art gap (tasks 73 to 77, 79) | Kiro-Task 73 to 77, 79 (plans) | owner corrections |
| 20 | Tooling: ingest scripts, daily log, model-test scorer, router, ledger (tasks 64, 71, 78, 82, 83) | Kiro-Task 64, 71, 78, 82, 83 (83: see status note) | `kiro_route.py`, `make_kiro_ledger.py`, verification |
| 21 | Evidence layer: hooks, agents, steering fixes, raw logs, `docs/kiro_evidence/` (A3, A7, A8) | whatever A3 delivers, level V only after the main line verifies | route logs copied, verification |
| 22 | Release package: README, JUDGES.md, CREDITS.md, `scripts/release/` (tasks 85 to 89 proposed below) | Kiro-Task 85 to 89 | verification, EXPORT_NOTES |
Rows 4, 5 and 8 depend on which real commits exist; if two milestones collapse into one real commit, merge the rows and keep both trailers. Milestones 1 to 3 hold no Kiro-Task trailer until the ledger or the owner supports one.

## 4. Repository layout at the root
```
README.md  JUDGES.md  CREDITS.md  LICENSE  .gitignore  index.html
.kiro/ (agents hooks settings specs steering)   .claude/skills/
css/ js/ shared/ scripts/ (tests, engine, MCP server, tools, release/)
assets/ (audio fonts units ... with their licence files)   colab/
docs/ (kiro_evidence/ with raw/, KIRO_LEDGER.md, PROMPT_LOG.md, ASSET_PROVENANCE.md, game_mode.md, mcp_agent_protocol.md, design docs)
```
- **README.md** (English; Kiro drafts, owner approves): one-line pitch; screenshot or gif; run in 3 commands (`git clone <url>`, `cd <repo> && python3 -m http.server 8080`, open `http://127.0.0.1:8080/`); how to play (angle, hold to charge, release, wind, move die, defend); what exists today versus the design (1 vs 1 prototype; the MCP server in `scripts/` lets an outside agent play the Python engine; the multi-device "bring your own agent" idea is the design, built only if it ships by the freeze, and the README says so either way); hosted URL (`HOSTED_URL` placeholder, P14 blocks the push); how Kiro and Claude Code split the work (one paragraph, then a link to JUDGES.md); Qwen disclosure; licence MIT; credits link.
- **JUDGES.md** (one page): table of the 8 write-up topics, each with a path and a command that reproduces it, then one line per criterion.

| Topic | Path | Reproduce |
|---|---|---|
| IDE / CLI / Web / Crew | `scripts/kiro_route.py`, `docs/kiro_evidence/raw/route_logs/` | read the logs; say which of the four were really used (CLI yes; IDE only if the owner runs the hooks; Web and Crew not evidenced) |
| Custom agents | `.kiro/agents/*.json` | `ls .kiro/agents`; outputs in `docs/kiro_evidence/raw/` once A7 runs |
| Hooks | `.kiro/hooks/` | save a watched file in the Kiro IDE; kept output in `raw/` (owner step) |
| Specs vs vibe coding | `.kiro/specs/` (21 folders), `docs/KIRO_LEDGER.md` | compare modules built from specs (particles, audio, wind) with `index.html` (main line, no spec) |
| Steering | `.kiro/steering/` | read `rules.md`, `kiro_assignment.md` |
| MCP | `.kiro/settings/mcp.json`, `scripts/mcp_stdio_server.py` | `python3 -B scripts/test_mcp_stdio.py` |
| Property-based testing | `scripts/test_particles.js`, plus `test_properties.*` if A2 merges | `node scripts/test_particles.js` |
| Powers | none | state "not used" |
Criteria lines: Potential Impact, Technological Implementation, Design, Innovation, Presentation, each one sentence with a path. No sentence may claim more than the ledger's main-line verification column supports.
- **CREDITS.md**: audio (copy from `assets/audio/CREDITS.md`, keep `_licenses/`), fonts (OFL files and `assets/fonts/README.md`), art generated with Qwen-Image-Edit via Colab (model and licence to be confirmed by the owner; COMPLIANCE_CHECK says Apache-2.0 UNVERIFIED), tools (Kiro CLI, Claude Code, Python, Node), and any other source the provenance gate finds.
- **`(not published)`: do not publish.** The rules extract is a paraphrase of a public page, so publishing it harms nobody, but judges have the rules. COMPLIANCE_CHECK is internal: it lists our own MISSING items, doubts about eligibility and country, and the credit-request status. Those lines are private or self-damaging. JUDGES.md carries a short mapping to the rules written fresh. The owner can overrule for the extract only.
- **`docs/kiro_evidence/`**: README, daily files, `raw/` (route logs, test runs from `end_of_day.py --apply`, hook output, agent output, an MCP transcript, `git worktree list` kept as text with local paths replaced), `commits_by_kiro_task.md` (A8, generated from the trailers of the NEW repo).

## 5. Clean checkout verification
Run on the release directory, in a temp folder, never in the working project. Build artefacts of an earlier run must not be present (`git status --short` is empty).
```
T=$(mktemp -d); git clone --no-local ../pk-release "$T/pk"; cd "$T/pk"
git status --short | wc -l                     # expect 0
git ls-files | wc -l; du -sh .git              # record both numbers
python3 scripts/release/check_asset_refs.py    # every assets/ path named in index.html, js/, css/, make_preload_links.py exists; exit 1 on a miss
python3 -m http.server 8080 --bind 127.0.0.1 > "$T/server.log" 2>&1 &
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/index.html   # 200
```
- Browser (the main line's built-in browser): open the page, wait for the load gate. Expect the text for 60 of 60 pictures. Console shows no error. Then `grep -c '" 404 ' "$T/server.log"` must print 0 (the server logs every missing file).
- Case sensitivity: macOS ignores letter case, GitHub and Linux do not. Repeat the clone and the 404 count on Linux (Docker if present, else a GitHub Codespace or a private-repo Actions run; UNVERIFIED which is available). A wrong-case path only fails there.
- Node: `for f in scripts/test_*.js; do node "$f" > "$T/o.txt" 2>&1 && echo "PASS $f" || echo "FAIL $f"; tail -n 2 "$T/o.txt"; done`
- Python: the same loop with `python3 -B`. **Four Python tests need packages the rules say the tests do not need:** `test_fonts.py` (fontTools; it fails by design with an install hint), `test_ingest_sheets.py` (numpy, Pillow), `test_ingest_wind_sheets.py` (Pillow), `test_postprocess_audio.py` (numpy). A bare checkout makes four red lines. Fix: a Kiro task changes them to print `SKIP: <package> missing` and exit 0 when the import fails (same assertions when present), and tech.md gets one sentence naming them. This edits tests, so the owner approves first (question 3). Expected green on a bare Python 3: every other `test_*.py`.
- **`test_i18n.js` (red today: `assets/i18n/zh-TW.json` does not exist, and `js/i18n.js` is not loaded by the page).** Options: (1) a Kiro task generates the JSON from the keys the module already defines and the test goes green; (2) move the module and its test out of the release and say so in the ledger row; (3) ship it red with an explanation. Recommend (1), fallback (2). Option (3) is the worst for the Technological Implementation score. Do not hide it silently.
- Save every output under `(not published)` after the gate, and quote the last line of each test in JUDGES.md only after the main line has seen it.
- Afterwards `kill %1` and delete `$T`.

## 6. Sequence and owner steps (Taiwan time; deadline Dec 5 06:00 = Dec 4 14:00 PT)
| When | Step | Who |
|---|---|---|
| Now to Nov 13 | Tasks 85 to 89 (below); main line reads the diffs and runs their tests | Kiro writes, main line verifies |
| Nov 13 | Owner answers questions 1 to 4 (section 7); creates `~/pk_privacy_terms.txt` | owner |
| Nov 14 | Commit the working tree on a local branch so the last milestone is a real commit (208 uncommitted changes today; the main line commits, no push, no Co-Authored-By) | main line |
| Nov 14 | DRY RUN: `build_history.py --dry-run` on the current tree, then the P-checks on the export. Fix every BLOCK | main line |
| Nov 15 | Owner creates an EMPTY repository on GitHub under the account (no README, no licence, no template). Private for rehearsal is the owner's choice; the final state must be public | owner only |
| Nov 20 | Rehearsal build `--apply` into `(not published)`, clean-checkout run on Linux, push only if the owner says (to the private rehearsal repository) | main line, owner pushes |
| Nov 27 | Feature freeze (queue) | all |
| Nov 28 | Final build `--apply`; P15 and P16; clean checkout; first-commit tree check; README placeholders only for the hosted URL | main line |
| Nov 29 | Owner pushes to the new repository, sets it Public, checks that About shows MIT, opens the page logged out. The existing old repository is never touched by this plan; whether to delete or rename it is the owner's decision | owner only |
| Nov 30 | History freeze. From here only normal commits on top, each with a `Kiro-Task` trailer where it applies. No rewrite after it is public | rule |
| Dec 1 | Hosted URL live on Contabo/Coolify (relay and page); put the URL in README and the Devpost form; clean-checkout run against the hosted page | owner deploys, main line checks |
| Dec 2 | Video (under 3 minutes, YouTube public, no copyrighted music) uploaded. Credit form deadline Dec 2 04:00 is already done per the compliance file | owner |
| Dec 3 evening | Devpost form complete: description, video, repo URL, category, write-up from JUDGES.md plus kiro_evidence | owner only |
| Dec 4 | Buffer. Re-read the live rules page (Devpost blocks automated fetches; use the browser) | owner, main line |
Only the owner can: create the repository, set visibility, push, check About, deploy, fill in Devpost, upload the video. A dry run precedes every push; nothing is pushed on a script's say-so.

## 7. Risks and what could not be verified
- **Owner questions.** (1) Were the first-commit steering files and spec made in Kiro (IDE or CLI) and by whom? The answer decides whether milestones 1 and 2 may carry a Kiro trailer. (2) Did any shipped picture come from a tool other than Qwen (the AWS image-call log and the Gemini files suggest it)? (3) May tests be changed to SKIP when an optional package is missing? (4) Publish `(not published)`? Default no.
- Not verified: file sizes; which tracked files hold the email, the paths and the secret-like words (by design not read); whether `(not published)` is tracked; the 73 `.kiro` file count; the zip contents; whether any real commit message carries a Co-Authored-By line; the first commit hash; the committer identities beyond six reflog lines; case-sensitivity problems; whether `kiro_models.json` and `push_queue_to_drive.sh` pass the gate; whether Docker or Linux is available.
- The privacy gate finds patterns, not meaning. A private sentence in plain words (a remark about money or family in a Chinese note) passes P1 to P9. That is why notes in Chinese are EXCLUDED by default (P10) and only translated files are included, and why the terms file is needed.
- Old art in old snapshots (for example the "flawed environment assets" that were later replaced) raises the repository size; check `git count-objects -vH` after `--apply`. If large, drop those milestones' asset paths from the early snapshots, not from the last one.
- Evidence honesty: the Kiro share is the tooling, plans, effects, sound, wind, dock and engine; `index.html` (about 3,000 lines) is the main line's. A trailer on every commit would look like more than it is. The validator exists to stop that.
- Leaks through a Kiro-written script: `scripts/release/*` will touch the real tree. Those scripts take no network action and no remote.

## 8. Kiro from the very first commit, and who does what
- Milestone 1 is the real first commit's content, checked by tree hash (section 3, step 4). The licence, `.kiro/steering/*` and `.kiro/specs/core-throw-loop` therefore appear at commit 1 with the real date. The message keeps the real subject. It makes no claim about who typed the files until question 1 is answered.
- From milestone 4 on, each message names the Kiro task or spec and states the main line's part. The validator refuses: a task not in the ledger; a status other than `ok`; a file named under "Kiro part" that no ledger row, inventory row or real diff supports.
- Dates and authorship: copied from the real log, grouped, never changed. No date is moved to look earlier; the new repository's real creation date shows only in the last milestone and later commits.
- Proposed task briefs (numbers are the main line's to assign):

| Proposed | Task | Model | Kiro delivers | Main line does |
|---|---|---|---|---|
| 85 | `export_tree.py`, `export_manifest.json`, `check_asset_refs.py` | Terra | scripts and their tests (stdlib only) | runs them, compares against section 1 |
| 86 | `privacy_gate.py` (P1 to P16), test with fake private strings built at test time, never stored | Terra | script, tests, README of the gate | runs it on the real tree, reads file:line only, fixes hits |
| 87 | `build_history.py`, `validate_trailers.py`, `milestones.tsv` draft | Terra writes, Sonnet reviews | scripts, tests on a toy repo | dry run, fixes `end_rev`, runs `--apply`, tree-hash check |
| 88 | `README.md`, `JUDGES.md`, `CREDITS.md` drafts in English | Sonnet | drafts in `docs/`, not at the root | checks every path and command, edits the claims, copies to the root of the new repo |
| 89 | `clean_checkout.sh` plus the SKIP change for the four optional-package tests and the i18n fix | Terra | script, test edits (after question 3) | runs on a clean clone and on Linux, records raw output |
Kiro cannot run shells in the researcher agent, so Kiro's own reports will say "not run"; the main line runs and records, as the ledger rule demands. The main line does the work Kiro cannot: commit the working tree, run the Colab/Qwen art, `--apply`, verification, `docs/kiro_verified.json` updates. The owner does everything in section 6 marked owner. Kiro never merges, pushes, deploys or creates repositories.
