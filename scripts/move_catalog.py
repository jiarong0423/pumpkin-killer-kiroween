#!/usr/bin/env python3
"""Z8 step 1: the move catalog and the static wiring gates (read-only; reads files, writes only its own output).

One table of every move the game declares and, for each layer, what that layer says: spec data (shared/heroes.json), page (index.html), engine (scripts/mcp_game_server.py),
MCP (scripts/mcp_stdio_server.py), audio map (js/audio.js DEFAULT_EVENT_MAP). A declaration a layer does not make is `absent`, so a missing one is visible before any run.
The same file also runs the static gates:
  M1s  hero facts (hp, damage, weapon) must agree between spec, page and engine
  M2s  every hero's weapon has a throw sound declared in the page and that event exists in the audio map; every projectile ultimate has its `ult_<hero>` and `ult_<hero>_hit` events
  M4   an audio event defined in the map but never referenced anywhere in the page or modules (allowlist: scripts/move_wiring_allowlist.json, each entry with a reason)
  M6   the rooms' refusal list: the page UI guard, the MCP bridge guard, the translated hint and the protocol doc must name the same heroes
Usage: python3 -B scripts/move_catalog.py [--write]   (--write saves docs/move_table_<date>.json; without it the table is only checked and summarised)
Exit code: 0 = no mismatch, 1 = at least one mismatch (listed with an ERROR prefix), 2 = a source file could not be read.
Log: logs_local/move_catalog.log (appended).
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOG = ROOT / "logs_local" / "move_catalog.log"
ALLOW = HERE / "move_wiring_allowlist.json"


def say(text):
    line = "%s %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
    print(line)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def load_spec():
    return json.loads(read("shared/heroes.json"))


def load_page(html):
    out = {"heroes": {}}
    block = re.search(r"const HERO_PROFILES = \{(.*?)\n    \};", html, re.S)
    for match in re.finditer(r"\n      (\w+): \{(.*?)\n      \}", block.group(1), re.S):
        body = match.group(2)
        fields = dict(re.findall(r"\b(weapon|imgKey|dmg|hp): (\"[^\"]+\"|[\d.]+)", body))
        out["heroes"][match.group(1)] = {k: (v.strip('"') if v.startswith('"') else float(v)) for k, v in fields.items()}
    out["ult_built"] = re.findall(r"\"(\w+)\"", re.search(r"const ULT_BUILT = \[(.*?)\];", html, re.S).group(1))
    for name in ("THROW_SOUND", "HIT_SOUND", "FLIGHT_SOUND"):
        found = re.search(r"const %s = \{(.*?)\};" % name, html, re.S)
        out[name.lower()] = dict(re.findall(r"(\w+): \"(\w+)\"", found.group(1))) if found else {}
    guard = re.search(r"function toggleUltimate\(\) \{(.*?)\n    \}", html, re.S).group(1)
    line = next((l for l in guard.splitlines() if "relayLive()" in l and "relay.noItems" in l), "")
    out["room_refused_page"] = sorted(re.findall(r"currentHero === \"(\w+)\"", line))
    return out


def load_engine():
    text = read("scripts/mcp_game_server.py")
    return {"ultimates_handled": sorted(set(re.findall(r"special == \"(\w+)\"", text))), "templates_from": "shared/heroes.json"}


def load_bridge():
    text = read("scripts/mcp_stdio_server.py")
    line = next((l for l in text.splitlines() if 'atype == "ultimate" and unit["hero"] in' in l), "")
    tuple_text = re.search(r"unit\[\"hero\"\] in \(([^)]*)\)", line)
    return {"room_refused_bridge": sorted(re.findall(r"\"(\w+)\"", tuple_text.group(1))) if tuple_text else []}


def load_audio_events():
    text = read("js/audio.js")
    start = text.index("var DEFAULT_EVENT_MAP = {")
    i = text.index("{", start)
    depth, end = 0, None
    for j in range(i, len(text)):
        depth += text[j] == "{"
        depth -= text[j] == "}"
        if depth == 0:
            end = j + 1
            break
    body = json.loads(text[i:end])   # the embedded map is plain JSON
    return sorted(body.get("events", {}).keys()), (start, end)


def referenced(name, html, modules, audio_span):
    for blob, label in [(html, "index.html")] + modules:
        text = blob
        if label == "js/audio.js":
            text = blob[:audio_span[0]] + blob[audio_span[1]:]
        if re.search(r"[\"']%s[\"']" % re.escape(name), text):
            return True
    return False


def build():
    spec, html = load_spec(), read("index.html")
    page, engine, bridge = load_page(html), load_engine(), load_bridge()
    events, audio_span = load_audio_events()
    modules = [(read("js/" + p.name), "js/" + p.name) for p in sorted((ROOT / "js").glob("*.js"))]
    prefixes = sorted(set(re.findall(r"\"(\w+_)\" \+", html)))
    errors, rows = [], []
    for hero in sorted(spec):
        s, p = spec[hero], page["heroes"].get(hero, {})
        row = {"hero": hero, "spec": {"hp": s["hp"], "dmg": s["dmg"], "weapon": s["weapon"], "ultimate": s.get("ultimate", {}).get("kind"), "status_on_hit": sorted((s.get("statusOnHit") or {}).keys())},
               "page": {"hp": p.get("hp", "absent"), "dmg": p.get("dmg", "absent"), "weapon": p.get("weapon", "absent"), "ult_built": hero in page["ult_built"]},
               "engine": {"ultimate_special_handled": hero in engine["ultimates_handled"] or hero == "knight"},
               "sounds": {"throw": page["throw_sound"].get(s["weapon"], "absent"), "flight": page["flight_sound"].get(s["weapon"], "absent"), "hit": page["hit_sound"].get(s["weapon"], "shared impact"),
                          "ultimate": "ult_%s" % hero if ("ult_%s" % hero) in events else "absent",
                          "ultimate_hit": "ult_%s_hit" % hero if ("ult_%s_hit" % hero) in events else "absent"},
               "room": {"ultimate": "refused" if hero in page["room_refused_page"] or hero in bridge["room_refused_bridge"] else "allowed"}}
        rows.append(row)
        for key in ("hp", "dmg", "weapon"):
            if p.get(key) != s[key]:
                errors.append("M1s %s: %s is %r in the spec and %r in the page" % (hero, key, s[key], p.get(key, "absent")))
        if not row["page"]["ult_built"]:
            errors.append("M1s %s: the spec has an ultimate (%s) but ULT_BUILT of the page does not list it" % (hero, row["spec"]["ultimate"]))
        if hero != "knight" and not row["engine"]["ultimate_special_handled"] and hero not in ("bride", "hunchback", "wizard"):
            errors.append("M1s %s: the engine has no `special == \"%s\"` branch" % (hero, hero))
        if row["sounds"]["throw"] == "absent":
            errors.append("M2s %s: weapon %s has no THROW_SOUND entry in the page" % (hero, s["weapon"]))
        elif row["sounds"]["throw"] not in events:
            errors.append("M2s %s: throw sound %s is not an event of the audio map" % (hero, row["sounds"]["throw"]))
        if row["sounds"]["ultimate"] == "absent":
            errors.append("M2s %s: no audio event ult_%s" % (hero, hero))
    # M6: the room refusal list on every layer
    page_list, bridge_list = page["room_refused_page"], bridge["room_refused_bridge"]
    if page_list != bridge_list:
        errors.append("M6 the page UI refuses %s in a room but the MCP bridge refuses %s" % (page_list, bridge_list))
    doc_lines = read("docs/mcp_agent_protocol.md").lower().splitlines()
    names = {"knight": ("knight", "pumpkin guard"), "reaper": ("necromancer", "reaper")}
    for hero in bridge_list:
        if not any("ultimate" in line and any(word in line for word in names.get(hero, (hero,))) for line in doc_lines):
            errors.append("M6 the protocol doc docs/mcp_agent_protocol.md has no line that says the %s ultimate is refused in a room" % hero)
    hint = json.loads(read("assets/i18n/en.json")).get("relay.noItems", "")
    if not hint:
        errors.append("M6 assets/i18n/en.json has no relay.noItems text")
    # M4: defined but never referenced
    allow = json.loads(ALLOW.read_text(encoding="utf-8")) if ALLOW.exists() else {"audio_events": {}}
    unwired = []
    for name in events:
        if referenced(name, html, modules, audio_span) or any(name.startswith(prefix) for prefix in prefixes):
            continue
        if name in allow.get("audio_events", {}):
            continue
        unwired.append(name)
        errors.append("M4 audio event %s is defined in the map but nothing references it" % name)
    return {"built": datetime.date.today().isoformat(), "heroes": rows, "page_room_refused": page_list, "bridge_room_refused": bridge_list, "audio_events": len(events),
            "audio_events_unwired": unwired, "dynamic_prefixes": prefixes, "allowlisted_audio_events": sorted(allow.get("audio_events", {}))}, errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    try:
        table, errors = build()
    except (OSError, ValueError, AttributeError, StopIteration) as exc:
        say("ERROR cannot read a source: %r" % (exc,))
        return 2
    say("move_catalog: %d heroes, %d audio events, %d dynamic name prefixes, %d allowlisted, %d mismatches" % (
        len(table["heroes"]), table["audio_events"], len(table["dynamic_prefixes"]), len(table["allowlisted_audio_events"]), len(errors)))
    for error in errors:
        say("ERROR " + error)
    if args.write:
        out = ROOT / "docs" / ("move_table_%s.json" % datetime.date.today().strftime("%Y%m%d"))
        out.write_text(json.dumps(table, indent=1, ensure_ascii=False), encoding="utf-8")
        say("wrote %s" % out.relative_to(ROOT))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
