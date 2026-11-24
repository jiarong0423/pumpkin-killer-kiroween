# Bottom dock design (Kiro task 19)

Status: proposal. Files: `css/dock.css` (stylesheet), `(not published)` (look), `docs/dock_asset_requests.md` (Colab images),
`.kiro/specs/dock-design/` (spec). `index.html`, `assets/`, `js/`, `scripts/` were not touched. Nothing was rendered: see "Not verified" at the end.

Owner constraints (2026-11-09) that drive this design: the screen must not be messy; the look must have texture and feel premium, Halloween magic like a wizard school;
the click menu above the character (move / attack / defend) already exists and the dock must not duplicate it; attack is by pointer (move the pointer to aim, press and hold
on the field to charge); no aim line, the thrown path is shown after the throw.

## a. What the mockup's bar contains (`(not published)`, 1672x941)

The bar is a dark stone slab with an iron-and-wood rim, about 120 px tall in a 941 px picture (12.7 % of the height), below the graveyard ground. Left to right:

| # | Item | Details seen in the mockup |
|---|---|---|
| 1 | Portrait frame | About 150 px square, the active unit's face (pumpkin wizard with hat), thick gold-brown frame with a metal corner. |
| 2 | Name and HP | Class name "巫師炮手" in white serif, "85/85" below, a green HP bar underneath. |
| 3 | Throw button | Dark rounded tile with a carved pumpkin icon and the label 投射. Selected: orange rim and warm glow. |
| 4 | Move button | Same tile, boot icon, label 移動. Unselected: grey stone, no glow. |
| 5 | Defend button | Same tile, shield icon, label 防禦. Unselected. |
| 6 | Divider | A thin carved vertical line. |
| 7 | Angle selector | Label 角度, a dark pill with left and right triangle arrows and "55°" in large gold numerals. |
| 8 | Power meter | Label 力度, a dark pill with 12 square orange segments (about 5 lit), a flat segmented bar. |
| 9 | Ammo slot | Label 彈藥, a small dark square socket with the pumpkin cannonball icon. |
| 10 | Special-weapon slot | Label 特殊武器, an empty dashed-outline socket. |
| 11 | Divider | A second carved line. |
| 12 | Lock button | One big orange plate, label 鎖定, gold rim, brightest object on the screen. |

Accents: candles and carved pumpkins stand on the ground at the bottom-left and bottom-right of the picture, outside the slab. The slab itself has rivets at the corners, a
thin rim light on the top edge, and no text smaller than the unit HP numbers. The top bar uses the same dark-glass and gold-rim language, so the bottom bar is one of a set.

## b. Proposed dock for the current game

### b1. What each current control does, and what the click menu already covers

| Current control | What it does (read from `index.html`) | Click menu covers it? | Decision |
|---|---|---|---|
| `#skill-normal` | `selectSkill('normal')`: normal throw is the selected shot | No | KEEP |
| `#skill-double` + `#badge-double` | selects the double shot, 2 charges (`skillCharges.double`) | No | KEEP |
| `#skill-heavy` + `#badge-heavy` | selects the heavy shot, 2 charges | No | KEEP |
| `#skill-heal` + `#badge-heal` | instantly heals +35 HP, 2 charges (does not select) | No | KEEP |
| `#skill-shield` + `#badge-shield` | `toggleShieldDefend()`: first press enters defend placement, second press locks the shield | Entering Defend: YES (menu item "防禦"). Locking: NO | REMOVE from view, KEEP in the DOM (hidden). The lock step moves to the new Lock button |
| Hero tabs `.hero-tab` (4) | `switchHero(key)`: change the class you control (prototype class picker) | No | KEEP, restyled as 44 px chips |
| Move button (🎲, no id) | `moveWithDice()` | YES (menu item "移動") | REMOVE |
| Reset button (🔄, no id) | `resetGame()` | No | KEEP, small, far right |
| (none) | attack | YES (menu item "攻擊" and press-hold on the field) | nothing to add |

Why `#skill-shield` stays in the DOM: `toggleShieldDefend`, `cancelDefendMode`, `lockShield` and `updateShieldButton` read or write its `classList`, `title` and the text of `#badge-shield`.
Deleting it would throw. `dock.css` hides it with the class `dock-hidden`.

Why a Lock button exists now: the menu's "防禦" calls `toggleShieldDefend()`, which enters placement mode. The player then drags the shield and must press the shield button again to lock
(message: "再按一次🛡️鎖定"). With the shield button hidden, that confirm needs a home. The dock's orange Lock button is that home: it is hidden (`hidden` attribute) except while `defendMode` is true,
and its click calls `toggleShieldDefend()`. The same button becomes the round Lock of the 4 vs 4 mode later. This is not a duplicate of the menu: the menu chooses, the Lock confirms.

