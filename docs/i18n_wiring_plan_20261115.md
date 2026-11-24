# i18n wiring plan for index.html (Kiro task 139), 2026-11-15
Line numbers are for `index.html` at 3109 lines today; the main line edits it, so re-find lines with `node scripts/test_i18n.js` (it prints every line that still holds CJK outside comments). `T` = `I18N.t`. Nothing here was applied.
Library (done, tested): `js/i18n.js` keeps the global `I18N` and now also `I18n`; `apply(root)`, `toggle()`, `lang()`, `init(fallback)`, `loadDictionaries(langs, loader)`. `setLang("zh")` is accepted as `zh-TW`. Tests: `node scripts/test_i18n.js --no-page` passes (22); without the flag 4 page checks fail until this plan is applied.
`data-i18n="key"` sets textContent. `data-i18n-attr="title:key;aria-label:key2"` sets attributes. Keys with `{params}` cannot go in markup; JS sets those.

## A. Load and boot
1. After line 288 (`wind_fx.js`), before the inline `<script>` at 289: add `<script src="js/i18n.js"></script>`.
2. After line 294 (`FONT_DISPLAY`): add `const T = (k, v) => I18N.t(k, v);`
3. Line 296: `document.fonts.load(f, "南瓜殺手AaBb0123")` -> `"\u5357\u74dc\u6bba\u624bAaBb0123"` (font sample, stays Chinese on purpose, escaped so the CJK check passes).
4. Lines 3103 to 3105 (`initStartScreen(); showStartScreen(); requestAnimationFrame(loop);`) and `updateShieldButton();` at 3102 -> `I18N.loadDictionaries().catch(() => {}).then(() => { I18N.init("zh-TW"); I18N.apply(document); updateShieldButton(); initStartScreen(); showStartScreen(); requestAnimationFrame(loop); });` Chinese stays the default; a saved choice wins. If the JSON fails to load (page opened from `file://`), `T` returns the key; the game must be served over http.
5. After `toggleHelp` (about line 427): `function toggleLang() { I18N.toggle(); I18N.apply(document); buildStartScreen(); updateShieldButton(); }`
6. Language button: after line 229 (help button) add `<button id="lang-btn" type="button" class="skill-btn" data-i18n-attr="title:lang.title" onclick="toggleLang()"><span>🌐</span><span class="btn-tip" data-i18n="lang.label"></span></button>`. It shows `EN` on the Chinese page and `中文` on the English page, and the choice is saved by `I18N.setLang`.
7. `scripts/release/export_manifest.json`: `js/` already includes `js/i18n.js`. Add before the `assets/` rules (after the `assets/fonts/` rule): `{ "match": "assets/i18n/", "decision": "INCLUDE", "reason": "UI dictionaries fetched at run time by js/i18n.js; the path is built in code, so check_asset_refs cannot see it" }`.

## B. Static markup (add the attribute, delete the Chinese text)
8. 6: `<title>Pumpkin Killer (...)</title>` -> `<title data-i18n="page.title">Pumpkin Killer</title>`
9. 215 `<h1 data-i18n="start.title"></h1>`; 216 `<h2 data-i18n="start.pickHero"></h2>`; 218 `<h2 data-i18n="start.pickScene"></h2>`; 220 start-go button gets `data-i18n="start.go"`, text removed.
10. 223: `title="補充物資..."` -> `data-i18n-attr="title:supply.title"`; `<span class="ts-label">物資</span>` -> `... data-i18n="supply.label"></span>`. 224: `title:supply.aiTitle`, label `supply.aiLabel`.
11. 227: `title="音樂與音效開關（M）"` -> `data-i18n-attr="title:dock.soundTitle"`; tip span `data-i18n="dock.soundTip"`.
12. 228: delete `title="重新對戰..."` (line 1641 sets it each frame, it needs `{n}`); `aria-label="重新對戰"` -> `data-i18n-attr="aria-label:dock.resetAria"`; tip `dock.resetTip`.
13. 229: `title="說明（H）" aria-label="說明"` -> `data-i18n-attr="title:dock.helpTitle;aria-label:dock.helpAria"`.
14. 232 to 237 (six help spans): add `data-i18n` = `help.tapUnit`, `help.holdThrow`, `help.wind`, `help.crit`, `help.ult`, `help.guard`; empty the span.
15. 245: `aria-label="目前角色"` -> `data-i18n-attr="aria-label:dock.portraitAria"`. 247: `<span class="dock-name" id="dock-name">骷髏長矛兵</span>` -> same with empty text (`updateDock` line 1628 fills it).
16. 250 to 254 hero tabs: `title="X"` -> `data-i18n-attr="title:hero.skeleton.name"` (skeleton, wizard, bat, reaper use `hero.<id>.name`; knight uses `hero.knight.tabTitle`); `<span class="hero-name">X</span>` -> `data-i18n="hero.<id>.tab"`.
17. 260 to 263 and 264: `title="..."` -> `data-i18n-attr="title:skill.normalTitle"` / `skill.doubleTitle` / `skill.heavyTitle` / `skill.healTitle` / `skill.ultTitle`; tip spans `skill.normalTip`, `skill.doubleTip`, `skill.heavyTip`, `skill.healTip`, `skill.ultTip`.
18. 266: `title="浮空盾"` -> `data-i18n-attr="title:skill.shield"`; tip span `data-i18n="skill.shield"`.
19. 270 label `data-i18n="dock.angle"`; 272 label `data-i18n="dock.power"`; 277 lock button: `title="鎖定盾牌位置"` -> `data-i18n-attr="title:dock.lockTitle"`, `data-i18n="dock.lock"`, text removed.

