# Kiro 85 R4 (task 88, spec task T4) result, claude-sonnet-5.5

## What changed
- Created `(not published)`, `(not published)`, `(not published)`.
- Edited `.kiro/specs/release-package/tasks.md`: ticked four T4 boxes (English and 1 vs 1, JUDGES mapping, CREDITS list, `HOSTED_URL`). Left unticked: the backticked-path box, and "main line reviews".
- Ran no test, no script, no git, no network. Nothing here is a test result.

## Verify (main line)
- `grep -c HOSTED_URL (not published)` should print 1.
- Search the three drafts for an at-sign, a `<local path>` path or the author's name (the privacy gate terms file). I ran such a search with the file tool and found no match.
- Open each drafted command in JUDGES.md and run it; I ran none of them.

## Paths I checked (by directory listing or file read, not by a script)
- Docs: docs/game_mode.md, mcp_agent_protocol.md, ASSET_PROVENANCE.md, PROMPT_LOG.md, KIRO_LEDGER.md, kiro_verified.json, KIRO_IMPACT_INVENTORY_20261110.md, audio_sources.md, kiro_task_06.md, kiro_74/75/76 plan files, kiro_evidence/raw/hook_runs.log.
- Scripts: kiro_route, make_kiro_ledger, make_preload_links, daily_log, build_fonts, ingest_sheets, ingest_wind_sheets, sim_balance.js, sim_ai_nosim.js, eval_agent_learning, mcp_stdio_server, mcp_game_server, bake_sprites, bake_fx, key_skeleton_poses, key_magenta_items, make_unarmed_bat, make_unarmed_skeleton, and tests test_kiro_route, test_daily_log, test_particles, test_audio, test_wind_fx, test_i18n, test_mcp_game, test_mcp_stdio, test_constants_sync, test_fonts, test_ingest_sheets, test_ingest_wind_sheets, test_postprocess_audio. `scripts/release/` exists.
- js: particles, particles_draw, audio, ambient_sfx, wind_fx, class_stats, ultimate, scene_layers, i18n. css: dock.css. (not published) index.html.
- `.kiro`: settings/mcp.json, steering/ (6 files), agents/ (7), hooks/pk-checks.json and test-rig-on-save.kiro.hook, specs folders particles, sound-design, wind-design, shared-constants, physics-pbt, powers/pumpkin-killer-seat/plugin.json.
- assets: all 17 files in audio/_licenses, every audio file named in CREDITS.md (music 7, ambient 13, sfx 26 listed), audio/CREDITS.md, fonts (3 woff2/ttf, 3 OFL files, README), the folders poses, weapons, ui, units, sprites, fx, env, portraits, and colab_inputs/ref_bar_from_video.png.

## Not verified / needs the main line
1. Sibling links: README.md names `JUDGES.md`, `CREDITS.md`, `LICENSE`; JUDGES.md names `README.md`. Those exist only after the drafts are copied to the release root (LICENSE exists today). So the "every backticked path exists" box is not ticked.
2. Private detail outside my files: `LICENSE` and `.kiro/powers/pumpkin-killer-seat/plugin.json` hold the author's name. Privacy gate P7 will flag them. I did not touch them.
3. `.kiro/specs/physics-pbt/tasks.md` ticks `(not published)` and `(not published)`; neither exists. JUDGES.md says so. Decide whether to fix the spec or the sentence.
4. `docs/kiro_verified.json` has no entry for tasks 06, 20, 25, 19 (particles, sound, wind, dock). JUDGES.md marks them "not checked" even though `docs/kiro_evidence/README.md` quotes main-line runs. Add entries if you re-run them.
5. `docs/kiro_evidence/raw/hook_runs.log` has a "kiro result saved" run with no recorded trigger. JUDGES.md says it does not prove an IDE run. Correct that line if you know the trigger.
6. The route logs (`kiro_route_kiro_task_*.log` in the working root) are git-ignored, so they are not in a normal checkout. JUDGES.md names the router and the ledger and does not cite the logs by path. Add the log folder path after the export step copies them.
7. Asset provenance is incomplete in the source files (units, env, most of ui, portraits, newer art). CREDITS.md lists these as "provenance not recorded". R0 answer 2 (other image tools) is still open; edit that section when it arrives.
8. Audio authors are missing for several OpenGameArt and BigSoundBank files; listed as "not recorded".
9. README.md uses a `<REPOSITORY_URL>` placeholder in the clone command so that no account name appears. Replace it with the real URL on release day.
