# Audio and art inventory with source check, 2026-11-24

Method: every audio file on disk was matched to `assets/audio/CREDITS.md` (script, 2026-11-24); every recorded sha256 was recomputed; the saved licence files in `assets/audio/_licenses/` were read; then the source pages were opened in a browser (OpenGameArt blocks automated fetching with HTTP 403, so the pages were read in the built-in browser through the same-origin page) and the licence field on each page was copied. Nothing below is taken from a summary.

## Audio: 84 files

| Group | Files | Evidence | State |
|---|---:|---|---|
| CC0, and a licence file saved on the download day names the file in `assets/audio/_licenses/` | 16 | licence text saved on the download day | OK |
| CC0, credits row names the exact page | 26 | page read again on 2026-11-24 | OK |
| CC0, credits row names only the site (BigSoundBank: crow, cat growl and meow, night bed, thunder, wind bed, bell, chime, step) or a Kenney pack | 16 | site-wide licence: 10 BigSoundBank pages and 4 Kenney pack pages read on 2026-11-24, all CC0; two files are pitch-shifted copies of CC0 files | OK, exact pages not recorded |
| Gemini-generated, supplied by the owner (`throw_*_gemini`, `throw_cannon_rocket`, `throw_soundwave_sonic`, `impact_flame_evil_spell`, 15 `ult_*`) | 22 | owner states commercial use is allowed; no page | NOT CC0; owner confirmation open |
| Pixabay files (`status_frost_owner`, `status_shock_owner`, `status_slow_owner`, `status_stun_owner`) | 4 | owner: downloaded from Pixabay (2026-11-24); Pixabay Content License page read the same day: free use, no attribution, modification allowed, no standalone redistribution of unchanged content | NOT CC0; usable, exact pages and authors not recorded |
| **Total** | **84** | | |

Source pages read on 2026-11-24: OpenGameArt 33 of 35 show "License(s): CC0" and nothing else; the two that answer 404 are `ghost-moans` (feeds `ambient/ghost_moan1.ogg` and `ghost_moan3.ogg`, both wired in `js/ambient_sfx.js`) and `laugh-evil-1` (feeds `ambient/evil_laugh.ogg`, not wired). Kenney (casino, impact, interface, rpg audio): "Creative Commons CC0". BigSoundBank: the licence page lists several licences ("Royalty-Free Sound License (CC0-like)", WTFPL, public domain, a custom contract on request); each sound page read shows "CC0 (public domain)".
Not shipped: `music/alt_haunted_track.ogg` and `alt_music_box_waltz.ogg` (CC0 but not wired; the export manifest excludes them).
Checksums: 51 recorded hashes checked, one typo in the credits (`punch_heavy.ogg`; the file matches the full hash in `_licenses/LICENSE_oga-punch-qubodup.txt`), fixed.

What to do: (1) the four Pixabay files need no attribution (licence page read 2026-11-24) and their exact titles are not recorded; the owner may replace them with CC0 files only if the public repository should hold no non-CC0 audio; (2) the owner finds the `ghost-moans` page (or replaces the two ghost moans with another CC0 pair from a page that exists); (3) the owner confirms the Gemini terms for the 22 files; (4) after that, add the exact BigSoundBank pages to `assets/audio/CREDITS.md`.

## Pictures

| Folder | Files | Source in the repository | State |
|---|---:|---|---|
| `assets/poses/` | 158 | Qwen-Image-Edit-2509 on Colab (Apache-2.0 model; pages read 2026-11-16) | model terms read; output terms not separately confirmed |
| `assets/weapons/` | 12 | same | same |
| `assets/ui/` | 88 | shield slabs from the same pipeline; the rest not documented | PARTLY unknown |
| `assets/units/` | 32 | four originals made with Gemini from free prompts (owner statement, 2026-11-16); the rest not documented | unknown, owner to confirm |
| `assets/portraits/` | 16 | not documented | unknown, owner to confirm |
| `assets/env/` | 47 | not documented | unknown, owner to confirm |
| `assets/sprites/`, `assets/fx/`, `assets/avatars/` | 72, 71, avatars | baked or cropped from the folders above | follow their sources |
| `assets/fonts/` | 10 | Google Fonts, SIL Open Font License 1.1 with the licence files | OK |
Deleted on 2026-11-24 at the owner's word: the 8-second screen recording and `ref_bar_from_video.png` (a sketch only, used for nothing that ships).
The art folders marked "unknown" need the owner's statement of how they were made before the README may say the pictures are original or credited. Record: `docs/ASSET_PROVENANCE.md`.
