# Pumpkin Killer: 中英文映射表 / i18n mapping table (2026-11-16)

Machine-readable twin: `docs/i18n_mapping_table_20261116.json` (same rows, plus per-surface measurements and proposals). Older draft: `docs/i18n_mapping_20261115.md` (superseded for status, kept for the format decisions).

Generated 2026-11-16 03:08 from a snapshot of `index.html` (3517 lines, sha256 `e7a221c5f960`), `assets/i18n/en.json` (`8bc967c97e67`), `assets/i18n/zh-TW.json` (`4cd5f57a4982`). The main line was editing these files while this ran: `where` line numbers are valid for the snapshot only, so look rows up by key.

## 0. Result
- 181 i18n keys; zh-TW and en have the same key set (no key exists in one file only); every `T()` / `data-i18n` key used in `index.html` exists in both. Page is already wired: every Chinese character left in `index.html` sits in a code comment (no Chinese string literal).
- Status over all 196 rows (keys + 15 strings outside the JSON): HARDCODED 4, MISMATCH 3, MISSING_ZH 3, OK 164, TERM_INCONSISTENT 22.
- Code check (does the text still describe the game?): STALE 5 (`hero.bat.blurb`, `hero.wizard.blurb`, `help.guard`, `help.wind`, `shield.tipGuard`), INCOMPLETE 2 (`hero.skeleton.blurb`, `hero.reaper.blurb`).
- **BUG:** `useSupply()` prints "🧪 undefined" (it reads `it.label`; `SUPPLY_ITEMS` now only has `labelKey`). Fix: `T(it.labelKey)`.
- Two heroes carry two different names: the Guard (南瓜重裝盾衛 / 南瓜盾衛 / 盾衛; Heavy Pumpkin Guard / Pumpkin Guard / Guard) and the Bat Assassin (page "Bat Assassin", docs and owner brief "Bat-cat Assassin").
- English overflows (measured): 20 surface checks over budget, 3 of them the reviewer-confirmed ones; section 3 has a shorter English for each.
- No disease name anywhere in the UI strings (checked zh and en). Traditional characters only (no Simplified form found).

### Status legend
OK = both languages exist and mean the same. MISSING_EN / MISSING_ZH = one side absent. HARDCODED = text not in the i18n files (must be moved, or confirmed language-neutral/unused). MISMATCH = zh and en differ in meaning (or the placeholder/number sets differ). TERM_INCONSISTENT = same concept named two ways. Extra column **code**: `ok` / `STALE` (both languages agree with each other but not with the game) / `INCOMPLETE` / `BUG`.

## 1. Where the width limits come from
Measured with the real font files (method and calibration in the JSON `meta.method`): gameover.restart 580 px (reviewer ~576), shield.expired 574 px (reviewer ~573), storm line 450 px with a one-digit round (reviewer 445). Accuracy about +-3 %. Chinese is counted 1 em per character (PK Body has no CJK glyphs; the browser falls back to PingFang TC / Microsoft JhengHei / Noto Sans TC).

| Surface | Font | Limit used | Source |
|---|---|---|---|
| Result panel line / title | 20 px body / 44 px display | 520 (hard 560) | panel `bw = 560` in `drawRuleOverlay` |
| HUD centre piece (countdown, round, weather) | 28 / 17 / 15 px | 400 (hard 440) | `CW = 440` in `drawTopHUD` |
| Unit-anchored popup (`floatTexts`) | 18 px bold | 560 | reviewer threshold; units stand at x 160..760 (player) / 1160..1760 (AI), so a popup wider than 2 x x is clipped by the canvas edge |
| Centred popup (`x = CANVAS_W / 2`) | 18 px bold | 900 (soft) | my estimate; canvas is 1920 wide |
| Action menu button | 20 px bold | 96 | button `w = 108` |
| Move arrow button | 20 px bold | 92 | button 104 px |
| Dock hero chip caption | 12 px serif, nowrap | 40 | chip `--chip: 44px` |
| Dock skill tile caption | 12 px serif | 54 | tile `--tile-w: 60px` |
| Dock hero name | 17 px serif, nowrap | 140 | `dock-id` 182 px minus HP% (desktop tier only; hidden below 1200 px) |
| Help pill line | 11 px | 440 (2 lines) | pill `width: min(250px,52%)`, wraps |
| Start card name / scene card name | 17 px | 162 (wraps) / 180 | card 190 px, padding 12; scene card 200 px |

Robust fix that makes length a non-issue for all languages: clamp `ft.x` in the popup draw loop (`index.html`, "10. Floating Text Popups") to `[w/2 + 12, CANVAS_W - w/2 - 12]` using `ctx.measureText`. The shorter strings below are still worth taking: long toasts are also hard to read at 18 px.

## 2. TERMS: one canonical term per game term
Owner rules applied: a pale ghost-white nun (art only; no UI string mentions colour), no disease names, poison may be called curse, Chinese stays Traditional. US English proposed for all English (page already mixes both).

### Heroes (names the page uses; internal id in brackets)

| Concept | zh-TW canonical | English canonical | Short form (tab/chip) | Variants found | Verdict | Action |
|---|---|---|---|---|---|---|
| Skeleton Spearman (id skeleton) | 骷髏長矛兵 | Skeleton Spearman | 骷髏 / Skeleton (chip: Bones) | page: consistent. docs: "Skeleton Spearman" 12 files. | OK | Note: weapon/ultimate are javelins (標槍 / Javelin). |
| Pumpkin Wizard (id wizard) | 南瓜巫師 | Pumpkin Wizard | 巫師 / Wizard (chip: Mage) | consistent everywhere. | OK | - |
| Bat Assassin (id bat) | 蝙蝠刺客 | Bat Assassin | 刺客 / Assassin (chip: Bat) | page: Bat Assassin / 蝙蝠刺客. Docs: "Bat-cat Assassin" 9 files, "Cat-bat" 18 files, 蝙蝠貓 8 files. Code comments say "cat-bat". | TERM_INCONSISTENT | Two names for one hero (page vs (not published) brief "bat-cat assassin"). Default: keep the page name "Bat Assassin" (no cat in the art/name); owner to confirm, then rename docs. |
| Pumpkin Guard (id knight) | 南瓜盾衛 | Pumpkin Guard | 盾衛 / Guard | page: 南瓜重裝盾衛/Heavy Pumpkin Guard (hero.knight.name: start card, dock, HUD, popup), 南瓜盾衛/Pumpkin Guard (tooltip, shield.tipGuard, toast.guardOnly), 盾衛/Guard (chip, help). Docs: "Pumpkin Guard" 16 files, "Heavy Pumpkin Guard" 1, "Pumpkin Knight" 6 (old). | TERM_INCONSISTENT | Flagged: hero called two different names. Recommend 南瓜盾衛 / Pumpkin Guard as the one full name (drop 重裝/Heavy); 盾衛/Guard stays as the short form. Owner decision (zh name is theirs). |
| Necromancer (id reaper) | 死靈法師 | Necromancer | 死靈 / Necro | page consistent. Docs: "Grim Reaper" 8 files, 死神 13 files (old names). Internal id stays reaper. | OK | Never show "Reaper"/死神 in the UI. |
| Ghost Bride (id bride) | 鬼娃新娘 | Ghost Bride | 新娘 / Bride | consistent. | OK | Her ultimate is "Bat Swarm" (蝙蝠群): not the Bat Assassin's. |
| Bell Tower Hunchback (id hunchback) | 鐘樓怪人 | Bell Tower Hunchback | 怪人 / Hunchback (chip: Bell) | page: "Bell Tower" two words (also scene.belltower.name). Docs: "Bell-tower Hunchback" 18 files (hyphen). | OK | Hyphenation differs only in docs. |
| Ghost Nun (id hag) | 鬼修女 | Ghost Nun | 修女 / Nun | consistent on the page. Internal id "hag" appears in file names and code only. | OK | Never show "Hag" in the UI. Owner rule (pale ghost-white nun) is art/prompt only; no UI string mentions colour or any disease. |

### Statuses

| Concept | zh-TW canonical | English canonical | Short form (tab/chip) | Variants found | Verdict | Action |
|---|---|---|---|---|---|---|
| Bleed | 流血 | Bleed |  | status.bleed only. | OK | Applied by javelin and axe (2 rounds). |
| Poison (owner: may be called curse) | 中毒 | Poison |  | status.poison; hero.bride.blurb 中毒/Poisons. | OK | Keep Poison. If the owner renames it to Curse (詛咒), Frost Curse (霜咒) would sit beside it; keep the two words distinct. |
| Stun | 暈眩 | Stun |  | status.stun, status.stunTimer, help.crit: consistent. | OK | Plain gameplay word, not a disease name. |
| Slow | 減速 | Slow |  | toast.slowed, status.slowNext: consistent. Effect = cannot move for one round. | OK | No standalone badge text (only a chain at the feet). |
| Frost Curse (code: weak) | 霜咒 | Frost Curse |  | status.frostWeak says 傷害/damage, status.frostApplied says 攻擊/attacks. | TERM_INCONSISTENT | Use "damage -15%" in both (proposal in table). |
| Burn | 灼燒 | Burn |  | status.burn only (new). | OK | Not mentioned in hero.reaper.blurb (proposal in table). |
| Hallucination | 幻覺 | Hallucination |  | status.halluActive / status.halluApplied: consistent. | OK | Not a disease name; alternative plain word "Daze" if the owner wants zero symptom words. |
| Crit / Knockback | 爆擊 / 擊退 | Crit / Knocked back |  | consistent. | OK | - |

### Ultimate and energy

