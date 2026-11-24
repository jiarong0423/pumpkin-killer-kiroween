# Dock design: requirements

Scope: the bottom dock of the game screen. Files: `css/dock.css`, `(not published)`, `docs/dock_design.md`, `docs/dock_asset_requests.md`.
Wiring into `index.html` is out of scope for this spec (separate task, `index.html` is locked).

Terms: **dock** is the element `#bottom-dock`. **Shot button** is a `.skill-btn` inside `.skill-bar`. **Hero chip** is a `.hero-tab`. **Click menu** is the move / attack / defend menu above the
player's character. **Ground line** is canvas y = 860 of 1080, 79.6 % of the container height. **Tier L / M / S** are container widths above 1200 px, up to 1200 px, and up to 900 px.

## R1 Content

1. The dock shall contain the shot buttons `#skill-normal`, `#skill-double`, `#skill-heavy` and `#skill-heal`, with the badges `#badge-double`, `#badge-heavy` and `#badge-heal`.
2. The dock shall contain the four hero chips.
3. The dock shall contain a reset button.
4. The dock shall show the active character's portrait, name and HP bar (tier L), and the HP bar with its number (tiers M and S).
5. The dock shall show a read-only angle value and a segmented power meter of 20 segments.
6. The dock shall show an ammo slot and a special-weapon slot.
7. The dock shall provide a Lock button.
8. The dock shall not contain a Move button, an Attack button or a Defend button.

## R2 No duplication with the click menu

1. The dock shall not offer any action that the click menu already offers (move, attack, defend).
2. The element `#skill-shield` and its badge `#badge-shield` shall remain in the DOM with the class `dock-hidden`, so that existing code reading them does not fail.
3. While `defendMode` is true, the dock shall show the Lock button, and activating it shall call `toggleShieldDefend()`.
4. While `defendMode` is false, the Lock button shall be hidden (`hidden` attribute).
5. The dock shall not draw or control an aim line.

## R3 Layout and clean screen

1. The dock shall sit below the ground line in every supported container width (720 px and up).
2. Where the container is wider than 1200 px, the dock shall be 104 px high and 12 px above the container bottom.
3. Where the container is 1200 px or narrower, the dock shall be 88 px high and 8 px above the bottom, and the portrait and candles shall be hidden.
4. Where the container is 900 px or narrower, the dock shall be 76 px high and 6 px above the bottom, and the grooves and rivets shall be hidden.
5. The dock shall not rise above the ground line, except for decorative candles that rise at most 14 px in tier L.
6. The dock shall take pointer events, so that a press on it does not start a charge on the field.
7. Decorative elements shall have no pointer events.

## R4 Touch and text

1. Every interactive element of the dock (shot buttons, hero chips, Lock, reset) shall be at least 44 px wide and 44 px high in every tier.
2. Where the device has hover, hover styles shall apply; where it does not, hover styles shall not apply.
3. The dock shall use no text smaller than 12 px.
4. The dock shall keep a contrast ratio of at least 4.5:1 for text under 24 px, and 3:1 for text of 24 px bold or larger.
5. The dock shall not convey state by colour alone: HP shall show a number, a cooldown shall show a sweep and a badge number, a disabled button shall change opacity and cursor as well as colour.

## R5 Button states

1. Each shot button shall have distinct styles for normal, hover, active (selected), pressed, disabled, cooldown and keyboard focus.
2. When a shot button has the class `.cooldown`, the dock shall draw a clockwise dark sweep sized by the custom property `--cd` (1 = just used, 0 = ready).
3. When a shot button has the class `.ready` and is not `.active`, the dock shall draw a breathing violet ring.
4. When a shot button is `.locked` or `:disabled`, the dock shall ignore hover and press styles on it and show the `not-allowed` cursor.
5. Where the hero chip has the class `.active`, the dock shall style it cyan, and the selected shot button orange, so the two meanings never share a colour.

## R6 Meters

1. When the custom property `--power` on `.power-meter` is set to a value from 0 to 100, the dock shall light that fraction of the segments from the left.
2. When the custom property `--hp` on `.dock-hp` is set to a value from 0 to 100, the dock shall fill that fraction of the bar.
3. Where `.dock-hp` has the class `.is-low`, the dock shall colour the fill red and pulse it.
4. The power meter shall not show a prediction of where the shot will land.

## R7 Throw drama

1. When the portrait has the class `.is-charging`, `.is-shout` or `.is-hit`, the dock shall play a charging jitter, a release flash, or a red hit shake respectively.
2. When the dock has the class `.is-my-turn`, the portrait ring shall breathe in cyan.

## R8 Visual language

1. The dock shall use only CSS: gradients, borders, box-shadows, pseudo-elements and custom properties. It shall not load images or external fonts.
2. The dock shall use the palette defined by the custom properties at the top of `css/dock.css`, with one meaning per colour.
3. While `prefers-reduced-motion: reduce` is set, the dock shall stop all animation and shorten transitions to near zero.
4. The dock shall not animate any property faster than 120 ms.

## R9 Compatibility

1. The stylesheet shall keep the existing ids and classes: `#bottom-dock`, `.skill-bar`, `.skill-btn`, `.active`, `.locked`, `.count-badge`, `.btn-tip`, `.hero-selector`, `.hero-tab`, and the ids in R1.1 and R2.2.
2. New elements shall use new class names that start with `dock-` or `power-`.
3. Every rule of the stylesheet shall begin with `#bottom-dock`, or be inside a `@keyframes` or `@media` block, so that it wins over the inline `<style>` of `index.html` regardless of load order.
4. Where the old markup carries inline colours on `.skill-bar` or `.skill-btn`, the stylesheet shall override them.
5. The hero chip children shall have `pointer-events: none`, so `event.target` in `switchHero()` is the button.
6. The preview page shall not load or call any game code.

## R10 Assets

1. The asset request list shall contain at most 12 items, each with a name, size, content, one-sentence prompt and place of use.
2. No image shall be created by code to stand in for a Colab image.