### b2. Items to ADD from the mockup

| Item | Class | Source of data (public state only) | Notes |
|---|---|---|---|
| Portrait | `.dock-portrait` | `currentHero` | Emoji glyph now, real art later via `--portrait-img`. Doubles as the attacker "big head" cut-in (states `.is-charging`, `.is-shout`, `.is-hit`). |
| Name + HP bar | `.dock-name`, `.dock-hp` (`--hp` 0..100) | `player.hp / player.maxHp` | Green above 60 %, amber `.is-mid` 30 to 60 %, red `.is-low` below 30 % (pulses). |
| Angle readout | `.dock-angle` | `playerAngle` (25..80) | Read-only. The pointer sets the angle, so the mockup's arrows are dropped. |
| Power meter | `.power-meter` (`--power` 0..100) | `chargePower` | 20 segments, fills while the player holds. Steps of 5 look best. Not a preview of the shot: it shows only the current charge. |
| Ammo slot | `.dock-ammo` | `currentHero` weapon | Icon of the class weapon (cannonball, shuriken, spear, small shield). Optional count (open question: bat bag count). |
| Special-weapon slot | `.dock-special` (`.is-full`) | airdrop item slot | One slot, a new crate replaces the old item (decided in `game_mode.md`). Dashed violet socket when empty. |
| Lock | `.dock-lock` | `defendMode` | See b1. |

### b3. Layout

The dock is below the ground line. The canvas ground is at y = 860 of 1080, which is 79.6 % of the container height. The container is 16:9 and capped at 1400 px wide today,
so on a 1920x1080 monitor the game is 1400x787 and the dock uses tier L. If Phase B (full-screen mobile) lifts the cap, only the size variables at the top of `dock.css` change.

Groups, left to right: **hero cluster** | carved groove | **shot buttons** | groove | **readouts (angle, power)** | groove | **slots (ammo, special)** | **Lock (when needed)** | **reset**.

#### Tier L: container wider than 1200 px (1920x1080 monitor, container 1400x787)

Dock: 96 % of the container, max 1280 px, 104 px high, 12 px from the bottom, wood frame 6 px, inner padding 6 px, gap 10 px.

| Item | Size | Notes |
|---|---|---|
| Portrait | 80x80 | Gold-brown frame 3 px. |
| Name row | 182x20 | Name 17 px serif left, HP number 14 px right. |
| HP bar | 182x12 | |
| Hero chips x4 | 44x44 each, 2 px apart | Glyph 20 px + 2-character name 12 px. |
| Shot buttons x4 | 60x76 each, 6 px apart | Icon 25 px, label 12 px, count badge 22 px round. |
| Angle plate | 88 wide | Label 12 px, value 28 px. |
| Power plate | flexible, 110 to 320 wide | Label 12 px, value 16 px, meter 22 px high, 20 segments. |
| Ammo slot, Special slot | 60x60 each, 8 px apart | Label 12 px above. |
| Lock | 120x68 | Label 24 px. Shown only when needed. |
| Reset | 44x44 | Rightmost, dimmer, away from the shot buttons so it is not hit by mistake. |
| Candles | 9x18, stick up 14 px | Two, top corners. Decoration only. |

Minimum width check (Lock visible): hero cluster 80+10+182 = 272, shot buttons 4x60+3x6 = 258, readouts 88+8+110 = 206, slots 2x60+8 = 128, Lock 120, reset 44 = 1,028 px.
Add 8 gaps of 10 px, 3 grooves of 3 px and frame plus padding 24 px: 1,141 px. The dock is 96 % of the container, so at the tier edge (1,201 px) it is 1,153 px wide. It fits by 12 px with the
power meter at its minimum. Without the Lock there are 142 px to spare.

#### Tier M: container 901 to 1200 px

Dock 88 px high, 8 px from the bottom. The portrait and candles are dropped (the active hero chip glows and stands in). The HP number moves inside the bar (16 px high). Shot buttons 56x68, slots 52x52, Lock 96x56.
Known limit: widths at 901 px are 182 + 242 + 190 + 112 + 44 = 770, plus 7 gaps of 8, 3 grooves and frame = 855 px in an 865 px dock, so it fits without the Lock. With the Lock (+104 px) it overflows
below a container width of about 1,000 px. The Lock appears only during shield placement, so the exposure is small. If it matters, the fix is to hide the special slot while the Lock shows.

#### Tier S: 900 px and below (the 800 px pane)

Dock 76 px high, 6 px from the bottom, frame 4 px, padding 4 px, gap 6 px, grooves hidden, rivets hidden.

