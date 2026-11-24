# Placed concept review

1. Floating coffin platforms: OK. The blue left and purple right coffins are clear, sit above the fighters, and do not cover the main play space.
2. Landing rings: PROBLEM. They are not present in this still, so their visibility and ground-hit-only behaviour cannot be checked.
3. HP numbers: PROBLEM. The numbers above both unit bars are too small and blur into the player-name and bar details at this view size.
4. Sound, reset, and help buttons: PROBLEM. The half-transparent buttons are hard to identify because the wind ghost and mist sit over their low-contrast circles.
5. Banners, centre piece, supply slots, and ultimate diamonds: PROBLEM. The large banners frame the screen well, but the small round, supply, and ultimate information is crowded and difficult to read.

## Top fixes

1. Raise the three wind controls to `opacity: 0.82` and give each a `rgba(5, 12, 35, 0.82)` circular backing with a 2 px cyan outline; keep the ghost mist behind, not over, their icons.
2. Render each HP number at at least 28 canvas px in solid white with a 2 px near-black stroke, centred 14 px above its HP bar and separated from the player name.
3. Increase the small top-HUD labels and diamonds by 25%, give the round card a 12 px internal padding, and leave at least 20 canvas px between the round card, timer card, and adjacent banner content.

## Cannot judge from this still

- Whether landing rings appear only after a ground hit, remain readable during effects, and disappear at the right time.
- Whether the semi-transparent controls remain readable while the wind ghost animates or when hovered/clicked.
- Whether the platform and HUD placement stays clear during throws, impacts, camera shake, and different unit positions.
