# Work queue 2026-11-15 — every competition gap and rule, cut into blocks for Kiro

Sources: official rules copy `(not published)`, `(not published)`, `docs/PLAN_20261115.md`, `(not published)`, `scripts/release/check_asset_refs.py` (7 missing references today), `docs/kiro_verified.json`.
Executor key: **K-CLI** = main line runs `scripts/kiro_route.py` with a brief; **K-IDE** = owner pastes into Kiro IDE with the folder `pumpkin-killer` OPEN as workspace (the IDE session of 11-15 15:41 failed because no workspace was open: "Spec workflow requires an open workspace"); **OWNER** = only the owner can; **MAIN** = main line verifies, files, merges.
Rules for every block: a spec or brief first, one task at a time, real dates, nothing ticked without a command output the main line has seen; at most 3 K-CLI blocks at once; one `index.html` block at a time.

## A. Rules checklist (official rules to current state)
| Rule | State | Block |
|---|---|---|
| New project, started after 10-30 09:00 PT | ok: first commit 2026-10-31; disclose pre-existing code, libraries, fonts, CC0 audio | B14 |
| Built with Kiro, enough variety (IDE, CLI, Web, Crew) | CLI strong; IDE, Web, Crew no evidence | B01, B02 |
| Public GitHub repository (not GitLab), all source, assets, instructions | not published | B10, B11 |
| Open source licence visible in the About box | LICENSE (MIT) exists; About not checked | B11 (OWNER) |
| `/.kiro` at the root and not in `.gitignore` | present; `.gitignore` to recheck on the export | B10 |
| Working app URL, free and unrestricted until 2027-01-29 | none | B03 |
| Text description in English | draft only | B13 |
| Demo video under 3 min, public YouTube, shows it working on its device, no copyrighted music | none | B16 |
| Write-up on Kiro use (8 topics) | `JUDGES.md` draft | B12 |
| English for all materials | game text is Traditional Chinese | B09 |
| Category chosen (Costume Contest), bonus prizes chosen | decided: Best Demo, Blog, Social Blitz | B13 |
| Blog post (third-party platform, says Kiroween 2026), Social Blitz post (hashtag first, owner's own words) | none | B17 |
| Credits request by 12-01 12:00 PT, redeem by 12-04 | requested per owner | B18 (OWNER) |
| Draft saved on Devpost before the deadline; no edits after | not started | B13 |

## B. Blocks (in order of priority; each block = one brief or one owner action)
| ID | Block | Executor | Depends on | Done when (command or file) |
|---|---|---|---|---|
| B01 | IDE evidence: open the folder as workspace, hook run on saving `index.html`, one MCP tool call from IDE chat, power visible (no install), session note | K-IDE then MAIN files it | owner opens folder `pumpkin-killer` | `docs/kiro_evidence/IDE_SESSION_20261115.md` and two raw files exist and show real output |
| B02 | Web and Crew evidence: one small task in Kiro Web on the new repository (A11/A12 of the queue) and one Crew mention only if really used | K-IDE or OWNER | B11 repo exists, GitHub App connected by owner | PR or task view saved; if not done, the write-up says "not used" |
| B03 | Public URL: deploy files exist (`deploy/`, `scripts/release/smoke_url.py` verified); owner runs the ingress and deploy; smoke test against the live URL | OWNER, MAIN | `deploy/` done | `python3 -B scripts/release/smoke_url.py <url>` prints PASS |
| B04 | Ultimates: spec `ultimates-v2`, then one task per hero: bat, skeleton, wizard effects; shield knight ultimate (A, B, C hidden points); ready chime | K-CLI (spec first), art by OWNER on Colab | B03 not required | each ultimate plays in the page; test or recorded run; `check_asset_refs.py` shows no missing chime |
| B05 | AI difficulty: three levels from three knobs; sweep script; middle level near 25 to 30 percent hit rate | K-CLI | none | sweep table file with the three hit rates, rerun by MAIN |
| B06 | Opening flow, simplest: start screen with name, coin toss, seat selection with per-unit seat labels | K-CLI after OWNER makes concept images (`docs/phase2/`) | B04 not required | the three screens work in the page |
| B07 | Missing pictures: `bg_belltower.png`, `bg_pumpkin_field.png`, `fx_feet_chain.png`, `unit_knight_unarmed.png` | OWNER on Colab/Qwen, or drop the reference | none | `check_asset_refs.py` missing count falls to 0 or each drop is a one-line code change |
| B08 | Missing sounds: `move_step.ogg`, `ultimate_ready_chime.ogg`, `item_pickup.ogg` (options in `docs/audio_gap_options_20261115.md`) | K-CLI after OWNER picks a source | B04 for the chime | files exist with licence lines in `CREDITS.md`, or references dropped |
| B09 | English interface: load `js/i18n.js`, create `assets/i18n/` files, language switch, English for start screen, buttons, hints, results | K-CLI (one `index.html` task) | B06 for the start screen | `node scripts/test_i18n.js` prints pass; page shows English |
| B10 | Export and privacy: `~/pk_privacy_terms.txt`, owner name removed from `.kiro/powers/*/plugin.json`, export tree `--apply` to `(not published)`, `privacy_gate.py` on it, `.kiro` not ignored | OWNER (terms file), K-CLI (fixes), MAIN | R0 answers | gate exits 0 on the export |
| B11 | (target repo fixed 2026-11-15: pumpkin-killer-kiroween, verified empty by ls-remote) History and upload: commit the working tree, single-commit export (milestones only if green), clean checkout on the export, private push to the new repository, then Public, topic `kiroween`, About shows MIT | MAIN, K-CLI (T3, T6), OWNER (Public) | B10 | remote head equals local head; clean checkout exits 0 |
| B12 | Write-up: `JUDGES.md` with the 8 topics, honest status per topic; Kiro-usage table; `CREDITS.md` complete | K-CLI | B01, B10 | every backticked path exists; each claim cites a file |
| B13 | README v2 review and Devpost text: full read of the README draft, English description, testing instructions, disclosure of pre-existing code; Devpost draft saved | MAIN review, K-CLI draft, OWNER pastes | B03 for the URL | README under 120 lines, first screen has picture and hook, text matches the video |
| B14 | Disclosure list: libraries, fonts (OFL), CC0 audio, Qwen art, anything made before 10-30 | K-CLI | none | section in `CREDITS.md` or the write-up |
| B15 | Known test gaps: `test_i18n.js`, optional-package tests, clean-checkout blind spots (missing references not counted, only committed files copied) | K-CLI | B09 | clean checkout reports missing references as failures |
| B16 | Video: script, English narration, 3-minute cut, OCR privacy check, YouTube upload | OWNER records and uploads; K-CLI drafts shot list | B03, range freeze | public link returns 200; no frame says fallback or failure |
| B17 | Blog post and Social Blitz post | OWNER writes in their own words; K-CLI drafts an outline for the blog only | B13 | URLs saved for the form |
| B18 | Credits and final form: redeem credit codes by 12-04, category and bonus prizes ticked, all links pasted, submit before 12-05 06:00 | OWNER | all | submission shows Submitted |
| B19 | 4 vs 4: frozen. Reopen only if every block above is done | — | — | — |
| B20 | Local LLM agent: adapter from the local LM Studio server (model on this machine) to the six MCP tools, public information only; same sweep and single-match learning curve as the scripted levels; licence of the model checked before any mention in README or CREDITS; shown only in local recordings and MCP transcripts (the hosted page has no model) | K-CLI (adapter, sweep), MAIN (licence check, rerun) | B05 (levels, adaptive level) | table row "llm" in `docs/ai_levels_sweep_*.md`; licence line in `CREDITS.md`; README says plainly it is local only |
| B21 | Finish the remaining heroes (ghost bride, bell-tower hunchback, reaper, necromancer: owner target is 8 heroes in total) with their normal attacks and ultimates (owner 2026-11-15: four heroes are too boring) | K-CLI plan (task 116) then one `index.html` task at a time; art by OWNER only where the existing Drive candidates are not enough | B04 pattern (ultimate module + test) | each hero selectable on the start screen, attack and ultimate play in the browser, `sim_balance` within range; plan in `docs/remaining_heroes_plan_20261115.md` |

## C. Order of dispatch (what runs first)
1. Now, in parallel: B04 spec (K-CLI), B05 (K-CLI), B14 (K-CLI). Owner: open the folder in the IDE and paste the W2 text (B01); write `~/pk_privacy_terms.txt` (B10).
2. Next: B09, B12, B15, B13 review. Owner: ingress and deploy (B03), Colab pictures (B07), concept images for B06.
3. Then: B10 export, B11 history and private push, B06, B08.
4. Last: B16 to B18 after the range freeze (12-02 06:00) and the one strong review (12-03 06:00).

## D. Cut order if time runs out
B19, B06 concepts (keep the existing start screen), B09 beyond the start screen, B05 beyond one tuned level, B04 beyond the four playable heroes, B08 generated music (keep CC0), the 22-milestone history.
