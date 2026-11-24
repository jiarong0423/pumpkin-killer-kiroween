# Kiro task 60 — the remaining controls fixes from task 58 (write the patch spec, implement what is isolated)

Read: docs/kiro_58_recommendations.md (rank list), (not published) (newest rows last), index.html, (not published)

Already fixed by the main line: P0-1, P1-1, P1-3 (Space), P1-4 (heal), P1-5 (wind label), P1-9 (result delay), P1-11 (mouse buttons). Open items to cover: C3 (a mouse / touch exit from Move and Defend: a small cancel plate), P1-6 (angle text under the pips), P1-7 (shield counter only for the knight), P1-8 (HUD text at least 20 canvas px), P1-12 (power on the thrower: a short arc or bar above the head while charging), P1-13 (help text), P1-14 (low HP colour), P2-1..P2-7 (reset hold-to-confirm, inert slot titles, 攻擊 menu item, enemy-turn cue, debug keys behind ?debug, last power, distance in steps), and touch targets of at least 44 px (section 4).

Write `(not published)`: for EACH item a ready-to-apply patch (exact old text and new text, with the surrounding lines) against the CURRENT index.html and css/dock.css, grouped so one group can be applied and tested at a time, with the one check that proves it (a node or page check). Do not edit index.html. Say what you could not verify.
