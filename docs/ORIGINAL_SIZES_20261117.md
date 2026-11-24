# Original sizes versus now (2026-11-17)

Source of "original": commit `209812fe` (2026-11-16 16:01, before the phone-ratio pass `92efc12d` at 21:15) and `shared/size_frozen.json`. World is 1920 x 1080, ground y 860; world coordinates, physics and hit logic did not change in the phone work (`142feccc` only added the side padding `PAD` and subtracts it from pointer input). Only DRAWN sizes changed.

| Thing | Original | Now | Changed by |
|---|---|---|---|
| Unit art frame | 220 x 220 | 260 x 260 (`BODY_PX`) | `92efc12d`, owner asked for bigger characters |
| Hit box | 70 half-width x 190 high (reaper 57 x 165) | same | not changed |
| Projectile hit radius | `sqrt(len*thick)/2 - 20` | same | not changed |
| Projectile sizes (len x thick) | spear 210x33, cannon 40x40, shuriken 58x58, flame 150x55, cross 118x82, wave 170x170, axe 130x130, shield 62x92 | same | not changed |
| Bride wave ring (drawn) | `wLen * (0.14 + 0.26 t)` | times 260/220 | today, drawing only |
| HP bar | 150 x 13, 218 above the feet | same size, lifted by 40 | `BODY_LIFT` |
| Crate on the ground | 96 x 96 | 64 x 64 world px (never below 26 CSS px) | `92efc12d`, owner: too big |
| Crate carried by the ghost | 72 x 72 | 52 x 52 | `92efc12d` |
| Crate item icon | 34 px | 40 px (0.62 x crate, min 40) | today |
| HUD supply box | 52 px (`css/dock.css`) | 38 px minimum, 7.2 percent of the stage width (about 40 px at 800x360) | `142feccc`, today |

Known conflict: `scripts/test_size_frozen.js` fails 2 of 5 checks since `92efc12d` (it still pins the 220 frame and the old HP bar line). At `209812fe` it passed 5/5. The owner's record on 2026-11-16 said "character size is locked at 220"; the later request for bigger characters produced 260. One of the two must be updated: either the pin moves to 260, or the art goes back to 220.
