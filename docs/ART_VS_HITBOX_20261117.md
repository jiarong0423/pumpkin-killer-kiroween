# Drawn art versus the hit box (2026-11-17)

Method and draw rule: header of `scripts/probe_art_vs_hitbox.py` (numbers from the page's own draw code, the 1024 px pictures and the box in `shared/heroes.json`). Unit 220, feet line y = 0, centre x = 0, box 140 x 190 (reaper 114 x 165).

| Hero | Picture | Drawn width | Art x range (opaque pixels) | Art height above the feet (low to high) | Box (width x height) | Share of the art inside the box |
|---|---|---|---|---|---|---|
| skeleton | 1024x1024 | 220 | -90 to 91 | 1 to 176 | 140 x 190 | 95.2% |
| wizard | 1024x1024 | 220 | -73 to 62 | -4 to 192 | 140 x 190 | 99.2% |
| bat | 1024x1024 | 220 | -70 to 74 | -0 to 188 | 140 x 190 | 99.6% |
| knight | 1024x1024 | 220 | -83 to 94 | -4 to 188 | 140 x 190 | 93.1% |
| reaper | 1024x1024 | 220 | -76 to 75 | -10 to 183 | 114 x 165 | 84.7% |
| bride | 1024x1024 | 220 | -82 to 83 | -10 to 169 | 140 x 190 | 92.1% |
| hunchback | 1024x1024 | 220 | -93 to 92 | -10 to 174 | 140 x 190 | 88.2% |
| hag | 1024x1024 | 220 | -47 to 85 | -1 to 189 | 140 x 190 | 97.0% |

The share is below 100 percent because the held weapon, cape and hood stick out sideways and the picture is drawn 15 px below the feet line; the hit reach adds the projectile radius on top of the box (see `docs/HIT_RANGE_MEASURED_20261117.md`).
