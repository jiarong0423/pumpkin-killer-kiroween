#!/usr/bin/env python3
"""Write docs/character_plan_20261116.json: the current roster table, FACTS only (numbers are read from index.html; rules are written from the code and the owner decisions).

Used as the input of the game-design and balance review (docs/character_plan_review_20261116.json). Exit code 1 if a hero is missing in the page.
Usage: python3 -B scripts/make_roster_json.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def profile(hid):
    m = re.search(r"\n      %s: \{\n(.*?)\n      \}" % hid, HTML, re.S)
    if not m:
        return None
    body = m.group(1)
    g = lambda k: (re.search(r"%s:\s*([^,\n]+)" % k, body) or [None, None])[1]
    return {"hp": float(g("hp")), "dmg": float(g("dmg")), "weapon": g("weapon").strip('" '), "imgKey": g("imgKey").strip('" ')}


RULES = {
    "skeleton": {"name": "Skeleton Spearman", "normal": "Javelin, bleeds (2 per round start, 2 rounds), frost curse on hit (target attacks 15 percent weaker for its next 2 throws: the code multiplies by 0.85)", "ultimate": "Triple javelin: each carries 1.5 x normal / 3, +5 percent per earlier hit, the third of three is a head crit", "special": "Head shots crit"},
    "wizard": {"name": "Pumpkin Wizard", "normal": "Cannonball, poison on hit (2 rounds)", "ultimate": "Big pumpkin blast: 1.5 x normal splash within 234 px of the landing point, 13 flames burn", "special": "Lobbed shell with splash ultimate; damage 24 is the same as the skeleton (the bride 25 and the knight total 30 are higher)"},
    "bat": {"name": "Bat-cat Assassin", "normal": "One shuriken, slows the target's next move", "ultimate": "Shuriken rain: 5 shurikens, each 1.5 x normal / 5", "special": "Fast, light"},
    "knight": {"name": "Pumpkin Guard", "normal": "Thrown small shield bounces 1 to 6 times (die), total damage shared", "ultimate": "Hidden shield points (js/knight_ult.js): up to 3 hidden blocks (A, B, C) marked on remembered enemy paths while defending, each stops one of the next enemy throws that crosses it; wired in the page", "special": "Floating shield (coffin) over its own head on a slight arc: can give up the attack to place it"},
    "reaper": {"name": "Necromancer", "normal": "Purple flame, flat quick trajectory. The planned burn status (2 per round for 3 rounds) is NOT implemented in the page: the flame deals its direct damage only", "ultimate": "Soul-fire volley: 3 flames 11.5 each, 0.15 s apart, burn once", "special": "Three circling ghost fires are its energy pips"},
    "bride": {"name": "Ghost Bride", "normal": "Sound wave 105 px half width, hits only the aimed unit, stepped falloff 100/75/50 percent at 40/75/105 px, counts where it lands, poison on hit", "ultimate": "Bat swarm: a hit inside 40 px calls a swarm on every enemy for 25 x 1.3 = 32.5, shield cannot stop it (1v1 total 57.5 at full falloff)", "special": "Aim precision matters more than for any other hero"},
    "hunchback": {"name": "Bell-tower Hunchback", "normal": "Giant spinning axe, bleeds, knockback 50 px on a surviving direct hit (kept inside its zone)", "ultimate": "Boomerang axe: pierces every unit on the way out (21 each, shields do not stop it), returns to the first unit hit for 31.5 only if the outbound pass hit someone (1v1 total 52.5)", "special": "Highest HP of the roster except the knight"},
    "hag": {"name": "Ghost Nun", "normal": "Spinning silver cross wrapped in black smoke, no status", "ultimate": "Silver cross strike: two contacts at 0.5 x normal each (11 + 11 = 22 total, provisional), one touched enemy gets an electric stun (next turn shortened to 7 s)", "special": "HP and damage are PROVISIONAL guesses of the main line (the owner gave no numbers)"},
}
PROVISIONAL = {"hag": ["hp", "dmg", "ultimate multiplier 0.5"], "reaper": ["hp 105 dmg 23 working values"], "knight": ["dmg 30 is the TOTAL over the bounces"], "bride": ["band widths 40/75/105 invented"], "hunchback": ["boomerang return speed 1400 invented", "knockback 50 px"]}
ART = {"skeleton": "complete", "wizard": "complete (face-locked frames)", "bat": "complete", "knight": "complete (no-shield idle, throw frames)", "reaper": "complete (idle2, charge2, ultimate point)",
       "bride": "windup, late-charge (old wide-mouth frame), release, hit; expression change is small", "hunchback": "windup and hit done; release uses the empty-handed stance (a clean throw frame is still missing)", "hag": "empty-handed idle, idle2, windup, late charge, release, hit; silver cross is a separate picture"}
ULT_WIRED = {"skeleton": True, "wizard": True, "bat": True, "reaper": True, "bride": True, "hunchback": True, "hag": True, "knight": True}


def main():
    heroes, missing = [], []
    for hid, r in RULES.items():
        p = profile(hid)
        if p is None:
            missing.append(hid)
            continue
        heroes.append(dict(id=hid, name=r["name"], hp=p["hp"], damage=p["dmg"], weapon=p["weapon"], normal_attack=r["normal"], ultimate=r["ultimate"], ultimate_wired_in_page=ULT_WIRED[hid],
                           special=r["special"], provisional=PROVISIONAL.get(hid, []), art=ART[hid],
                           hits_to_kill_the_average_enemy=None))
    avg_hp = sum(h["hp"] for h in heroes) / len(heroes)
    for h in heroes:
        h["hits_to_kill_the_average_enemy"] = round(avg_hp / h["damage"], 1)
    data = {
        "generated": "2026-11-16", "source": "index.html (hp, damage, weapon) and the main line's reading of the code; scripts/make_roster_json.py",
        "match_rules": {"mode": "1 v 1 in the page (4 v 4 planned for rooms)", "turn_seconds": 12, "wind_range": [-4, 4], "wind_acceleration": {"headwind_px_s2_per_unit": 84, "tailwind_px_s2_per_unit": 56},
                         "weather": "rain x0.9 attack, storm x0.9 attack and +1.5 wind, snow x0.5 movement, fog and clear no change (js/weather.js), seeded by match seed and round",
                         "energy": "each successful throw adds 1 pip, 3 pips arm the ultimate, at most 2 ultimates per match, ultimate damage is capped at 1.5 x the normal hit on one unit (the bride and the hunchback exceed it in their own ways)",
                         "head_shot": "crit multiplier and a stun on the top quarter of the body near the middle",
                         "fence": "central wall, 8 damage per hit"},
        "heroes": heroes,
        "average_hp": round(avg_hp, 1),
        "known_gaps": ["necromancer burn status not implemented", "reaper hit box is 50 px wide, everyone else 70", "hunchback clean release frame", "class_stats.js rows for bride, hunchback, reaper are older numbers and the balance simulator has no ghost nun", "weather is not in the MCP round hash yet"],
    }
    path = os.path.join(ROOT, "docs", "character_plan_20261116.json")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("wrote", os.path.relpath(path, ROOT), "heroes", len(heroes), "missing", missing)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
