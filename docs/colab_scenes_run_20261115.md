# New scene run sheet — 2026-11-15

1. Queue `colab/jobs_scenes_20261115.json` in the Q3 runner with `VARIANTS = 1`; each job takes about seven minutes.
2. Run outdoor `bg_ruined_church` and `bg_abandoned_school` first; the owner chooses each outdoor or `_b` interior alternative before installation.
3. For every output, verify 16:9, the same horizon height and open middle battlefield band as `bg_graveyard`, and clear top and bottom UI space.
4. Reject text, letters, digits, signs, watermarks, characters, weapons, UI, copied graveyard landmarks, brands, and any likeness to a real location.
5. Reject any output that does not look original or does not retain the deep blue-violet, restrained orange, and cyan cartoon scene language.
6. After owner approval, copy the chosen PNG to `(not published)`.
7. A later page task must add one `SCENES` entry for `{ id: "church", name: "廢墟教堂 / Ruined Church", bg: "assets/env/bg_ruined_church.png" }` and one for `{ id: "school", name: "荒廢學校 / Abandoned School", bg: "assets/env/bg_abandoned_school.png" }`.
8. That later page task must add a preload link for each chosen scene background, while leaving the existing start-screen cache behavior intact.
9. After its page changes and the approved files are present, run `python3 -B scripts/release/check_asset_refs.py`.
10. Do not edit `index.html` as part of this art-queue task.
