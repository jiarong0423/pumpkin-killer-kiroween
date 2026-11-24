#!/usr/bin/env python3
"""Public, deterministic controller for the adaptive AI difficulty level."""

ADAPTIVE_LEVEL = {
    "INITIAL_LEVEL": 2,
    "WINDOW_THROWS": 3,
    "HIGH_RATE": 0.40,
    "LOW_RATE": 0.15,
    "MAX_CHANGES": 2,
    "COOLDOWN_THROWS": 2,
    "UP_REASON": "human rolling hit rate above 40%",
    "DOWN_REASON": "human rolling hit rate below 15%",
}


class AdaptiveLevel:
    """Adjust a public level from the human seat's most recent hit results."""

    def __init__(self):
        self.level = ADAPTIVE_LEVEL["INITIAL_LEVEL"]
        self.last_change = None
        self._hits = []
        self._changes = 0
        self._cooldown = 0

    def record_hit(self, hit):
        """Record one human throw and return the public controller state."""
        self._hits.append(bool(hit))
        self._hits = self._hits[-ADAPTIVE_LEVEL["WINDOW_THROWS"]:]
        if len(self._hits) < ADAPTIVE_LEVEL["WINDOW_THROWS"]:
            return self.public_state()
        if self._cooldown:
            self._cooldown -= 1
            return self.public_state()
        if self._changes >= ADAPTIVE_LEVEL["MAX_CHANGES"]:
            return self.public_state()

        hit_rate = sum(self._hits) / len(self._hits)
        if hit_rate > ADAPTIVE_LEVEL["HIGH_RATE"] and self.level < 3:
            self._change(1, ADAPTIVE_LEVEL["UP_REASON"])
        elif hit_rate < ADAPTIVE_LEVEL["LOW_RATE"] and self.level > 1:
            self._change(-1, ADAPTIVE_LEVEL["DOWN_REASON"])
        return self.public_state()

    def _change(self, delta, reason):
        self.level += delta
        self.last_change = reason
        self._changes += 1
        self._cooldown = ADAPTIVE_LEVEL["COOLDOWN_THROWS"]

    def public_state(self):
        """Return only the level and last public adjustment reason."""
        return {"level": self.level, "last_change": self.last_change}
