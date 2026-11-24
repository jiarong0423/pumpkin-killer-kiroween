# Tasks: delivery plan

Mirror of the work packages in `docs/plan_v1.md`. Format: id, name, owner, dates, depends on. Verification and gates are in the plan table. None is ticked: this spec describes work that has not started. Items marked (S) are STRETCH.

## Planning (this task)

- [x] P1. Write `docs/plan_v1.md` (sections a to g, plus h for assumptions).
- [x] P2. Write this spec (requirements, design, tasks).
- [ ] P3. Main line reviews the plan and sends corrections (task 43b).

## Work packages

- [ ] WP01 Owner decision batch 1 (Q1-Q8). owner. 11-09 to 11-10. -
- [ ] WP02 Baseline: all test scripts plus headless smoke. main. 11-09 to 11-10. -
- [ ] WP03 Kiro task 44: `(not published)`, `(not published)`. Kiro. 11-09 to 11-10. -
- [ ] WP04 Colab notebook fix (negative prompt, TAG, ONLY list). main. 11-10. -
- [ ] WP05 Colab Run 1: 3 idles and 2 backgrounds. Colab. 11-10. WP03, WP04
- [ ] WP06 Intake of Kiro tasks 41 and 42. main. 11-10 to 11-11. -
- [ ] WP07 UI pass 1: wire generated art, help text, hint overlap. main. 11-10 to 11-12. WP02
- [ ] WP08 Triage and merge the kiro/* branches. main. 11-10 to 11-12. WP02
- [ ] WP09 Owner picks idles; main copies to inputs. owner. 11-11. WP05
- [ ] WP10 Colab Run 2: reaper set, crate, parachute. Colab. 11-11 to 11-12. WP03, WP09
- [ ] WP11 Kiro task 45: specs new-classes, ultimate-machine, scenes-v2, ai-ledger. Kiro. 11-11 to 11-13. WP01, WP06
- [ ] WP12 Shared data and MCP parity. main. 11-11 to 11-13. WP01, WP06
- [ ] WP13 Balance sim run 1. main. 11-12. WP06
- [ ] WP14 Colab Run 3: hunchback set, icons. Colab. 11-12 to 11-13. WP10
- [ ] WP15 Kiro task 46: `(not published)`. Kiro. 11-12 to 11-13. WP02
- [ ] WP16 Hooks repair and new save hooks. Kiro and owner. 11-12 to 11-14. WP06
- [ ] WP17 Number pass in index.html from the class table. main. 11-13 to 11-14. WP12, WP13
- [ ] WP18 Colab Run 4: bride set, HUD parts. Colab. 11-13 to 11-14. WP14
- [ ] WP19 AI landing-ledger learner. main. 11-13 to 11-15. WP01, WP12
- [ ] WP20 Scene data table and wind ranges. main. 11-13 to 11-15. WP06
- [ ] WP21 Colab Run 5: portraits, power cells, sockets. Colab. 11-14 to 11-15. WP18
- [ ] WP22 Ultimate ledger wiring. main. 11-14 to 11-16. WP01, WP06, WP17
- [ ] WP23 Reaper class. main. 11-14 to 11-16. WP10, WP17
- [ ] WP24 Fence and drop art wiring. main. 11-15 to 11-16. WP18
- [ ] WP25 UI art batch wiring. main. 11-15 to 11-17. WP07, WP14, WP18
- [ ] WP26 Hunchback class. main. 11-16 to 11-18. WP14, WP17
- [ ] WP27 Kiro task 47: `(not published)` draft. Kiro. 11-16 to 11-18. -
- [ ] WP28 Weapon effects wiring. main. 11-17 to 11-20. WP06
- [ ] WP29 Colab Run 6: reruns. Colab. 11-17 to 11-18. WP21
- [ ] WP30 Ultimate machine. main. 11-17 to 11-20. WP22, WP23
- [ ] WP31 Bride class. main. 11-17 to 11-19. WP17, WP18
- [ ] WP32 Scene backgrounds and safe-zone checks. main. 11-18 to 11-20. WP05, WP20
- [ ] WP33 Portraits and power/socket cells wired. main. 11-18 to 11-20. WP21, WP23, WP26
- [ ] WP34 Cross-check 1. sub-agents. 11-18. WP22, WP23, WP26
- [ ] WP35 Audio wiring from existing CC0 files. main. 11-19 to 11-21. WP23
- [ ] WP36 2 v 2 go/no-go gate. owner. 11-19. WP13, WP26, WP31
- [ ] WP37 (S) Colab Run 7. Colab. 11-19 to 11-20. WP29
- [ ] WP38 Balance sim run 2 and tuning. main. 11-20 to 11-21. WP17, WP30, WP31
- [ ] WP39 (S) Colab Run 8. Colab. 11-20 to 11-21. WP37
- [ ] WP40 (S) 2 v 2 refactor. main. 11-20 to 11-25. WP36
- [ ] WP41 Win and lose screens, KO animation. main. 11-21 to 11-22. WP07
- [ ] WP42 Owner listening session. owner. 11-21. WP35
- [ ] WP43 Fonts (OFL, Latin subset). main. 11-21 to 11-22. WP07
- [ ] WP44 Regression playtest, 100 headless matches. main and sub-agent. 11-21 to 11-22. WP30, WP31, WP38
- [ ] WP45 (S) Scene extras: ground strips, themes, toll shake. main. 11-21 to 11-23. WP32, WP37
- [ ] WP46 Audio mix pass and CREDITS completeness. main. 11-22 to 11-23. WP15, WP42
- [ ] WP47 (S) Colab Run 9 (art freeze 11-22). Colab. 11-22. WP39
- [ ] WP48 MCP agent demo. Kiro. 11-22 to 11-24. WP12
- [ ] WP49 (S) Stretch UI wiring. main. 11-22 to 11-24. WP25, WP39, WP47
- [ ] WP50 i18n: English default plus 中文. main. 11-23 to 11-25. WP01, WP44
- [ ] WP51 Demo video script and shot list. Kiro. 11-23 to 11-24. WP27
- [ ] WP52 README rewrite in English. main. 11-24 to 11-25. WP08, WP48
- [ ] WP53 Bug-fix buffer (10 h reserved). main. 11-24 to 11-27. WP44
- [ ] WP54 Custom agents on the release candidate. Kiro. 11-25. WP30, WP50
- [ ] WP55 Cross-check 2. sub-agents. 11-25. WP50
- [ ] WP56 Worktree evidence and diagram refresh. main and Kiro. 11-26. WP48, WP54
- [ ] WP57 Final regression, performance check, screenshots. main. 11-26 to 11-27. WP55
- [ ] WP58 Devpost write-up. Kiro and main. 11-26 to 11-28. WP27, WP56
- [ ] WP59 Push and deploy (owner explicit yes). main. 11-27. WP57
- [ ] WP60 Record gameplay footage. owner and main. 11-28. WP57
- [ ] WP61 Edit video and upload (owner yes). owner. 11-28 to 11-29. WP51, WP60
- [ ] WP62 Submission checklist and read-back (owner explicit yes). main. 11-29. WP58, WP59, WP61

## Checkpoints

- [ ] CP1 11-12 · [ ] CP2 11-15 · [ ] CP3 11-18 · [ ] CP4 11-21 · [ ] CP5 11-24 · [ ] CP6 11-27 · [ ] CP7 11-29 (rules in section c of the plan)

## Owner windows

- [ ] OW1 11-10 · [ ] OW2 11-11 · [ ] OW3 11-16 · [ ] OW4 11-19 · [ ] OW5 11-21 · [ ] OW6 11-25 · [ ] OW7 11-27 · [ ] OW8 11-28 and 11-29 (questions in section b3 of the plan)