| Item | Size at 800 px |
|---|---|
| Hero chips x4 | 44x44 (row 182 wide) with a 14 px HP bar above |
| Shot buttons x4 | 44x60, 4 px apart, icon 22 px, label 12 px |
| Angle plate | 56 wide, value 20 px |
| Power plate | 80 to flexible, meter 16 px, 20 segments |
| Ammo, Special | 44x44 |
| Lock | 60x48 |
| Reset | 44x44 |

Width at 800 px (container 800, dock 768): 182 + 188 + 142 + 92 + 44 = 648, plus 5 gaps of 6 and frame plus padding 16 = 694 without the Lock. With the Lock (60 px plus one more 6 px gap) it is 760,
which fits in 768 only because the grooves are hidden in this tier.

Smallest supported pane: about 720 px wide. Below that the dock rises into the characters' feet.

#### Clearance above the dock (px between the ground line and the dock top)

Computed as container height x (1 - 0.796) minus bottom margin minus dock height. Container height = width x 9/16.

| Container width | Tier | Ground line y | Dock top y | Clear gap |
|---|---|---|---|---|
| 1400 | L | 626.8 | 671.5 | 44.7 |
| 1201 | L | 537.8 | 559.6 | 21.8 |
| 1200 | M | 537.3 | 579.0 | 41.7 |
| 901 | M | 403.4 | 410.8 | 7.4 |
| 900 | S | 403.0 | 424.0 | 21.0 |
| 800 | S | 358.2 | 368.0 | 9.8 |

The candles rise 14 px above the dock, which leaves at least 7 px of gap at 1201 px. They are hidden in tiers M and S.

### b4. States for every button

Applies to `.skill-btn` (shot buttons) and, with the noted differences, to `.hero-tab` and `.dock-lock`.

| State | Look | Trigger |
|---|---|---|
| Normal | Stone tile, iron rim 2 px, inset bevel, 3 px dark drop edge, icon with drop shadow, label in dim lavender | default |
| Hover (pointer devices only, `@media (hover: hover)`) | Lifts 2 px, rim turns candle gold, 16 px gold glow, label brightens | `:hover` |
| Active (selected) | Warm orange inner glow, gold rim, label gold. Does not lift | class `.active` (set by `selectSkill`) |
| Pressed | Sinks 2 px, inner shadow, drop edge shrinks to 1 px | `:active` |
| Disabled | 50 % opacity, greyscale, no hover, `not-allowed` cursor | `:disabled`, `.locked` |
| Cooldown | Dark clockwise sweep over the tile, `--cd` from 1 (just used) to 0 (ready), no hover | class `.cooldown` + `style="--cd:0.5"` |
| Ready pulse | Violet ring around the tile breathes (1.8 s) when a charge is available and the tile is not selected | class `.ready` |
| Focus | 3 px cyan outline, 3 px offset | `:focus-visible` |
| Count badge | Red wax-seal circle top-right, gold rim, white number 12 px. Grey when 0 (`.is-empty`) | `.count-badge` |

Hero chip: active is cyan (not orange) so "who I am" and "which shot" never share a colour. Lock: orange plate, gold rim, ready pulse 1.8 s, pressed sinks 3 px, disabled greyscale.
HP bar: low HP pulses. Special slot: `.is-full` draws a solid violet rim that breathes.

Touch targets: every interactive element is at least 44x44 px in every tier (CSS `min-width` / `min-height` enforce it). Hover effects are wrapped in `@media (hover: hover)` so a tap never leaves a stuck hover.

### b5. How the dock stays out of the way

- The dock only occupies the strip under the ground line (table above). Nothing in the dock rises over the playfield except two 14 px candles in tier L.
- Landing rings, HP bars, name tags and the click menu all live above the ground line. The click menu opens 318 px above the character (`MOVE_ROW_DY`), so it never meets the dock.
- The dock plate is solid and takes pointer events: pressing on it does not start a charge on the field.
- Fewer controls than today: 4 shot buttons, 4 hero chips and reset, instead of 5 skill buttons, 4 hero tabs, move and reset in three separate floating pills.

## c. Visual language

**Theme.** A wizard-school common room at night: aged stone slab in a wooden beam, candle light from above, ghost fire along the rim. Everything is drawn with layered CSS gradients, so nothing is flat.

**Materials**
- Stone: three-stop vertical gradient (`#2a2337`, `#1d1828`, `#120e1a`), diagonal chisel lines (repeating gradients at 97 deg and 8 deg), three soft blotches for weathering, a corner vignette.
- Wood: `#6c4526` to `#26160b` gradient with vertical grain from repeating gradients, used as the 6 px frame.
- Iron: rivets in the corners (radial gradients), rims on tiles `#6f6580`.
- Candle light: a warm radial wash at the top centre of the slab and two CSS candles with flickering flames (1.6 s loop, second candle offset by 0.7 s).
- Ghost fire: a cyan-to-violet line along the top edge that drifts sideways (7 s loop).

