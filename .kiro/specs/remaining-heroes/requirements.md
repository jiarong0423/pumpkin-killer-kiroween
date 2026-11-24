# Requirements: remaining heroes (hunchback, necromancer, ghost bride)
Written 2026-11-15 by Kiro from the main line's findings, `index.html` (lines 1 to 620 only), `js/class_stats.js`, `scripts/check_pose_set.py` and `docs/ultimate_mapping.md`. Nothing here was run. I did not list `assets/`, so the file counts in "Verified" are the main line's, not mine.

## Verified in the files, and where the brief differs
| Fact | Result |
|---|---|
| `HERO_PROFILES` holds only skeleton, wizard, bat, knight | Confirmed (`index.html` ~line 505 to 540: skeleton, wizard, bat, knight). |
| `HERO_BLURB` has four entries | Confirmed. `DOCK_PORTRAIT` and `DOCK_GLYPH` are used by `buildStartScreen` but are defined after line 620, which I did not read. Not verified. |
| `COMING_HEROES` has the three cards, `SHOW_COMING_SOON` is `false` | Confirmed. The cards are 鬼娃新娘, 鐘樓怪人 and 死靈法師. The bride blurb still says "everything on the flight path is hurt", which contradicts the owner's one-unit rule. |
| `ULT_BUILT = ["bat", "skeleton", "wizard"]` | Confirmed. |
| The page loads only `skel_*` and `bat_*` poses | Confirmed in `imgList`. Wizard and knight use only their `unit_*` pictures. |
| The page anticipates `proj_axe`, bleed, three purple fires | Partly. `BLEED_DMG = 2` (2 damage at each of the next 2 round starts) exists, and its comment names the hunchback's axe. `fx_ghostfire_purple` is loaded, with a comment about "circling reaper fires". `proj_axe` and `fx_axe_thrown` are not in `imgList`, and I have not read the weapon code. |
| `js/class_stats.js` has numbers for all three, two conflicting bride tables, an obsolete reaper combo | Confirmed, with more detail. Its `CLASS_KEYS` lists eight keys: skeleton, wizard, bat, knight, bride, hunchback, `reaper` and `necromancer`. The `necromancer` row was added by "task 118" as the eighth hero. So the table already treats the reaper and the necromancer as two heroes, which the owner's rename contradicts (open question 1). |
| Two bride tables | `CLASSES` (recommended): sound wave, hp 75, dmg 27, one unit, falloff. `PROVISIONAL`: bouquet, hp 100, dmg 12, splash 90 px. Hunchback also differs: `CLASSES` hp 130, dmg 20, knockback 50 px, speed 0.8; `PROVISIONAL` hp 100, dmg 22, knockback 100 px, speed 0.85. Both use `proj_bell`, not an axe. |
| Necromancer legacy alias only for `charge2` | **Differs.** `check_pose_set.py` lists five legacy names under key `reaper`: `idle1` (`necro_idle`), `charge2` (`necro_windup`), `release`, `empty`, `hit`. The script's `CLASSES` has no `necromancer` key, only `reaper`. |
| `ultimate_mapping.md` rows 5 to 7 partly stale | Confirmed. Row 7 is the skull-and-scythe reaper, which the owner dropped. Row 6 names a bronze bell weapon, not the axe. Row 5 (single-target wave plus a piercing ultimate) matches the owner's rule. |

## Terms
- `N`: the hero's normal damage. Every number below that comes from `docs/ultimate_mapping.md` or from `js/class_stats.js` and not from the owner is **INVENTED** and is named in one constants block so the owner's number changes in one place.
- Hero id: `hunchback`, `reaper` (display name 死靈法師) and `bride`. Files and keys named `reaper_*` and `necro_*` keep those names.

## General
1. The page shall use one stats table per hero. Where `js/class_stats.js` has two, the table the owner picks (open question 2) shall be the only one that `index.html` reads; the other shall be removed or marked obsolete. (check: "one stats table per hero")
2. A hero shall appear on the start screen only after all of its other requirements pass and the main line has verified it in the browser. The order inside one hero is: profile, poses, normal attack, ultimate, sounds, balance, start-screen card, `ULT_BUILT`. (check: "card and ULT_BUILT come last", main line reads the diff)
3. When any hero is added, the page's list of computer-opponent classes (the hard-coded four-name arrays for `aiClass` in `startMatch` and its initial value) shall include it. (check: "AI can pick every built hero")
4. If a picture, a pose frame or a sound file for a hero is missing, then the page shall still start and play: it shall draw the idle frame or the glyph and use the synthesized sound, never a blank unit or an error. (test: "missing asset falls back")
5. A normal attack by any of these three heroes shall hit at most one unit. (test: "normal attack hits one unit")

