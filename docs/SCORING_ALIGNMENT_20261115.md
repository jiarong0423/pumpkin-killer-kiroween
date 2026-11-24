# Priorities by the official judging criteria and usage rules (2026-11-15)

Source: `(not published)` (sections 4 and 6). Five equal criteria, 20 percent each; stage 1 is pass/fail (fits the theme, reasonably applies Kiro). Category: Costume Contest (a haunting, polished, unforgettable UI). This file ranks work by what it adds to a criterion, not by what is fun to build.

## Stage 1 (pass/fail): must all be true
| Requirement | Now | Work block |
|---|---|---|
| Built with Kiro, enough use | strong in CLI, IDE used for hooks and specs | B01, B12 |
| Public GitHub repo, MIT in About, `.kiro` at root and not ignored | not pushed yet | B10, B11 |
| URL to the working app (free, open until 2027-01-29) | missing | B03 |
| Video under 3 minutes, public YouTube, shows it working | missing | B16 |
| English materials (video, description, test steps) | game text is Chinese | B09, B13 |
| New project after 10-30, pre-existing code disclosed | first commit 10-31 | B14 |

## Stage 2: criterion by criterion
| Criterion (20 percent each) | What judges ask | What we have | Gap | Best next work (value for cost) |
|---|---|---|---|---|
| Potential Impact | real problem, real audience, would someone use it | a playable game plus an open agent-seat protocol | the "problem" story is thin | one clear pitch line in README and video: bring your own agent, measured levels; no code |
| Technological Implementation | how deeply and skilfully Kiro is used; a strategy; a variety of tools; experimentation | specs (release-package, ultimates-v2, levels-ui, remaining-heroes), steering always loaded, hooks run in the IDE, custom agents, MCP server, power installed, PBT tests, 40+ tracked Kiro tasks with a verified ledger | MCP not loaded in the IDE; Web and Crew not used; powers not shown activating | B01: fix the IDE MCP load, one transcript; show the verified ledger; say plainly what was not used |
| Design | complete, coherent, polished, intentional | strong art, HUD, effects | unfinished things visible (4 of 7 heroes, missing pictures, Chinese-only text) | B09 English labels, B07 missing pictures or drop references, effects polish (B04), start screen already cleaned |
| Innovation/Idea | novel concept, unusual combination | agents take a seat by MCP from public information only; one-match learning; adaptive public level; hidden-point shield | not yet visible in the game page | B05 wiring: show the level in the HUD; one short transcript of an agent playing |
| Presentation | video shows it working end to end; clear pitch; memorable | none yet | video and URL | B16 and B03 before anything else is added |

## Where the hero count fits
Heroes add to Design (a complete roster) and a little to Innovation (class synergies), and they add risk (balance, art wiring, `index.html` changes). The roster should be complete and polished at the number we can finish, not at a larger number half done. Seven exists on paper (the necromancer is the renamed reaper). Recommendation: ship 6 or 7 heroes that are balanced and shown cleanly; the 8th only if everything on the Stage 1 list is already green by 12-01.

## Order that follows from the scoring
1. Stage 1 items (URL, repository, video, English text): without them nothing else counts.
2. Technological Implementation evidence (IDE MCP, ledger, specs, hooks): 20 percent and the contest's own theme.
3. Design: remove visible gaps (missing pictures, English labels), finish heroes in order hunchback, necromancer, bride.
4. Innovation made visible: level in the HUD, one recorded agent match.
5. Extra heroes beyond 7, 4 v 4, local LLM seat: only with time left after 12-01.

## Prize notes (rules section 6 and 8)
One Overall OR one Category prize, plus any bonus. Best Demo needs the best Presentation score and a top 10 percent total. Blog and Social Blitz need posts written by the owner (the Kiro team judges "original thoughts vs AI writing").
