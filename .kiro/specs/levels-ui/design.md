# Design: levels and start screen (levels-ui)
Written 2026-11-15. Requirements: `requirements.md` (numbers in brackets). Nothing here was run. I did not read the code files named below, so every interface is a proposal that task 1 checks.

## Split
The page is one large file with one writer (the main line). The level logic stays in the existing shared module, and the page only calls it.

| Piece | File | Does | Tested by |
|---|---|---|---|
| Level table | `scripts/agent_levels.py` (source) and a matching table the page can read | `easy`, `normal`, `hard` parameters. [1, 2, 3] | a check that compares the two tables |
| Adaptive rule | `js/adaptive_level.js` (exists) and `scripts/adaptive_level.py` (exists) | The rule: start `normal`, last 3 human throws, above 40 percent up, below 15 percent down, 2 changes max, 2-throw cooldown. [4 to 10] | shared vectors in `scripts/adaptive_level_vectors.json` |
| Match wiring | `index.html` | Creates one adaptive state per match, feeds it the human throw results, applies the level to the computer seats, draws the HUD, resets at match start and end. [1, 12 to 16] | main line run in the browser, recorded |
| Start screen | `index.html` | Hero cards and battlefield cards come from the built list, so the removed items do not show. [17 to 20] | main line run in the browser, recorded |
| README | `README.md` | One "planned" paragraph. [20] | `grep` of the lines |

## Level table in the page [2]
The Python file is the source of the three levels. The page needs the same numbers in JavaScript. Options:
- A: copy the numbers by hand into the page. Simple, drifts easily.
- B: generate a small JSON or JS file from `agent_levels.py` and load it. One source, one extra file.
Recommendation: B, plus a check that fails when the generated file differs from the Python table. Task 1 reads how `agent_levels.py` stores its parameters and settles this. If the page's computer cannot use the Python parameters directly (it may use its own aiming code), task 1 says so in its result file and requirement 1 is restated in terms of what the page can do.

## Adaptive state per match [4 to 8, 10, 15]
One state object per match, created at match start and dropped at match end:
`{ level, history (last 3 human throw results), changes, cooldown, reason }`.
- The page calls the module once per human throw with hit or miss. It never feeds computer throws [10].
- The module returns the new level and, when it changed, the reason text.
- Start: `level = "normal"`, `changes = 0`, `cooldown = 0`, `reason = ""` [4].
- Fewer than 3 throws: no change [5]. Above 40 percent: up one step. Below 15 percent: down one step. Bounds at `easy` and `hard` [6].
- `changes` stops at 2 [7]. After a change `cooldown = 2` human throws; it counts down per human throw [8].
- The state lives only in memory. The page does not call `localStorage`, set cookies, or send anything [16].
Whether "last 3 throws" and the percent values use `>` and `<` strictly follows the shared vectors. The vectors win over this text [9].

## Multiplayer [11]
Not decided (owner question 1). Until answered, the page keeps the adaptive rule only for matches with exactly one human seat and shows a fixed `normal` otherwise. The state object takes a list of human throw results, so the answer changes one line in the page, not the module.

## HUD [12 to 14]
- One HUD line: `Computer: <level>`. In adaptive mode the line is `Computer: <level> (adaptive)`.
- Under it, the reason of the last change, shown until the next change or match end. Empty before the first change.
- Public state: `{ ai_level, ai_reason }`, two string fields, added next to the existing public fields (the knight spec adds `ult_points_left` the same way). The throw history stays private [14].
- The texts are in Chinese like the rest of the page; exact wording is the main line's choice and not tested, only that the level word and a non-empty reason appear after a change.

## Start screen [17 to 21]
- Remove the three grey cards (ghost bride, hunchback, necromancer) and the two "in production" battlefield cards.
- Do not hide them with CSS. Remove them from the markup or the data list, so no hidden element is left behind and no test finds them.
- If the hero row is built from a list, the list becomes the built heroes only. Task 1 finds out which it is.
- Do not touch the code of any built hero, the finished battlefield, or save/load [21].
- The removed items are written in `README.md` as planned. That edit is outside this spec's folder and `index.html`, so the main line or the owner applies it; task 5 describes it [20].

## Risks
- I have not read `index.html`. The cards may be shared with the ultimates or the knight "still being made" label; task 1 checks that removing a card does not remove a built hero.
- If a hero list is also used by the opponent picker, the removal may need to happen in more than one place.
- `index.html` allows one task at a time. The wiring and the start-screen cleanup are separate tasks and queue behind each other and behind the ultimates wiring tasks.
- HUD correctness cannot be judged by a unit test. The check is a recorded browser run.
