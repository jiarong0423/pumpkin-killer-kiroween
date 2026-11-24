# Pumpkin Killer (南瓜殺手) — the whole game's style, for the model that writes prompts, scripts and opinions (2026-11-10)

## What the game is
A 2D turn-based artillery duel for the Kiroween hackathon (Halloween). 1 v 1 today, two sides on a night graveyard separated by a fence; each turn the player aims an angle, charges the power, throws; wind pushes the shot; head hits crit and stun; three successful hits light three pips and allow one ultimate (two per match). Seven classes: skeleton spear soldier, pumpkin wizard (cannon), black cat assassin (shuriken, slows), pumpkin shield knight (thrown shield, floating hidden shield), ghost bride (scream, poison, bat swarm), bell-tower hunchback (giant axe, two-handed throw), necromancer (a purple flame in one raised hand, burns, ultimate of three flames). Owner-facing language is Traditional Chinese; the owner decides everything about the look.

## The look (look at the pictures, do not rely on this text)
- Dark-fantasy CARTOON, chibi two-heads-tall characters, thick clean near-black outlines plus a thin warm ORANGE outer glow outline, flat three-tone cel shading with soft highlights, no photo look, no plastic shine, no painterly gradients. Dark clothes (black, navy, purple) with ONE saturated accent colour per character (skeleton cyan eye-fire, pumpkins orange glow, cat orange ears, wizard purple and gold, bride pale teal veil, hunchback moss green and rust, necromancer purple flame).
- Scene: deep blue-violet night, a huge full moon, a haunted castle on the hill, bare twisted trees, tombstones, small orange lantern lights, cyan ghost-fire wisps, a black iron fence with a pumpkin lantern in the middle. Mood: spooky but fun, never gory.
- UI: dark gothic metal and carved stone, thin cyan (player) and violet (opponent) edge glows, gold trim on the centre; no HP bars in the top HUD (HP numbers sit above the units); the wind is shown only by a big friendly ghost blowing mist (speed and frequency = strength).
- Reference pictures: (not published) (the original concept), (not published) (the seven idle characters), assets/units/, assets/poses/, assets/portraits/, assets/fx/sprites/, assets/ui/, (not published) (idle against each generated frame), (not published) (the current top HUD). docs/art_style_guide.md and docs/pose_spec.md are the written rules.

## Hard rules from the owner (the newest rows of (not published) win)
1. Every picture comes from an image model; code never draws art, it only moves and fades pictures.
2. Same character in every frame: SAME FACE (the owner's biggest complaint: faces changed between frames), same size and feet line, same direction (the class idle's direction), same hand for the item.
3. The thrown item disappears from the hand at the throw and returns at the next turn; the release and empty frames show an empty hand.
4. Continuous animation: an idle loop, a charge that follows the power meter in three steps, a release, an empty stance, a hit; frames are consecutive moments, nothing jumps.
5. Fairness: nothing hidden is shown to a player or an agent (positions and wind are read as a human reads them).
6. Names: only Chinese characters and English letters, at most 8.
7. Nothing may overlap on screen; text must be readable; no emoji used as pictures.
8. No spending beyond the plan; nothing is pushed or deployed; the owner approves anything that costs credits.
