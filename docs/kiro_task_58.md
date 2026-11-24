# Kiro task 58 — review the current game's details and controls (a player's view)

Read: (not published) (the original concept), (not published) (a real screenshot of the game canvas in a match: the top HUD, units, fence), (not published) (every clickable element with its position, whether a real click reaches it, text, title), (not published) (newest rows last), docs/dock_design.md, (not published) If you cannot view the pictures, say so first and work from the audit and the docs only; do NOT invent what a picture shows.

Owner request (2026-11-09): "look at the screenshot and say what Kiro finds, about the current game's details and the controls". Known: the right-side dock buttons were dead for real mouse clicks (fixed today: pointer-events); the owner finds the top HUD not refined and wants no HP bar there (see 'Top HUD redesign').

Find, from a player's point of view:
1. Controls that do nothing, do something surprising, or give no feedback (click, key, drag). Use the audit first, then the code in index.html (onclick handlers, pointer handlers, keyboard).
2. Things a first-time player cannot discover (the shield lock, the ultimate button, the move dice, the power meter) and what a one-line hint should say.
3. Text that is cut, overlapping, wrong or inconsistent (the top HUD wind label showed duplicated characters in a screenshot the owner sent: '風 有風').
4. Touch and small-screen problems (target sizes below 44 px, things that only work with the mouse).
5. A ranked list: P0 (blocks play), P1 (confusing), P2 (polish), each with the file and line to change and a one-line fix. Do not edit index.html.
Write (not published) Also state what you could not verify.
