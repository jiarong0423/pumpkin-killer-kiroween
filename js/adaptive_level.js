/* Public, deterministic controller for the adaptive AI difficulty level. */
const ADAPTIVE_LEVEL = {
  INITIAL_LEVEL: 2,
  WINDOW_THROWS: 3,
  HIGH_RATE: 0.40,
  LOW_RATE: 0.15,
  MAX_CHANGES: 2,
  COOLDOWN_THROWS: 2,
  UP_REASON: "human rolling hit rate above 40%",
  DOWN_REASON: "human rolling hit rate below 15%"
};

class AdaptiveLevel {
  constructor() {
    this.level = ADAPTIVE_LEVEL.INITIAL_LEVEL;
    this.last_change = null;
    this.hits = [];
    this.changes = 0;
    this.cooldown = 0;
  }

  recordHit(hit) {
    this.hits.push(Boolean(hit));
    this.hits = this.hits.slice(-ADAPTIVE_LEVEL.WINDOW_THROWS);
    if (this.hits.length < ADAPTIVE_LEVEL.WINDOW_THROWS) return this.publicState();
    if (this.cooldown) {
      this.cooldown -= 1;
      return this.publicState();
    }
    if (this.changes >= ADAPTIVE_LEVEL.MAX_CHANGES) return this.publicState();

    const hitRate = this.hits.filter(Boolean).length / this.hits.length;
    if (hitRate > ADAPTIVE_LEVEL.HIGH_RATE && this.level < 3) {
      this.change(1, ADAPTIVE_LEVEL.UP_REASON);
    } else if (hitRate < ADAPTIVE_LEVEL.LOW_RATE && this.level > 1) {
      this.change(-1, ADAPTIVE_LEVEL.DOWN_REASON);
    }
    return this.publicState();
  }

  change(delta, reason) {
    this.level += delta;
    this.last_change = reason;
    this.changes += 1;
    this.cooldown = ADAPTIVE_LEVEL.COOLDOWN_THROWS;
  }

  publicState() {
    return { level: this.level, last_change: this.last_change };
  }
}

if (typeof module !== "undefined") module.exports = { ADAPTIVE_LEVEL, AdaptiveLevel };
else {
  globalThis.ADAPTIVE_LEVEL = ADAPTIVE_LEVEL;
  globalThis.AdaptiveLevel = AdaptiveLevel;
}
