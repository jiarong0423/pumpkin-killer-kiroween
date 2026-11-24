# Kiro task 31 - design the ghost airdrop (supply drop) system: rules, items, balance (design only)

## Owner words (2026-11-09, in order)
"Ghosts carry supply crates and drop them" (concept mockup). "Supplies thrown from the air can be picked up." "Add a supply slot (補充物資欄位)." "Make the ghost, and have the crate come down on a PARACHUTE." "I said ghost airdrop." Already decided earlier (docs/game_mode.md): the slot holds ONE item; picking up a new crate REPLACES the old item.

## What the main line already built (prototype, read index.html: SUPPLY_ITEMS, scheduleAirdrop, updateAirdrop, drawAirdrop, useSupply)
- Every 2nd round (roundNum even) a ghost flies left to right at y~170 at 330 px/s, releases a crate over a target x, the crate descends on a parachute at 150 px/s (slight sway), lands at GROUND_Y-20, the parachute collapses.
- Side alternates each drop (one near the player at player.targetX+140.., next near the AI at ai.targetX-140..), offset 0..160 px: fair by construction.
- Pick up = a unit's x within 70 px of the crate (stand on it; units move by the Move die, 36 px per pip). Player item goes to the dock slot "物資"; tap the slot on your turn to use it. The AI uses a pickup at once (heal).
- Items so far: heal +30 HP, heavy shot +1. Art for ghost, crate and parachute is being generated on Colab (not available to you; never draw art).

## Do exactly this
1. Read docs/game_mode.md (Airdrops section), (not published), docs/experience_design.md if present, and the airdrop code above (read only).
2. Write docs/airdrop_design.md answering, with a recommendation and one-line reason each (mark everything you cannot test as "unverified"):
   a. Frequency and timing: every 2nd round is a guess; propose a rule that avoids snowballing and avoids a drop that nobody can reach (units move at most a few steps per turn: compute reach from DICE_STEP_PX and the dice range in index.html).
   b. Landing zones: where a crate may land (never on the fence, never inside a shield, never off-screen), the fair-side rule, and a reachable-in-one-turn guarantee for the side it favours.
   c. Item table: 5 to 7 items (id, icon idea, effect, who may take, duration, counter-play). Must not break balance (heal cap, no free kill, no item that ignores the shield). Say which need new engine support (e.g. extra die, poison shell, shield repair) and which already work. Ultimates are NOT designed: no ultimate-related item.
   d. Pickup rules: stand-on radius, who gets it if both units are in range, what happens when the slot is full (replace, per the owner), can a thrown projectile destroy a crate (propose yes/no).
   e. The agents (AI and sub-agent opponents): which crate/slot state is public (it is visible to humans, so it must be in the public state), how an AI decides to detour to a crate, and what the MCP server (scripts/mcp_stdio_server.py) should expose (field names only, no code).
   f. Feel and feedback: ghost entrance (sound cue from docs/sound_mapping.md ambient family, a short spooky laugh), parachute sway, landing thump, pickup chime, slot glow; screen must stay clean. Name the existing sound events to reuse.
   g. A short test list the main line can turn into automated checks (determinism with a seed, reachability, replace rule, fairness over 20 drops).
3. Also write docs/airdrop_asset_requests.md: only the Colab images still needed beyond ghost / crate / parachute (e.g. item icons for each item in your table, 96x96 each, one-sentence prompts, flat magenta background).
4. Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download anything. Do not create images.
6. COMPARE WITH PLAY EXPERIENCE (owner: "let him compare the play experience"): use web_search / web_fetch to study how known games handle parachute crate drops (for example Worms' weapon crates, Cat vs Dog / Gunbound-style turn games, Fortnite or PUBG supply drops for readability, Hearthstone-style item feedback). In docs/airdrop_design.md add a section "Comparison": a table of 4 to 6 games (game, what the drop does, how it is announced, how a player reaches it, balance trick, what we copy, what we avoid), citing the page you read. Mark anything you only saw in a search snippet. Then list where our prototype (rules a to g) differs from the best practice and what to change first. Also compare with the owner's own play feel: (not published) says short messages, nothing messy, readable screen.
7. Finish with a 6-line summary and say what you could not verify.
