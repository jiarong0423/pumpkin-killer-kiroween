# Direction check, 2026-11-16 (answer to "has the direction drifted?"; sources: the owner's pasted outside review of the recording, the contest rules summary in it, the repository facts below)

## Facts checked in the repository
- First commit 2026-10-31, after the 2026-10-30 eligibility start. `.kiro/` is tracked (102 files) and not ignored.
- Deadline: Kiroween 2026-12-04 14:00 Pacific (= 2026-12-05 06:00 Taiwan). QNX runs to 2026-12-15 and overlaps; the outside review calls QNX the owner's better chance, so this game gets one focused feature, not new scope.

## The core (MVP): three things only
1. Cross-device, no-install play between people (phone and computer), a human always on the field; an AI can take an empty seat (no AI against AI; owner, 2026-11-16).
2. Balance proved by tests and simulation (property tests: damage never negative, every match ends, no hero or pairing wins by numbers alone), written up for the Kiro section.
3. Legible on a phone: small text, character size, HP bars, avatars, the first ten seconds of the video.

## What is on the line and what has drifted
| Work | Verdict |
|---|---|
| Seat assignment, relay client, determinism, round hash, shared hero table | ON the line (they are what makes cross-device play and an AI seat real). Do next, in this order: phone legibility, same-screen seats with an AI seat, then relay |
| Balance numbers, burn, knight bounce fix, harness playtests, Kiro 170 and 171 | ON the line (balance evidence). Stop after Kiro 170 finishes: no more number rounds |
| Start screen, avatars, nun placeholder, blurbs, empty boxes | ON the line (first ten seconds), done |
| Hero names, status icon debate, ultimate multiplier tuning, weather polish, fog effect, class_stats rebuild details, licence paperwork beyond what a public export needs | DRIFT risk: parked in `(not published)` P2 and "decided not to do"; do only what blocks the contest (credits, privacy gate) |
| New heroes, scenes, mechanics | OUT (owner: eight heroes are enough) |

## Next 1 to 2 nodes
1. Phone legibility (rotate hint, canvas text and bars scale with the display, touch target size).
2. Seats: same-screen human against human, an AI seat, a "switch sides" curtain between human turns; the relay waits until this works.

## Update 2026-11-16 (owner: do everything, Kiro the majority)
- The UI itself moves to Kiro through steering and specs (`.kiro/steering/ui_aesthetics.md`, `.kiro/specs/ui-polish`, `.kiro/specs/seats-and-items`): Kiro tasks 178 (UI), 179 (property tests and the Kiro usage document), 180 (asset pipeline: steering, checker, manifest, hook). The main line only verifies and integrates.
- Share of code lines added today: Kiro 54 percent in the first three hours, 81 percent from 03:00 (rough: lines undercount the main line's verification, art and review work). Roles are disclosed plainly in `docs/KIRO_USAGE_20261116.md` (task 179).
- Pictures: generated with Qwen-Image-Edit on Colab by the owner's pipeline and disclosed as such; Kiro owns the art rules, naming, manifest, checks and loading. The licence of the generation model for contest and public use must be confirmed by the owner; it is recorded as "to be confirmed" in `docs/ASSET_PROVENANCE.md` and `.kiro/steering/art_pipeline.md`.
- OPEN OWNER DECISION: contest category. An outside review argued for Frankenstein (Python deterministic engine, PWA, relay, MCP agents, golden vectors stitched together; mostly Kiro's work) instead of Costume Contest (judged on the interface, mostly not Kiro's work). The five scoring criteria are the same in every category. Nothing about the submission was changed; the owner chooses.
- SECOND OPEN CATEGORY OPTION (outside review, 2026-11-16): Resurrection ("Flash died and with it the whole era of artillery games; we bring the idea back with a PWA, cross-device play, MCP agents and a reproducible engine"). It reads better in one sentence than Frankenstein and the fence in the middle echoes the original wall. Cautions it raises, now written into `.kiro/specs/cross-device/`: never name or show the original game (the page title still says "classic cat-and-dog artillery feel" in Chinese and must go; gap queue row 25); the video must show the NEW part (two devices and an AI on one table, scan a QR code and be playing in seconds, a measured join time); the cross-device basics must be solid (finger drag, readable sizes, reconnect, same turn results on both screens, which the determinism contract and round hash support). The owner chooses the category.

## Plan of record (owner pasted, 2026-11-16)
Core sentence: a human starts the match, an empty seat can be filled by an AI; phone and computer join by a web address; no AI against AI. Category: Resurrection (Flash-era artillery games vanished with Flash; the modern browser brings the idea back and lets phone, computer and AI sit at one table), plus Best Demo. Never name or show the original game; say "inspired by Flash-era artillery games".
Status against that plan (2026-11-16, evening):
| Item | State |
|---|---|
| Cards 4 + 4, short chips, avatars, nun avatar, opaque start screen | DONE (3c0ff50, 6e2303f) |
| Turn timer not running on the selection screen | VERIFIED in code (`matchStarted` guard) |
| Empty supply boxes show a dash | DONE |
| Title "南瓜殺手" not cut, small texts, HP bars, phone checks, plates with avatar and status | Kiro 178 (spec ui-polish), running |
| Seat row ("Player 1 (you)", "Open: wait for a friend / add AI"), AI on the same rules, at least one human, symmetric items | spec seats-and-items written; Kiro task after 178 |
| Join by QR, reconnect, same results, measured join time, naming cleanup | spec cross-device written; Kiro task after the seats task |
| Property tests (damage not negative, every match ends, no forced win), Kiro usage text | Kiro 179, running |
| Art rules in steering, asset checker, manifest, hook | Kiro 180, running |
| Complete avatars and hunchback frame | Colab queue staged, waiting for the owner's Drive consent click |
| Public GitHub repo, About licence, hosted URL, video, Devpost text, category, model licence check | OWNER |

## Owner decision, 2026-11-16 (evening): category
The owner leans to the Resurrection track and thinks it has the better chance than the game track. Not yet submitted anywhere; drafts follow that framing: `docs/SUBMISSION_STORY_20261116.md` (Chinese draft; the owner finalises the public text). The page and the Kiro description keep the same story: Flash is gone, the idea is back, phone, computer and AI at one table.

## Owner confirmation, 2026-11-16 (late): Resurrection is OK (the idea is original, so it is allowed). Ultimate names fixed: knight 銅牆鐵壁 / Shield Wall, bat 天女散花 / Scattered Blossoms (散華 is the Japanese word, not used in the page). Knight name: 南瓜重裝盾衛 / Heavy Pumpkin Guard.

Owner check 2026-11-16: eligibility from Taiwan confirmed by the owner (earlier auditor note about the country list is closed). Licence of the image model: Apache-2.0 per model cards, owner has not yet opened the texts.
