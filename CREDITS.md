# Credits

The browser game itself uses no third-party frontend library or bundler (vanilla HTML5 Canvas and ES JavaScript). The container backend uses Python 3.12 with `websockets==15.0.1` (`requirements.txt`, plus `boto3==1.34.162` in `deploy/relay/requirements.txt` if Bedrock is enabled) and **Node.js 22** (running `scripts/page_judge_seat.js` / `PageJudgeRelay`).

This page lists every third-party asset and its licence. Where the repository does not record a source, the entry says "provenance not recorded". Nothing is guessed.

## Sounds and music (CC0, owner-supplied Gemini SFX, and Google Flow Music)

Every third-party file below is from a source whose page shows CC0 (checked in a browser on 2026-11-24; two OpenGameArt pages now answer 404 and four files from Pixabay are under the Pixabay Content License, not CC0: see `assets/audio/CREDITS.md`, last section). The 22 Gemini-generated files are not CC0 material. Attribution is not required for CC0 and is given as a courtesy. The per-file record (work, author, page, hash) is `assets/audio/CREDITS.md`. The CC0 sources are Kenney, OpenGameArt authors and BigSoundBank. The page-by-page source list is `docs/audio_sources.md`.

Sources with a saved licence text in `assets/audio/_licenses/`:

| Files | Work and author | Licence file |
|---|---|---|
| `assets/audio/music/bed_ambient.ogg` | Creepy Ambient Loop, epb9000 (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-creepy-ambient-epb9000.txt` |
| `assets/audio/music/victory_sting.ogg` | Short Jingle, OO (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-short-jingle.txt` |
| `assets/audio/music/defeat_sting.ogg` | Game Over (dark) short music clips, Robin Lamb (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-game-over-dark.txt` |
| `assets/audio/music/tension_drone.ogg` | Ambient Horror, Pixels67 (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-ambient-horror.txt` |
| `assets/audio/sfx/ui_click.ogg`, `assets/audio/sfx/ui_hover.ogg`, `assets/audio/sfx/dice_tick.ogg` | Interface Sounds, Kenney | `assets/audio/_licenses/LICENSE_kenney-interface.txt` |
| `assets/audio/sfx/dice_rattle.ogg`, `assets/audio/sfx/dice_throw_short.ogg` | Casino Audio, Kenney | `assets/audio/_licenses/LICENSE_kenney-casino.txt`, `assets/audio/_licenses/kenney_casino-audio_License.txt` |
| `assets/audio/sfx/move_step_footstep.ogg`, `assets/audio/sfx/throw_axe_chop.ogg`, `assets/audio/sfx/coin_flip.ogg` | RPG Audio, Kenney | `assets/audio/_licenses/kenney_rpg-audio_License.txt` |
| `assets/audio/sfx/throw_cross_bell.ogg`, `assets/audio/sfx/ultimate_ready_glass.ogg`, `assets/audio/sfx/poison_tick_soft.ogg` | Impact Sounds, Kenney | `assets/audio/_licenses/kenney_impact-sounds_License.txt` |
| `assets/audio/sfx/shield_place_spell.ogg`, `assets/audio/sfx/throw_cannon_boom.ogg`, `assets/audio/sfx/fence_break.ogg` | Sci-Fi Sounds, Kenney | `assets/audio/_licenses/LICENSE_kenney-scifi.txt` |
| `assets/audio/sfx/whoosh_spear.ogg` | Whoosh #2, Joseph Sardin (BigSoundBank) | `assets/audio/_licenses/LICENSE_bigsoundbank-s0573.txt` |
| `assets/audio/sfx/heartbeat.ogg` | Heartbeat #3, Joseph Sardin (BigSoundBank) | `assets/audio/_licenses/LICENSE_bigsoundbank-s0770.txt` |
| `assets/audio/sfx/spell_magic.ogg` | Magic Spell SFX, Arcanorum (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-magic-spell-sfx.txt` |
| `assets/audio/sfx/heal_harp.ogg` | Magic Words + Healing Sound Effect, PFNienow (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-magic-words-healing.txt` |
| `assets/audio/sfx/roar_ko.ogg`, `assets/audio/sfx/stone_ground.ogg`, `assets/audio/sfx/stone_ground_heavy.ogg` (a pitch-shifted copy) | 80 CC0 RPG SFX, NoirPhantom89 (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-80-cc0-rpg-sfx.txt` |
| `assets/audio/sfx/punch_hit.ogg`, `assets/audio/sfx/punch_heavy.ogg` | Punch, looneybits (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-punch-qubodup.txt` |
| `assets/audio/sfx/swish_throw.ogg`, `assets/audio/sfx/swish_shield.ogg` (a pitch-shifted copy) | Swishes Sound Pack, qubodup (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-swishes.txt` |
| `assets/audio/sfx/thwack_wood.ogg` | Thwack Sounds (author: see the OpenGameArt page) | `assets/audio/_licenses/LICENSE_oga-thwack.txt` |
| `assets/audio/sfx/metal_bing.ogg` | Metal Impact Sounds, Hazmat Harry (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-metal-impact.txt` |
| `assets/audio/sfx/ghost_real.ogg` | Ghost, Clint Bellanger (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-ghost-ogrebane.txt` |
| `assets/audio/sfx/throw_flame_fire.ogg` | Catching Fire (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-catching-fire.txt` |
| `assets/audio/sfx/flight_spear_whoosh.ogg` | Wind Whoosh Loop (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-wind-whoosh-loop.txt` |
| `assets/audio/sfx/flight_cannon_wind.ogg` | Air Whoosh (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-air-whoosh.txt` |
| `assets/audio/sfx/flight_shield_wind.ogg` | Short Wind Sound (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-short-wind.txt` |
| `assets/audio/music/rhythm_percussion_loop.ogg` | Cinematic Percussion Loop (OpenGameArt) | `assets/audio/_licenses/LICENSE_oga-cinematic-percussion-loop.txt` |

Sources recorded as CC0 on the source page, with no licence text saved. The page and licence line are in `docs/audio_sources.md`; the author is not recorded in the repository unless named here:

| Files | Source |
|---|---|
| `assets/audio/ambient/crow.ogg`, `assets/audio/ambient/cat_meow.ogg`, `assets/audio/ambient/cat_growl.ogg`, `assets/audio/ambient/thunder.ogg`, `assets/audio/ambient/wind_bed.ogg`, `assets/audio/ambient/night_bed.ogg` | BigSoundBank (author provenance not recorded) |
| `assets/audio/sfx/bell_round.ogg`, `assets/audio/sfx/chime_single.ogg`, `assets/audio/sfx/step_leaf.ogg` | BigSoundBank (author provenance not recorded) |
| `assets/audio/ambient/ghost_moan1.ogg`, `assets/audio/ambient/ghost_moan3.ogg` | Ghost Moans, qubodup (OpenGameArt) |
| `assets/audio/ambient/witch_cackle.ogg`, `assets/audio/ambient/evil_laugh.ogg` | Witch Cackle and Evil Laugh (OpenGameArt; author not recorded) |
| `assets/audio/ambient/zombie_moan.ogg` | Zombie Moans, darsycho (OpenGameArt) |
| `assets/audio/ambient/dog_bark.ogg` | 80 CC0 Creature SFX (OpenGameArt; author not recorded) |
| `assets/audio/ambient/ghost_cackle.ogg` | Ghostly Cackle Laugh 1 (OpenGameArt; author not recorded) |
| `assets/audio/sfx/bones_rattle.ogg` | Bones 2 (OpenGameArt; author not recorded) |
| `assets/audio/sfx/rock_break.ogg` | Breaking Rock (OpenGameArt; author not recorded) |
| `assets/audio/music/bed_artifact_room.ogg` | Artifact Room, Fupi (OpenGameArt) |

Owner-supplied sound effects generated with Gemini (`docs/audio_sources.md`, `assets/audio/CREDITS.md`; commercial use under the tool's terms confirmed by the owner):

| Files | Source |
|---|---|
| `assets/audio/sfx/throw_cannon_rocket.ogg`, `assets/audio/sfx/throw_shuriken_gemini.ogg`, `assets/audio/sfx/throw_shield_gemini.ogg`, `assets/audio/sfx/throw_soundwave_sonic.ogg`, `assets/audio/sfx/throw_axe_gemini.ogg`, `assets/audio/sfx/throw_cross_gemini.ogg`, `assets/audio/sfx/impact_flame_evil_spell.ogg` | Owner's Gemini sound set (`pumpkin_slayer_sfx_v3`), trimmed and normalised in repository |
| `assets/audio/sfx/status_frost_owner.ogg`, `assets/audio/sfx/status_shock_owner.ogg`, `assets/audio/sfx/status_slow_owner.ogg`, `assets/audio/sfx/status_stun_owner.ogg` | Pixabay Content License, not CC0 (owner-supplied MP3 files for frost, shock, slow, and stun downloaded from Pixabay on 2026-11-22, cut and normalised in repository; licence summary checked 2026-11-24: free use, modification allowed, no attribution required, standalone redistribution prohibited) |
| `assets/audio/sfx/ult_skeleton.ogg`, `assets/audio/sfx/ult_skeleton_hit.ogg`, `assets/audio/sfx/ult_wizard.ogg`, `assets/audio/sfx/ult_wizard_hit.ogg`, `assets/audio/sfx/ult_bat.ogg`, `assets/audio/sfx/ult_bat_hit.ogg`, `assets/audio/sfx/ult_knight.ogg`, `assets/audio/sfx/ult_reaper.ogg`, `assets/audio/sfx/ult_reaper_hit.ogg`, `assets/audio/sfx/ult_bride.ogg`, `assets/audio/sfx/ult_bride_hit.ogg`, `assets/audio/sfx/ult_hunchback.ogg`, `assets/audio/sfx/ult_hunchback_hit.ogg`, `assets/audio/sfx/ult_hag.ogg`, `assets/audio/sfx/ult_hag_hit.ogg` | Owner's Gemini ultimate sound set (`pumpkin_slayer_ultimates_sfx.zip`), split into cast and hit parts in repository |

Owner-supplied background music generated with Google Flow Music (`docs/audio_sources.md`, `assets/audio/CREDITS.md`; Plus plan, Google Terms of Service and Generative AI Prohibited Use Policy):

| Files | Source |
|---|---|
| `assets/audio/music/bgm_title_phantom_v1.m4a` | "Phantom Trajectory" (title, lobby and result screens; generated by the owner in Google Flow Music; replaces `bed_artifact_room.ogg`, which is no longer played) |
| `assets/audio/music/bgm_battle_ghoul_v1.m4a` | "Artillery Ghoul Battle Theme" (battle; generated by the owner in Google Flow Music; replaces `rhythm_percussion_loop.ogg`, which is no longer played) |

Sounds that no file covers (`charge`, `flight_shuriken`) are synthesised in code by `js/audio.js`.

## Fonts (SIL Open Font License 1.1)

| File | Font | Licence file |
|---|---|---|
| `assets/fonts/CinzelDecorative-Bold.ttf` | Cinzel Decorative Bold, unmodified | `assets/fonts/OFL-CinzelDecorative.txt` |
| `assets/fonts/pk-body-400.woff2`, `assets/fonts/pk-body-700.woff2` | Noto Sans TC, subset and renamed "PK Body" | `assets/fonts/OFL-NotoSansTC.txt` |
| `assets/fonts/pk-display-cjk-900.woff2` | Noto Serif TC, subset and renamed "PK Display CJK" | `assets/fonts/OFL-NotoSerifTC.txt` |

Sources and sizes are in `assets/fonts/README.md`. The subsets are built by `scripts/build_fonts.py`.

## Pictures

`docs/ASSET_PROVENANCE.md` records both first-party/generated art and third-party CC0 particle sprites (`assets/fx/kenney/`), noting known tools where recorded and "unknown" where unlogged. Kiro generated no images.

Made with an image model or third-party CC0 pack, tool/source recorded:

| Folder / Files | What | Tool / Source | Notes |
|---|---|---|---|
| `assets/poses/` | Skeleton action poses + `wizard_release_new`, `hunchback_release_new` | Qwen-Image-Edit-2509 on Colab; Flow AI (`hunchback_release_new`) | keyed from flat background (`scripts/key_skeleton_poses.py`); Apache-2.0 model card (`docs/ASSET_PROVENANCE.md`) |
| `assets/weapons/` | Small shield, dart, dart bag, spear | Qwen-Image-Edit-2509 on Colab | keyed by `scripts/key_magenta_items.py`; Apache-2.0 model card |
| `assets/ui/shield_slab_blue.png`, `assets/ui/shield_slab_purple.png` | Floating shield slabs | Qwen-Image-Edit-2509 on Colab | keyed by `scripts/key_magenta_items.py` |
| `assets/fx/kenney/*` (6 sprites) | Particle Pack 1.1 (`circle_03/05`, `light_01`, `star_06`, `twirl_02/03`) | Kenney (`kenney.nl`) | **CC0** (`assets/fx/kenney/License.txt`) |
| `assets/fx/sprites/fx_cross_silver.*`, `fx_slash_arc.*`, `fx_arcane_circle.*`, `fx_star_ring.*`, `fx_fire_tongue.*` | Silver cross (`2026-11-25` upright replacement) and attack/magic FX sprites | Gemini / Flow AI (owner-supplied) | Commercial terms follow owner statement in `docs/ASSET_PROVENANCE.md` |
| `assets/portraits/hag_front.*`, `assets/portraits/bat_front.*` | Silver Cross Sister & Bat-cat Assassin front portraits | Qwen-Image-Edit-2511 (`hag_front`), Flow AI (`bat_front`) | Remaining 6 front portraits (`skeleton`, `wizard`, `knight`, `reaper`, `bride`, `hunchback`) pre-date 2026-11-09 |
| `assets/avatars/avatar_*.png` | Hero selection & lobby avatars (256×256) | `scripts/make_avatars.py` / `scripts/install_avatars.py` (Pillow) | Cropped from `assets/portraits/*_front.png` (`avatar_bat.png` regenerated from `bat_front.png` on 2026-11-26) |

Derived by script from other pictures (they follow the status of their source): `assets/units/unit_bat_unarmed.png` and `assets/units/unit_skeleton_unarmed.png` (`scripts/make_unarmed_bat.py`, `scripts/make_unarmed_skeleton.py`), the baked sprites (`scripts/bake_sprites.py`), WebP siblings (`scripts/make_webp_assets.py`), and `assets/fx/` sheets (`scripts/bake_fx.py`).

### Provenance not recorded

The repository does not record the exact generation prompt or tool for these older files:

- `assets/units/` original unit art (bat, knight, skeleton and wizard, with their raw files) and the bride, hunchback and reaper unit pictures (`docs/ASSET_PROVENANCE.md` notes the owner's statement that initial unit pictures came from unprompt-logged Gemini generation).
- `assets/env/` (background, ground, platforms, fence, crates, older projectile/effect sheets).
- `assets/ui/` apart from the two shield slabs (plates, icons, frames, banners, wind plate).
- `assets/portraits/{skeleton,wizard,knight,reaper,bride,hunchback}_front.png` (tool/prompt not logged in repo).
- Pictures from later image-model runs. `docs/PROMPT_LOG.md` records experiments, without mapping every file by name.
- *(Note: temporary Colab input `ref_bar_from_video.png` and its sketch video were deleted on 2026-11-24 and never shipped; `docs/ASSET_PROVENANCE.md:33`.)*

## Tools used

| Tool | Used for | Where it is recorded |
|---|---|---|
| Kiro (CLI, ACP, IDE, Crew 0.12.2) | Specs, steering, hooks, scripts, Python engine, initial relay & MCP stdio server, doc audit | `docs/KIRO_LEDGER.md`, `scripts/kiro_route.py`, `docs/kiro_evidence/raw/ide_hook_run_20261115.txt`, `docs/crew_audit_usage_doc_result.md` |
| Models named in Kiro ledger (`gpt-5.6-terra`, `claude-sonnet-5.5`) | Routed Kiro task execution | `docs/KIRO_LEDGER.md` |
| Claude Code & Gemini | Page integration, 3v3 lobby, Streamable HTTP `/mcp`, `PageJudgeRelay`, red-team & fixes | `.kiro/steering/team_plan.md`, `docs/KIRO_USAGE_20261116.md` |
| GLM-5.3 & DeepSeek V4 Pro (Nebius Token Factory API) | External adversarial review & brute-force relay audit (`LLM-REVIEW-1`) | `docs/llm/llm_findings_verdict_20261126.md`, `scripts/llm_review.py` |
| Qwen-Image-Edit-2509 / 2511 & Gemini / Flow AI / Google Flow Music | Poses, weapons, shield slabs, portraits (`hag_front`, `bat_front`), FX sprites, SFX, background music | `docs/ASSET_PROVENANCE.md`, `docs/PROMPT_LOG.md`, `docs/audio_sources.md` |

## Disclosure of pre-existing work (contest rule "New Projects Only")

Updated 2026-11-26 from repository records (Submission Period began 2026-10-30).

- **Start date.** First development commit: 2026-10-31 (within the Submission Period beginning 2026-10-30). No shipped code or art predates 2026-10-30.
- **Code libraries.** Browser game: none (plain HTML5 Canvas + JS/CSS). Container runtime: Python 3.12 (`websockets==15.0.1`, optional `boto3==1.34.162`) and Node.js 22 (`PageJudgeRelay`).
- **Fonts.** Three SIL OFL fonts (`Cinzel Decorative`, `Noto Sans TC`, `Noto Serif TC`), listed above with licence files.
- **Sounds and music.** CC0 audio from Kenney, OpenGameArt, and BigSoundBank, plus 4 Pixabay Content License status sounds, 22 owner-supplied Gemini SFX files and 2 background-music tracks the owner generated with Google Flow Music (`assets/audio/CREDITS.md`; unsampled sounds synthesized in `js/audio.js`).
- **Pictures.** Third-party CC0 particle sprites from Kenney (`assets/fx/kenney/`), plus owner-pipelined Qwen-Image-Edit, Gemini, and Flow AI artwork (`docs/ASSET_PROVENANCE.md`). Temporary sketch `ref_bar_from_video.png` was deleted and never shipped.
- **Generated code and text.** Kiro and AI coding/review assistants wrote code, tests, and docs under owner direction and verification (`docs/KIRO_USAGE_20261116.md`).
