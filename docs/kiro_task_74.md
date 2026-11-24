# Kiro task 74 — game flow and system planning (Sonnet = flow and systems; main line verifies everything)

Owner 2026-11-10: Sonnet plans the GAME FLOW and SYSTEMS; GPT/Terra does the art (task 73, do not touch art). Read first: (not published) (sections 三, 四, 五), (not published) (the owner rules are rows in it; they are DECIDED and not to be reopened), docs/ultimate_rules.md, js/class_stats.js, the HERO_PROFILES / ULT_BUILT / status-effect code in index.html (read only), docs/kiro_54*, kiro_55*, kiro_56*, kiro_57* outputs if present in ../pumpkin-killer_kiro54 .. kiro57 /docs.

Facts from the read-only inventory (verify the ones you rely on in the code, say so when one is wrong):
- HERO_PROFILES (index.html ~486) has only skeleton, wizard, bat, knight; js/class_stats.js also has bride, hunchback, reaper, and no necromancer. Bride, hunchback and reaper have unit and pose art but are not playable.
- ULT_BUILT = ["bat","skeleton","wizard"]; knight, bride, hunchback, reaper have no ultimate.
- Status effects now in the game: bleed (2 dmg x 2 round starts), poison (2 dmg x 2), frost = weak (-15% damage for 2 throws, motion 1.6x slower), slow (cannot move one round), stun (stars, 7 s turn). Walls lose 8 percent per hit.
- No sounds mapped for frost, stun, bleed, ultimates, new-class attacks; three sound files missing (move_step, item_pickup, ultimate_ready_chime).
- Scene picker lists two scenes without backgrounds (belltower, pumpkin field).

Deliver ONE file: docs/kiro_74_flow_plan_claude-sonnet-5.5.md (max 250 lines), no code edits anywhere:
1. Make-a-class-playable checklist (the exact steps and files, in order) for bride, hunchback, reaper, then necromancer; the class stat table proposal per class with reasoning against the existing four (use numbers from class_stats.js; the owner agreed: no across-the-board nerfs).
2. Ultimate rules for knight (defend-mode A-B-C hidden points, already DECIDED in the log), bride, hunchback, reaper, necromancer (log rows exist for the necromancer); only fill gaps, do not change decided rules; mark every number as provisional.
3. Status-effect system spec: one table of every status (source, duration, damage, visual, sound, stacking, what clears it, interaction with ultimate and shield), consistent with the log rows.
4. 4v4 / multi-unit: three options with turn flow, HUD and AI impact each, a recommendation, and the exact owner decision needed (this is an open owner decision, B1).
5. Sound event map: every game event (list them from the code) against existing sound files, the gaps, and which gaps to fill with synthesised sounds versus CC0 files (assets/audio/CREDITS.md lists the licences).
6. A schedule: ordered steps with size, dependencies, what can run in parallel, which steps need the owner, and a verification command or measurement per step that the main line can run itself.
Do not claim anything was run or tested. Plain English with the Chinese in-game terms where the log uses them.