## Hero 1: hunchback (id `hunchback`, 鐘樓怪人)
6. **Profile and weapon.** The page shall have a `HERO_PROFILES.hunchback` entry with `name`, `hp`, `weapon: "proj_axe"`, `imgKey`, `wLen`, `wThick`, `dmg` and `tipColor`, plus matching `DOCK_PORTRAIT`, `DOCK_GLYPH` and `HERO_BLURB` entries, and shall load `proj_axe` (and `fx_axe_thrown` for the thrown spin). (test: "hunchback profile complete")
7. **Poses.** The system shall map the eight states `idle1`, `idle2`, `charge1`, `charge2`, `charge3`, `release`, `empty`, `hit` to the eight `hunchback_*` files, and shall show: idle (alternating the two frames) while waiting; the three charge frames in order while the player holds; `release` at the throw; `empty` while the axe is in flight; `hit` when struck. (check: `python3 -B scripts/check_pose_set.py --strict` reports hunchback 8/8; recorded browser run of every state)
8. **Normal attack.** When the hunchback throws, the system shall launch one heavy, slow axe (launch speed scale below 1, from the stats table), and when it hits a unit shall apply the table damage, apply bleed (`BLEED_DMG` at each of the next 2 round starts, a second bleed refreshing the count and not stacking), and push the unit back by the table knockback, away from the hunchback. (tests: "axe damage", "bleed applies and refreshes", "knockback direction")
9. The knockback shall never move a unit through the fence, off the canvas, or outside its side's movement range; it shall stop at the limit. (test: "knockback is clamped")
10. **Ultimate (provisional).** When the hunchback ultimate is released and the axe hits unit A, the system shall deal the normal hit to A, then one toll: a ground ring that damages A and up to 2 units next to A (neighbours fixed at impact), 1.5 x `N` each, no knockback and no bleed from the toll. If the axe misses, there shall be no toll. (INVENTED: ring, neighbour rule, no extra status; from `ultimate_mapping.md` row 6, whose weapon text is stale; test: "tower toll damage and targets")
11. **Start-screen card.** The hunchback card shall come from `HERO_PROFILES` (not `COMING_HEROES`), with a blurb that says: heavy slow axe, bleed, knockback. Its entry shall be removed from `COMING_HEROES`. (check: recorded browser run)
12. **Sounds.** The hunchback shall use only sound events that exist in `docs/audio_event_map.json` (throw, impact, charge, ultimate ready). `THROW_SOUND` shall map `proj_axe` to one of them. (test: "every hunchback sound event exists")
13. **Balance.** After the hunchback is wired, `scripts/sim_balance.js` shall run with it, and each pairing win rate shall be 40 to 60 percent and its class average 45 to 55 percent (the band in `js/class_stats.js`); otherwise the numbers are retuned in the stats table, not in the page. (check: sim output pasted in the result file)

## Hero 2: necromancer (id `reaper`, 死靈法師)
14. **Profile and weapon.** The page shall have a `HERO_PROFILES.reaper` entry named 死靈法師 with a purple-flame weapon (`proj_soulflame`; art `fx_flame_hand_purple` and `fx_ghostfire_purple`), plus `DOCK_PORTRAIT` (from `reaper_front`), `DOCK_GLYPH` and `HERO_BLURB`. (test: "necromancer profile complete")
15. **Poses.** The system shall map the eight states to the `reaper_*` files, using the legacy files `necro_idle`, `necro_windup`, `necro_release`, `necro_empty` and `necro_hit` where the standard names do not exist, as `scripts/check_pose_set.py` does. The old skull and scythe pictures shall not be used. (check: `check_pose_set.py` reports reaper 8/8; recorded browser run)
16. **Normal attack.** When the necromancer throws, the system shall push one purple flame forward from the hand. When the flame hits a unit it shall deal the table damage and set a burn (table: `BURN_DAMAGE` per round for `BURN_TURNS` turns). A second burn refreshes the count and does not stack. The burn shall not kill (it stops at 1 HP). (tests: "flame damage", "burn refreshes, does not stack", "burn is non-lethal")
17. **Ultimate (provisional).** When the necromancer ultimate is released, the system shall show the three purple fires orbiting behind the hero, the hand pointing forward, then the three fires changing colour and flying out. Each fire that hits a unit deals 1.5 x `N` divided by 3, to the unit it touches; the total on one unit is at most 1.5 x `N`. There is no separate trigger hit. (From the start-screen text `COMING_HEROES`; the numbers, the number of targets and the timings are INVENTED. `ultimate_mapping.md` row 7 and `class_stats.js` `reaper_combo` are obsolete; test: "three flames total at most 1.5 N")
18. **Start-screen card, sounds, balance.** The same as requirements 11, 12 and 13 for the necromancer. The card text shall describe the flame and the three fires. (check: recorded browser run; tests: "every necromancer sound event exists"; sim output)

