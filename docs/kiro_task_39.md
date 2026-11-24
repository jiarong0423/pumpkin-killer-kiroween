# Kiro task 39 - design WHEN an ultimate may be used, and the ultimate MAPPING table ("link-up" table)

## Owner words (2026-11-09)
"An ultimate cannot be used at any time (不能隨時放大招)." "Make a link-up (連連看, a matching table) of all the ultimates I just described." "Kiro, design it."

## Owner rules already confirmed (all in (not published), newest rows at the bottom; they win over every other document)
- Normal attack: ONE shot at ONE unit. Ultimate: hits MULTIPLE units.
- Energy: THREE successful hits light three pips above the unit's head; only then the ultimate can be triggered; each player counts their own; at most 2 ultimates per match.
- Damage: each unit hit by an ultimate takes 1.5 x the class's normal attack. Structure: a TRIGGER hit first, then follow-up strikes; the trigger hit is a normal hit and is not part of the 1.5 x.
- Grim reaper: attack = thrown skulls; ultimate = after a skull hits, three scythe slashes (single-target combo for now), total 1.5 x, split evenly.
- Cat-bat: normal = one shuriken; the 5-shuriken scatter is its ultimate (already built: each shuriken 1.5 x normal / 5).
- Ghost bride: attack = SOUND WAVES (an area effect). Hunchback: bell-tower character. Knight: bouncing shield (die 1 to 6 collisions, damage split evenly). Skeleton: javelin with frost curse (the unit hit attacks 30% weaker for its next 2 throws). Wizard: cannon.
- At least 6 classes, at most 4 v 4 on the field; one character chosen at the start; screen stays clean; free CC0 sound only; art made on Colab.

## Read (read only)
docs/ultimates_design.md (your own task 35 designs: they used a 4-pip bar and per-class ideas that may now conflict with the owner rules above: correct them), docs/roster_design.md, docs/converge_characters.md, docs/review_reconcile.md and (not published) if present, docs/sound_mapping.md, index.html (energy, ultUsed, executeThrow ultimate branch for the cat, the click action menu code), js/particles.js preset names.

## Do exactly this
1. Write docs/ultimate_rules.md: WHEN an ultimate may be used, because it must NOT be usable at any moment. Cover: only on the owner's own turn; the exact input (click menu entry vs button, and what the pips do when ready); must it be armed before aiming and does it REPLACE that turn's normal attack; may it be used after moving (dice), after defending, while a floating shield is placed; at most one per round; any lockout (e.g. not in round 1, not two rounds in a row); what happens if the unit is hit or killed while armed; how the opponent and the sub-agent opponents see it (public state field names only); how the AI decides to use its own; what the UI shows (ready cue, armed state, used count 0/1/2, cancel); and what blocks it (frozen, weakened, dead). Give a recommendation, 2 alternatives with trade-offs, and a table of edge cases with the rule for each. Keep rules simple enough to explain in two short sentences on the screen.
2. Write docs/ultimate_mapping.md: the LINK-UP table. One row per class (skeleton, wizard, cat-bat, knight, ghost bride, hunchback, grim reaper): ultimate name (Traditional Chinese plus English), the owner's own words that define it (quote the row of the owner log, or write "owner has not specified; Kiro proposal"), trigger hit, follow-up strikes, targets (who is hit), damage math under the 1.5 x rule with a worked example from that class's normal damage, controls, effects (existing preset or sprite names, new ones listed), sounds (existing event names or new), art needed (Colab asset names), engine status (built / design only), and a "conflicts with owner rules?" column (yes/no, what to change). Add a second table linking each owner statement to the rows that implement it (the matching in the other direction), so nothing the owner said is left unlinked, and a third table listing every conflict between docs/ultimates_design.md and the owner rules, with the corrected value.
3. Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download or create images.
4. Finish with a 6-line summary and say what you could not verify.
