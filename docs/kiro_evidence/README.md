# Kiro evidence folder (judges' view: what Kiro made and how it can be checked)

Every row names a commit or file and the command that the main line ran itself on 2026-11-10. Results are quoted from that run, not from a Kiro report.

## Sound module (Kiro CLI task 20)
- Origin: commit c409781 (2026-11-09) "Sound design: music and effect-sound module with synthesized fallbacks, event map, CC0 source list, tests (Kiro CLI, brief docs/kiro_task_20.md)"; merged by 45d0b87. 9 files, 2,289 lines: js/audio.js, scripts/test_audio.js (616 lines), docs/audio_event_map.json, docs/audio_sources.md, docs/sound_design.md, .kiro/specs/sound-design/{requirements,design,tasks}.md.
- Source search and licence checks: Kiro tasks 22, 23, 24 and 30 (briefs docs/kiro_task_22.md and so on); the main line downloaded the CC0 files and recorded licences and hashes in assets/audio/CREDITS.md (7 music files, 46 effect files in the folders).
- Synthesised sounds: the module contains the synthesised fallbacks (59 mentions of "synth" in js/audio.js); the three files that do not exist yet (move_step, item_pickup, ultimate_ready_chime) sound through them.
- Run today: `node scripts/test_audio.js` = 32 passed, 0 failed (includes "the module has no DOM, no Math.random, no Date"); `node scripts/test_ambient_sfx.js` = 13 passed, 0 failed.

## Particle effects with property tests (Kiro CLI task 06)
- Origin: commit c8f18c1 "Particle effects system with 12 presets and seeded property tests (implemented with Kiro CLI from docs/kiro_task_06.md)"; merged by 6d4101a. js/particles.js 980 lines, js/particles_draw.js 191 lines.
- This is the project's property-based testing: scripts/test_particles.js, 300 seeded cases per property.
- Run today: `node scripts/test_particles.js` = 48/48 properties passed.

## Wind visuals
- js/wind_fx.js 374 lines (commit 7dcfc9c, wind strength factor 72). Run today: `node scripts/test_wind_fx.js` = all 19 tests passed.

## More
- Whole inventory with files, lines, loaded or not: docs/KIRO_IMPACT_INVENTORY_20261110.md.
- Task ledger: docs/KIRO_LEDGER.md (regenerate with `python3 -B scripts/make_kiro_ledger.py --apply`); the main line's own re-checks: docs/kiro_verified.json.
- Still to evidence (queue A3): hook run logs, agent outputs for rules-reviewer and asset-inventory, a recorded MCP transcript.