## Hero 3: ghost bride (id `bride`, 鬼娃新娘)
19. **Profile and weapon.** The page shall have a `HERO_PROFILES.bride` entry with a sound-ring weapon (`sound_wave`, drawn as widening rings), and the `DOCK_*` and `HERO_BLURB` entries. The old bouquet shall not be used. (test: "bride profile complete")
20. **Poses.** The eight states map to the eight `bride_*` files, the same rule as requirement 7. (check: `check_pose_set.py` reports bride 8/8; recorded browser run)
21. **Normal attack.** When the bride throws, the system shall send one sound ring along the flight path as a visual effect. The ring shall damage only the first unit it touches, with the table damage (and falloff if the owner keeps it, open question 2). Units farther along the path shall take nothing. (tests: "ring hits one unit", "ring is visual")
22. **Ultimate (provisional).** When the bride ultimate is released and the ring touches unit A, the system shall deal the normal hit to A, then pass the wave on along the path, hitting each farther unit once, up to 4 units in all, 1.5 x `N` each. (INVENTED: the 4-unit cap, the 0.1 s spacing; from `ultimate_mapping.md` row 5; test: "piercing wail damage and targets")
23. **Start-screen card.** The card blurb shall say the ring hits one unit, replacing today's text "everything on the flight path is hurt". (check: recorded browser run; the old sentence is not in the page)
24. **Sounds and balance.** The same as requirements 12 and 13 for the bride. The stand-ins `spell_magic.ogg` and `ghost_real.ogg` may be used only if they exist and are credited as CC0 in `assets/audio/CREDITS.md`; otherwise use the synthesized sound. (tests/checks as above)

## Ultimates for all three
25. Each hero's ultimate shall follow the ultimate rules of `docs/ultimate_rules.md` and the `ultimates-v2` spec: three pips, armed on the unit's own turn, at most 2 per match, and its id shall be added to `ULT_BUILT` only after its ultimate passes. (check: main line reads `ULT_BUILT`)
26. For each ultimate, the follow-up damage on one unit shall total at most 1.5 x `N`, rounded to 0.1 per strike, with `N` after the frost curse. (test: "property: ultimate damage never exceeds 1.5 N", same name as in `ultimates-v2`)

## Records
27. Each task ends with its test output pasted into its result file and rerun by the main line, which records it in `docs/kiro_verified.json`. Kiro's report alone never counts as verification.

## Out of scope
Skeleton, wizard, bat and knight code; new art (owner, Colab); 4 v 4 target selection; the levels spec (`levels-ui`); English labels (W6); the eighth hero until the owner names it (open question 1).

## Open questions for the owner
1. **Which hero is the eighth?** Your target is 8 heroes. The necromancer is the old reaper, so the playable list is skeleton, wizard, bat, knight, bride, hunchback and necromancer: 7. `js/class_stats.js` already has an eighth row (`necromancer`, added by task 118 next to the old `reaper` row), but that row and the reaper row describe the same hero now. Options: (a) name a new eighth hero (not in any doc I read), (b) take a hero from `docs/roster_design.md` (Plague Doctor or Lantern Warden; not your roster), (c) ship 7 and set the target to 7. Recommended: (c) for the freeze, and name the eighth later. Until you answer, the plan uses 7 and removes the duplicate `reaper` row from the balance table.
2. **Which stats for the bride and the hunchback?** The recommended table (bride hp 75, dmg 27, one-unit wave with falloff; hunchback hp 130, dmg 20, knockback 50 px) or the provisional one (bride hp 100, dmg 12, bouquet splash; hunchback hp 100, dmg 22, knockback 100 px)? Recommended: the recommended table, because its bride wave is one unit as you said. Requirement 1 waits for this.
3. **Hunchback ultimate with an axe.** Keep the bell-tower toll (ground ring) although his weapon is an axe? Recommended: yes, it fits the tower.
4. **Bleed.** Does a second hit refresh the count (recommended) or stack? Can bleed kill (the burn cannot)?
5. **Bride poison.** A comment in `index.html` says the bride's wave is planned to poison. Do you want poison on her ring? Recommended: no, it is not in your brief.
6. **Necromancer ultimate.** Is three fires with 1.5 x `N` in total (0.5 x each) what you want, and may the three fires hit different units? Recommended: yes to both.
7. **Ids.** Keep `reaper` as the internal id and file prefix, with 死靈法師 as the shown name (as you said)? Recommended: yes.
