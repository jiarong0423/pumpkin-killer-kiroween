/* Page AI difficulty knobs, calibrated by scripts/sweep_page_ai_levels.js. */
const LEVEL_TABLE = {
  easy: { viewPosNoise: 350, viewWindNoise: 3.2, aimError: 36 },
  normal: { viewPosNoise: 150, viewWindNoise: 1.2, aimError: 14 },
  hard: { viewPosNoise: 65, viewWindNoise: 0.5, aimError: 5 }
};

function levelName(levelNumber) {
  return ({ 1: "easy", 2: "normal", 3: "hard" })[levelNumber] || "normal";
}

function knobsFor(levelNumber) {
  const ok = levelNumber === 1 || levelNumber === 2 || levelNumber === 3;
  const knobs = LEVEL_TABLE[levelName(levelNumber)];
  return { ...knobs, ok };
}

const AiLevelsPage = { knobsFor, levelName };

if (typeof module !== "undefined") module.exports = AiLevelsPage;
else globalThis.AiLevelsPage = AiLevelsPage;
