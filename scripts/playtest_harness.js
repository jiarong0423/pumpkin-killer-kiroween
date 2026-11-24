/* Playtest harness (2026-11-16): load it into the running game page, then play whole matches against the built-in opponent.
 *   await (await fetch('/scripts/playtest_harness.js')).text().then(eval);       // once per page load
 *   const r = await PT.match('knight', 'skeleton', { skill: 0.8, useUlt: true }); // resolves with the result when the match is over (about 1 to 2 minutes)
 * skill 0..1 is how well the player aims (0.9 = a good human, 0.5 = a beginner). The opponent is the page's own AI (random class unless given).
 * Result: { winner: 'player'|'ai', rounds, playerHero, aiHero, playerHp, aiHp, ultsUsed, log: [...], seconds }. Nothing is written anywhere.
 * The harness only calls the page's own functions (estimatePowerForTarget, executeThrow, toggleUltimate, the pointer events for the knight's points), it changes no rule.
 */
(function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const gauss = () => { let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  async function match(playerHero, aiHero, opts) {
    opts = opts || {};
    const skill = opts.skill == null ? 0.8 : opts.skill, useUlt = opts.useUlt !== false, maxRounds = opts.maxRounds || 30, t0 = Date.now();
    if (gameOver || matchStarted) { try { resetGame(); } catch (e) {} }   // a finished match must be reset first, as the page does on the result click
    pickedHero = playerHero; pickedScene = opts.scene || "graveyard"; startMatch();
    await sleep(700);
    if (aiHero) { aiClass = aiHero; ai.profile = aiHero; applyClassStats(); }
    const log = []; let rounds = 0;
    const rect = () => canvas.getBoundingClientRect();
    const tap = (x, y) => { const rc = rect(), sx = rc.width / CANVAS_W, sy = rc.height / CANVAS_H; const ev = (t) => canvas.dispatchEvent(new PointerEvent(t, { clientX: rc.left + x * sx, clientY: rc.top + y * sy, pointerId: 99, pointerType: "mouse", bubbles: true, isPrimary: true, buttons: 1 })); ev("pointerdown"); ev("pointerup"); };
    while (!gameOver && rounds < maxRounds) {
      let guard = 0;
      while ((turn !== "player" || projectiles.length || isCharging) && !gameOver && guard < 600) { await sleep(100); guard++; }
      if (gameOver) break;
      rounds++;
      const info = { round: rounds, playerHp: Math.round(player.hp), aiHp: Math.round(ai.hp), energy: energy.player, wind: Math.round(effWind() * 10) / 10 };
      // the knight: store three points with the ultimate when it is ready (the points go where the player expects the enemy to shoot through)
      if (playerHero === "knight" && useUlt && energy.player >= 3 && ultUsed.player < 2 && !knightPts.length) {
        toggleUltimate(); await sleep(200);
        if (knightPlacing) { [0.55, 0.42, 0.3].forEach((f) => { const x = player.x + (ai.x - player.x) * f * 0.8; tap(x, shieldArcY(shieldClampX(x))); }); info.ult = "knight points"; }
      } else if (useUlt && energy.player >= 3 && ultUsed.player < 2 && ULT_BUILT.indexOf(playerHero) >= 0 && playerHero !== "knight" && !ultArmed.player) {
        toggleUltimate(); info.ult = "armed";
      }
      // aim: the estimate plus a human-like error that shrinks with skill
      const W = HERO_PROFILES[playerHero];
      const fwd = W.weapon === "cannonball" ? WIZARD_MUZZLE.fwd : (W.weapon === "proj_shield" ? 51 : 58), up = W.weapon === "cannonball" ? WIZARD_MUZZLE.up : (W.weapon === "proj_shield" ? 73 : 110);
      playerAngle = (ai.x - player.x) < 700 ? 66 : 54;   // fixed aim angle (the real page follows the mouse); a steeper one at short range so the shot clears the fence
      let power = estimatePowerForTarget(player.x + fwd, player.y - up, ai.x, 1, playerAngle, effWind());
      power = Math.max(15, Math.min(100, power + gauss() * (1 - skill) * 14));
      info.power = Math.round(power);
      log.push(info);
      turn = "busy";   // like releaseAndThrow: one throw per turn, input locked until the round resolves
      executeThrow("player", power);
      await sleep(600);
    }
    // let the last shots finish
    let g2 = 0; while (projectiles.length && g2 < 100) { await sleep(100); g2++; }
    await sleep(500);
    return { winner: gameOver || (ai.hp <= 0 ? "player" : player.hp <= 0 ? "ai" : "none"), rounds, playerHero, aiHero: ai.profile, playerHp: Math.round(player.hp), aiHp: Math.round(ai.hp), ultsUsed: ultUsed.player, log, seconds: Math.round((Date.now() - t0) / 1000) };
  }
  window.PT = { match, sleep };
})();