**Colour roles (one meaning each)**

| Colour | Hex | Used for |
|---|---|---|
| Candle gold | `#ffcf5a` | numbers, labels, hover rim, selected rim |
| Pumpkin orange | `#ff8a1f` | selected shot, power fill, Lock |
| Spectral cyan | `#5df2ee` | "me / my turn": active hero chip, portrait ring, focus ring |
| Spectral violet | `#a98bff` | "available / special": ready ring, special slot, portrait glow |
| Healing green / warn amber / danger red | `#62e88a` / `#ffb347` / `#ff5d6c` | HP bar only |
| Ink / dim ink | `#f6ecd8` / `#b9aecb` | text |

**Clean screen rules**
1. The dock never covers a character, HP bar, landing ring or the click menu (clearance table).
2. No panel, tooltip or tutorial text is added above the dock. Explanations go in `title` attributes.
3. One selected shot at a time. One glow colour per meaning. At most two things pulse at once (typically the Lock or ready ring, plus my-turn ring).
4. No aim line, no ghost trajectory. The power meter shows the charge only.
5. Decoration (candles, wisps, rivets) has no pointer events and drops out in tiers M and S.

**Motion.** Hover: lift 2 px + glow, 120 to 150 ms. Press: sink 2 px, 120 ms. Ready: ring or plate breathes at 1.8 s. My-turn: portrait ring 2 s. Throw drama on the portrait: charging jitters
1 px (180 ms loop), release flashes and scales to 1.1 (350 ms, once), hit tints red and shakes 4 times. HP low: bar brightens at 1 s. All animation stops under `prefers-reduced-motion: reduce`. Nothing on the dock animates faster than 0.12 s, so it never competes with the throw.

**Readability**
- Text colours on the dark recess: gold `#ffcf5a` on `#0c0913` is about 12:1; ink `#f6ecd8` on stone about 14:1; dim `#b9aecb` on `#1d1828` about 7:1. Lock text `#2a1204` on orange `#ec6a0e` is about 4.5:1 at 24 px bold (large text needs 3:1).
- Minimum font size is 12 px everywhere, including tier S. Values (angle, power, HP) are 14 to 28 px. Labels are bold serif with letter spacing.
- Meaning never relies on colour alone: HP always has its number, cooldown has the sweep plus a badge number, disabled has greyscale plus opacity plus a not-allowed cursor.
- Labels are two characters (普通, 雙發, 重彈, 回血, 彈藥, 特殊) so they fit the 44 px tiles. The mockup's 特殊武器 is shortened to 特殊.

## Integration notes for the main line (not done here)

1. Link `css/dock.css` after the inline `<style>`. Every rule starts with `#bottom-dock`, so order does not matter, but keep it after.
2. Replace the dock markup with the block in `(not published)` (everything inside `<div id="bottom-dock">`). Keep `#skill-shield` and `#badge-shield` (class `dock-hidden`).
3. `switchHero()` uses `event.target`. The new chips contain spans, so `dock.css` sets `pointer-events: none` on the chip children to keep `event.target` the button. Chips need their `onclick="switchHero('...')"` re-added.
4. `selectSkill()` removes `.active` from every `.skill-btn`, including the reset button, and `resetGame` has no active state, so this is harmless. It also sets `.active` by id `skill-<name>`, which the new markup keeps.
5. The inline styles on the old `.skill-bar` and on `#skill-shield` are overridden by `!important` rules in `dock.css`. Removing them from the markup is cleaner.
6. Each frame, a small `updateDock()` should set: `--hp` and the `.dock-hp-num` text, `.is-mid` / `.is-low`, `#dock-angle-value`, `--power` (rounded to 5), `.is-charging` on the dock and the portrait, `.is-my-turn`, badge numbers, `.locked` and `.ready` on shot buttons, and `lockBtn.hidden = !defendMode`.
7. `--portrait-img`, icon backgrounds and the frame images come from the Colab list in `docs/dock_asset_requests.md`. Until they arrive the emoji stay.

## Not verified

- I cannot render a page. I did not see `dock.css` or `dock_preview.html` in a browser. Sizes, widths and clearances above are arithmetic from the CSS values, not measurements. The owner should open the preview and judge.
- Emoji icons look different on each operating system; the 60x76 tile proportions were chosen without seeing them.
- The `conic-gradient` cooldown, `clip-path: inset(... calc(...))` power fill, CSS `mask-image` segments and `container-type` (preview only) need a current Chrome, Edge, Safari 16+ or Firefox. Not tested in any.
- Contrast ratios are estimates from the hex values, not measured with a tool.
- Whether the Lock at tier M under 960 px overflows depends on real font widths.
