# Kiro task 94 — workstream W9: close the cheap asset gaps (CSS fallbacks and sound options)

`python3 -B scripts/release/check_asset_refs.py` reports these real missing references: three `.woff` fonts in `css/fonts.css` (`pk-display-cjk-900.woff`, `pk-body-400.woff`, `pk-body-700.woff`; the `.woff2` files exist and `scripts/build_fonts.py` builds `.woff` only when the brotli package is missing), and three sounds `(not published)`, `ultimate_ready_chime.ogg`, `item_pickup.ogg`. Pictures are not yours (the owner makes them on Colab).

Read: `css/fonts.css`, `scripts/test_fonts.py`, `docs/audio_sources_verified.md`, `docs/audio_sources.md`, `docs/sound_mapping.md`, `assets/audio/_licenses` (names only), and how `js/audio.js` handles a missing file (grep for the three names).

Do exactly this:
1. `css/fonts.css`: remove the three dangling `.woff` fallback `src` entries only if `.woff2` is listed for the same face; keep everything else byte for byte. Then run `python3 -B scripts/test_fonts.py` and `python3 -B scripts/test_preload_links.py`; both must still print OK. Edit nothing else in the CSS.
2. Sounds: do not generate or download anything. For each of the three names, find in `docs/audio_sources_verified.md` or `docs/audio_sources.md` a CC0 source already verified there that fits, and write `docs/audio_gap_options_20261115.md` (max 40 lines): per name, the candidate (source page, licence as recorded there, duration), whether `js/audio.js` falls back silently when the file is missing (cite the line), and a recommendation (add the file, or drop the reference). If no verified source exists for a name, say so.

Write `(not published)` (max 25 lines): what changed, commands with last output lines, what you did not verify. Touch no other file. No network, no git.