| Concept | zh-TW canonical | English canonical | Short form (tab/chip) | Variants found | Verdict | Action |
|---|---|---|---|---|---|---|
| Ultimate (generic) | 大招 | Ultimate | 大招 / Ult (tile caption) | consistent; only the tile caption is abbreviated (proposal). | OK | - |
| Energy pips (three, one per hit) | 能量 / 三格 (能量格) | Energy / pips |  | zh uses 能量 (skill.ultTitle, ult.noEnergy) and 三格 (help.ult, ult.titleReady); English uses Energy and "pips". Needs 3 hits; max 2 per match. | OK | Canonical: 能量格 / Energy pip. No change required. |
| Bat Assassin ultimate | 手裡劍雨 | Shuriken Rain |  | ult.shuriken. | OK | - |
| Skeleton Spearman ultimate | 三連標槍 | Triple Javelin |  | ult.spear. | OK | - |
| Pumpkin Wizard ultimate | 南瓜連環爆 | Pumpkin Chain Blast |  | ult.cannon. | OK | - |
| Bell Tower Hunchback ultimate | 迴旋巨斧 | Boomerang Axe |  | ult.boomerang; blurb says 巨斧 / Giant axe. | OK | - |
| Ghost Nun ultimate | 銀十字連擊 | Silver Cross Strike |  | ult.nun; 連擊 = combo. | MISMATCH | English -> Silver Cross Combo. |
| Necromancer ultimate | 三發鬼火 | Triple Soulfire |  | ult.soulfire (Soulfire) vs hero.reaper.blurb (Ghost Flame). | TERM_INCONSISTENT | English -> Triple Ghost Flame. |
| Ghost Bride ultimate | 蝙蝠群 | Bat Swarm |  | ult.swarm. | OK | Bride owns it (owner 2026-11-16). |
| Pumpkin Guard ultimate | (no name string) | (no name string) |  | 7 of 8 heroes show "✨ 大招：<name>" when cast; the Guard shows nothing at cast time, only knightUlt.place / locked / blocked. | MISSING_ZH | Proposal: key ult.knight zh "✨ 大招：隱藏防禦點" / en "✨ Ultimate: Hidden Defense Points" (owner approves the name). |

### Wall, wind, weather, shield

| Concept | zh-TW canonical | English canonical | Short form (tab/chip) | Variants found | Verdict | Action |
|---|---|---|---|---|---|---|
| Fence (code: wall) | 圍籬 (中央圍籬) | Fence (Center Fence) |  | fence.label, fence.broken, toast.fenceBlock, toast.fenceBroken: consistent. Code and some docs say "wall" / "picket fence". | OK | UI never says wall. |
| Floating Shield | 浮空盾 | Floating Shield |  | 浮空盾 in 12 strings; toast.defendHelp also says 盾牌 + 棺材 (shield + coffin); HANDOFF says 浮空棺. | TERM_INCONSISTENT | Rule text: 浮空盾 / Floating Shield. The coffin is the art: name it only in the help line that teaches dragging (proposal in help.guard / toast.defendHelp). |
| Wind | 風 | Wind |  | help.wind, weather.storm (風更強 / stronger wind), hud.weather. | OK | - |
| Wind ghost (the wind indicator) | 風鬼 | wind ghost |  | Docs 19 + 21 files; no on-screen word. help.wind says "arrow" which does not exist. | TERM_INCONSISTENT | Teach it as 風鬼 / wind ghost in help.wind (proposal). |
| Headwind / tailwind | 逆風 / 順風 | Headwind / Tailwind |  | Docs: 逆風 9, 順風 11. No UI string at all (code: headwind drags more, WIND_HEAD 84 vs WIND_TAIL 56). | MISSING_EN | Add to help.wind (proposal) or leave to the ghost; either way these are the two words. |
| Weather | 天氣 (晴 / 下雨 / 下雪 / 暴風雨 / 起霧) | Weather (Clear / Rain / Snow / Storm / Fog) |  | weather.* + hud.weather: consistent. | OK | Storm wording shortened (proposal). |
| Trail (remembered path) | 軌跡 / 有效路徑 | Trail / valid path |  | hud.trailTag, toast.aiShield, toast.shieldSnapped. | OK | - |

### General wording

| Concept | zh-TW canonical | English canonical | Short form (tab/chip) | Variants found | Verdict | Action |
|---|---|---|---|---|---|---|
| Round | 回合 | Round |  | zh: 回合 in 5 strings, 輪 in 3 (shield.*). English always Round. | TERM_INCONSISTENT | zh -> 回合 everywhere. |
| Character (what the player picks) | 角色 | character |  | 角色/character in 3 strings; 職業/class in 3 (toast.switchHero, ult.unbuilt, shield.tipOther). | TERM_INCONSISTENT | zh -> 角色, en -> character everywhere. |
| Opponent | 對手 | Opponent |  | toast.aiShield says "AI". | TERM_INCONSISTENT | Use 對手 / Opponent. |
| Heal | 回血 | Heal |  | supply.heal 補血 and toast.healed 生命恢復 vs 回血 in 4 strings. | TERM_INCONSISTENT | zh -> 回血. |
| Restart vs Reset | 重新對戰 | Restart |  | dock.resetTitle/aria: Restart match; dock.resetTip, toast.resetLocked, dock.resetLockedTitle: Reset/重置. | TERM_INCONSISTENT | Restart / 重新對戰 everywhere (chip caption is hidden). |
| Tap vs Click | 點 | Tap (canvas, help) / Click (hover tooltips) |  | en: "Click" in help.tapUnit, supply.title, ult titles; "Tap" in knightUlt.place. | TERM_INCONSISTENT | Rule in table notes. |
| English spelling | - | US English |  | UK: "defence" (knightUlt.place), "centre" (hero.bride.blurb); US: "defense" (shield.expired), "Center" (fence.label), "canceled". | TERM_INCONSISTENT | US everywhere. |
| Distance unit | 步 / px | steps / px |  | HUD (hud.round) in steps; toast.gapShift and toast.moveResult in px. | TERM_INCONSISTENT | P2: show steps in both toasts (needs code: divide by DICE_STEP_PX). |
| Supply (crate) | 物資 | Supply |  | consistent; AI label "Opp. Supply" is the only abbreviation. | OK | - |
| Move / Attack / Defend; Forward / Back | 移動 / 攻擊 / 防禦；前進 / 後退 | Move / Attack / Defend; Forward / Back |  | consistent. | OK | - |
| Timer | 倒數 N 秒 | Time left: N s |  | hud.countdown, status.stunTimer. | OK | - |

## 3. English that does not fit, with a shorter line
"clip" = nowrap DOM or canvas text that is cut or overlaps; "wrap" = DOM text that just wraps to a second line. Rows 1 to 3 are the ones the UI reviewer reported (marked "reviewer").

