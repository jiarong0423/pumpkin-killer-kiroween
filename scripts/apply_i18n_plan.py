#!/usr/bin/env python3
"""Checked, one-way application of docs/i18n_wiring_plan_20261115.md."""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "index.html"

# Each source string is copied from the unmodified page.  The IDs mirror the plan.
EDITS = [
    ("01.i18n-script", '  <script src="js/wind_fx.js"></script>\n', '  <script src="js/wind_fx.js"></script>\n  <script src="js/i18n.js"></script>\n'),
    ("02.t-helper", '    const FONT_DISPLAY = \' "PK Display", "Noto Serif TC", "Songti TC", Georgia, serif\';\n', '    const FONT_DISPLAY = \' "PK Display", "Noto Serif TC", "Songti TC", Georgia, serif\';\n    const T = (k, v) => I18N.t(k, v);\n'),
    ("03.font-sample", 'document.fonts.load(f, "南瓜殺手AaBb0123")', 'document.fonts.load(f, "\\u5357\\u74dc\\u6bba\\u624bAaBb0123")'),
    ("04.boot", '    updateShieldButton();\n    initStartScreen();\n    showStartScreen();\n    requestAnimationFrame(loop);', '    I18N.loadDictionaries().catch(() => {}).then(() => { I18N.init("zh-TW"); I18N.apply(document); updateShieldButton(); initStartScreen(); showStartScreen(); requestAnimationFrame(loop); });'),
    ("05.toggle-lang", '    function toggleSound() {\n', '    function toggleLang() { I18N.toggle(); I18N.apply(document); buildStartScreen(); updateShieldButton(); }\n\n    function toggleSound() {\n'),
    ("06.lang-button", '      <button id="help-btn" type="button" title="說明（H）" aria-label="說明" onclick="toggleHelp()">?</button>\n', '      <button id="lang-btn" type="button" class="skill-btn" data-i18n-attr="title:lang.title" onclick="toggleLang()"><span>🌐</span><span class="btn-tip" data-i18n="lang.label"></span></button>\n      <button id="help-btn" type="button" data-i18n-attr="title:dock.helpTitle;aria-label:dock.helpAria" onclick="toggleHelp()">?</button>\n'),
    ("08.title", '<title>Pumpkin Killer (南瓜殺手) — 經典貓狗大戰手感 ✕ 浮空盾預判 ✕ 軌跡記憶</title>', '<title data-i18n="page.title">Pumpkin Killer</title>'),
    ("09.start-markup", '      <h1>🎃 南瓜殺手</h1>\n      <h2>選一個角色（開局後不能換）</h2>\n      <div class="pick-row" id="pick-heroes"></div>\n      <h2>選一個戰場</h2>\n      <div class="pick-row" id="pick-scenes"></div>\n      <button id="start-go" type="button">開始戰鬥</button>', '      <h1 data-i18n="start.title"></h1>\n      <h2 data-i18n="start.pickHero"></h2>\n      <div class="pick-row" id="pick-heroes"></div>\n      <h2 data-i18n="start.pickScene"></h2>\n      <div class="pick-row" id="pick-scenes"></div>\n      <button id="start-go" type="button" data-i18n="start.go"></button>'),
    ("10.supply-markup", '    <div id="supply-slot" class="top-supply left" title="補充物資：撿到的箱子放這裡，點一下使用；新的會取代舊的" onclick="useSupply()"><span class="ts-label">物資</span><span class="ts-box"><span id="special-icon"></span></span></div>\n    <div id="supply-slot-ai" class="top-supply right" title="對手手上的物資（只看得到，不能用）"><span class="ts-label">對手物資</span><span class="ts-box"><span id="special-icon-ai"></span></span></div>', '    <div id="supply-slot" class="top-supply left" data-i18n-attr="title:supply.title" onclick="useSupply()"><span class="ts-label" data-i18n="supply.label"></span><span class="ts-box"><span id="special-icon"></span></span></div>\n    <div id="supply-slot-ai" class="top-supply right" data-i18n-attr="title:supply.aiTitle"><span class="ts-label" data-i18n="supply.aiLabel"></span><span class="ts-box"><span id="special-icon-ai"></span></span></div>'),
    ("11.sound-markup", '      <button id="sound-btn" class="skill-btn" title="音樂與音效開關（M）" onclick="toggleSound()"><span id="sound-ico">🔊</span><span class="btn-tip">聲音</span></button>', '      <button id="sound-btn" class="skill-btn" data-i18n-attr="title:dock.soundTitle" onclick="toggleSound()"><span id="sound-ico">🔊</span><span class="btn-tip" data-i18n="dock.soundTip"></span></button>'),
    ("12.reset-markup", '      <button id="reset-btn" class="skill-btn dock-reset" title="重新對戰（只有前 2 個回合能按）" aria-label="重新對戰" onclick="resetPressed()"><span>🔄</span><span class="btn-tip">重置</span></button>', '      <button id="reset-btn" class="skill-btn dock-reset" data-i18n-attr="aria-label:dock.resetAria" onclick="resetPressed()"><span>🔄</span><span class="btn-tip" data-i18n="dock.resetTip"></span></button>'),
    ("14.help-markup", '      <span>👆 點角色：移動／攻擊／防禦</span>\n      <span>🎯 按住蓄力，放開投擲</span>\n      <span>🌬 風看上方箭頭，風越強越偏</span>\n      <span>💥 打中頭部＝爆擊＋暈眩</span>\n      <span>✨ 三格亮滿，按 U 放大招</span>\n      <span>🛡 盾衛：點 A、B、C 預判三發</span>', '      <span data-i18n="help.tapUnit"></span>\n      <span data-i18n="help.holdThrow"></span>\n      <span data-i18n="help.wind"></span>\n      <span data-i18n="help.crit"></span>\n      <span data-i18n="help.ult"></span>\n      <span data-i18n="help.guard"></span>'),
    ("15.portrait-markup", '<div class="dock-portrait" aria-label="目前角色"><div class="dock-portrait-art" id="dock-portrait-art">💀</div></div>\n        <div class="dock-id">\n          <div class="dock-name-row"><span class="dock-name" id="dock-name">骷髏長矛兵</span>', '<div class="dock-portrait" data-i18n-attr="aria-label:dock.portraitAria"><div class="dock-portrait-art" id="dock-portrait-art">💀</div></div>\n        <div class="dock-id">\n          <div class="dock-name-row"><span class="dock-name" id="dock-name"></span>'),
    ("16.hero-tabs", '            <button class="hero-tab active" data-hero="skeleton" title="骷髏長矛兵" onclick="switchHero(\'skeleton\')"><span class="hero-glyph">💀</span><span class="hero-name">骷髏</span></button>\n            <button class="hero-tab" data-hero="wizard" title="南瓜巫師" onclick="switchHero(\'wizard\')"><span class="hero-glyph">🎃</span><span class="hero-name">巫師</span></button>\n            <button class="hero-tab" data-hero="bat" title="蝙蝠刺客" onclick="switchHero(\'bat\')"><span class="hero-glyph">🦇</span><span class="hero-name">刺客</span></button>\n            <button class="hero-tab" data-hero="knight" title="南瓜盾衛" onclick="switchHero(\'knight\')"><span class="hero-glyph">🛡️</span><span class="hero-name">盾衛</span></button>\n            <button class="hero-tab" data-hero="reaper" title="死靈法師" onclick="switchHero(\'reaper\')"><span class="hero-glyph">🔥</span><span class="hero-name">死靈</span></button>', '            <button class="hero-tab active" data-hero="skeleton" data-i18n-attr="title:hero.skeleton.name" onclick="switchHero(\'skeleton\')"><span class="hero-glyph">💀</span><span class="hero-name" data-i18n="hero.skeleton.tab"></span></button>\n            <button class="hero-tab" data-hero="wizard" data-i18n-attr="title:hero.wizard.name" onclick="switchHero(\'wizard\')"><span class="hero-glyph">🎃</span><span class="hero-name" data-i18n="hero.wizard.tab"></span></button>\n            <button class="hero-tab" data-hero="bat" data-i18n-attr="title:hero.bat.name" onclick="switchHero(\'bat\')"><span class="hero-glyph">🦇</span><span class="hero-name" data-i18n="hero.bat.tab"></span></button>\n            <button class="hero-tab" data-hero="knight" data-i18n-attr="title:hero.knight.tabTitle" onclick="switchHero(\'knight\')"><span class="hero-glyph">🛡️</span><span class="hero-name" data-i18n="hero.knight.tab"></span></button>\n            <button class="hero-tab" data-hero="reaper" data-i18n-attr="title:hero.reaper.name" onclick="switchHero(\'reaper\')"><span class="hero-glyph">🔥</span><span class="hero-name" data-i18n="hero.reaper.tab"></span></button>'),
    ("17.skills", '        <button id="skill-normal" class="skill-btn active" title="普通投擲" onclick="selectSkill(\'normal\')"><span>🎯</span><span class="btn-tip">普通</span></button>\n        <button id="skill-double" class="skill-btn" title="雙重投擲 (連續拋射兩發)" onclick="selectSkill(\'double\')"><span>💥</span><span class="btn-tip">雙發</span><span class="count-badge" id="badge-double">2</span></button>\n        <button id="skill-heavy" class="skill-btn" title="重型炸彈 (高爆範圍傷害)" onclick="selectSkill(\'heavy\')"><span>💣</span><span class="btn-tip">重彈</span><span class="count-badge" id="badge-heavy">2</span></button>\n        <button id="skill-heal" class="skill-btn" title="萬聖糖果回血 (+35 HP)" onclick="selectSkill(\'heal\')"><span>🧪</span><span class="btn-tip">回血</span><span class="count-badge" id="badge-heal">2</span></button>\n        <button id="skill-ult" class="skill-btn is-locked" title="大招：三格能量全亮才能用，點一下準備，再點取消" onclick="toggleUltimate()"><span>✨</span><span class="btn-tip">大招</span></button>', '        <button id="skill-normal" class="skill-btn active" data-i18n-attr="title:skill.normalTitle" onclick="selectSkill(\'normal\')"><span>🎯</span><span class="btn-tip" data-i18n="skill.normalTip"></span></button>\n        <button id="skill-double" class="skill-btn" data-i18n-attr="title:skill.doubleTitle" onclick="selectSkill(\'double\')"><span>💥</span><span class="btn-tip" data-i18n="skill.doubleTip"></span><span class="count-badge" id="badge-double">2</span></button>\n        <button id="skill-heavy" class="skill-btn" data-i18n-attr="title:skill.heavyTitle" onclick="selectSkill(\'heavy\')"><span>💣</span><span class="btn-tip" data-i18n="skill.heavyTip"></span><span class="count-badge" id="badge-heavy">2</span></button>\n        <button id="skill-heal" class="skill-btn" data-i18n-attr="title:skill.healTitle" onclick="selectSkill(\'heal\')"><span>🧪</span><span class="btn-tip" data-i18n="skill.healTip"></span><span class="count-badge" id="badge-heal">2</span></button>\n        <button id="skill-ult" class="skill-btn is-locked" data-i18n-attr="title:skill.ultTitle" onclick="toggleUltimate()"><span>✨</span><span class="btn-tip" data-i18n="skill.ultTip"></span></button>'),
    ("18.shield-markup", '        <button id="skill-shield" class="skill-btn dock-hidden" title="浮空盾" onclick="toggleShieldDefend()"><span>🛡️</span><span class="btn-tip">浮空盾</span><span class="count-badge" id="badge-shield">4</span></button>', '        <button id="skill-shield" class="skill-btn dock-hidden" data-i18n-attr="title:skill.shield" onclick="toggleShieldDefend()"><span>🛡️</span><span class="btn-tip" data-i18n="skill.shield"></span><span class="count-badge" id="badge-shield">4</span></button>'),
    ("19.readouts", '        <div class="dock-plate dock-angle"><span class="dock-label">角度</span><span class="dock-value" id="dock-angle-value">55°</span></div>\n        <div class="dock-plate dock-power">\n          <div class="dock-power-head"><span class="dock-label">力度</span><span class="dock-value" id="dock-power-value">0</span></div>\n          <div class="power-meter" id="dock-power" style="--power:0"><i class="power-track"></i><i class="power-fill"></i></div>\n        </div>\n      </div>\n      <i class="dock-sep"></i>\n      <button class="dock-lock" id="dock-lock" title="鎖定盾牌位置" hidden onclick="toggleShieldDefend()">鎖定</button>', '        <div class="dock-plate dock-angle"><span class="dock-label" data-i18n="dock.angle"></span><span class="dock-value" id="dock-angle-value">55°</span></div>\n        <div class="dock-plate dock-power">\n          <div class="dock-power-head"><span class="dock-label" data-i18n="dock.power"></span><span class="dock-value" id="dock-power-value">0</span></div>\n          <div class="power-meter" id="dock-power" style="--power:0"><i class="power-track"></i><i class="power-fill"></i></div>\n        </div>\n      </div>\n      <i class="dock-sep"></i>\n      <button class="dock-lock" id="dock-lock" data-i18n-attr="title:dock.lockTitle" data-i18n="dock.lock" hidden onclick="toggleShieldDefend()"></button>'),
    ("20.blurbs", '      skeleton: "標槍：傷害 24，命中附「霜咒」，被擊中的單位接下來 2 次攻擊 −15%。",\n      wizard: "南瓜砲：傷害 28，彈道高、威力大，是最直接的輸出。",\n      bat: "手裡劍：一次射出 5 枚，散落一小片範圍，每枚 8 傷害，中幾枚算幾枚。",\n      knight: "彈跳小盾：骰子決定 1 到 6 次碰撞，總傷害平均分給每次碰撞；也能放浮空盾防禦。",\n      reaper: "紫色鬼火：掌心推出一團火焰，傷害 23，彈道平直輕快；背後的三團鬼火是他的能量。"', '      skeleton: "hero.skeleton.blurb",\n      wizard: "hero.wizard.blurb",\n      bat: "hero.bat.blurb",\n      knight: "hero.knight.blurb",\n      reaper: "hero.reaper.blurb"'),
    ("21.blurb-lookup", '${HERO_BLURB[k]}', '${T(HERO_BLURB[k])}'),
    ("22.coming-heroes", '      { glyph: "👰", name: "鬼娃新娘", blurb: "音波攻擊：尖叫放出音波環，攻擊範圍寬，飛行路徑上都會受傷。" },\n      { glyph: "🔔", name: "鐘樓怪人", blurb: "巨斧：又重又慢，一擊傷害大。（外型：灰綠皮膚的壯碩怪人，衣服破爛）" }', '      { glyph: "👰", get name() { return T("hero.bride.name"); }, get blurb() { return T("hero.bride.blurb"); } },\n      { glyph: "🔔", get name() { return T("hero.hunchback.name"); }, get blurb() { return T("hero.hunchback.blurb"); } }'),
    ("23.scenes", '      { id: "graveyard", name: "月夜墓園", bg: "assets/env/bg_graveyard.png" },\n      { id: "belltower", name: "鐘樓", bg: "assets/env/bg_belltower.png" },\n      { id: "pumpkin", name: "南瓜田", bg: "assets/env/bg_pumpkin_field.png" }', '      { id: "graveyard", get name() { return T("scene.graveyard.name"); }, bg: "assets/env/bg_graveyard.png" },\n      { id: "belltower", get name() { return T("scene.belltower.name"); }, bg: "assets/env/bg_belltower.png" },\n      { id: "pumpkin", get name() { return T("scene.pumpkin.name"); }, bg: "assets/env/bg_pumpkin_field.png" }'),
    ("24.in-production", '<small>製作中</small>', '<small>${T("start.inProduction")}</small>'),
    ("24.scene-in-production", '${ok ? "" : "製作中"}', '${ok ? "" : T("start.inProduction")}'),
    ("25.preload-gate", '        if (keepLabel.t === undefined) keepLabel.t = b.textContent;\n        const done = settledCount >= IMG_TOTAL || performance.now() - t0 > 15000;\n        if (done) { if (b.dataset.gate === "1") { b.disabled = false; b.textContent = keepLabel.t; delete b.dataset.gate; } return; }\n        b.disabled = true; b.dataset.gate = "1"; b.textContent = `載入中 ${settledCount}/${IMG_TOTAL}`;', '        const done = settledCount >= IMG_TOTAL || performance.now() - t0 > 15000;\n        if (done) { if (b.dataset.gate === "1") { b.disabled = false; b.textContent = T("start.go"); delete b.dataset.gate; } return; }\n        b.disabled = true; b.dataset.gate = "1"; b.textContent = T("start.loading", { done: settledCount, total: IMG_TOTAL });'),
    ("26.profiles", '        name: "骷髏長矛兵",', '        get name() { return T("hero.skeleton.name"); },'),
    ("26.wizard", '        name: "南瓜巫師",', '        get name() { return T("hero.wizard.name"); },'),
    ("26.bat", '        name: "蝙蝠刺客",', '        get name() { return T("hero.bat.name"); },'),
    ("26.reaper", '        name: "死靈法師",   // id stays reaper (owner renamed the reaper to the necromancer; flame magic, no scythe)', '        get name() { return T("hero.reaper.name"); },   // id stays reaper (owner renamed the reaper to the necromancer; flame magic, no scythe)'),
    ("26.knight", '        name: "南瓜重裝盾衛",', '        get name() { return T("hero.knight.name"); },'),
    ("27.ultimate-toasts", 'text: "🔧 這個職業的大招還在製作中"', 'text: T("ult.unbuilt")'),
    ("27.cancel", 'text: "大招取消"', 'text: T("ult.cancel")'),
    ("27.energy", 'text: ultUsed.player >= 2 ? "大招已用完" : "能量未滿（要打中 3 次）"', 'text: ultUsed.player >= 2 ? T("ult.spent") : T("ult.noEnergy")'),
    ("27.armed", 'text: "✨ 大招已準備：下一發出手"', 'text: T("ult.armed")'),
    ("28.menu", 'const items = [{ id: "move", label: "🎲 移動", col: "#ffd32a" }, { id: "attack", label: "🎯 攻擊", col: "#ff7675" }];\n      if (canControlShield()) items.push({ id: "defend", label: "🛡️ 防禦", col: "#4deeea" });', 'const items = [{ id: "move", label: T("menu.move"), col: "#ffd32a" }, { id: "attack", label: T("menu.attack"), col: "#ff7675" }];\n      if (canControlShield()) items.push({ id: "defend", label: T("menu.defend"), col: "#4deeea" });'),
    ("29.move-toasts", 'text: "🎯 移動游標瞄準，在場上按住蓄力，放開就投擲"', 'text: T("toast.aimHint")'),
    ("29.slowed", 'text: "減速：這回合不能移動"', 'text: T("toast.slowed")'),
    ("29.moved", 'text: "本回合已經移動過了，可以直接攻擊"', 'text: T("toast.alreadyMoved")'),
    ("29.move-help", 'text: "🎲 移動：選擇方向（← 後退 / → 前進，或點箭頭），再擲骰子決定距離。Esc 取消"', 'text: T("toast.moveHelp")'),
    ("29.move-cancel", 'text: "已取消移動"', 'text: T("toast.moveCancel")'),
    ("30.move-roll", 'text: `🎲 ${dir > 0 ? "前進" : "後退"}：擲骰子決定距離（移動完還可以攻擊）`', 'text: T("toast.moveRoll", { dir: T(dir > 0 ? "move.forward" : "move.back") })'),
    ("31.move-result", 'text: `🎲 ${d.final}：${o.dir > 0 ? "前進" : "後退"} ${moved} px${moved < o.steps * DICE_STEP_PX ? "（到邊界）" : ""}`', 'text: T("toast.moveResult", { roll: d.final, dir: T(o.dir > 0 ? "move.forward" : "move.back"), moved: moved, edge: moved < o.steps * DICE_STEP_PX ? T("move.atEdge") : "" })'),
    ("32.gap", 'text: `🎲 1-2 站位動態變化！雙方距離: ${Math.round(Math.abs(ai.targetX - player.targetX))} px`', 'text: T("toast.gapShift", { px: Math.round(Math.abs(ai.targetX - player.targetX)) })'),
    ("32.heal", 'text: "只能在自己的回合回血"', 'text: T("toast.healOwnTurn")'),
    ("32.hp-full", 'text: "血量已滿，不用回血"', 'text: T("toast.hpFull")'),
    ("32.healed", 'text: "🧪 生命恢復 +35 HP!"', 'text: T("toast.healed")'),
    ("33.guard", 'text: "🎃 只有南瓜盾衛能操控浮空防禦"', 'text: T("toast.guardOnly")'),
    ("33.shield-no-moves", 'text: "🛡️ 浮空盾移動次數用完了"', 'text: T("toast.shieldNoMoves")'),
    ("33.defend-help", 'text: "🛡️ 防禦模式：拖曳浮空盾到想擋的路徑，再按一次🛡️鎖定（本回合不能攻擊，Esc 取消）"', 'text: T("toast.defendHelp")'),
    ("33.defend-cancel", 'text: "已取消防禦模式"', 'text: T("toast.defendCancel")'),
    ("33.no-attack", 'text: "🛡️ 防禦模式中不能攻擊"', 'text: T("toast.noAttackInDefend")'),
    ("34.shield-lock", 'text: sp.snapped ? `🛡️ 卡在有效路徑！剩 ${sp.actions} 次移動、攔截 ${sp.charges} 次` : `🛡️ 已鎖定（不在記憶路徑上），剩 ${sp.actions} 次移動`', 'text: sp.snapped ? T("toast.shieldSnapped", { moves: sp.actions, charges: sp.charges }) : T("toast.shieldLocked", { moves: sp.actions })'),
    ("35.switch", 'text: `切換職業: ${HERO_PROFILES[heroKey].name}`', 'text: T("toast.switchHero", { name: HERO_PROFILES[heroKey].name })'),
    ("35.shield-tips", '? "防禦（只有南瓜盾衛）：放棄攻擊，放置或移動浮空盾，拖曳後再按一次鎖定"\n        : "只有南瓜盾衛可以選擇防禦；其他職業只能攻擊或移動";', '? T("shield.tipGuard")\n        : T("shield.tipOther");'),
    ("36.frost", 'text: "🧊 被霜咒：傷害 -15%"', 'text: T("status.frostWeak")'),
    ("36.shuriken", 'text: "✨ 大招：手裡劍雨"', 'text: T("ult.shuriken")'),
    ("36.spear", 'text: "✨ 大招：三連標槍"', 'text: T("ult.spear")'),
    ("36.cannon", 'text: "✨ 大招：南瓜連環爆"', 'text: T("ult.cannon")'),
    ("36.soulfire", 'text: "✨ 大招：三發鬼火"', 'text: T("ult.soulfire")'),
    ("37.bounce", 'text: `🎲 ${pj.bounceN} 彈 · 每彈 ${pj.bounceDmg}`', 'text: T("toast.bounce", { n: pj.bounceN, dmg: pj.bounceDmg })'),
    ("37.flip", 'text: `↔ 全部角色水平翻轉：${flipAllArt ? "開" : "關"}`', 'text: T("toast.flip", { state: T(flipAllArt ? "toast.flipOn" : "toast.flipOff") })'),
    ("38.hallu-active", 'text: "😵 幻覺中：這回合不能行動"', 'text: T("status.halluActive")'),
    ("38.ai-shield", 'text: "AI 浮空盾切入軌跡（防禦回合，不攻擊）"', 'text: T("toast.aiShield")'),
    ("38.hallu-applied", 'text: "😵 幻覺：下回合停止"', 'text: T("status.halluApplied")'),
    ("39.stun-timer", 'text: "⭐ 暈眩！只剩 " + STUN_SECONDS + " 秒"', 'text: T("status.stunTimer", { sec: STUN_SECONDS })'),
    ("39.stun", 'text: "⭐ 暈眩"', 'text: T("status.stun")'),
    ("39.crit", 'text: "💥 爆擊！"', 'text: T("status.crit")'),
    ("40.shield-expired", 'text: "🛡️ 浮空盾 2 回合防禦期滿收回"', 'text: T("shield.expired")'),
    ("40.shield-holding", 'text: `🛡️ 浮空盾持續防禦中 (剩餘 ${s.durationRounds} 輪)`', 'text: T("shield.holding", { rounds: s.durationRounds })'),
    ("40.shield-blocked", 'text: `🛡️ 凌空預判攔截！(0 傷害！防禦餘 ${shield.durationRounds} 輪)`', 'text: T("shield.blocked", { rounds: shield.durationRounds })'),
    ("41.reset-locked", 'text: "🔒 第 " + RESET_LAST_ROUND + " 回合後不能重置"', 'text: T("toast.resetLocked", { n: RESET_LAST_ROUND })'),
    ("42.supply-labels", 'heal:  { icon: "🧪", label: "補血 +30", use:', 'heal:  { icon: "🧪", labelKey: "supply.heal", use:'),
    ("42.supply-heavy", 'heavy: { icon: "💣", label: "重彈 +1",  use:', 'heavy: { icon: "💣", labelKey: "supply.heavy",  use:'),
    ("43.pickup", 'text: SUPPLY_ITEMS[d.item].icon + " 拿到物資：" + SUPPLY_ITEMS[d.item].label', 'text: T("toast.pickup", { icon: SUPPLY_ITEMS[d.item].icon, label: T(SUPPLY_ITEMS[d.item].labelKey) })'),
    ("43.ai-pickup", 'text: "對手撿到物資"', 'text: T("toast.aiPickup")'),
    ("44.poison", 'text: "☠ 中毒"', 'text: T("status.poison")'),
    ("44.bleed", 'text: "🩸 流血"', 'text: T("status.bleed")'),
    ("45.reset-title", 'rb.title = ok ? "重新對戰（只有前 " + RESET_LAST_ROUND + " 個回合能按）" : "已鎖定：第 " + RESET_LAST_ROUND + " 回合後不能重置";', 'rb.title = ok ? T("dock.resetTitle", { n: RESET_LAST_ROUND }) : T("dock.resetLockedTitle", { n: RESET_LAST_ROUND });'),
    ("46.ultimate-title", 'ub.title = ultUsed.player >= 2 ? "大招已用完（一場最多 2 次）" : energy.player >= 3 ? (ultArmed.player ? "大招已準備：下一發出手（再點取消）" : "三格已亮：點一下準備大招") : "大招：要先命中 3 次點亮三格（目前 " + energy.player + "/3）";', 'ub.title = ultUsed.player >= 2 ? T("ult.titleUsedUp") : energy.player >= 3 ? (ultArmed.player ? T("ult.titleArmed") : T("ult.titleReady")) : T("ult.titleCharging", { n: energy.player });'),
    ("47.timeout", 'text: "⏱ 逾時！本回合棄權"', 'text: T("toast.timeout")'),
    ("47.fence", 'text: wallHp > 0 ? "💥 圍籬攔截！" : "💥 圍籬被打壞了！"', 'text: wallHp > 0 ? T("toast.fenceBlock") : T("toast.fenceBroken")'),
    ("48.triple-hit", 'text: "💥 三連全中！"', 'text: T("ult.tripleHit")'),
    ("48.slow-next", 'text: "減速：下回合不能移動"', 'text: T("status.slowNext")'),
    ("48.direct-hit", 'text: `💥 直擊 -${dmgNow}!`', 'text: T("toast.directHit", { dmg: dmgNow })'),
    ("48.frost-applied", 'text: "🧊 霜咒：攻擊 -15%（2 次）"', 'text: T("status.frostApplied")'),
    ("49.mud", 'text: "泥土偏斜"', 'text: T("toast.mudDeflect")'),
    ("49.shield-stuck", 'text: "盾插進地板，不能再彈了"', 'text: T("toast.shieldStuck")'),
    ("49.blast", 'text: "🔥 爆炸 -" + p.ultBlast', 'text: T("ult.blast", { dmg: p.ultBlast })'),
    ("49.rearm", 'text: "🔄 補給武器"', 'text: T("toast.rearm")'),
    ("50.player-shield-label", 'drawAirborneShield(shields.player, "#e67e22", "#ffd32a", "我方浮空盾");', 'drawAirborneShield(shields.player, "#e67e22", "#ffd32a");'),
    ("50.ai-shield-label", 'drawAirborneShield(shields.ai, "#00cec9", "#81ecec", "AI 浮空盾（被看穿了）");', 'drawAirborneShield(shields.ai, "#00cec9", "#81ecec");'),
    ("51.trail", 'ctx.fillText(`軌跡 [R${traj.round}]`, traj.landingX, traj.landingY - 12);', 'ctx.fillText(T("hud.trailTag", { round: traj.round }), traj.landingX, traj.landingY - 12);'),
    ("51.shield-text", 'ctx.fillText(s.preview ? "左右拖曳，沿著路徑滑動" : `剩 ${s.durationRounds} 輪`, 0, top - 30);', 'ctx.fillText(s.preview ? T("shield.dragHint") : T("shield.roundsLeft", { rounds: s.durationRounds }), 0, top - 30);'),
    ("51.shield-text-fallback", 'ctx.fillText(s.preview ? "左右拖曳，沿著路徑滑動" : `剩 ${s.durationRounds} 輪`, 0, -H / 2 - 30);', 'ctx.fillText(s.preview ? T("shield.dragHint") : T("shield.roundsLeft", { rounds: s.durationRounds }), 0, -H / 2 - 30);'),
    ("52.fence-art", 'ctx.fillText(wallHp > 0 ? `中央圍籬 (${wallHp}%)` : "圍籬已損毀", FENCE_X, GROUND_Y - dh - 10);', 'ctx.fillText(wallHp > 0 ? T("fence.label", { hp: wallHp }) : T("fence.broken"), FENCE_X, GROUND_Y - dh - 10);'),
    ("52.fence-fallback", 'ctx.fillText(wallHp > 0 ? `中央圍籬 (${wallHp}%)` : "圍籬已損毀", FENCE_X, top - 56);', 'ctx.fillText(wallHp > 0 ? T("fence.label", { hp: wallHp }) : T("fence.broken"), FENCE_X, top - 56);'),
    ("53.hud-labels", 'text("大招", right ? x + SW - 118 : x + 118, dyy + 17, 15, "#cfd8ff");', 'text(T("hud.ult"), right ? x + SW - 118 : x + 118, dyy + 17, 15, "#cfd8ff");'),
    ("53.you", 'nameOf(player, currentHero, "我方")', 'nameOf(player, currentHero, T("hud.you"))'),
    ("53.opponent", 'nameOf(ai, ai.profile || "skeleton", "對手")', 'nameOf(ai, ai.profile || "skeleton", T("hud.opponent"))'),
    ("54.countdown", 'text(`倒數 ${sec} 秒`, cx, cy + chh * 0.42, 28, col);', 'text(T("hud.countdown", { sec: sec }), cx, cy + chh * 0.42, 28, col);'),
    ("54.opponent-turn", 'else if (!gameOver) text("對手回合", cx, cy + chh * 0.42, 26, "#d3b6ff");', 'else if (!gameOver) text(T("hud.opponentTurn"), cx, cy + chh * 0.42, 26, "#d3b6ff");'),
    ("54.round", 'text(`第 ${roundNum} 回合 ・ 距離 ${Math.round(dist / DICE_STEP_PX)} 步`, cx, cy + chh * 0.82, 17, "#cfd8ff");', 'text(T("hud.round", { round: roundNum, dist: Math.round(dist / DICE_STEP_PX) }), cx, cy + chh * 0.82, 17, "#cfd8ff");'),
    ("55.move-buttons", 'for (const [dx, label, col] of [[-MOVE_BTN_DX, "◀ 後退", "#74b9ff"], [MOVE_BTN_DX, "前進 ▶", "#ffd32a"]]) {', 'for (const [dx, label, col] of [[-MOVE_BTN_DX, T("move.backBtn"), "#74b9ff"], [MOVE_BTN_DX, T("move.fwdBtn"), "#ffd32a"]]) {'),
    ("56.move-pointer", 'ctx.fillText(Math.abs(movePoint.val) < 0.18 ? "往左或往右指，放開擲骰" : (movePoint.val > 0 ? "放開：前進並擲骰" : "放開：後退並擲骰"), px, py + 52);', 'ctx.fillText(Math.abs(movePoint.val) < 0.18 ? T("move.aimNeutral") : (movePoint.val > 0 ? T("move.releaseFwd") : T("move.releaseBack")), px, py + 52);'),
    ("57.angle", 'ctx.fillText(`角度 ${playerAngle}°`, player.x, player.y - 232);', 'ctx.fillText(T("hud.angle", { angle: playerAngle }), player.x, player.y - 232);'),
    ("57.game-over", 'ctx.fillText(gameOver === "player" ? "🎃 你贏了！" : "💀 你輸了", CANVAS_W / 2, by + 66);', 'ctx.fillText(T(gameOver === "player" ? "gameover.win" : "gameover.lose"), CANVAS_W / 2, by + 66);'),
    ("57.restart", 'ctx.fillText("點一下畫面，回到選角重新開始", CANVAS_W / 2, by + 116);', 'ctx.fillText(T("gameover.restart"), CANVAS_W / 2, by + 116);'),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the checked transformation")
    parser.add_argument("--dry-run", action="store_true", help="check only (the default)")
    parser.add_argument("--file", type=Path, default=DEFAULT_PAGE, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.apply and args.dry_run:
        parser.error("choose --apply or --dry-run")
    return args


# Plan item 38 intentionally replaces both active-hallucination call sites.
EXPECTED_COUNTS = {"38.hallu-active": 2}


def status(source: str) -> tuple[list[tuple[str, str]], bool]:
    failures = []
    already_applied = 0
    for edit_id, old, new in EDITS:
        expected = EXPECTED_COUNTS.get(edit_id, 1)
        found = source.count(old)
        replacement_count = source.count(new)
        if replacement_count == expected and (found == 0 or old in new):
            already_applied += 1
            print(f"SKIP {edit_id} already applied")
        elif found == expected:
            print(f"OK {edit_id}")
        else:
            reason = f"expected {expected} old occurrence(s), found {found}"
            failures.append((edit_id, reason))
            print(f"FAIL {edit_id} {reason}")
    if already_applied == len(EDITS):
        print("NOTHING TO DO")
        return failures, True
    if already_applied:
        for edit_id, old, new in EDITS:
            expected = EXPECTED_COUNTS.get(edit_id, 1)
            if source.count(new) == expected and (source.count(old) == 0 or old in new):
                failures.append((edit_id, "partially applied page"))
        print("FAIL plan mixed applied and unapplied edits")
    return failures, False


def main() -> int:
    args = parse_args()
    page = args.file.resolve()
    try:
        source = page.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL read {exc}")
        return 1
    failures, complete = status(source)
    if failures:
        print(f"FAIL count={len(failures)}")
        return 1
    if complete:
        return 0
    print(f"OK count={len(EDITS)}")
    if not args.apply:
        return 0
    result = source
    for edit_id, old, new in EDITS:
        result = result.replace(old, new, EXPECTED_COUNTS.get(edit_id, 1))
    if result == source:
        print("FAIL no changes produced")
        return 1
    backup_dir = (ROOT / "docs" / "audition") if page == DEFAULT_PAGE else page.parent / "docs" / "audition"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"backup_index_i18n_{stamp}.html"
    shutil.copy2(page, backup)
    page.write_text(result, encoding="utf-8")
    print(f"APPLIED count={len(EDITS)} backup={backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
