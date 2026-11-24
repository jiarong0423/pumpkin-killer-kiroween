# Pose set specification (all classes, owner rules 2026-11-09)

Every class gets the same connected set of pictures. Colab prompts must repeat these rules word for word.

## Set (5 frames)
1. **Idle** — the item is in the hand.
2. **Wind-up charge** — the item pulled BACK behind the body, body leaning back, face straining.
3. **Release** — the throw: the item has left the hand (the hand is empty, or the flame / weapon is a streak ahead of it), body lunging forward, face roaring.
4. **Empty** — the same stance as the idle but the hand is empty (shown from the throw until the next turn; the item returns automatically at the next turn).
5. **Hit** — staggering, eyes shut, arms shielding the head.

## Looping and full charge (owner 2026-11-09: 'make everything a loop', 'a complete wind-up charge')
- **Idle loops:** 2 idle frames (a small breath / flame flicker) that alternate slowly, so a unit never stands frozen.
- **Charge is a progression, not one picture:** 3 charge frames shown by the power meter while the player holds: LOW (the item starts to pull back), MID (pulled back, body leaning, face tightening), FULL (maximum pull, flame / item biggest, face straining). The picture follows the power value, so a half-charged throw looks half-charged.
- **Cycle:** idle loop -> charge LOW -> MID -> FULL (held) -> release -> empty (until the next turn) -> idle loop. Hit interrupts any of them and returns to idle.
- Frames per class: idle x2, charge x3, release, empty, hit = 8 pictures.

## Hard rules
- **One direction:** every frame faces the SAME side as the idle picture (today: LEFT). The throw goes toward that side. Never mirror a frame by luck: say "strict side view facing LEFT" in the prompt.
- **One hand:** the hand that holds the item in the idle picture is the throwing hand in EVERY frame; never switch hands (owner 2026-11-09: 'it even switched hands'). The other hand stays empty at the side.
- **One size:** the character keeps EXACTLY the size, scale and proportions of the idle picture (same head size, same body height). The pose may be wider, never bigger.
- **One baseline:** the feet stand on the same line in every frame (the picture is cropped to the same bottom edge).
- **Face changes** with the phase: calm (idle) -> strain (wind-up) -> roar (release) -> calm (empty) -> pain (hit).
- **Held item:** disappears at the release and returns at the next turn (code, not art).
- **No extra limbs, one head, no weapon the class does not own.**
- **Real art only:** every picture comes from Colab; code only moves, fades and flips for the opponent side.

## Prompt template
"Edit this image, keep the exact same <character>, same size and scale as the reference. Strict side view facing LEFT, the same direction as the reference; the throw goes toward the LEFT. <pose>. One character, full body, feet on the same baseline. Flat solid magenta background (#FF00FF), no ground, no cast shadow, no text, no watermark."