## C. Strings built in JS
20. 362 to 366 `HERO_BLURB` values -> key strings: `skeleton: "hero.skeleton.blurb"`, `wizard: "hero.wizard.blurb"`, `bat: "hero.bat.blurb"`, `knight: "hero.knight.blurb"`, `reaper: "hero.reaper.blurb"`.
21. 387: `${HERO_BLURB[k]}` -> `${T(HERO_BLURB[k])}`.
22. 369, 370 `COMING_HEROES`: `name: "鬼娃新娘", blurb: "..."` -> `get name() { return T("hero.bride.name"); }, get blurb() { return T("hero.bride.blurb"); }`; same for `hero.hunchback.*`.
23. 373 to 375 `SCENES`: `name: "月夜墓園"` -> `get name() { return T("scene.graveyard.name"); }`; `belltower` -> `scene.belltower.name`; `pumpkin` -> `scene.pumpkin.name`.
24. 393: `<small>製作中</small>` -> `<small>${T("start.inProduction")}</small>`; 400: `"製作中"` -> `T("start.inProduction")`.
25. 527 delete `if (keepLabel.t === undefined) keepLabel.t = b.textContent;`; 529 `b.textContent = keepLabel.t;` -> `b.textContent = T("start.go");`; 530 `` `載入中 ${settledCount}/${IMG_TOTAL}` `` -> `T("start.loading", { done: settledCount, total: IMG_TOTAL })`.
26. 539, 548, 557, 566, 575 (`HERO_PROFILES.*.name`): `name: "骷髏長矛兵"` -> `get name() { return T("hero.skeleton.name"); }`; wizard (548), bat (557), `reaper` (566, `hero.reaper.name`), knight (575, `hero.knight.name`). Every reader of `.name` keeps working and follows the language.
27. 602 `"🔧 這個職業的大招還在製作中"` -> `T("ult.unbuilt")`; 603 `"大招取消"` -> `T("ult.cancel")`; 604 `ultUsed.player >= 2 ? "大招已用完" : "能量未滿（要打中 3 次）"` -> `ultUsed.player >= 2 ? T("ult.spent") : T("ult.noEnergy")`; 605 `"✨ 大招已準備：下一發出手"` -> `T("ult.armed")`.
28. 782 `label: "🎲 移動"` -> `label: T("menu.move")`; `"🎯 攻擊"` -> `T("menu.attack")`; 783 `"🛡 防禦"` -> `T("menu.defend")`.
29. 791 -> `T("toast.aimHint")`; 798 -> `T("toast.slowed")`; 799 -> `T("toast.alreadyMoved")`; 803 -> `T("toast.moveHelp")`; 805 -> `T("toast.moveCancel")`.
30. 810: the template -> `T("toast.moveRoll", { dir: T(dir > 0 ? "move.forward" : "move.back") })`.
31. 831: the template -> `T("toast.moveResult", { roll: d.final, dir: T(o.dir > 0 ? "move.forward" : "move.back"), moved: moved, edge: moved < o.steps * DICE_STEP_PX ? T("move.atEdge") : "" })`.
32. 853 -> `T("toast.gapShift", { px: Math.round(Math.abs(ai.targetX - player.targetX)) })`; 862 -> `T("toast.healOwnTurn")`; 863 -> `T("toast.hpFull")`; 871 -> `T("toast.healed")`.
33. 889 -> `T("toast.guardOnly")`; 895 -> `T("toast.shieldNoMoves")`; 903 -> `T("toast.defendHelp")`; 929 -> `T("toast.defendCancel")`; 961 -> `T("toast.noAttackInDefend")`.
34. 919: `sp.snapped ? ... : ...` -> `sp.snapped ? T("toast.shieldSnapped", { moves: sp.actions, charges: sp.charges }) : T("toast.shieldLocked", { moves: sp.actions })`.
35. 942 -> `T("toast.switchHero", { name: HERO_PROFILES[heroKey].name })`; 953/954 -> `T("shield.tipGuard")` / `T("shield.tipOther")`.
36. 1051 -> `T("status.frostWeak")`; 1061 `T("ult.shuriken")`; 1073 `T("ult.spear")`; 1081 `T("ult.cannon")`; 1090 `T("ult.soulfire")` (new key).
37. 1098 -> `T("toast.bounce", { n: pj.bounceN, dmg: pj.bounceDmg })`; 1277 -> `T("toast.flip", { state: T(flipAllArt ? "toast.flipOn" : "toast.flipOff") })`.
38. 1362 and 1436 -> `T("status.halluActive")` (new key); 1811 -> `T("status.halluApplied")` (new key); 1384 -> `T("toast.aiShield")`.
39. 1407: `"⭐ 暈眩！只剩 " + STUN_SECONDS + " 秒"` -> `T("status.stunTimer", { sec: STUN_SECONDS })`; 1799 -> `T("status.stun")`; 1798 -> `T("status.crit")`.
40. 1426 -> `T("shield.expired")`; 1429 -> `T("shield.holding", { rounds: s.durationRounds })`; 1780 -> `T("shield.blocked", { rounds: shield.durationRounds })`.
41. 1446: `"🔒 第 " + RESET_LAST_ROUND + " 回合後不能重置"` -> `T("toast.resetLocked", { n: RESET_LAST_ROUND })`.
42. 1519 `label: "補血 +30"` -> `labelKey: "supply.heal"`; 1520 `label: "重彈 +1"` -> `labelKey: "supply.heavy"`.
43. 1563: `SUPPLY_ITEMS[d.item].icon + " 拿到物資：" + SUPPLY_ITEMS[d.item].label` -> `T("toast.pickup", { icon: SUPPLY_ITEMS[d.item].icon, label: T(SUPPLY_ITEMS[d.item].labelKey) })`; 1567 -> `T("toast.aiPickup")`.
44. 1597 -> `T("status.poison")`; 1598 -> `T("status.bleed")`.
45. 1641: `rb.title = ok ? "重新對戰（只有前 " + RESET_LAST_ROUND + " 個回合能按）" : "已鎖定：第 " + RESET_LAST_ROUND + " 回合後不能重置"` -> `rb.title = ok ? T("dock.resetTitle", { n: RESET_LAST_ROUND }) : T("dock.resetLockedTitle", { n: RESET_LAST_ROUND })`.
46. 1644: the `ub.title` chain -> `ultUsed.player >= 2 ? T("ult.titleUsedUp") : energy.player >= 3 ? (ultArmed.player ? T("ult.titleArmed") : T("ult.titleReady")) : T("ult.titleCharging", { n: energy.player })`.
47. 1672 -> `T("toast.timeout")`; 1754 -> `wallHp > 0 ? T("toast.fenceBlock") : T("toast.fenceBroken")`.
48. 1804 -> `T("ult.tripleHit")`; 1808 -> `T("status.slowNext")`; 1826 -> `T("toast.directHit", { dmg: dmgNow })`; 1829 -> `T("status.frostApplied")`.
49. 1847 -> `T("toast.mudDeflect")`; 1848 -> `T("toast.shieldStuck")`; 1865 -> `T("ult.blast", { dmg: p.ultBlast })`; 1901 -> `T("toast.rearm")`.
50. 1993 and 1997: delete the unused 4th argument (`, "我方浮空盾"` and `, "AI 浮空盾（被看穿了）"`); `drawAirborneShield` never reads `label`.
51. 2100 -> `T("hud.trailTag", { round: traj.round })`; 2153 and 2187 -> `s.preview ? T("shield.dragHint") : T("shield.roundsLeft", { rounds: s.durationRounds })`.
52. 2591 and 2650 -> `wallHp > 0 ? T("fence.label", { hp: wallHp }) : T("fence.broken")`.
53. 2846 `"大招"` -> `T("hud.ult")`; 2855 `"我方"` -> `T("hud.you")`; 2856 `"對手"` -> `T("hud.opponent")`.
54. 2870 -> `T("hud.countdown", { sec: sec })`; 2873 -> `T("hud.opponentTurn")`; 2874 -> `T("hud.round", { round: roundNum, dist: Math.round(dist / DICE_STEP_PX) })`.
55. 3007 `"◀ 後退"` -> `T("move.backBtn")`; `"前進 ▶"` -> `T("move.fwdBtn")`.
56. 3026 -> `Math.abs(movePoint.val) < 0.18 ? T("move.aimNeutral") : (movePoint.val > 0 ? T("move.releaseFwd") : T("move.releaseBack"))`.
57. 3049 -> `T("hud.angle", { angle: playerAngle })`; 3068 -> `T(gameOver === "player" ? "gameover.win" : "gameover.lose")`; 3071 -> `T("gameover.restart")`.

## D. Keys added in this task (both JSON files)
`ult.soulfire` (line 1090), `status.halluActive` (1362, 1436), `status.halluApplied` (1811), `lang.title` and `lang.label` (language button). The page now has 158 keys per language. Every other string in the page already had a key. The English is a machine draft: the owner approves it before public use. `docs/i18n_mapping_20261115.json` does not list the five new keys.

## E. Stays Chinese on purpose
Game text is Chinese by default (owner 2026-11-15), so the zh-TW dictionary holds it. Not translated: the font sample in item 3; every comment; unit names of the owner's design if the owner wants them shown in Chinese in English mode (open question).

## F. Check after applying
`node scripts/test_i18n.js` (all 26 checks, no `--no-page`), `node scripts/test_ultimate_fx.js`, then a recorded browser run in each language: start screen, one match, a toast, the game-over screen. English strings are longer than Chinese; look for cut-off HUD banners and toasts (docs/ui_reskin_plan.md d12).
