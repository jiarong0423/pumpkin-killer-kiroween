# Missing-reference mapping, 2026-11-15 (contest-gap-run task 3)

Why: `python3 -B scripts/release/check_asset_refs.py` lists every file the page names that does not exist. A judge sees a 404 or a silent hole for each. This page says, for each of the seven today, which job makes it, where it installs and what to do if it never arrives. Written from the files listed below; nothing was downloaded, played, installed or run on Colab. `python3 -B scripts/release/check_missing_mapped.py` fails if a missing path is not in this page, so the page cannot go stale unnoticed.

Counts today (`check_asset_refs.py`): `refs=121 missing=7`.

## The seven missing references
| Missing path | Needed by (line numbers in `index.html` today) | Job id and queue file | Output name Colab writes | Install route | Fallback if it never arrives (made by the main line, one writer) |
|---|---|---|---|---|---|
| `assets/env/bg_belltower.png` | `SCENES` entry `belltower` (377) | `bg_belltower` in `colab/jobs_missing_20261115.json` | `bg_belltower_v1_<tag>.png` | `scripts/ingest_missing_20261115.py` installs backgrounds to `assets/env/<job id>.png`; the picture must be exactly 16:9 | Delete the `belltower` entry from `SCENES`. The page already hides a scene whose picture failed to load, so nothing broken shows today, but the 404 and the missing reference remain until the entry is deleted. |
| `(not published)` | `SCENES` entry `pumpkin` (378) | `bg_pumpkin_field` in `colab/jobs_missing_20261115.json` | `bg_pumpkin_field_v1_<tag>.png` | as above | Delete the `pumpkin` entry from `SCENES`. |
| `assets/fx/sprites/fx_feet_chain.png` | `imgList` key `fx_chain` (467), drawn for a slowed unit (2523 to 2524, guarded by `complete` and `naturalWidth`) | `fx_feet_chain` in `colab/jobs_missing_20261115.json` | `fx_feet_chain_v1_<tag>.png` | `scripts/ingest_missing_20261115.py` keys it and installs to `assets/fx/sprites/fx_feet_chain.png`; `scripts/ingest_queue.py` also handles `fx_*` names for tag `q1` | Delete `fx_chain` from `imgList`; the slow status still shows its text badge. |
| `assets/units/unit_knight_unarmed.png` | `imgList` key `unit_knight_unarmed` (491) and `UNARMED_ART` (2215) | `unit_knight_unarmed` in `colab/jobs_missing_20261115.json` | `unit_knight_unarmed_v1_<tag>.png` | `scripts/ingest_missing_20261115.py` installs to `assets/units/unit_knight_unarmed.png` | Remove both entries; the comment in the page says the painted shield stays until the picture exists. |
| `(not published)` | audio event `move_step`, called at 826 | none (audio is not a Colab picture job) | none | none needed | Set `"file": null` in both copies of the event map: `docs/audio_event_map.json` (line 555) and `js/audio.js` (line 605). `step_leaf.ogg` already plays on half the steps and the synthesized step on the rest. |
| `(not published)` | audio event `item_pickup`, called at 1571 and 1575 | none | none | Owner listens to Kenney `confirmation_001.ogg` (CC0, pack already credited) and decides | If not approved: `"file": null` in both map copies (`docs/audio_event_map.json` line 708, `js/audio.js` line 758). If approved: add the file and one `assets/audio/CREDITS.md` row. |
| `(not published)` | audio event `ultimate_ready_chime` | none | none | No CC0 source with a visible licence is recorded | `"file": null` in both map copies (`docs/audio_event_map.json` line 639, `js/audio.js` line 689); the synthesized chime plays. `index.html` has no call for this event today. |
The two map copies must stay identical (`node scripts/test_audio.js` checks it). Sources and reasons for the three sounds: `docs/audio_gap_options_20261115.md`.

## When the pictures arrive (owner downloads, main line installs)
1. Put the downloaded PNGs in one folder. Dry run (writes nothing): `python3 -B scripts/ingest_missing_20261115.py --jobs colab/jobs_missing_20261115.json --drive-out <folder>`.
2. If the dry run reports no rejected picture, repeat with `--apply`. It keeps backups and appends provenance rows.
3. Run `python3 -B scripts/release/check_asset_refs.py` and read the SUMMARY line.

## Expected missing count after each outcome
| Outcome | Missing |
|---|---|
| Nothing changes | 7 |
| The four pictures installed | 3 (the audio files) |
| The four pictures installed and `move_step`, `ultimate_ready_chime` and `item_pickup` set to null | 0 |
| No pictures, all four entries deleted from `index.html`, three sounds set to null | 0 |

## Problems found while mapping (not fixed here)
- The job `fx_feet_chain` uses the older reference key `bar`, and `bg_*`, coin and ghoststar jobs differ in reference style. `bar` and the keys `knight` and `out:fx_ghost_idle_v1_ghost1.png` are not in the `refs` table of `colab/jobs_missing_20261115.json`, so the new runner stops on them. The main line adds them to the table before the run.
- `ingest_missing_20261115.py` installs `ghoststar_blow` and `ghoststar_blow_hard` as `(not published)`. The page loads `fx_ghost_blow.png` and `fx_ghost_blow_hard.png`, which exist today, so those two outputs would not replace anything without a rename. They are not page gaps.
- The coin pictures install to `(not published)` and no page code names them yet.
- The scene pictures `bg_ruined_church`, `bg_abandoned_school` and their `_b` takes install to `assets/env/`. The page does not name them yet; adding a scene needs an `index.html` edit and a cleared 16:9 check.
- The ingest script needs Pillow. The `python3` on the machine where this page was written has no Pillow, so `scripts/test_ingest_missing.py` was not run here.
- `assets/i18n/` is excluded by the export manifest (see `docs/kiro_141_1_result_gpt-5.6-terra.md`). That is a gap of the same kind (a runtime file the export would drop) and is not in the seven.
