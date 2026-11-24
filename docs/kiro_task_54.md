# Kiro task 54 — the knight's ultimate is the defend-mode A-B-C shield

Read: (not published) (newest rows last: 'Knight ULTIMATE = defend mode', and the earlier shield rows: thrown shield, floating shield invisible to the opponent, 'A-B-C three points matching the enemy's next three attacks'), docs/ultimate_rules.md, docs/ultimate_mapping.md (the old 'Shield Chain' row is DROPPED), index.html (toggleShieldDefend, lockShield, shields, historyTrajectories, the shield drag code near pointermove), docs/kiro_51_recommendations.md section 6 (its guard / bash readings are DROPPED).

Owner rule (2026-11-09): the knight's ultimate is a defend-mode action. With three lit energy pips the knight, in defend mode, places THREE hidden shield points A, B and C on the enemy's remembered paths (the last up to 4 enemy shots); each point answers one of the enemy's next three attacks in order; the enemy cannot see them (a point is revealed only for 1.4 s when it blocks). It uses the whole turn (no throw), max 2 ultimates per match, pips public.

Design with numbers and a clear interaction script:
1. Placement UI: how the three points are put down in defend mode (drag the shield to A, tap lock-point, then B, then C? one drag each? a limit on moves per turn), what happens if fewer than three are placed, how cancelling works.
2. Rule per point: how wide a point is, which projectile it blocks (any enemy projectile passing through; ultimates multi-unit hits?), full block or partial (give a number), what happens when the enemy attack does not pass through it, and when an enemy attack skips a point (does the next attack use the same point or the next one).
3. Lifetime: three attacks or N rounds, whichever first; interaction with the existing 2-round / 2-charge floating shield (does the ultimate replace it?).
4. Fair information: the AI opponent must not see the points; the AI knight uses the same rule with only public information (its own pips, the human's last shots). Give an AI rule that is not a simulator.
5. Balance: effect on hit rate (model like kiro_51), match length 8 to 12 rounds, a number that makes it worth a full turn without making the knight unkillable. Does a blocked hit count for the enemy's energy? (recommend one).
6. Art/effects list for Colab and code (three glowing rune points, reveal flash, block spark) in docs/art_style_guide.md style; sound events to reuse from (not published)

Write (not published) Do not edit index.html. Use `python3 -B` / `node` for any scripts.
