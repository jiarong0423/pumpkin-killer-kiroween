#!/usr/bin/env python3
"""Front-versus-back comparison report (docs/MATRIX_SPEC_20261117.md).

Reads logs_local/matrix_engine.json and any of matrix_page_vm.json, matrix_page_desktop.json, matrix_page_phone.json that
exist, and writes docs/FRONT_BACK_COMPARE_20261117.md: per cell and per size (rounds mean, left win share, hits per
throw, near misses, pity triggers, comeback hits, errors), a flag where a page end differs from the engine by more than
25 percent in rounds or more than 20 points in left win share, every error with its seed, a seed-level consistency check
(tiers and right hero must be identical on every end), and a short list of what differs with a probable cause that is
DERIVED FROM THE DATA AND MARKED AS A HYPOTHESIS.

Run:   python3 -B scripts/compare_front_back.py [--logs logs_local] [--out docs/FRONT_BACK_COMPARE_20261117.md]
Exit:  0 when the report was written, 2 when the engine file is missing or unreadable (nothing to compare against).
A missing or unreadable page file is listed in the report and skipped; it is never an error.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"]
PAGE_ENDS = (("vm", "matrix_page_vm.json"), ("desktop", "matrix_page_desktop.json"), ("phone", "matrix_page_phone.json"))
ROUNDS_FLAG = 0.25      # relative difference in mean rounds
WIN_FLAG = 20.0         # points of left win share
HIT_FLAG = 0.08         # hits per throw (absolute), hypothesis threshold only
SIZE_ROUNDS_HYP = 0.15  # relative difference of a size's mean rounds that earns a hypothesis
SIZE_WIN_HYP = 10.0     # points of a size's left win share that earns a hypothesis
LEFT_WIN = ("left", "cap_left")


def load_file(path):
    """(data, note): data is None when the file is missing or unusable."""
    if not os.path.exists(path):
        return None, "missing"
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as error:
        return None, "unreadable (%s)" % error
    if not isinstance(data, dict) or not isinstance(data.get("matches"), list):
        return None, "no `matches` list"
    return data, "ok"


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def summarize(matches):
    """Row for a group of match records; counters the end cannot measure (null) stay None."""
    n = len(matches)
    row = {"n": n, "rounds": None, "left_win": None, "hits_per_throw": None, "near_misses": None, "pity": None,
           "comeback": None, "errors": sum(len(m.get("errors") or []) for m in matches), "caps": 0, "none": 0}
    if not n:
        return row
    rounds = [_num(m.get("rounds")) for m in matches if _num(m.get("rounds")) is not None]
    row["rounds"] = sum(rounds) / len(rounds) if rounds else None
    row["left_win"] = 100.0 * sum(1 for m in matches if m.get("winner") in LEFT_WIN) / n
    row["caps"] = sum(1 for m in matches if m.get("winner") in ("cap_left", "cap_right"))
    row["none"] = sum(1 for m in matches if m.get("winner") == "none")
    throws = sum(_num(m.get("throws")) or 0 for m in matches)
    measurable = [m for m in matches if _num(m.get("throws")) is not None and _num(m.get("direct_hits")) is not None]
    if measurable and throws:
        row["hits_per_throw"] = sum(m["direct_hits"] for m in measurable) / sum(m["throws"] for m in measurable)
    for key, field in (("near_misses", "near_misses"), ("pity", "pity_triggers"), ("comeback", "comeback_hits")):
        values = [_num(m.get(field)) for m in matches]
        row[key] = sum(v for v in values if v is not None) if any(v is not None for v in values) else None
    return row


def group_cells(matches):
    cells = {}
    for match in matches:
        cells.setdefault((match.get("hero"), match.get("size")), []).append(match)
    return cells


def group_sizes(matches):
    sizes = {}
    for match in matches:
        sizes.setdefault(match.get("size"), []).append(match)
    return sizes


def differs(engine_row, page_row):
    """Flags {'rounds': rel, 'win': points} for a cell or a size; empty when within the limits or not comparable."""
    flags = {}
    if engine_row["rounds"] and page_row["rounds"] is not None:
        rel = (page_row["rounds"] - engine_row["rounds"]) / engine_row["rounds"]
        if abs(rel) > ROUNDS_FLAG:
            flags["rounds"] = rel
    if engine_row["left_win"] is not None and page_row["left_win"] is not None:
        diff = page_row["left_win"] - engine_row["left_win"]
        if abs(diff) > WIN_FLAG:
            flags["win"] = diff
    return flags


def seed_consistency(engine_matches, page_matches):
    """Seeds on both ends must carry identical tiers and right hero (same seeded draw). Returns (problems, shared, only_engine, only_page)."""
    by_seed = {m.get("seed"): m for m in engine_matches}
    problems, shared, only_page = [], 0, 0
    for match in page_matches:
        other = by_seed.get(match.get("seed"))
        if other is None:
            only_page += 1
            continue
        shared += 1
        for field in ("hero", "hero_right", "size", "tier_left", "tier_right"):
            if match.get(field) != other.get(field):
                problems.append((match.get("seed"), field, other.get(field), match.get(field)))
    only_engine = len(by_seed) - shared
    return problems, shared, only_engine, only_page


def fmt(value, spec="%.1f", none="n/a"):
    return none if value is None else spec % value


def cell_text(row):
    if not row or not row["n"]:
        return "-"
    return "%s r / %s%% / %s" % (fmt(row["rounds"]), fmt(row["left_win"], "%.0f"), fmt(row["hits_per_throw"], "%.2f"))


def derive_hypotheses(engine, pages, size_rows, cell_flags, consistency):
    """Short list of (statement, evidence) pairs derived from the numbers; every one is a hypothesis, not a finding."""
    found = []
    for name, rows in size_rows.items():
        for size in (1, 2, 3):
            e, p = engine["sizes"].get(size), rows.get(size)
            if not e or not p or not e["n"] or not p["n"]:
                continue
            tag = "%s %dv%d" % (name, size, size)
            if e["rounds"] and p["rounds"] is not None:
                rel = (p["rounds"] - e["rounds"]) / e["rounds"]
                if abs(rel) > SIZE_ROUNDS_HYP:
                    if rel > 0:
                        cause = ("the page AI hits less often or loses turns the engine bot does not lose (defend, skip, timeout); "
                                 "a hits-per-throw gap in the same size would support it")
                    else:
                        cause = ("the page side kills faster: stronger page AI aim than the engine tier noise, ultimates fired by the page AI "
                                 "(the engine bot never fires one), or a damage rule applied differently")
                    found.append(("%s: mean rounds %s against %s on the engine (%+.0f%%). Probable cause: %s." % (
                        tag, fmt(p["rounds"]), fmt(e["rounds"]), 100 * rel, cause), "size rounds"))
            if e["hits_per_throw"] is not None and p["hits_per_throw"] is not None and abs(p["hits_per_throw"] - e["hits_per_throw"]) > HIT_FLAG:
                gap = p["hits_per_throw"] - e["hits_per_throw"]
                found.append(("%s: hits per throw %.2f against %.2f on the engine (%+.2f). Probable cause: %s." % (
                    tag, p["hits_per_throw"], e["hits_per_throw"], gap,
                    "the page AI level aims %s than the engine's power-error tiers (aim model, not a rule)" %
                    ("better" if gap > 0 else "worse")), "size hits"))
            if e["left_win"] is not None and p["left_win"] is not None and abs(p["left_win"] - e["left_win"]) > SIZE_WIN_HYP:
                found.append(("%s: left side wins %.0f%% against %.0f%% on the engine. Probable cause: a side or opener effect "
                              "(who throws first in a round, the AI seat on the left, tier mapping to the left side) rather than hero balance, "
                              "because it shows over all heroes of the size." % (tag, p["left_win"], e["left_win"]), "size win"))
            for field, label in (("near_misses", "near misses"), ("pity", "pity triggers"), ("comeback", "comeback hits")):
                if size > 1 and e[field] and p[field] is not None and e[field] > 0:
                    ratio = p[field] / e[field]
                    if ratio < 0.7 or ratio > 1.3:
                        found.append(("%s: %s %d against %d on the engine (x%.2f). Probable cause: the comeback pack is applied or counted "
                                      "differently on the page (when a near miss or a pity charge is counted), or the page throws fewer/more misses."
                                      % (tag, label, p[field], e[field], ratio), "size comeback"))
                if size > 1 and p[field] is None and e[field]:
                    found.append(("%s: the page file has no %s counter (null); the comparison of that counter is not possible." % (tag, label),
                                  "null counter"))
    by_hero = {}
    for (hero, size), flags in cell_flags.items():
        if flags:
            by_hero.setdefault(hero, []).append(size)
    for hero, sizes in sorted(by_hero.items()):
        if len(sizes) >= 2:
            found.append(("%s is flagged in %d sizes (%s): Probable cause: a hero-specific rule or ultimate differs between the page and the "
                          "engine (the engine bot never fires ultimates; the page AI does)." % (hero, len(sizes), ", ".join("%dv%d" % (s, s) for s in sorted(sizes))),
                          "hero cluster"))
    for name, (problems, shared, only_engine, only_page) in consistency.items():
        if problems:
            found.append(("%s: %d seed records disagree with the engine on hero, size or tier (first: seed %s, %s, engine %s, page %s). "
                          "Probable cause: the seeded draw (mulberry32 over seed ^ 0x5eed, right hero formula) is implemented differently; "
                          "the matrices are then not like for like." % (name, len(problems), problems[0][0], problems[0][1], problems[0][2], problems[0][3]),
                          "seed mismatch"))
        if only_engine or only_page:
            found.append(("%s: %d seeds only on the engine, %d only on the page: the page run is incomplete or used other cells." % (
                name, only_engine, only_page), "coverage"))
    return found


def build_report(engine, pages, missing_notes, out_lines=None):
    """Return the markdown text. `engine` and each page value is {data, cells, sizes}."""
    lines = []
    add = lines.append
    add("# Front versus back match matrix, comparison (2026-11-17)")
    add("")
    add("Generated by `scripts/compare_front_back.py` from `logs_local/matrix_*.json`. Spec: `docs/MATRIX_SPEC_20261117.md`. "
        "Cells are (hero, size); left = the player side; a cell is flagged when a page end differs from the engine by more than "
        "%d percent in mean rounds or more than %d points in left win share. Cell format: mean rounds / left win percent / hits per throw."
        % (int(ROUNDS_FLAG * 100), int(WIN_FLAG)))
    add("")
    add("## Files")
    add("| end | file | matches | note |")
    add("|---|---|---|---|")
    add("| engine | matrix_engine.json | %d | ok |" % len(engine["data"]["matches"]))
    for name, filename in PAGE_ENDS:
        if name in pages:
            add("| page %s | %s | %d | ok |" % (name, filename, len(pages[name]["data"]["matches"])))
        else:
            add("| page %s | %s | 0 | %s |" % (name, filename, missing_notes.get(name, "missing")))
    add("")
    page_names = [name for name, _ in PAGE_ENDS if name in pages]
    cell_flags = {}
    size_rows = {name: pages[name]["sizes"] for name in page_names}
    add("## Per size")
    header = "| size | engine |" + "".join(" page %s | flag |" % name for name in page_names)
    add(header)
    add("|---|---|" + "---|---|" * len(page_names))
    for size in (1, 2, 3):
        e = engine["sizes"].get(size)
        row = "| %dv%d | %s |" % (size, size, cell_text(e))
        for name in page_names:
            p = pages[name]["sizes"].get(size)
            flags = differs(e, p) if e and p else {}
            row += " %s | %s |" % (cell_text(p), ", ".join(flag_text(flags)) or "")
        add(row)
    add("")
    add("Counters per size (engine / page ends): near misses, pity triggers, comeback hits, errors, caps, no-winner matches.")
    add("")
    add("| size | end | near misses | pity triggers | comeback hits | errors | caps | none |")
    add("|---|---|---|---|---|---|---|---|")
    for size in (1, 2, 3):
        for name, rows in [("engine", engine["sizes"])] + [("page " + n, pages[n]["sizes"]) for n in page_names]:
            r = rows.get(size)
            if r and r["n"]:
                add("| %dv%d | %s | %s | %s | %s | %d | %d | %d |" % (size, size, name, fmt(r["near_misses"], "%d"), fmt(r["pity"], "%d"),
                                                                     fmt(r["comeback"], "%d"), r["errors"], r["caps"], r["none"]))
    add("")
    add("## Per cell")
    add("| hero | size | engine |" + "".join(" page %s | flag |" % name for name in page_names))
    add("|---|---|---|" + "---|---|" * len(page_names))
    flagged_total = 0
    for hero in HEROES:
        for size in (1, 2, 3):
            e = engine["cells"].get((hero, size))
            if not e:
                continue
            row = "| %s | %dv%d | %s |" % (hero, size, size, cell_text(e))
            any_flag = {}
            for name in page_names:
                p = pages[name]["cells"].get((hero, size))
                flags = differs(e, p) if p else {}
                if flags:
                    any_flag[name] = flags
                row += " %s | %s |" % (cell_text(p), ", ".join(flag_text(flags)))
            if any_flag:
                flagged_total += 1
            cell_flags[(hero, size)] = any_flag
            add(row)
    add("")
    add("Flagged cells: %d of %d." % (flagged_total, len(cell_flags)))
    add("")
    add("## Errors (every one, with its seed)")
    errors = []
    for end_name, data in [("engine", engine["data"])] + [("page " + n, pages[n]["data"]) for n in page_names]:
        for match in data["matches"]:
            for error in match.get("errors") or []:
                errors.append((end_name, match.get("seed"), match.get("hero"), match.get("size"), str(error)))
    if errors:
        add("| end | seed | hero | size | error |")
        add("|---|---|---|---|---|")
        for end_name, seed, hero, size, error in errors:
            add("| %s | %s | %s | %sv%s | %s |" % (end_name, seed, hero, size, size, error.replace("|", "/").replace("\n", " ")[:300]))
    else:
        add("None on any end.")
    add("")
    add("## Seed consistency (same seed must give the same hero, right hero and hidden tiers on every end)")
    consistency = {}
    for name in page_names:
        consistency[name] = seed_consistency(engine["data"]["matches"], pages[name]["data"]["matches"])
        problems, shared, only_engine, only_page = consistency[name]
        add("- page %s: %d shared seeds, %d only on the engine, %d only on the page, %d disagreements%s" % (
            name, shared, only_engine, only_page, len(problems),
            "" if not problems else " (first: seed %s field %s engine=%s page=%s)" % problems[0]))
    if not page_names:
        add("- no page file to compare yet")
    add("")
    add("## What differs and probable cause (HYPOTHESES derived from the numbers above, not confirmed)")
    hypotheses = derive_hypotheses(engine, pages, size_rows, cell_flags, consistency)
    if not page_names:
        add("- No page file exists yet, so nothing can be compared. The engine side alone: " + engine_only_summary(engine))
    elif not hypotheses:
        add("- No size shows a difference above the hypothesis limits (rounds %d%%, left win %d points, hits per throw %.2f). Cell flags, if any, "
            "are sampling noise at 10 matches per cell unless they repeat across sizes or ends." % (int(SIZE_ROUNDS_HYP * 100), int(SIZE_WIN_HYP), HIT_FLAG))
    for number, (text, _kind) in enumerate(hypotheses, 1):
        add("%d. [hypothesis] %s" % (number, text))
    add("")
    add("Known engine-side differences that can explain gaps (stated before the data): the engine bot plays plain throws only (no ultimates, no skills, "
        "no defend), moves at random 35 percent of its turns, and its tier is a power-error sd (7.5 / 14 / 36 since 2026-11-17, was 1.6 / 5 / 9) on perfect-angle aim; the page AI levels "
        "have their own aim model. At 10 matches per cell a win share has a standard error of about 15 points, so single-cell flags are weak evidence.")
    return "\n".join(lines) + "\n"


def flag_text(flags):
    out = []
    if "rounds" in flags:
        out.append("R %+.0f%%" % (100 * flags["rounds"]))
    if "win" in flags:
        out.append("W %+.0f pt" % flags["win"])
    return out


def engine_only_summary(engine):
    parts = []
    for size in (1, 2, 3):
        e = engine["sizes"].get(size)
        if e and e["n"]:
            parts.append("%dv%d rounds %s, left win %s%%" % (size, size, fmt(e["rounds"]), fmt(e["left_win"], "%.0f")))
    return "; ".join(parts) + "."


def prepare(data):
    matches = data["matches"]
    cells = {key: summarize(group) for key, group in group_cells(matches).items()}
    sizes = {key: summarize(group) for key, group in group_sizes(matches).items()}
    return {"data": data, "cells": cells, "sizes": sizes}


def compare(logs_dir, out_path):
    """Write the report; returns (text, status) with status 0 or 2."""
    engine_data, note = load_file(os.path.join(logs_dir, "matrix_engine.json"))
    if engine_data is None:
        return "engine file %s: %s" % (os.path.join(logs_dir, "matrix_engine.json"), note), 2
    pages, missing = {}, {}
    for name, filename in PAGE_ENDS:
        data, note = load_file(os.path.join(logs_dir, filename))
        if data is None:
            missing[name] = note
        else:
            pages[name] = prepare(data)
    text = build_report(prepare(engine_data), pages, missing)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return text, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--logs", default=os.path.join(ROOT, "logs_local"))
    parser.add_argument("--out", default=os.path.join(ROOT, "docs", "FRONT_BACK_COMPARE_20261117.md"))
    args = parser.parse_args(argv)
    text, status = compare(args.logs, args.out)
    if status:
        print("ERROR " + text)
        return status
    present = [name for name, filename in PAGE_ENDS if os.path.exists(os.path.join(args.logs, filename))]
    print("wrote %s (page files read: %s)" % (args.out, ", ".join(present) or "none yet"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
