# Kiro task 30 - sound mapping table: which sound goes to which game event (design only)

## Why
The owner picked real CC0 sounds and said: make the mapping table first, then see how to wire it, and let Kiro screen it ("who pairs with whom"). You cannot hear anything: decide from names, lengths, source pages and the game design; mark every claim about how something sounds "unverified".

## Read first
docs/audio_event_map.json (30 events, current file per event), docs/sound_design.md (if present), docs/audio_sources.md, (not published), js/ambient_sfx.js (ambient layer: bat/ghost, 9-22 s gaps, max 2 at once).

## Candidates (already converted, ready to wire)
Ambient dir assets/audio/ambient: crow 0.5s, cat_meow 1.8s, cat_growl 5s, ghost_moan1 3s, ghost_moan3 4s, witch_cackle 1.2s, evil_laugh 2.5s, zombie_moan 4s, thunder 4s, wind_bed 20s (loop-ish bed), night_bed 28s (forest night bed).
SFX dir assets/audio/sfx: bell_round 5s (church bell), chime_single 2.5s, bones_rattle 1.1s, step_leaf 0.5s, rock_break 0.4s.
Not yet converted (owner has not picked): files listed in (not published) (wolf howl, roars, monsters, creaks, etc.). Do not map those; list only which ones you would ask the owner to pick.

## Do exactly this
1. Write docs/sound_mapping.md with three tables:
   a. EVENT table: for each existing event in audio_event_map.json that should change or gain a layer (e.g. round_start/round_end -> bell_round, move_step -> step_leaf, impact_ground_heavy -> rock_break layer, ko -> bones_rattle or zombie_moan, shield_place/heal sparkle -> chime_single, charge or flight with wind) give: event, new file(s), role (replace / extra layer / random variant), volume, pitch range, reason. Keep the screen/sound clean: at most 2 layers per event.
   b. AMBIENT sprinkle table: each ambient file with kind name, weight, min gap seconds, volume, pan, and a rule so the same sound never repeats back to back and never plays during a throw or KO. Beds (wind_bed, night_bed): loop volume under the music, crossfade, when they play.
   c. REJECT list: any candidate that should not be used and why (e.g. cat_growl too long, evil_laugh fits only a victory moment).
2. Write docs/sound_mapping.json: the same data, machine-readable (events: {name: {add: [...]}}, ambient: {kind: {...}}) so the main line can load it without retyping.
3. Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download anything. Do not create images.
4. Finish with a 6-line summary and say what you could not verify (you cannot hear).
