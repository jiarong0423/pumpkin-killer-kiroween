#!/usr/bin/env python3
"""Verify shared hero combat values stay aligned with the playable page."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def page_profiles(source):
    hero_ids = ("skeleton", "wizard", "bat", "reaper", "hag", "bride", "hunchback", "knight")
    result = {}
    for hero_id in hero_ids:
        match = re.search(r"^      %s: \{(?P<body>.*?)(?=^      (?:%s): \{|^    \};)" %
                          (hero_id, "|".join(hero_ids)), source, re.MULTILINE | re.DOTALL)
        if not match:
            raise AssertionError("could not parse %s from HERO_PROFILES" % hero_id)
        body = match.group("body")
        values = {}
        for key in ("hp", "dmg"):
            number = re.search(r"\b%s:\s*(\d+(?:\.\d+)?)" % key, body)
            if not number:
                raise AssertionError("could not parse %s.%s" % (hero_id, key))
            values[key] = float(number.group(1))
        weapon = re.search(r'\bweapon:\s*"([^"]+)"', body)
        if not weapon:
            raise AssertionError("could not parse %s.weapon" % hero_id)
        values["weapon"] = weapon.group(1)
        result[hero_id] = values
    return result


def main():
    page = page_profiles(read(os.path.join(ROOT, "index.html")))
    shared = json.loads(read(os.path.join(ROOT, "shared", "heroes.json")))
    assert set(shared) == set(page), "shared hero ids differ from HERO_PROFILES"
    for hero_id, expected in page.items():
        actual = shared[hero_id]
        for key, value in expected.items():
            assert actual[key] == value, "%s.%s: index.html=%r heroes.json=%r" % (
                hero_id, key, value, actual[key])
    print("OK: shared/heroes.json matches index.html HERO_PROFILES for 8 heroes.")


if __name__ == "__main__":
    main()
