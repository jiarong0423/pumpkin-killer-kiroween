# Kiro task 19 - design the bottom dock (items / skills / hero bar) - design files only

## Why
The owner wants the bottom items (skill buttons, hero tabs, move / reset buttons) made refined, and wants YOU (Kiro) to design them. The ORIGINAL picture is the reference:
`(not published)` (the owner's concept mockup). Open it with the file read tool and study its bottom bar closely: a stone-and-wood frame with candle and ghost-fire accents, the active
character portrait at the left with name and HP bar, big action buttons (throw / move / defend), the angle and power readouts with a segmented power meter, an ammo slot, a special-weapon slot,
and one big orange "lock" button. The current game bar is much plainer (`index.html`, the HTML between `<div class="skill-bar">` around lines 170-220 and the `.skill-bar`, `.skill-btn`,
`.hero-selector`, `.hero-tab` rules in the `<style>` block).

## Do exactly this
1. Read `(not published)`, `docs/game_mode.md`, `docs/ROLES.md`, and the dock markup and CSS in `index.html` (read only). Note what each current button does (ids `skill-normal`, `skill-double`,
   `skill-heavy`, `skill-heal`, `skill-shield`, the hero tabs, move, reset) and which actions the new click-menu (click your character) already covers (move / attack / defend).
2. Write `docs/dock_design.md`: (a) what the mockup's bar contains, item by item; (b) the proposed dock for the current game: layout at 1920x1080 and at a small 800 px wide pane, each item with size,
   state styles (normal, hover, active, disabled, cooldown), spacing and a 44 px minimum touch target; what to REMOVE because the click-menu replaced it; what to ADD from the mockup (portrait, HP bar,
   power meter, ammo slot, special-weapon slot); (c) the visual language: Halloween magic, aged stone and wood, candle glow, spectral cyan/violet/gold accents, a clean screen (nothing may cover the
   characters), motion (hover glow, press depress, ready pulse), and readability rules (contrast, font sizes).
3. Write `css/dock.css`: a complete, drop-in stylesheet for the proposed dock using CSS only (gradients, borders, box-shadows, pseudo-elements, CSS variables, no external fonts or images).
   Keep every existing id and class name so `index.html` keeps working; new elements get new classes. Include `@media (max-width: 900px)` rules.
4. Write `(not published)`: a standalone page that links `../css/dock.css` and contains the proposed dock markup with sample data, so the owner can open it and judge the look. No JavaScript needed except
   a few lines to toggle the active states. It must not touch the game.
5. Write `docs/dock_asset_requests.md`: the images that would make the dock look premium and that must come from Colab (never faked with code): for each, a name, size, what it shows, a one-sentence generation prompt,
   and where the dock would use it (e.g. stone-and-wood frame, candle, button plate, portrait frames, power-meter segments, ammo icons). Keep the list to at most 12 items, ordered by visual impact.
6. Write the spec `.kiro/specs/dock-design/` (requirements in EARS form, design, tasks). Tasks small and checkable.
7. Do not touch `index.html`, `assets/`, `js/`, `scripts/`. Do not use git. Do not create images. You may run project test scripts but nothing else in the shell.
8. Finish with a 6-line summary and say what you could not verify (you cannot render the page; say so).

## Constraints from the owner (2026-11-09)
- The screen must not be messy; the look must have texture and feel premium, Halloween-magic like a wizard school.
- The click menu above the character (move / attack / defend) already exists; the dock should not duplicate it. Attack by pointer: move the pointer to aim, press and hold on the field to charge.
- No aim line. The thrown path is shown after the throw.
