# Orientation, frozen (owner 2026-11-16: "fix what you are sure of so nothing needs another flip")
| Object | Decision | Where it is pinned |
|---|---|---|
| All hero pictures | native art faces LEFT; the page mirrors the player's side | `ART_FACES_RIGHT` in `index.html`, `shared/orientation_frozen.json` |
| Hunchback (all frames) | mirrored once in code (`ART_FACES_RIGHT.unit_hunchback = true`) | same |
| Hunchback wind-up picture | the file itself was mirrored on 2026-11-16 (the owner saw the charge pose reversed) | sha256 in the frozen file |
| Wind ghost | bound to the wind: mirrored by the wind sign, wisps follow, no number or chip, placed below the sign board text (left when the wind blows right) | code markers in the frozen file, `scripts/test_orientation_frozen.js` |
| Avatars (`assets/avatars/*`) | installed as generated (three-quarter turn toward the viewer's left), plates by `scripts/install_avatars.py` | not part of the hero-facing set |
Check: `node scripts/test_orientation_frozen.js` (in the suite), `python3 -B scripts/freeze_orientation.py` (prints differences). Change on purpose: look at the picture, then `python3 -B scripts/freeze_orientation.py --write`. A Kiro hook runs the check when a hero picture is saved.
