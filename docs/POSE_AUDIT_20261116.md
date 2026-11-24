# Pose audit 2026-11-16 (scripts/pose_audit.py, facts from index.html and the picture files)

windup = wind-up frame, charge2 = late charge frame; 'diff' = how much the picture's silhouette differs from the idle (under 0.04 = a copy of the idle).

| Hero | States the page can show | Missing in the page | Picture files: diff against idle | Copies / absent |
|---|---|---|---|---|
| skeleton | hit, idle, release, windup | - | skel_windup.png 0.66; skel_release.png 0.65; skel_hit.png 0.59 | - |
| wizard | charge2, hit, release, windup | - | wizard_charge1.png 0.05; wizard_charge2.png 0.05; wizard_charge3.png 0.17; wizard_hit.png 0.28 | - |
| bat | draw, hit, release, windup | - | bat_draw.png 0.43; bat_windup.png 0.35; bat_release.png 0.42; bat_hit.png 0.49 | - |
| knight | hit, release, windup | - | knight_unarmed_windup.png 0.33; knight_unarmed_release.png 0.17; knight_unarmed_hit.png 0.29 | - |
| reaper | charge2, hit, idle2, release, ult, windup | - | necro_windup.png 0.53; necro_charge2.png 0.25; necro_release.png 0.45; necro_hit.png 0.37 | - |
| bride | charge2, hit, release, windup | - | bride_windup.png 0.00; bride_release_new.png 0.39; bride_hit_new.png 0.29 | bride_windup.png |
| hunchback | hit, release, windup | - | hunchback_unarmed.png 0.45; hunchback_windup.png 0.46; hunchback_release_new.png 0.30; hunchback_hit_new.png 0.43 | - |
| hag | charge2, hit, idle2, release, windup | - | hag_charge1.png 0.01; hag_charge2.png 0.00; hag_charge3.png 0.26; hag_release.png 0.39; hag_hit.png 0.17 | hag_charge1.png, hag_charge2.png |