| # | Key | Surface | English now | px now | Limit | Proposed English | px after |
|---|---|---|---|---|---|---|---|
| 1 | `shield.expired` (reviewer) | canvas popup (floatTexts, unit-anchored) | 🛡️ Floating Shield's 2-round defense ended and it was withdrawn | 574.2 | 560 | 🛡️ Floating Shield expired after 2 rounds | 355.2 |
| 2 | `gameover.restart` (reviewer) | canvas result panel line (20px, panel 560 px) | Click anywhere to return to character select and play again | 580.2 | 520 | Click anywhere to pick a character and play again | 486.7 |
| 3 | `weather.storm` (reviewer) | assembled hud.weather line (15px, piece 440 px) | Storm (attacks -10%, stronger wind) | 458.4 | 400 | Storm (attacks -10%, wind up) | 414.1 |
| 4 | `skill.ultTip` | dock skill tile caption (DOM, 12px serif, tile 60px) | Ultimate | 57.9 | 54 | Ult | 20.3 |
| 5 | `toast.defendHelp` | canvas popup (floatTexts, centred) | 🛡️ Defend: drag the shield (coffin) along the arc and let go: it stays where you let go (… | 1052.6 | 900 | 🛡️ Defend: drag the coffin along the arc, let go to place it (no attack this round, Esc cancels) | 802.7 |
| 6 | `move.fwdBtn` | canvas move arrow button (20px, button 104 px) | Forward ▶ | 108.2 | 92 | Fwd ▶ | 66.4 |
| 7 | `toast.moveHelp` | canvas popup (floatTexts, centred) | 🎲 Move: choose a direction (← back / → forward, or click an arrow), then roll the die for… | 974.6 | 900 | 🎲 Move: pick a direction (← back / → forward, or an arrow), then roll for distance. Esc cancels | 824.6 |
| 8 | `toast.moveRoll` | canvas popup (floatTexts, unit-anchored) | 🎲 {dir}: roll the die for distance (you can still attack after moving) | 615.0 | 560 | 🎲 {dir}: rolling for distance (you can still attack) | 459.4 |
| 9 | `toast.aimHint` | canvas popup (floatTexts, unit-anchored) | 🎯 Move the cursor to aim, hold on the field to charge, release to throw | 621.5 | 560 | 🎯 Move the cursor to aim, hold to charge, release to throw | 516.9 |
| 10 | `hero.skeleton.name` | start card name (17px) | Skeleton Spearman | 164.9 | 162 | (no string fix; wraps, acceptable) |  |
| 11 | `hero.skeleton.name` | dock hero name (17px serif, row 182 px shared with HP%) | Skeleton Spearman | 170.8 | 140 | (no string fix; CSS ellipsis / smaller caption) |  |
| 12 | `hero.wizard.name` | dock hero name (17px serif, row 182 px shared with HP%) | Pumpkin Wizard | 149.0 | 140 | (no string fix; CSS ellipsis / smaller caption) |  |
| 13 | `hero.knight.name` | start card name (17px) | Heavy Pumpkin Guard | 187.3 | 162 | Pumpkin Guard | 140.1 |
| 14 | `hero.knight.name` | dock hero name (17px serif, row 182 px shared with HP%) | Heavy Pumpkin Guard | 199.0 | 140 | Pumpkin Guard | 140.1 |
| 15 | `hero.skeleton.tab` | dock hero chip caption (12px serif, chip 44 px, nowrap) | Skeleton | 53.9 | 40 | Bones | 38.0 |
| 16 | `hero.wizard.tab` | dock hero chip caption (12px serif, chip 44 px, nowrap) | Wizard | 45.4 | 40 | Mage | 33.2 |
| 17 | `hero.bat.tab` | dock hero chip caption (12px serif, chip 44 px, nowrap) | Assassin | 53.3 | 40 | Bat | 21.0 |
| 18 | `hero.hunchback.name` | start card name (17px) | Bell Tower Hunchback | 187.9 | 162 | (no string fix; wraps, acceptable) |  |
| 19 | `hero.hunchback.name` | dock hero name (17px serif, row 182 px shared with HP%) | Bell Tower Hunchback | 198.9 | 140 | (no string fix; CSS ellipsis / smaller caption) |  |
| 20 | `hero.hunchback.tab` | dock hero chip caption (12px serif, chip 44 px, nowrap) | Hunchback | 70.8 | 40 | Bell | 24.2 |

Notes: the storm line after the fix (414 px) is under the hard 440 px but above my 400 px comfort line; if more room is wanted drop the "Weather: " prefix (`hud.weather` en: `{label} (until round {round})`). `hero.knight.name` after the fix (140 px) sits right at the dock budget; the dock row also needs `min-width:0; overflow:hidden; text-overflow:ellipsis` on `.dock-name` for Skeleton Spearman, Bell Tower Hunchback and Pumpkin Wizard (all over 140 px at 17 px serif). `move.fwdBtn`: either "Fwd ▶" or widen the canvas button from 104 to 124 px and keep "Forward ▶". Zh never overflows (largest: `toast.defendHelp` 703 px, centred).

## 4. Help text: help.guard (and the other stale help lines)
Code at snapshot: the Guard Ultimate asks for taps **1, 2, 3** (`knightMarks` letter = `String(n)`), three hidden points that each stop one shot within 70 px for 3 enemy rounds. The Guard's normal defence is **Defend** from the click menu, then **drag the shield (the coffin) along the arc and let go** (turn is spent, lasts 2 rounds, blocks 2 shots).

| Key | Now (zh-TW) | Now (en) | Proposed zh-TW | Proposed en |
|---|---|---|---|---|
| `help.guard` | 🛡 盾衛：點 A、B、C 預判三發 | 🛡 Guard: click A, B, C to predict three shots | 🛡 盾衛：拖曳棺材擋攻擊；大招點 1、2、3 設防 | 🛡 Guard: drag the coffin to block; Ultimate: tap 1, 2, 3 to set defense points |
| `help.wind` | 🌬 風看上方箭頭，風越強越偏 | 🌬 Check the wind above: stronger wind, bigger drift | 🌬 看上方風鬼：吹得越猛，風越強；逆風更吃力 | 🌬 Watch the wind ghost above: the harder it blows, the stronger the wind; headwind drags more |
| `shield.tipGuard` | 防禦（只有南瓜盾衛）：放棄攻擊，放置或移動浮空盾，拖曳後再按一次鎖定 | Defend (Pumpkin Guard only): give up your attack to place or move the Floating Shield; drag it, then press again to lock | 防禦（只有南瓜盾衛）：放棄攻擊，放置或移動浮空盾；沿弧線拖曳，放開就定位 | Defend (Pumpkin Guard only): give up your attack to place or move the Floating Shield; drag it along the arc and let go to set it |
| `help.tapUnit` | 👆 點角色：移動／攻擊／防禦 | 👆 Click your character: Move / Attack / Defend | 👆 點角色：移動／攻擊／防禦 | 👆 Tap your character: Move / Attack / Defend |

If one line is too tight for both halves of `help.guard`, split it: keep `help.guard` = "🛡 盾衛：拖曳棺材擋攻擊 / 🛡 Guard: drag the coffin to block" and add a seventh span `help.guardUlt` = "✨ 盾衛大招：點 1、2、3 設隱藏防禦點 / ✨ Guard Ultimate: tap 1, 2, 3 to set hidden defense points" (needs one more `<span data-i18n>` in `#instruction-pill`; the pill wraps, so 2 lines each is fine). `help.wind` proposal mentions headwind (逆風) because that is where the game is mean (drag 84 vs help 56 per wind unit).

## 5. Strings that are not in the i18n files
| Where | Text now | Status | Code | Note |
|---|---|---|---|---|
| index.html:1735 | (none: shows undefined) | HARDCODED | BUG | useSupply() builds the popup from it.label, but SUPPLY_ITEMS now has labelKey only, so the popup reads "🧪 undefined" in both languages. Fix: T(it.labelKey) (keys supply.heal / supply.heavy already exist). |
| manifest.webmanifest:name | Pumpkin Killer — classic cat-and-dog artillery feel ✕ floating-shield predictio… | MISSING_ZH | n/a | English only and 92 characters (home screens cut it at about 12-20). A manifest cannot switch language at run time. Proposal: name "Pumpkin Killer 南瓜殺手", short_name "南瓜殺手" or "Pumpkin Killer" (owner picks one); "lang" stays "en" unless the zh manifest is served separately. |
| manifest.webmanifest:short_name | Pumpkin Killer | MISSING_ZH | n/a | English only; add 南瓜殺手 in the same name field or ship a zh manifest. |
| index.html:9 | Pumpkin Killer | OK | ok | Static fallback only; replaced by page.title on load. page.title itself is 92 characters in English (tab shows about 30): proposal zh "南瓜殺手 Pumpkin Killer — 浮空盾預判 ✕ 軌跡記憶", en "Pumpkin Killer — floating-shield prediction ✕ trail memory" (drops 經典貓狗大戰手感 / classic cat-and-dog artillery feel: owner call). |
| index.html:1324 | ▲ ▼ | OK | ok | Language-neutral symbols, no translation needed. |
| index.html:2832 | ⭐ | OK | ok | Symbol only. The word is status.stun. |
| index.html:227 | ? | OK | ok | Symbol; title and aria-label come from dock.helpTitle / dock.helpAria. |
| index.html:1801, index.html:1933, index.html:2068 | -N | OK | ok | Numbers only. |
| index.html:3439 | ▶ N / ◀ N | OK | ok | Symbols and a number. |
| index.html:401 | (empty alt) | HARDCODED | a11y | alt="" is empty; screen readers skip the portrait. Optional: alt = hero name (already next to it in .nm, so empty is acceptable). |
| js/weather.js:18-22 | Clear / Rain / Snow / Storm / Fog | HARDCODED | unused | English-only labels that are never drawn. Safe to delete or leave; do not read them in new UI code. |
| js/class_stats.js:100-252 | (none) | HARDCODED | unused | Chinese hero names kept in a second place; if it ever reaches a screen or an MCP reply it will not follow the language switch. Its knight name is the long 南瓜重裝盾衛. |
| index.html (end of file) | Service worker registration failed: | OK | ok | Not player-facing. |
| scripts/mcp_game_server.py, scripts/mcp_stdio_server.py | (English only) | OK | n/a | Out of scope for the player UI mapping; not scanned in detail. |
| index.html knightBegin() / lockShield area (no popup with the ultimate name) | (missing) | MISSING_ZH | n/a | MISSING_EN too. The other 7 heroes show a named popup when the Ultimate fires; the Guard has none. Proposal: zh "✨ 大招：隱藏防禦點", en "✨ Ultimate: Hidden Defense Points" (owner approves the name). |

## 6. Full table (every key in assets/i18n)
`px` = English / zh-TW width at the surface font vs limit (worst surface for multi-surface keys; blank = tooltip, aria or no limit). Line numbers: snapshot. Notes are shortened here; the JSON has the full text, all measured surfaces and proposals.

### page.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `page.title` | Pumpkin Killer (南瓜殺手) — 經典貓狗大戰手感 ✕ 浮空盾預判 ✕ 軌跡記憶 | Pumpkin Killer — classic cat-and-dog artillery feel ✕ floating-shield prediction ✕ trail memory | 9 | browser tab title (document.title) |  | OK | ok |  |

### start.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `start.title` | 🎃 南瓜殺手 | 🎃 Pumpkin Killer | 212 | start screen h1 (DOM) | 331.0 / 166.4 / - | OK | ok |  |
| 3 | `start.pickHero` | 選一個角色（開局後不能換） | Pick a character (locked once the match starts) | 213 | start screen h2 (DOM) | 369.9 / 208.0 / - | OK | ok |  |
| 4 | `start.pickScene` | 選一個戰場 | Pick a battlefield | 215 | start screen h2 (DOM) | 133.4 / 80.0 / - | OK | ok |  |
| 5 | `start.go` | 開始戰鬥 | Start Battle | 217, 580 | start button (DOM) | 114.5 / 80.0 / - | OK | ok |  |
| 6 | `start.loading` | 載入中 {done}/{total} | Loading {done}/{total} | 581 | start button (DOM) | 150.9 / 131.3 / - | OK | ok |  |
| 7 | `start.inProduction` | 製作中 | In production | 408, 415 | grey card label (DOM; hidden while SHOW_COMING_SOON=false) | 83.8 / 37.5 / - | OK | ok |  |

### hero.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 8 | `hero.skeleton.name` | 骷髏長矛兵 | Skeleton Spearman | 248, 590 | start card name / dock hero name / HUD banner name / switch… | 164.9 / 85.0 / 162 OVER | OK | ok | Spearman, but the weapon and ultimate are javelins (標槍 / Javelin in hero.skeleton.blurb, ult.spear). Same split in Chinese (長矛兵 vs 標槍). Accepted: a s… |
| 9 | `hero.wizard.name` | 南瓜巫師 | Pumpkin Wizard | 249, 599 | start card name / dock hero name / HUD banner name / switch… | 149.0 / 68.0 / 140 OVER | OK | ok |  |
| 10 | `hero.bat.name` | 蝙蝠刺客 | Bat Assassin | 250, 608 | start card name / dock hero name / HUD banner name / switch… | 103.2 / 68.0 / 162 | TERM_INCONSISTENT | ok | Page says "Bat Assassin"; docs say "Bat-cat Assassin" (9 files) and "Cat-bat" (18 files); zh docs say 蝙蝠貓 (8). Owner to confirm which one; the page n… |
| 11 | `hero.knight.name` | 南瓜重裝盾衛 | Heavy Pumpkin Guard | 653 | start card name / dock hero name / HUD banner name / switch… | 187.3 / 102.0 / 162 OVER | TERM_INCONSISTENT | ok | Knight has 3 long names: 南瓜重裝盾衛/Heavy Pumpkin Guard (start card, dock, HUD, switch toast), 南瓜盾衛/Pumpkin Guard (tooltip, shield.tipGuard, toast.guardO… |
| 12 | `hero.knight.tabTitle` | 南瓜盾衛 | Pumpkin Guard | 251 | hero chip tooltip (title attr) |  | TERM_INCONSISTENT | ok | Second long name for the same hero (see hero.knight.name); proposal: make both keys identical or drop this key. |
| 13 | `hero.skeleton.tab` | 骷髏 | Skeleton | 248 | dock hero chip caption (DOM) | 53.9 / 24.0 / 40 OVER | OK | ok |  |
| 14 | `hero.wizard.tab` | 巫師 | Wizard | 249 | dock hero chip caption (DOM) | 45.4 / 24.0 / 40 OVER | OK | ok |  |
| 15 | `hero.bat.tab` | 刺客 | Assassin | 250 | dock hero chip caption (DOM) | 53.3 / 24.0 / 40 OVER | OK | ok |  |
| 16 | `hero.knight.tab` | 盾衛 | Guard | 251 | dock hero chip caption (DOM) | 39.2 / 24.0 / 40 | OK | ok |  |
| 17 | `hero.skeleton.blurb` | 標槍：傷害 24，命中附「霜咒」，被擊中的單位接下來 2 次攻擊 −15%。 | Javelin: 24 damage. A hit applies Frost Curse: the target's next 2 attacks deal −15%. | 373 | start card blurb (DOM) | 481.7 / 401.9 / - | OK | INCOMPLETE | CODE: Damage 24 and Frost Curse -15% x2 match the code; the javelin also makes the target bleed (applyBleed, 2 rounds) and the blurb does not say so. |
| 18 | `hero.wizard.blurb` | 南瓜砲：傷害 28，彈道高、威力大，是最直接的輸出。 | Pumpkin Cannon: 28 damage, high arc, big punch. The most direct damage dealer. | 374 | start card blurb (DOM) | 479.9 / 304.2 / - | OK | STALE | CODE: Says damage 28; HERO_PROFILES.wizard.dmg is 24 at snapshot (class_stats module/docs still say 28: owner to settle the number). Also omits that … |
| 19 | `hero.bat.blurb` | 手裡劍：一次射出 5 枚，散落一小片範圍，每枚 8 傷害，中幾枚算幾枚。 | Shuriken: throws 5 at once in a small spread, 8 damage each; every one that lands counts. | 375 | start card blurb (DOM) | 520.8 / 400.1 / - | OK | STALE | CODE: Both languages describe the old design (5 shuriken, 8 each). Code: the normal attack is ONE shuriken, damage 22 (HERO_PROFILES.bat.dmg), a hit … |
| 20 | `hero.knight.blurb` | 彈跳小盾：骰子決定 1 到 6 次碰撞，總傷害平均分給每次碰撞；也能放浮空盾防禦。 | Bouncing Shield: a die decides 1 to 6 collisions and the total damage is split evenly between them. It can al… | 376 | start card blurb (DOM) | 828.0 / 462.6 / - | OK | OK | CODE: Die decides 1-6 bounces, total 30 split evenly (HERO_PROFILES.knight.dmg 30, toast.bounce): consistent. |
| 21 | `hero.bride.name` | 鬼娃新娘 | Ghost Bride | 253, 383, 635 | start card name / dock hero name / HUD banner name / switch… | 98.2 / 68.0 / 162 | OK | ok |  |
| 22 | `hero.bride.tab` | 新娘 | Bride | 253 | dock hero chip caption (DOM) | 34.4 / 24.0 / 40 | OK | ok |  |
| 23 | `hero.bride.blurb` | 音波：尖叫放出音波環，只打瞄準的那一個目標，離中心越近傷害越高，命中會中毒。 | Sound wave: her scream sends out rings that hit only the unit it is aimed at; the closer to the centre, the h… | 378, 383 | start card blurb (DOM) | 742.8 / 475.0 / - | TERM_INCONSISTENT | ok | UK spelling "centre"; fence.label uses "Center". Use US spelling. |
| 24 | `hero.hunchback.name` | 鐘樓怪人 | Bell Tower Hunchback | 254, 384, 644 | start card name / dock hero name / HUD banner name / switch… | 187.9 / 68.0 / 162 OVER | OK | ok |  |
| 25 | `hero.hunchback.tab` | 怪人 | Hunchback | 254 | dock hero chip caption (DOM) | 70.8 / 24.0 / 40 OVER | OK | ok |  |
| 26 | `hero.hag.name` | 鬼修女 | Ghost Nun | 255, 626 | start card name / dock hero name / HUD banner name / switch… | 87.6 / 51.0 / 162 | OK | ok |  |
| 27 | `hero.hag.tab` | 修女 | Nun | 255 | dock hero chip caption (DOM) | 26.5 / 24.0 / 40 | OK | ok |  |
| 28 | `hero.hag.blurb` | 銀色十字：飄浮的鬼修女甩出纏著黑煙的旋轉銀十字，傷害 22，彈道平直輕快。 | Silver cross: a hovering ghost nun hurls a spinning silver cross wrapped in black smoke, 22 damage, flat and … | 380 | start card blurb (DOM) | 662.2 / 441.7 / - | OK | OK | CODE: 22 damage: matches HERO_PROFILES.hag.dmg. |
| 29 | `hero.hunchback.blurb` | 巨斧：旋轉飛出，傷害 21，命中會流血並擊退目標。 | Giant axe: heavy and spinning, 21 damage, makes the target bleed and knocks it back. | 379, 384 | start card blurb (DOM) | 499.1 / 291.7 / - | OK | OK | CODE: 21 damage, bleed, knock back 50 px: matches. |
| 30 | `hero.reaper.name` | 死靈法師 | Necromancer | 252, 617 | start card name / dock hero name / HUD banner name / switch… | 113.3 / 68.0 / 162 | OK | ok |  |
| 31 | `hero.reaper.tab` | 死靈 | Necro | 252 | dock hero chip caption (DOM) | 37.2 / 24.0 / 40 | OK | ok |  |
| 32 | `hero.reaper.blurb` | 紫色鬼火：掌心推出一團火焰，傷害 23，彈道平直輕快；背後的三團鬼火是他的能量。 | Purple Ghost Flame: pushes a ball of fire out of the palm, 23 damage, flat and light trajectory. The three gh… | 377 | start card blurb (DOM) | 832.6 / 479.2 / - | OK | INCOMPLETE | CODE: Damage 23 matches; the flame also applies Burn (2 damage x 3 rounds, never lethal) and the blurb does not say so. |

### scene.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 33 | `scene.graveyard.name` | 月夜墓園 | Moonlit Graveyard | 387 | start screen scene card name (DOM) | 155.8 / 68.0 / 180 | OK | ok |  |
| 34 | `scene.belltower.name` | 鐘樓 | Bell Tower | 388 | start screen scene card name (DOM) | 89.3 / 34.0 / 180 | OK | ok |  |
| 35 | `scene.church.name` | 廢墟教堂 | Ruined Church | 389 | start screen scene card name (DOM) | 123.3 / 68.0 / 180 | OK | ok |  |
| 36 | `scene.school.name` | 荒廢學校 | Abandoned School | 390 | start screen scene card name (DOM) | 157.3 / 68.0 / 180 | OK | ok |  |

### supply.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 37 | `supply.title` | 補充物資：撿到的箱子放這裡，點一下使用；新的會取代舊的 | Supply: a crate you pick up is stored here. Click to use it; a new one replaces the old one. | 220 | supply slot tooltip (title attr) |  | OK | ok |  |
| 38 | `supply.label` | 物資 | Supply | 220 | supply slot label above the box (DOM, 12px) | 41.3 / 24.0 / 90 | OK | ok |  |
| 39 | `supply.aiTitle` | 對手手上的物資（只看得到，不能用） | Opponent's supply (view only, cannot be used) | 221 | supply slot tooltip (title attr) |  | OK | ok |  |
| 40 | `supply.aiLabel` | 對手物資 | Opp. Supply | 221 | supply slot label above the box (DOM, 12px) | 72.7 / 48.0 / 90 | OK | ok |  |
| 41 | `supply.heal` | 補血 +30 | Heal +30 | 1715 | fragment of toast.pickup | 194.4 / 183.2 / 560 | TERM_INCONSISTENT | ok | zh uses 補血 / 生命恢復 here but 回血 in skill.healTip, skill.healTitle, toast.healOwnTurn, toast.hpFull. |
| 42 | `supply.heavy` | 重彈 +1 | Heavy +1 | 1716 | fragment of toast.pickup | 198.8 / 172.6 / 560 | OK | ok |  |

### dock.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 43 | `dock.soundTitle` | 音樂與音效開關（M） | Music and sound on/off (M) | 224 | top-controls / dock tooltip (title attr) |  | OK | ok |  |
| 44 | `dock.soundTip` | 聲音 | Sound | 224 | top-controls chip caption (CSS display:none, never shown) |  | OK | ok |  |
| 45 | `dock.resetTitle` | 重新對戰（只有前 {n} 個回合能按） | Restart match (only in the first {n} rounds) | 1845 | reset button tooltip (title attr) |  | OK | ok |  |
| 46 | `dock.resetLockedTitle` | 已鎖定：第 {n} 回合後不能重置 | Locked: reset is not available after round {n} | 1845 | top-controls / dock tooltip (title attr) |  | TERM_INCONSISTENT | ok | "Reset / 重置" here but "Restart match / 重新對戰" in dock.resetTitle and dock.resetAria. Pick one: 重新對戰 / Restart. |
| 47 | `dock.resetAria` | 重新對戰 | Restart match | 225 | aria-label (screen reader) |  | OK | ok |  |
| 48 | `dock.resetTip` | 重置 | Reset | 225 | top-controls chip caption (CSS display:none, never shown) |  | TERM_INCONSISTENT | ok | "Reset / 重置" here but "Restart match / 重新對戰" in dock.resetTitle and dock.resetAria. Pick one: 重新對戰 / Restart. |
| 49 | `dock.helpTitle` | 說明（H） | Help (H) | 227 | top-controls / dock tooltip (title attr) |  | OK | ok |  |
| 50 | `dock.helpAria` | 說明 | Help | 227 | aria-label (screen reader) |  | OK | ok |  |
| 51 | `dock.portraitAria` | 目前角色 | Current character | 243 | aria-label (screen reader) |  | OK | ok |  |
| 52 | `dock.angle` | 角度 | Angle | 271 | dock readout label (DOM, 12px serif) | 40.1 / 25.9 / 60 | OK | ok |  |
| 53 | `dock.power` | 力度 | Power | 273 | dock readout label (DOM, 12px serif) | 44.3 / 25.9 / 60 | OK | ok |  |
| 54 | `dock.lock` | 鎖定 | Lock | 278 | dock Lock button (DOM, 24px serif) | 59.6 / 48.0 / 100 | OK | ok |  |
| 55 | `dock.lockTitle` | 鎖定盾牌位置 | Lock shield position | 278 | top-controls / dock tooltip (title attr) |  | OK | ok |  |

### help.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 56 | `help.tapUnit` | 👆 點角色：移動／攻擊／防禦 | 👆 Click your character: Move / Attack / Defend | 230 | help pill line (DOM, 11px, pill 250px wide, max 2 lines) | 249.4 / 145.0 / 440 | TERM_INCONSISTENT | ok | English says "Click" while knightUlt.place says "Tap" (the game is played with a finger too). Rule proposed: "Tap" on the canvas and in the help pill… |
| 57 | `help.holdThrow` | 🎯 按住蓄力，放開投擲 | 🎯 Hold to charge, release to throw | 231 | help pill line (DOM, 11px, pill 250px wide, max 2 lines) | 187.2 / 112.0 / 440 | OK | ok |  |
| 58 | `help.wind` | 🌬 風看上方箭頭，風越強越偏 | 🌬 Check the wind above: stronger wind, bigger drift | 232 | help pill line (DOM, 11px, pill 250px wide, max 2 lines) | 281.2 / 145.0 / 440 | MISMATCH | STALE | zh says 看上方箭頭 (look at the arrow above) but en says "Check the wind above"; neither names the wind ghost. CODE: zh says arrow (箭頭), en says "the wind… |
| 59 | `help.crit` | 💥 打中頭部＝爆擊＋暈眩 | 💥 Head hit = Crit + Stun | 233 | help pill line (DOM, 11px, pill 250px wide, max 2 lines) | 127.3 / 123.0 / 440 | OK | ok |  |
| 60 | `help.ult` | ✨ 三格亮滿，按 U 放大招 | ✨ All three pips lit: press U for the Ultimate | 234 | help pill line (DOM, 11px, pill 250px wide, max 2 lines) | 233.3 / 125.2 / 440 | OK | ok |  |
| 61 | `help.guard` | 🛡 盾衛：點 A、B、C 預判三發 | 🛡 Guard: click A, B, C to predict three shots | 235 | help pill line (DOM, 11px, pill 250px wide, max 2 lines) | 233.1 / 149.7 / 440 | OK | STALE | CODE: Still says tap A, B, C to predict three shots. Code: the Guard Ultimate asks for taps 1, 2, 3 (knightMarks letter = String(n)); the normal defe… |

### skill.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 62 | `skill.normalTitle` | 普通投擲 | Normal throw | 261 | skill tile tooltip (title attr) |  | OK | ok |  |
| 63 | `skill.normalTip` | 普通 | Normal | 261 | dock skill tile caption (DOM, 12px serif, tile 60px) | 50.3 / 25.0 / 54 | OK | ok |  |
| 64 | `skill.doubleTitle` | 雙重投擲 (連續拋射兩發) | Double throw (two shots in a row) | 262 | skill tile tooltip (title attr) |  | OK | ok |  |
| 65 | `skill.doubleTip` | 雙發 | Double | 262 | dock skill tile caption (DOM, 12px serif, tile 60px) | 47.4 / 25.0 / 54 | OK | ok |  |
| 66 | `skill.heavyTitle` | 重型炸彈 (高爆範圍傷害) | Heavy bomb (high-explosive area damage) | 263 | skill tile tooltip (title attr) |  | OK | ok |  |
| 67 | `skill.heavyTip` | 重彈 | Heavy | 263 | dock skill tile caption (DOM, 12px serif, tile 60px) | 40.9 / 25.0 / 54 | OK | ok |  |
| 68 | `skill.healTitle` | 萬聖糖果回血 (+35 HP) | Halloween candy heal (+35 HP) | 264 | skill tile tooltip (title attr) |  | OK | ok |  |
| 69 | `skill.healTip` | 回血 | Heal | 264 | dock skill tile caption (DOM, 12px serif, tile 60px) | 31.0 / 25.0 / 54 | OK | ok |  |
| 70 | `skill.ultTitle` | 大招：三格能量全亮才能用，點一下準備，再點取消 | Ultimate: usable only when all three Energy pips are lit. Click to arm, click again to cancel | 265 | skill tile tooltip (title attr) |  | OK | ok |  |
| 71 | `skill.ultTip` | 大招 | Ultimate | 265 | dock skill tile caption (DOM, 12px serif, tile 60px) | 57.9 / 25.0 / 54 OVER | OK | ok |  |
| 72 | `skill.shield` | 浮空盾 | Floating Shield | 267 | Defend tile caption + tooltip (tile is dock-hidden, caption… | 100.6 / 37.4 / - | OK | ok |  |

### shield.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 73 | `shield.tipGuard` | 防禦（只有南瓜盾衛）：放棄攻擊，放置或移動浮空盾，拖曳後再按一次鎖定 | Defend (Pumpkin Guard only): give up your attack to place or move the Floating Shield; drag it, then press ag… | 1100 | Defend tile tooltip (title attr) |  | OK | STALE | CODE: Says "drag it, then press again to lock". Letting go places the shield (toast.defendHelp, lockShield from pointer-up); the second press is opti… |
| 74 | `shield.tipOther` | 只有南瓜盾衛可以選擇防禦；其他職業只能攻擊或移動 | Only the Pumpkin Guard can Defend; other classes can only Attack or Move | 1101 | Defend tile tooltip (title attr) |  | TERM_INCONSISTENT | ok | zh says 職業 / en says "class" here, but 角色 / "character" in start.pickHero, help.tapUnit, dock.portraitAria. One word for the player-facing concept: 角… |
| 75 | `shield.expired` | 🛡️ 浮空盾 2 回合防禦期滿收回 | 🛡️ Floating Shield's 2-round defense ended and it was withdrawn | 1620 | canvas popup (floatTexts, unit-anchored) | 574.2 / 238.0 / 560 OVER | OK | ok |  |
| 76 | `shield.holding` | 🛡️ 浮空盾持續防禦中 (剩餘 {rounds} 輪) | 🛡️ Floating Shield holding (rounds left: {rounds}) | 1623 | canvas popup (floatTexts, unit-anchored) | 362.2 / 255.8 / 560 | TERM_INCONSISTENT | ok | zh says 輪 for "round" here; 回合 everywhere else (hud.round, shield.expired, dock.resetTitle, toast.resetLocked). English always "round(s)". |
| 77 | `shield.blocked` | 🛡️ 凌空預判攔截！(0 傷害！防禦餘 {rounds} 輪) | 🛡️ Mid-air block! (0 damage! {rounds} rounds left) | 2003 | canvas popup (floatTexts, unit-anchored) | 370.6 / 320.4 / 560 | TERM_INCONSISTENT | ok | zh says 輪 for "round" here; 回合 everywhere else (hud.round, shield.expired, dock.resetTitle, toast.resetLocked). English always "round(s)". |
| 78 | `shield.dragHint` | 左右拖曳，沿著路徑滑動 | Drag left or right to slide along the path | 2420, 2439, 2473 | canvas label above the floating shield (12px) | 232.9 / 132.0 / 260 | OK | ok |  |
| 79 | `shield.roundsLeft` | 剩 {rounds} 輪 | Rounds left: {rounds} | 2420, 2439, 2473 | canvas label above the floating shield (12px) | 81.4 / 36.5 / 260 | TERM_INCONSISTENT | ok | zh says 輪 for "round" here; 回合 everywhere else (hud.round, shield.expired, dock.resetTitle, toast.resetLocked). English always "round(s)". |

### ult.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 80 | `ult.titleUsedUp` | 大招已用完（一場最多 2 次） | No Ultimates left (max 2 per match) | 1848 | ultimate tile tooltip (title attr) |  | OK | ok |  |
| 81 | `ult.titleArmed` | 大招已準備：下一發出手（再點取消） | Ultimate armed: fires on your next throw (click again to cancel) | 1848 | ultimate tile tooltip (title attr) |  | OK | ok |  |
| 82 | `ult.titleReady` | 三格已亮：點一下準備大招 | All three pips lit: click to arm the Ultimate | 1848 | ultimate tile tooltip (title attr) |  | OK | ok |  |
| 83 | `ult.titleCharging` | 大招：要先命中 3 次點亮三格（目前 {n}/3） | Ultimate: land 3 hits to light all three pips (now {n}/3) | 1848 | ultimate tile tooltip (title attr) |  | OK | ok |  |
| 84 | `ult.shuriken` | ✨ 大招：手裡劍雨 | ✨ Ultimate: Shuriken Rain | 1222 | canvas popup (floatTexts, unit-anchored) | 233.7 / 147.2 / 560 | OK | ok |  |
| 85 | `ult.spear` | ✨ 大招：三連標槍 | ✨ Ultimate: Triple Javelin | 1256 | canvas popup (floatTexts, unit-anchored) | 230.0 / 147.2 / 560 | OK | ok |  |
| 86 | `ult.swarm` | ✨ 大招：蝙蝠群 | ✨ Ultimate: Bat Swarm | 1249 | canvas popup (floatTexts, unit-anchored) | 206.4 / 129.2 / 560 | OK | ok |  |
| 87 | `ult.boomerang` | ✨ 大招：迴旋巨斧 | ✨ Ultimate: Boomerang Axe | 1242 | canvas popup (floatTexts, unit-anchored) | 248.8 / 147.2 / 560 | OK | ok |  |
| 88 | `ult.nun` | ✨ 大招：銀十字連擊 | ✨ Ultimate: Silver Cross Strike | 1235 | canvas popup (floatTexts, unit-anchored) | 270.8 / 165.2 / 560 | MISMATCH | ok | zh 連擊 = combo; English "Strike" drops the multi-hit meaning. Also: zh/en blurb call the weapon "銀色十字 / Silver cross". |
| 89 | `ult.cannon` | ✨ 大招：南瓜連環爆 | ✨ Ultimate: Pumpkin Chain Blast | 1265 | canvas popup (floatTexts, unit-anchored) | 293.8 / 165.2 / 560 | OK | ok |  |
| 90 | `ult.tripleHit` | 💥 三連全中！ | 💥 Triple hit! | 2038 | canvas popup (floatTexts, unit-anchored) | 108.9 / 111.2 / 560 | OK | ok |  |
| 91 | `ult.blast` | 🔥 爆炸 -{dmg} | 🔥 Blast -{dmg} | 2136 | canvas popup (floatTexts, unit-anchored) | 114.7 / 105.6 / 560 | OK | ok |  |
| 92 | `ult.unbuilt` | 🔧 這個職業的大招還在製作中 | 🔧 This class's Ultimate is still being built | 720 | canvas popup (floatTexts, unit-anchored) | 358.7 / 237.2 / 560 | TERM_INCONSISTENT | ok | zh says 職業 / en says "class" here, but 角色 / "character" in start.pickHero, help.tapUnit, dock.portraitAria. One word for the player-facing concept: 角… |
| 93 | `ult.cancel` | 大招取消 | Ultimate canceled | 715, 721 | canvas popup (floatTexts, unit-anchored) | 161.6 / 72.0 / 560 | OK | ok |  |
| 94 | `ult.spent` | 大招已用完 | No Ultimates left | 686, 716, 722 | canvas popup (floatTexts, unit-anchored) | 150.4 / 90.0 / 560 | OK | ok |  |
| 95 | `ult.noEnergy` | 能量未滿（要打中 3 次） | Energy not full (land 3 hits) | 686, 722 | canvas popup (floatTexts, unit-anchored) | 239.8 / 198.8 / 560 | OK | ok |  |
| 96 | `ult.armed` | ✨ 大招已準備：下一發出手 | ✨ Ultimate armed: fires on your next throw | 723 | canvas popup (floatTexts, unit-anchored) | 384.3 / 219.2 / 560 | OK | ok |  |
| 97 | `ult.soulfire` | ✨ 大招：三發鬼火 | ✨ Ultimate: Triple Soulfire | 1275 | canvas popup (floatTexts, unit-anchored) | 235.8 / 147.2 / 560 | TERM_INCONSISTENT | ok | zh 鬼火 on both sides, but English is "Ghost Flame" in hero.reaper.blurb and "Soulfire" here. |

### knightUlt.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 98 | `knightUlt.place` | 在弧線上點 1、2、3：三個隱藏防禦點，各擋一次攻擊 | Tap 1, 2, 3 on the arc: three hidden defence points, each stops one attack | 688 | canvas popup (floatTexts, centred) | 644.1 / 432.0 / 900 | TERM_INCONSISTENT | ok | English: "Tap" here but "Click" in help.tapUnit, dock tooltips; "defence" (UK) here vs "defense" (US) in shield.expired. Pick US spelling and one ver… |
| 99 | `knightUlt.locked` | ✨ 隱藏點已鎖定 | ✨ Hidden points locked | 704 | canvas popup (floatTexts, centred) | 209.5 / 129.2 / 900 | OK | ok |  |
| 100 | `knightUlt.blocked` | 擋下！ | Blocked! | 2012 | canvas popup (floatTexts, unit-anchored) | 78.4 / 54.0 / 560 | OK | ok |  |

### toast.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 101 | `toast.defendHelp` | 🛡️ 防禦：沿弧線拖曳盾牌（棺材），放開就停在那個位置（本回合不能攻擊，Esc 取消） | 🛡️ Defend: drag the shield (coffin) along the arc and let go: it stays where you let go (no attack this round… | 1044 | canvas popup (floatTexts, centred) | 1052.6 / 702.8 / 900 OVER | TERM_INCONSISTENT | ok | One object, three names in one sentence: 盾牌 (shield) + 棺材 (coffin) vs 浮空盾 / Floating Shield used by the other 12 shield strings. Also over the soft w… |
| 102 | `toast.moveHelp` | 🎲 移動：選擇方向（← 後退 / → 前進，或點箭頭），再擲骰子決定距離。Esc 取消 | 🎲 Move: choose a direction (← back / → forward, or click an arrow), then roll the die for distance. Esc to ca… | 943 | canvas popup (floatTexts, centred) | 974.6 / 654.1 / 900 OVER | OK | ok |  |
| 103 | `toast.moveCancel` | 已取消移動 | Move canceled | 945 | canvas popup (floatTexts, centred) | 130.9 / 90.0 / 900 | OK | ok |  |
| 104 | `toast.moveRoll` | 🎲 {dir}：擲骰子決定距離（移動完還可以攻擊） | 🎲 {dir}: roll the die for distance (you can still attack after moving) | 950 | canvas popup (floatTexts, unit-anchored) | 615.0 / 381.2 / 560 OVER | OK | ok |  |
| 105 | `toast.moveResult` | 🎲 {roll}：{dir} {moved} px{edge} | 🎲 {roll}: {dir} {moved} px{edge} | 972 | canvas popup (floatTexts, unit-anchored) | 295.7 / 237.6 / 560 | TERM_INCONSISTENT | ok | Distance in px here and in toast.gapShift, but in steps (步 / steps) in hud.round. DICE_STEP_PX converts between them in code. |
| 106 | `toast.gapShift` | 🎲 1-2 站位動態變化！雙方距離: {px} px | 🎲 Positions shifted! Distance between sides: {px} px | 994 | canvas popup (floatTexts, centred) | 456.3 / 318.8 / 900 | MISMATCH | ok | numbers differ zh ['1', '2'] vs en []. zh keeps the spec label "1-2" ("1-2 站位動態變化") that the English drops; players do not know what 1-2 means. Dista… |
| 107 | `toast.aimHint` | 🎯 移動游標瞄準，在場上按住蓄力，放開就投擲 | 🎯 Move the cursor to aim, hold on the field to charge, release to throw | 931 | canvas popup (floatTexts, unit-anchored) | 621.5 / 381.2 / 560 OVER | OK | ok |  |
| 108 | `toast.slowed` | 減速：這回合不能移動 | Slow: you cannot move this round | 938 | canvas popup (floatTexts, unit-anchored) | 301.9 / 180.0 / 560 | OK | ok |  |
| 109 | `toast.alreadyMoved` | 本回合已經移動過了，可以直接攻擊 | You already moved this round. You can attack now | 939 | canvas popup (floatTexts, unit-anchored) | 447.3 / 288.0 / 560 | OK | ok |  |
| 110 | `toast.healOwnTurn` | 只能在自己的回合回血 | You can only heal on your own turn | 1003 | canvas popup (floatTexts, unit-anchored) | 311.4 / 180.0 / 560 | OK | ok |  |
| 111 | `toast.hpFull` | 血量已滿，不用回血 | HP is full, no need to heal | 1004 | canvas popup (floatTexts, unit-anchored) | 224.0 / 162.0 / 560 | OK | ok |  |
| 112 | `toast.healed` | 🧪 生命恢復 +35 HP! | 🧪 Healed +35 HP! | 1012 | canvas popup (floatTexts, unit-anchored) | 156.0 / 165.6 / 560 | TERM_INCONSISTENT | ok | zh uses 補血 / 生命恢復 here but 回血 in skill.healTip, skill.healTitle, toast.healOwnTurn, toast.hpFull. |
| 113 | `toast.guardOnly` | 🎃 只有南瓜盾衛能操控浮空防禦 | 🎃 Only the Pumpkin Guard can control the Floating Shield | 1030 | canvas popup (floatTexts, unit-anchored) | 515.3 / 255.2 / 560 | OK | ok |  |
| 114 | `toast.shieldNoMoves` | 🛡️ 浮空盾移動次數用完了 | 🛡️ No Floating Shield moves left | 1036 | canvas popup (floatTexts, unit-anchored) | 280.6 / 201.2 / 560 | OK | ok |  |
| 115 | `toast.shieldSnapped` | 🛡️ 卡在有效路徑！剩 {moves} 次移動、攔截 {charges} 次 | 🛡️ Locked on a valid path! {moves} moves left, {charges} blocks | 1063 | canvas popup (floatTexts, unit-anchored) | 421.2 / 328.8 / 560 | OK | ok |  |
| 116 | `toast.shieldLocked` | 🛡️ 已鎖定（不在記憶路徑上），剩 {moves} 次移動 | 🛡️ Locked (not on a remembered path), {moves} moves left | 1063 | canvas popup (floatTexts, unit-anchored) | 457.7 / 346.0 / 560 | OK | ok |  |
| 117 | `toast.defendCancel` | 已取消防禦模式 | Defend mode canceled | 1073 | canvas popup (floatTexts, centred) | 201.9 / 126.0 / 900 | OK | ok |  |
| 118 | `toast.noAttackInDefend` | 🛡️ 防禦模式中不能攻擊 | 🛡️ You cannot attack in Defend mode | 1108 | canvas popup (floatTexts, unit-anchored) | 325.0 / 183.2 / 560 | OK | ok |  |
| 119 | `toast.switchHero` | 切換職業: {name} | Switched class: {name} | 1086 | canvas popup (floatTexts, unit-anchored) | 339.5 / 189.9 / 560 | TERM_INCONSISTENT | ok | zh says 職業 / en says "class" here, but 角色 / "character" in start.pickHero, help.tapUnit, dock.portraitAria. One word for the player-facing concept: 角… |
| 120 | `toast.flip` | ↔ 全部角色水平翻轉：{state} | ↔ Flip all characters horizontally: {state} | 1471 | canvas popup (floatTexts, centred) | 329.6 / 202.1 / 900 | OK | ok |  |
| 121 | `toast.flipOn` | 開 | On | 1471 | fragment of toast.flip | 327.7 / 202.1 / 900 | OK | ok |  |
| 122 | `toast.flipOff` | 關 | Off | 1471 | fragment of toast.flip | 329.6 / 202.1 / 900 | OK | ok |  |
| 123 | `toast.aiShield` | AI 浮空盾切入軌跡（防禦回合，不攻擊） | AI Floating Shield cuts into your trail (defend round, no attack) | 1578 | canvas popup (floatTexts, unit-anchored) | 554.5 / 327.5 / 560 | TERM_INCONSISTENT | ok | Calls the opponent "AI"; everywhere else 對手 / Opponent (hud.opponent, supply.aiLabel, toast.aiPickup, hud.opponentTurn). |
| 124 | `toast.resetLocked` | 🔒 第 {n} 回合後不能重置 | 🔒 Reset is locked after round {n} | 1640 | canvas popup (floatTexts, centred) | 283.3 / 194.6 / 900 | TERM_INCONSISTENT | ok | "Reset / 重置" here but "Restart match / 重新對戰" in dock.resetTitle and dock.resetAria. Pick one: 重新對戰 / Restart. |
| 125 | `toast.pickup` | {icon} 拿到物資：{label} | {icon} Picked up: {label} | 1759 | canvas popup (floatTexts, unit-anchored) | 198.8 / 172.6 / 560 | OK | ok |  |
| 126 | `toast.aiPickup` | 對手撿到物資 | Opponent picked up a supply | 1763 | canvas popup (floatTexts, unit-anchored) | 258.7 / 108.0 / 560 | OK | ok |  |
| 127 | `toast.rearm` | 🔄 補給武器 | 🔄 Weapon resupplied | 2172 | canvas popup (floatTexts, unit-anchored) | 192.4 / 93.2 / 560 | OK | ok |  |
| 128 | `toast.timeout` | ⏱ 逾時！本回合棄權 | ⏱ Time's up! Turn forfeited | 1877 | canvas popup (floatTexts, unit-anchored) | 242.7 / 165.2 / 560 | OK | ok |  |
| 129 | `toast.fenceBlock` | 💥 圍籬攔截！ | 💥 Fence block! | 1977 | canvas popup (floatTexts, unit-anchored) | 133.5 / 111.2 / 560 | OK | ok |  |
| 130 | `toast.fenceBroken` | 💥 圍籬被打壞了！ | 💥 Fence destroyed! | 1977 | canvas popup (floatTexts, unit-anchored) | 174.6 / 147.2 / 560 | OK | ok |  |
| 131 | `toast.directHit` | 💥 直擊 -{dmg}! | 💥 Direct hit -{dmg}! | 2087 | canvas popup (floatTexts, unit-anchored) | 158.6 / 112.3 / 560 | OK | ok |  |
| 132 | `toast.mudDeflect` | 泥土偏斜 | Deflected by the dirt | 2118 | canvas popup (floatTexts, unit-anchored) | 181.5 / 72.0 / 560 | OK | ok |  |
| 133 | `toast.shieldStuck` | 盾插進地板，不能再彈了 | The shield is stuck in the ground and cannot bounce any more | 2119 | canvas popup (floatTexts, unit-anchored) | 546.9 / 198.0 / 560 | OK | ok |  |
| 134 | `toast.bounce` | 🎲 {n} 彈 · 每彈 {dmg} | 🎲 {n} bounces · {dmg} each | 1289 | canvas popup (floatTexts, unit-anchored) | 231.3 / 168.5 / 560 | OK | ok |  |
| 135 | `toast.tapCancel` | 按住蓄力再放開 | Hold to charge, then release | 1125 | canvas popup (floatTexts, unit-anchored) | 249.6 / 126.0 / 560 | OK | ok |  |
| 136 | `toast.auraSimple` | 光圈：簡化（按 J 切換） | Aura: simple (press J to switch) | 2856 | canvas popup (floatTexts, centred) | 276.2 / 198.4 / 900 | OK | ok |  |
| 137 | `toast.auraFull` | 光圈：完整（按 J 切換） | Aura: full (press J to switch) | 2856 | canvas popup (floatTexts, centred) | 246.3 / 198.4 / 900 | OK | ok |  |

### status.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 138 | `status.knockback` | 擊退！ | Knocked back! | 2048 | canvas popup (floatTexts, unit-anchored) | 131.0 / 54.0 / 560 | OK | ok |  |
| 139 | `status.crit` | 💥 爆擊！ | 💥 Crit! | 2032 | canvas popup (floatTexts, unit-anchored) | 60.6 / 75.2 / 560 | OK | ok |  |
| 140 | `status.stun` | ⭐ 暈眩 | ⭐ Stun | 2033, 2062 | canvas popup (floatTexts, unit-anchored) | 63.0 / 57.2 / 560 | OK | ok |  |
| 141 | `status.stunTimer` | ⭐ 暈眩！只剩 {sec} 秒 | ⭐ Stunned! Only {sec} s left | 1601 | canvas popup (floatTexts, unit-anchored) | 221.8 / 158.6 / 560 | OK | ok |  |
| 142 | `status.slowNext` | 減速：下回合不能移動 | Slow: cannot move next round | 2043 | canvas popup (floatTexts, unit-anchored) | 271.0 / 180.0 / 560 | OK | ok |  |
| 143 | `status.frostWeak` | 🧊 被霜咒：傷害 -15% | 🧊 Frost Curse: damage -15% | 1204 | canvas popup (floatTexts, unit-anchored) | 252.5 / 178.6 / 560 | OK | ok |  |
| 144 | `status.frostApplied` | 🧊 霜咒：攻擊 -15%（2 次） | 🧊 Frost Curse: attacks -15% (2 times) | 2090 | canvas popup (floatTexts, unit-anchored) | 329.0 / 229.3 / 560 | TERM_INCONSISTENT | ok | Says 攻擊 -15% / "attacks -15%"; status.frostWeak and hero.skeleton.blurb say 傷害 / damage. The code lowers damage (x0.85) on the next 2 attacks. |
| 145 | `status.poison` | ☠ 中毒 | ☠ Poison | 1793 | canvas popup (floatTexts, unit-anchored) | 81.7 / 57.2 / 560 | OK | ok |  |
| 146 | `status.bleed` | 🩸 流血 | 🩸 Bleed | 1794 | canvas popup (floatTexts, unit-anchored) | 71.6 / 57.2 / 560 | OK | ok |  |
| 147 | `status.burn` | 🔥 灼燒 | 🔥 Burn | 1796 | canvas popup (floatTexts, unit-anchored) | 64.3 / 57.2 / 560 | OK | ok |  |
| 148 | `status.halluActive` | 😵 幻覺中：這回合不能行動 | 😵 Hallucinating: cannot act this round | 1556, 1630 | canvas popup (floatTexts, unit-anchored) | 339.9 / 219.2 / 560 | OK | ok |  |
| 149 | `status.halluApplied` | 😵 幻覺：下回合停止 | 😵 Hallucination: skips next round | 2072 | canvas popup (floatTexts, unit-anchored) | 298.6 / 165.2 / 560 | OK | ok |  |

### menu.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 150 | `menu.move` | 🎲 移動 | 🎲 Move | 922 | canvas action-menu button (20px, button 108 px) | 76.2 / 63.5 / 96 | OK | ok |  |
| 151 | `menu.attack` | 🎯 攻擊 | 🎯 Attack | 922 | canvas action-menu button (20px, button 108 px) | 87.6 / 63.5 / 96 | OK | ok |  |
| 152 | `menu.defend` | 🛡️ 防禦 | 🛡️ Defend | 923 | canvas action-menu button (20px, button 108 px) | 94.2 / 63.5 / 96 | OK | ok |  |

### move.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 153 | `move.forward` | 前進 | Forward | 950, 972 | fragment of toast.moveRoll | 615.0 / 381.2 / 560 OVER | OK | ok |  |
| 154 | `move.back` | 後退 | Back | 950, 972 | fragment of toast.moveRoll | 582.9 / 381.2 / 560 OVER | OK | ok |  |
| 155 | `move.backBtn` | ◀ 後退 | ◀ Back | 3404 | canvas move arrow button (20px, button 104 px) | 72.6 / 64.5 / 92 | OK | ok |  |
| 156 | `move.fwdBtn` | 前進 ▶ | Forward ▶ | 3404 | canvas move arrow button (20px, button 104 px) | 108.2 / 64.5 / 92 OVER | OK | ok |  |
| 157 | `move.aimNeutral` | 往左或往右指，放開擲骰 | Point left or right, release to roll | 3423 | canvas caption under the die (16px) | 253.2 / 176.0 / 560 | OK | ok |  |
| 158 | `move.releaseFwd` | 放開：前進並擲骰 | Release: move forward and roll | 3423 | canvas caption under the die (16px) | 245.6 / 128.0 / 560 | OK | ok |  |
| 159 | `move.releaseBack` | 放開：後退並擲骰 | Release: move back and roll | 3423 | canvas caption under the die (16px) | 220.0 / 128.0 / 560 | OK | ok |  |
| 160 | `move.atEdge` | （到邊界） |  (at the edge) | 972 | fragment of toast.moveResult | 295.7 / 237.6 / 560 | OK | ok |  |

### fence.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 161 | `fence.label` | 中央圍籬 ({hp}%) | Center Fence ({hp}%) | 2973, 3032 | canvas label above the fence (14px) | 142.5 / 108.1 / 200 | OK | ok |  |
| 162 | `fence.broken` | 圍籬已損毀 | Fence destroyed | 2973, 3032 | canvas label above the fence (14px) | 114.1 / 70.0 / 200 | OK | ok |  |

### hud.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 163 | `hud.you` | 我方 | You | 3251 | canvas HUD side banner name fallback (24px) | 44.2 / 48.0 / 340 | OK | ok |  |
| 164 | `hud.opponent` | 對手 | Opponent | 3252 | canvas HUD side banner name fallback (24px) | 119.4 / 48.0 / 340 | OK | ok |  |
| 165 | `hud.ult` | 大招 | Ultimate | 3242 | canvas HUD side banner caption (15px) | 65.1 / 30.0 / 100 | OK | ok |  |
| 166 | `hud.countdown` | 倒數 {sec} 秒 | Time left: {sec} s | 3266 | canvas HUD centre piece (28px, piece 440 px) | 191.6 / 129.8 / 400 | OK | ok |  |
| 167 | `hud.opponentTurn` | 對手回合 | Opponent's turn | 3269 | canvas HUD centre piece (26px, piece 440 px) | 212.1 / 104.0 / 400 | OK | ok |  |
| 168 | `hud.round` | 第 {round} 回合 ・ 距離 {dist} 步 | Round {round} · Distance {dist} steps | 3270 | canvas HUD centre piece (17px, piece 440 px) | 248.8 / 182.3 / 400 | OK | ok |  |
| 169 | `hud.angle` | 角度 {angle}° | Angle {angle}° | 3446 | canvas label above the player (18px) | 82.6 / 68.7 / 300 | OK | ok |  |
| 170 | `hud.trailTag` | 軌跡 [R{round}] | Trail [R{round}] | 2370 | canvas label on a remembered path (11px) | 56.3 / 53.3 / 120 | OK | ok |  |
| 171 | `hud.weather` | 天氣：{label}（到第 {round} 回合） | Weather: {label} (until round {round}) | 3271 | canvas HUD centre piece (15px, piece 440 px) | 256.9 / 210.7 / 400 | OK | ok |  |

### gameover.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 172 | `gameover.win` | 🎃 你贏了！ | 🎃 You win! | 3465 | canvas result panel title (44px display, panel 560 px) | 277.5 / 228.8 / 520 | OK | ok |  |
| 173 | `gameover.lose` | 💀 你輸了 | 💀 You lose | 3465 | canvas result panel title (44px display, panel 560 px) | 287.0 / 184.8 / 520 | OK | ok |  |
| 174 | `gameover.restart` | 點一下畫面，回到選角重新開始 | Click anywhere to return to character select and play again | 3468 | canvas result panel line (20px, panel 560 px) | 580.2 / 280.0 / 520 OVER | OK | ok |  |

### lang.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 175 | `lang.title` | 語言：中文（點一下切換成 English） | Language: English (click to switch to 中文) | 226 | top-controls / dock tooltip (title attr) |  | OK | ok | English contains CJK. Intentional: each side shows the OTHER language name (en.json holds 中文 on purpose). Not a mismatch. |
| 176 | `lang.label` | EN | 中文 | 226 | top-controls chip caption (CSS display:none, never shown) |  | OK | ok | English contains CJK. Intentional: each side shows the OTHER language name (en.json holds 中文 on purpose). Not a mismatch. |

### weather.*

| # | Key | zh-TW | English | where (index.html) | Surface | px en / zh / limit | Status | code | Note |
|---|---|---|---|---|---|---|---|---|---|
| 177 | `weather.clear` | 晴 | Clear | 737, 3271 | fragment of hud.weather | 228.3 / 174.5 / 400 | OK | ok |  |
| 178 | `weather.rain` | 下雨（攻擊 -10%） | Rain (attacks -10%) | 737 | fragment of hud.weather | 333.5 / 290.7 / 400 | OK | ok |  |
| 179 | `weather.snow` | 下雪（移動減半） | Snow (movement halved) | 737 | fragment of hud.weather | 379.8 / 279.5 / 400 | OK | ok |  |
| 180 | `weather.storm` | 暴風雨（攻擊 -10%、風更強） | Storm (attacks -10%, stronger wind) | 737 | fragment of hud.weather | 458.4 / 365.7 / 400 OVER | OK | ok |  |
| 181 | `weather.fog` | 起霧 | Fog | 737 | fragment of hud.weather | 216.7 / 189.5 / 400 | OK | ok |  |

## 7. Limits of this table
- Width numbers are font-metric estimates (+-3 %); they were not read back from a running page. Budgets other than the three reviewer figures are my estimates (named in section 1).
- Hero blurb "est. lines" in the JSON assume 162 px text width at 12.5 px; they were not rendered.
- Number claims in blurbs were checked against `HERO_PROFILES`, `weather.js` multipliers and constants at the snapshot only; the wizard 24 vs 28 question needs the owner.
- Not scanned in detail: agent-facing strings in `scripts/mcp_*.py`, docs, README, release drafts. `SHOW_COMING_SOON` is false, so `start.inProduction` and the grey cards are not shown today.
- Nothing in `index.html`, `js/`, `css/` or `assets/i18n/` was changed; only the two files named `i18n_mapping_table_20261116` were written.


## 7. Task 177 application (2026-11-16)

This section supersedes the affected snapshot rows above. The snapshot values and its measurements remain as the record of the review that produced this task.

| Rows updated | Status | Result |
|---|---|---|
| `gameover.restart`, `shield.expired`, `weather.storm`, `skill.ultTip`, `toast.defendHelp`, `move.fwdBtn`, `toast.moveHelp`, `toast.moveRoll`, `toast.aimHint` | OK | Applied the proposed shorter English text. `weather.storm` measures 414.1 px, which is above the 400 px comfort budget but below the 440 px hard limit. |
| `hero.skeleton.tab`, `hero.wizard.tab`, `hero.bat.tab`, `hero.hunchback.tab` | OK | Applied `Bones`, `Mage`, `Bat`, and `Bell` to fit the 40 px dock chips. |
| `help.wind`, `help.guard`, `shield.tipGuard`, `ult.nun`, `toast.gapShift` | OK | Corrected the stale instruction text, removed the `1-2` tag, and use Ghost Nun / 鬼修女 wording. |
| `status.frostWeak`, `status.frostApplied`, `ult.soulfire` | OK | Both Frost Curse lines now say damage −15%; the ultimate is `Triple Ghost Flame`. |
| `supply.heal`, `toast.healed`, `toast.switchHero`, `toast.aiShield`, `shield.holding`, `shield.blocked`, `shield.roundsLeft`, `dock.resetLockedTitle`, `dock.resetTip`, `toast.resetLocked`, `shield.tipOther`, `ult.unbuilt` | OK | Standardized 回血/Heal, 角色/character, 對手/Opponent, 回合/Round, and 重新對戰/Restart. |
| `help.tapUnit`, `knightUlt.place` | OK | Uses `Tap` for the touch-facing instructions and US spelling `defense`. |
| `toast.rotatePhone`, `ui.playAgain`, `ui.backToPick`, `ui.installApp`, `ui.installIosHint`, `weather.notice.rain`, `weather.notice.snow`, `weather.notice.storm`, `weather.notice.fog`, `hint.goal`, `hint.step1`, `hint.step2`, `hint.step3` | OK | Added the 13 specified new keys to both language files with identical placeholder sets. |
| `manifest.webmanifest` | OK | Uses the requested bilingual name, Chinese short name, and a short English description. |

### Remaining rows

- **Owner decision:** `hero.bat.name` remains Bat Assassin / 蝙蝠刺客. `hero.knight.name`, `hero.knight.tabTitle`, and `hero.knight.tab` remain Heavy Pumpkin Guard / Pumpkin Guard / Guard and 南瓜重裝盾衛 / 南瓜盾衛 / 盾衛. Task 177 explicitly preserves Bat Assassin and 盾衛 / Guard.
- **Page wiring required:** `ult.knight` remains absent because the page does not use this key and task 177 forbids unlisted unused keys. The Guard ultimate needs a named popup only when its page wiring is assigned.
- **Outside the permitted files:** the full English hero names still overflow their dock/start-card budgets (`Skeleton Spearman`, `Pumpkin Wizard`, `Heavy Pumpkin Guard`, and `Bell Tower Hunchback`). The mapping table's CSS fixes require `index.html`, which task 177 forbids. `Heavy Pumpkin Guard` also awaits the owner naming decision.
- **Outside the permitted files:** the documented `useSupply()` `undefined` popup bug and the remaining hardcoded/unused strings need their respective page or JavaScript tasks.
- **Already handled by the main line:** the seven hero blurbs, `status.burn`, and `toast.tapCancel` were left unchanged as required by this task.


### Task 177 verification

Commands run after rebuilding the fonts:

```text
python3 -B scripts/build_fonts.py
python3 -B scripts/test_fonts.py
node scripts/test_i18n.js
python3 -B scripts/test_pwa_files.py
```

Last lines of the actual output:

```text
build_fonts.py: total font bytes: 1118424 (1.07 MB)
test_fonts.py: OK
test_i18n.js: 25 passed, 1 failed (194 keys per language)
test_pwa_files.py: FAILED (failures=1)
```

`test_fonts.py` passed. `test_i18n.js` rejects the 13 task-required new keys because the current `index.html` does not reference them; changing the page or the test is outside task 177. `test_pwa_files.py` reports a stale `sw.js` precache after the manifest change; regenerating `sw.js` would touch a file outside task 177's allowed list. Neither failed check is reported as passed.
