# Element effects, 2026-11-15

`js/element_fx.js` is declarative normal-attack presentation data. It does not change damage, statuses, or combat resolution.

| Hero | Attribute | Normal attack: launch / trail / impact | Ultimate adds | Status icon | Code-made / art still needed |
|---|---|---|---|---|---|
| Skeleton | FROST | charge aura / ice shards / frost shatter | triple soul javelins | `ui_frost_curse` | New frost trail is code-made; spectral spear art remains optional. |
| Wizard | POISON | muzzle and smoke / toxic bubbles and orange sparks / cloud, drip, burst | chain blast and shock rings | `ui_poison_bubble` | New toxic trail is code-made; cannonball art is missing. |
| Bat-cat | SHADOW | rune halo / black wisps and gold dust / wisps and sparks | five-shuriken scatter | `ui_slow_shadow` | New shadow trail is code-made; front portrait and charge poses are missing. |
| Pumpkin Guard | IRON | bounce ring / steel sparks / ricochet sparks and ring | shield chain | `ui_shield_guard` | New iron trail is code-made; ricochet ultimate art and page timeline are missing. |
| Necromancer (`reaper`) | SOULFIRE | ghost fire and rune / purple flame / rune mark and sparks | three-soul fire volley, hallucination | `ui_hallucination_mark` | New soulfire trail is code-made; flame impact and burn-overlay art remain needed. |
| Ghost Bride | SOUND | charge aura / pale pink-white wave / sound rings and wave | piercing wail | `ui_sound_wave` | Ring effects are code-made; page wiring is absent. |
| Hunchback | BLOOD + BRONZE | charge and smoke / bronze bell trail / blood spray and toll rings | tower toll and knockback ring | `ui_bleed_drop` | Bell/ring effects are code-made; bell projectile and page wiring are absent. |
| Ghost Nun (`hag`) | HOLY LIGHTNING | spinning cross and electric spark / yellow-white arcs / electric impact | spinning cross path and electric stun | `ui_cross_curse` | New holy-lightning trail is code-made; cross, poses, smoke, and page wiring remain art work. |

## Current weak points

The Ghost Nun is weakest for both normal and ultimate effects because she is not playable and all character assets are queued. Bride and Hunchback are next: their code effects exist, but neither is wired into the page, and Hunchback lacks a projectile. Pumpkin Guard's normal throw works, but its ultimate lacks a timeline and page wiring. Necromancer has an ultimate timeline but its normal trail currently bypasses the particle system. The four current generic launch and impact combinations also conceal every hero's intended attribute.

## Main-line `index.html` handoff

1. In the **Update Flying Projectiles** trail ternary beginning `if (p.weapon !== "proj_flame") fxEmit(...)`, replace weapon selection with `ElementFx.trail(heroId, p.isHeavy)` and pass its preset and scale.
2. In `executeThrow`, replace the shared `fxEmit("weapon_rune_halo"...)`, `fxEmit("muzzle_flash"...)`, and wizard-only smoke block with `ElementFx.launch(heroId)` entries, preserving `dirX`, team, wizard recoil, and heavy-shot logic.
3. In the hero-collision block, replace the shared `fxEmit("impact_burst"...)` and `fxEmit("hit_sparks"...)` calls with `ElementFx.impact(heroId, "hero")`; keep KO effects and shield interception separate.
4. Map each `statusIcon` in the HUD/status renderer: `ui_frost_curse`, `ui_poison_bubble`, `ui_slow_shadow`, `ui_shield_guard`, `ui_hallucination_mark`, `ui_sound_wave`, `ui_bleed_drop`, `ui_cross_curse`. New icon files still need art where absent.
