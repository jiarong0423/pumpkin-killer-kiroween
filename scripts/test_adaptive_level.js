#!/usr/bin/env node
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { AdaptiveLevel } = require("../js/adaptive_level.js");

const vectors = JSON.parse(fs.readFileSync(path.join(__dirname, "adaptive_level_vectors.json"), "utf8"));
for (const vector of vectors) {
  const controller = new AdaptiveLevel();
  const levels = vector.hits.map((hit) => controller.recordHit(hit).level);
  assert.deepStrictEqual(levels, vector.levels, vector.name);
  assert.strictEqual(controller.publicState().last_change, vector.last_change, vector.name);
}

const state = new AdaptiveLevel().publicState();
assert.deepStrictEqual(Object.keys(state).sort(), ["last_change", "level"]);
console.log(`OK: ${vectors.length} shared adaptive-level vectors passed.`);
