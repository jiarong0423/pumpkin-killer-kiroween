# Ask: how do we make one-thumb touch aiming feel right in a browser artillery game?

Paste this whole file to the assistant you are asking. It is self-contained. Please answer the numbered questions at the end, with concrete numbers and short code where it helps, and say which parts are your opinion and which come from shipped games or documentation.

## 1. The game and the device
- A turn-based artillery duel in the browser (like Worms or Angry Birds). One HTML file, canvas 2D, plain JavaScript, no framework. A fixed world of 1920 x 1080 units; on a phone the stage is scaled to fit the height.
- Target device: Android phone, Chrome, landscape. CSS viewport about 756 x 360 px, devicePixelRatio 3 (screen 2268 x 1080 device px). The stage is 720 x 360 css px. The player's characters stand at the left (x from 10 to 35 percent of the stage width), the opponents at the right. A character is about 73 css px tall.
- Turn flow: the player chooses the throw ANGLE (25 to 80 degrees), then holds to charge POWER and releases to throw. Wind pushes the shot. A computer opponent plays the other side.

## 2. How the controls work today (the problem)
- Mouse: the angle follows the pointer: `angle = atan2(handY - pointerY, pointerX - handX)` measured from the throwing hand, clamped to 25..80. Press = start charging (power grows with hold time), release = throw. With a mouse this feels smooth and precise.
- Touch uses the same rule: press and drag on the field, the angle is the direction from the unit's hand to the finger. Problems on a phone:
  1. The finger has to be in the field next to the character, so the thumb covers the characters and the aim.
  2. Near the hand a 1 px tremor of the thumb swings the angle a lot: shake per event is about (1 / r) radians at distance r px from the hand: 1.9 degrees at r = 30 px, 0.4 degrees at r = 140 px. Far from the hand the angle changes slowly. The response is not linear.
  3. Small popup options above the character (an action menu with a few buttons, about 36 to 44 css px) are small and hidden by the thumb.
  4. The whole game feels laggy and the movement is not smooth (dropped frames). Not yet measured on the phone; a recorder of touch event rates and frame times is installed and a measurement is pending.
- The owner wants to play with ONE LEFT THUMB, controls placed out of the way like a MOBA (Arena of Valor, Honor of Kings: stick at the bottom left, buttons at the right) and nothing that makes the thumb cover the characters.

## 2b. Thumb occlusion and smoothness, in numbers (estimates are marked)
- A thumb pad touching the glass is roughly 12 to 14 mm wide (estimate), about 50 css px on this phone; the thumb itself covers the area below and beside the contact point. A character is 73 css px tall and about 60 css px wide, so one thumb placed next to the hand hides a whole character and the aim arrow.
- The popup action menu above the character is two buttons of about 40 x 18 css px each (see screenshot 1, buttons "move" and "attack" above the skeleton): far below the 44 px target size and exactly where the thumb has just been.
- Smoothness: "movement not smooth" is reported by the owner on the phone; with a mouse on the computer it is smooth. The game draws the whole 1920 x 1080 world to a canvas of about 2300 x 1080 device pixels every frame (dozens of drawImage calls, some shadowBlur and lighter-blend effects). Frame times on the phone have not been measured yet.

## 2c. Screenshots that go with this file (attach them)
1. `docs/media/ask_1_rail_and_popup_menu_756x360.jpg` - the new left rail (red knob showing 54), the small popup menu above the skeleton, the angle readout above it, the bottom dock (skill buttons, angle, power bar).
2. `docs/media/ask_2_real_phone_arrow_and_dock.jpg` - the real phone (Chrome fullscreen): red chevron arrow at 76 degrees, small supply boxes, gear at the right end of the dock.
3. `docs/media/ask_3_real_phone_settings_before_fix.jpg` - the settings sheet on the real phone (a label was 7 px too wide; fixed since): shows how tight the 360 px height is.
Tell the assistant: "the pictures are from the game described in section 1; the left rail is the thing added in section 3."

## 3. What we already did
- A thin vertical rail on the far left edge of the stage (about 41 x 191 css px, left of every character). Pressing it sets the angle from the finger height on the rail (top = 80 degrees, bottom = 25 degrees, about 3 px per degree, 18 px dead margin at both ends), keeping the press charges, releasing throws. The field still aims the old way.
- A red chevron arrow from the hero's real launch point along the current angle (shows the angle only, not the wind, power or path), semi-transparent, flashing alternately.
- The power meter is a colourful bar in the bottom dock (hold time).
- Simulated hand model (a model, not human data) comparing "absolute pointing" with "relative vertical drag": median time to settle is similar, the worst 5 percent is 1283 ms (absolute) against 650 ms (relative) at 60 Hz, and tremor jitter per event is 1.9 degrees against 0.3 degrees. Real touch rates and drops are not measured yet.

## 4. Constraints
- Plain browser JavaScript (Pointer Events, canvas 2D, CSS). No native code, no libraries unless small and necessary.
- Must keep the mouse path working. Must not need a second hand. Must be fair for a left-handed holder too if possible.
- Screen is small: every control must stay at least about 44 css px (Apple 44 pt, Google 48 dp); the stage height is 360 css px.
- Deterministic game rules: the throw is (angle, power); do not change the physics.

## 5. Questions (please answer each, with numbers)
1. What control scheme do the best shipped one-thumb touch artillery or aiming games use for angle and power (relative drag, floating or fixed stick, rail, dial, tap-to-set)? Name games and what they do. Which fits "left thumb only, thumb must not cover the characters"?
2. For my rail: what height, width, px-per-degree, dead zone and snapping feel right on a 360 px high landscape stage? Is a vertical rail on the edge the right shape, or is a floating stick (appears under the thumb, bottom left) better? How do games avoid the thumb hiding the visual feedback?
3. How should POWER be chosen with the same thumb: hold time (as now), a second axis (horizontal drag on the rail), or a release-distance pull like a slingshot? What are the pitfalls of hold-time power on a phone?
4. How should the small popup options (action menu above the character) work on touch: radial menu around the thumb, a bottom sheet, buttons at the edge? Give sizes and positions for a 720 x 360 stage.
5. How do I find and fix the lag? Give a ranked checklist for a canvas 2D game on Chrome Android at devicePixelRatio 3 (resolution scaling, shadowBlur and globalCompositeOperation cost, many drawImage calls, filters, OffscreenCanvas, `desynchronized`, fixed-step catch-up, `getCoalescedEvents`, `touch-action: none`, passive listeners), and how to measure each from a script (frame times, long tasks).
6. What numbers should count as "feels smooth" for this kind of aiming (frame time p95, input-to-photon latency, angle jitter per event, time to set an angle to within 2 degrees), so I can write the pass thresholds before testing?
7. What would you test first, with the smallest experiment, to decide between a rail, a floating stick and relative drag anywhere on the left half? How would you let the owner switch between them live and compare with the left thumb?

## 6. Answer format
Start with a 5-line recommendation. Then answer 1 to 7. End with the first three changes you would make, in order, with the smallest code sketch for each.
