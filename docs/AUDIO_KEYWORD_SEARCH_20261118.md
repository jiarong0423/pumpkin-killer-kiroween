# Keyword search for sound and effect material (2026-11-18)

Owner 2026-11-18: search by role keywords (spell, cannon, throw, sound wave, swinging something, big-move roar, the bride crying) and see which CC0 material comes out, and how many pairings there are. Nothing was downloaded; licences are as the search results show them and must be confirmed on each page before a download (OpenGameArt and Freesound mix licences).

## Searches run (6) and what they gave
| keyword group | CC0 candidates found | not usable |
|---|---|---|
| spell (法術) | "150 Combat Sound Effects" (untamedpixels, CC0, 78 magic and spell files, WAV 48 kHz); "magic spell sfx" (1 OGG, CC0); "RPG Sound Pack" (artisticdude, CC0, 2 spells) | "Spell Sounds Starter Pack" (CC-BY-SA / GPL); "Magic Sounds" collection (mixed licences) |
| cannon (砲擊) | "cannon fire" (CC0, 1 OGG); "Ships / cannon" set (CC0: cannon fire, hit, miss, ship destroyed); "25 CC0 bang / firework SFX" (CC0); "synthesized explosion" (CC0); Freesound 580040 "Gun / Cannon / Explosion" (CC0) | Freesound 654077 cannon shots (asks for credit) |
| throw / swing (投擲、甩東西) | "Swishes Sound Pack" (artisticdude, CC0, 13 WAV: 4 light, 9 heavy) | Construct whoosh library (commercial); no Kenney whoosh pack in the results |
| sound wave (音波) | "Seamless Energy Emission Loop" (CC0, a pulse that can be cut); "synthesized explosion" as a shockwave layer | "Big low frequency explosion boom" (CC-BY); "dynamite" (attribution notice) |
| roar (吼叫) | "80 CC0 creature SFX" (CC0, 1.9 MB, 3 roars + 13 monster); "80 CC0 creature SFX 2"; "Monster Sound Effects 2" (Ogrebane, CC0, 17 WAV); "CC0 Deep Monster Roar" (1 file); "Monster or beast sounds" (CC0) | "Monster and Creatures PACK 001" (CC-BY) |
| crying (哭泣) | NONE clearly CC0 for crying. CC0 ghost voices: "Ghost Monster Voice Moaning and Growling" (qubodup), "Scary High-pitched Ghost", "Female Scream 1" (a scream, not a sob) | Freesound "Female Sobbing" (CC-BY-NC), paid banshee packs, AI-generated sigh (CC-BY) |

## Pairings (role x keyword), 8 roles and what already exists in `assets/audio`
| role | its action | keyword | best CC0 candidate | already in the game |
|---|---|---|---|---|
| skeleton | spear throw | throw / swing | Swishes Sound Pack (light) | whoosh_spear.ogg |
| wizard | pumpkin shell | cannon | cannon fire / Ships cannon set | throw_cannon_boom.ogg |
| wizard | pumpkin blast (ultimate) | cannon + explosion | 25 CC0 bang SFX, synthesized explosion | impact_ground_heavy |
| bat | shuriken | throw | Swishes Sound Pack (light) | swish_throw.ogg |
| knight | shield | swing | Swishes Sound Pack (heavy) | swish_shield.ogg |
| reaper | flame | spell | 150 Combat Sound Effects (magic) | spell_magic.ogg (borrowed) |
| hag (nun) | silver cross | spell + chime | 150 Combat Sound Effects (holy / magic) | chime_single.ogg (borrowed) |
| bride | sound wave | sound wave | Seamless Energy Emission Loop | ghost_real.ogg (placeholder) |
| bride | ultimate (cry) | crying | none CC0; ghost moans from "Ghost Monster Voice Moaning and Growling" | ghost_moan1 / 3 in ambient |
| hunchback | axe | swing (heavy) | Swishes Sound Pack (heavy) | rock_break.ogg (placeholder) |
| hunchback, knight, reaper | ultimate roar | roar | 80 CC0 creature SFX (3 roars) | none |

Count: 11 pairings; 9 have a CC0 candidate, 1 (bride crying) has only an indirect candidate (ghost moan), 1 (ultimate roar) has a candidate pack but nothing in the game yet. Seven CC0 packs would cover everything except the crying.

## Not decided (owner)
- Which packs to download (each is one file from OpenGameArt; sizes mostly 1 to 3 MB; the 150-file combat pack is bigger): proposed first set = Swishes Sound Pack, 80 CC0 creature SFX, cannon fire + Ships cannon set. Needs the owner's word per pack.
- The bride crying: no CC0 recording found; options are the ghost moans, a generated sound (an audio job exists in `colab/audio_jobs.json`, run in the owner's Colab), or a recording by the owner.
- The owner said he will describe the sound effects himself; these candidates are only the starting list.
