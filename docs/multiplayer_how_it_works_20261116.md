# How multiplayer works

Joining needs no download and no installation. A friend opens the same web address or scans the room QR code. The link contains `?room=CODE`; PWA installation is optional and never blocks joining.

The relay creates each six-character room code with `secrets.choice` from `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`. It excludes `I`, `O`, `0`, and `1`. There are about 1.07 billion possible codes. If a code already exists, the relay draws again. The room code is unrelated to the match seed.

The relay also creates one non-zero 31-bit match seed. Every device uses `Determinism` and that seed to derive start positions, wind, weather, dice values, and the opening coin toss. Devices do not use `Math.random` for connected match state.

For a throw, the attacking device sends only the active unit id, angle, power, and start point. The attacked device runs the same fixed-step flight, judges the hit on its own unit, and deducts its own HP. Both devices calculate the round hash from the public state. A mismatch is shown as out of sync.

The relay orders and forwards messages. It does not simulate projectiles, decide damage, or hold private item-slot contents. Each device sees only its own side's private slots.
