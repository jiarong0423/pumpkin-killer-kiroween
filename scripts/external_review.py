#!/usr/bin/env python3
"""External review by two roles (owner request 2026-11-17, approved: Claude API, self-paid).

Default is a DRY RUN: it builds the numbers-only summary JSON and the two prompts and writes them under docs/external_review/ without any network call.
With --send it posts the same summary to the Claude Messages API twice, once as a PLAYER and once as a GAME DESIGNER, and saves both answers.

What is sent: only simulation numbers (win-rate matrix, round counts, hero hp and damage, team-length study rows). No file paths, no names, no keys, no source code.
The API key is read from the ANTHROPIC_API_KEY environment variable only; this script never prints it, never writes it to a file and never logs it. Run it like
    ANTHROPIC_API_KEY="$(security find-generic-password -a "$USER" -s anthropic-api-key -w)" python3 scripts/external_review.py --send
Options: --team-dir DIR (folder with sim_team_headless outputs, files named out_*.txt), --model NAME (default claude-sonnet-5-5), --max-tokens N (default 4000).
Logs: logs_local/external_review.log (no secrets). Exit code 1 on any failure, 2 on bad arguments.
"""
import argparse
import glob
import json
import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "docs", "external_review")
os.makedirs(os.path.join(ROOT, "logs_local"), exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
logging.basicConfig(filename=os.path.join(ROOT, "logs_local", "external_review.log"), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
API_URL = "https://api.anthropic.com/v1/messages"

ROLES = {
    "player": (
        "You are an experienced player of turn-based artillery games such as Worms and Hedgewars, and of mobile team games such as Honor of Kings where a match lasts about seven minutes. "
        "You judge only from the simulation numbers you are given. Be blunt and specific."
    ),
    "designer": (
        "You are a senior game designer who ships short competitive mobile and web games. "
        "You judge only from the simulation numbers you are given and propose changes with concrete numbers. Be blunt and specific."
    ),
}
QUESTION = (
    "Below is a JSON summary of repeated backend simulations of a turn-based artillery duel with 8 heroes and optional team matches (2 or 3 units per side). "
    "The owner wants every dimension to reach 10 out of 10 for fun and replayability and wants a team match to last about 7 minutes. "
    "Answer ONLY with one JSON object with these keys: "
    "ratings (object with integer scores 1 to 10 for fun, fairness, tension, pacing, team_play, replayability, each with a one-line reason that cites a number from the data), "
    "top_weaknesses (list of up to 8 strings, ranked, each citing a number), "
    "to_reach_10 (list of up to 8 objects with keys change, concrete_numbers, expected_effect, risk), "
    "seven_minute_plan (object with keys rounds_target, hp_scale, ramp_start_round, round_cap, reasoning), "
    "cannot_judge (list of strings). Do not add any text outside the JSON."
)


def run(cmd, timeout=600):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def one_v_one(matches, seed):
    r = run(["node", "scripts/sim_balance.js", "--matches", str(matches), "--seed", str(seed), "--json"])
    if not r.stdout.strip():
        raise RuntimeError("sim_balance produced no output: " + r.stderr[-200:])
    data = json.loads(r.stdout)
    keep = {k: data[k] for k in ("classes", "winRates", "avgRounds", "avgRoundsOverall", "timeouts", "totalMatches") if k in data}
    keep["matches_per_pairing"] = matches
    keep["seed"] = seed
    return keep


def parse_team_text(text):
    """Extract the headline rows of a sim_team_headless output (no paths, numbers only)."""
    rows = []
    for line in text.splitlines():
        m = re.match(r"^(2v2|3v3)\s+(\d+)\s+(\d+)/([\d.]+)/(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\(\d+\)\s+(\d+)/(\d+)/(\d+)", line)
        if m:
            rows.append({"size": m.group(1), "matches": int(m.group(2)), "rounds_min": int(m.group(3)), "rounds_mean": float(m.group(4)), "rounds_max": int(m.group(5)),
                         "hits_per_throw": float(m.group(7)), "wins_left": int(m.group(11)), "wins_right": int(m.group(12)), "draws": int(m.group(13))})
        m2 = re.match(r"^(2v2|3v3) rounds per match: mean ([\d.]+)\s+p10 (\d+)\s+p50 (\d+)\s+p90 (\d+)\s+max (\d+)\s+inside 8-13: (\d+)%\s+ended by the cap \((\d+)\): (\d+)", line)
        if m2:
            rows.append({"size": m2.group(1), "mean": float(m2.group(2)), "p10": int(m2.group(3)), "p50": int(m2.group(4)), "p90": int(m2.group(5)), "max": int(m2.group(6)),
                         "percent_inside_8_to_13": int(m2.group(7)), "cap": int(m2.group(8)), "ended_by_cap": int(m2.group(9))})
    return rows


def team_runs(team_dir):
    runs = []
    if not team_dir:
        return runs
    for path in sorted(glob.glob(os.path.join(team_dir, "out_*.txt"))):
        name = os.path.basename(path)[:-4]
        with open(path, encoding="utf-8", errors="replace") as fh:
            rows = parse_team_text(fh.read())
        if rows:
            runs.append({"run": name, "rows": rows})
    return runs


def hero_table():
    with open(os.path.join(ROOT, "shared", "heroes.json"), encoding="utf-8") as fh:
        heroes = json.load(fh)
    return {k: {"hp": v["hp"], "dmg": v["dmg"]} for k, v in heroes.items()}


def tuning():
    out = {}
    for name in ("team_tuning.json", "comeback.json"):
        p = os.path.join(ROOT, "shared", name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                d = json.load(fh)
            out[name[:-5]] = {k: v for k, v in d.items() if k not in ("note", "order", "round_cap_rule")}
    return out


def pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else None


def matrix_summary():
    """Numbers from the 240-match matrices (8 heroes x 3 sizes x 10 plays) of the engine and of the real page, played AFTER the changes listed in `changes_since_the_previous_review`. No paths."""
    out = {}
    for end, name in (("engine", "matrix_engine.json"), ("page", "matrix_page_vm.json")):
        path = os.path.join(ROOT, "logs_local", name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            matches = json.load(fh)["matches"]
        sizes = {}
        for n in (1, 2, 3):
            ms = [m for m in matches if m["size"] == n]
            if not ms:
                continue
            rounds = sorted(m["rounds"] for m in ms)
            throws = sum(m["throws"] for m in ms)
            hits = sum(m["direct_hits"] for m in ms)
            sizes["%dv%d" % (n, n)] = {
                "matches": len(ms), "rounds_mean": round(sum(rounds) / len(rounds), 1), "rounds_p10": rounds[len(rounds) // 10], "rounds_p90": rounds[(9 * len(rounds)) // 10],
                "left_side_wins_percent": pct(sum(1 for m in ms if m["winner"].endswith("left")), len(ms)),
                "ended_by_round_cap": sum(1 for m in ms if m["winner"].startswith("cap")), "hits_per_throw": round(hits / throws, 3) if throws else None,
                "comeback_hits_per_match": round(sum(m["comeback_hits"] or 0 for m in ms) / len(ms), 1), "pity_triggers_per_match": round(sum(m["pity_triggers"] or 0 for m in ms) / len(ms), 1),
            }
        by_hero = {}
        for m in matches:   # the left side's lead hero (unit 0): win share over all sizes
            row = by_hero.setdefault(m["hero"], [0, 0]); row[1] += 1; row[0] += 1 if m["winner"].endswith("left") else 0
        tiers = ["hard", "normal", "easy"]
        by_gap = {}
        for m in matches:   # hidden opponent strength: left win share by (right tier index - left tier index); +2 means the left side is hard and the right side easy
            gap = tiers.index(m["tier_right"]) - tiers.index(m["tier_left"])
            row = by_gap.setdefault(str(gap), [0, 0]); row[1] += 1; row[0] += 1 if m["winner"].endswith("left") else 0
        out[end] = {"by_size": sizes, "left_lead_hero_win_percent_all_sizes": {h: pct(a, b) for h, (a, b) in sorted(by_hero.items())},
                    "left_win_percent_by_strength_gap": {g: pct(a, b) for g, (a, b) in sorted(by_gap.items())}, "matches": len(matches)}
    return out


CHANGES_BEFORE_THE_MEASUREMENT = [
    "Team units now have their own heroes (mixed teams, no hero twice in a team, the opponent team too); before, a team used one hero for all units.",
    "The first team is now fixed for the whole match; before, the opener alternated each round, so the second mover of a round also opened the next round and attacked twice in a row. Side effect measured on the engine, where red always opens: red wins 59 percent (2v2) and 65 percent (3v3).",
    "The bride's sound wave is now judged at the point where it really lands; before, 21 of 3528 swept shots that landed 94 to 105 px from the unit did no damage.",
    "Hero hp and damage were rebalanced earlier the same day (knight and hunchback weaker, bat, bride, wizard stronger); the table is in hero_table_hp_dmg.",
    "Opponent strength is random and hidden; skill gap deciding matches and snowballing are accepted properties of the game (owner).",
]


def build_summary(args):
    summary = {
        "game": "turn-based artillery duel, wind, centre fence, 8 heroes, ultimates, supply crates; team matches of 2 or 3 units per side with one thrower per team per round",
        "hero_table_hp_dmg": hero_table(),
        "team_tuning_and_comeback_constants": tuning(),
        "duel_simulation_1v1": one_v_one(args.duel_matches, args.seed),
        "matrix_240_matches_per_end_after_the_latest_changes": matrix_summary(),
        "changes_made_before_these_numbers_were_measured": CHANGES_BEFORE_THE_MEASUREMENT,
        "team_simulation_runs": team_runs(args.team_dir),
        "not_measured": ["seconds per round (the 7 minute target cannot be converted from rounds without it)", "real human players: every number here is from computer-controlled matches"],
    }
    return summary


def call_api(key, model, max_tokens, system, summary_json):
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "thinking": {"type": "between_tools"},   # the API said to send this instead of "disabled" on this model: no thinking before the answer; without it the whole token budget went into a thinking block (2026-11-17)
        "messages": [{"role": "user", "content": QUESTION + "\n\nDATA:\n" + summary_json}],
    }
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true", help="really call the API (default: dry run)")
    ap.add_argument("--team-dir", default="")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--duel-matches", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    try:
        summary = build_summary(args)
    except Exception as exc:  # noqa: BLE001 - one failure path with a grep-able line
        logging.error("ERROR building the summary: %s", exc)
        print("ERROR building the summary:", exc)
        return 1
    text = json.dumps(summary, indent=1, sort_keys=True)
    with open(os.path.join(OUT_DIR, "sim_summary_20261117.json"), "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    for role, system in ROLES.items():
        with open(os.path.join(OUT_DIR, "prompt_%s.txt" % role), "w", encoding="utf-8") as fh:
            fh.write("SYSTEM:\n" + system + "\n\nUSER:\n" + QUESTION + "\n\nDATA: see sim_summary_20261117.json\n")
    logging.info("summary built bytes=%d send=%s", len(text), args.send)
    print("summary: %d bytes, %d team run files, written to docs/external_review/" % (len(text), len(summary["team_simulation_runs"])))
    if not args.send:
        print("dry run: no network call made")
        return 0
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        logging.error("ERROR ANTHROPIC_API_KEY is not set")
        print("ERROR: ANTHROPIC_API_KEY is not set (see the header of this script)")
        return 1
    failed = 0
    for role, system in ROLES.items():
        try:
            reply = call_api(key, args.model, args.max_tokens, system, text)
            answer = "".join(part.get("text", "") for part in reply.get("content", []) if part.get("type") == "text")
            usage = reply.get("usage", {})
            kinds = [part.get("type") for part in reply.get("content", [])]
            if not answer.strip():
                raise RuntimeError("the reply has no text block (block types %s, stop_reason %s, output tokens %s): raise --max-tokens" % (kinds, reply.get("stop_reason"), usage.get("output_tokens")))
            with open(os.path.join(OUT_DIR, "answer_%s.json" % role), "w", encoding="utf-8") as fh:
                fh.write(answer.strip() + "\n")
            logging.info("role=%s ok input_tokens=%s output_tokens=%s model=%s", role, usage.get("input_tokens"), usage.get("output_tokens"), reply.get("model"))
            print("%s: ok, %s input tokens, %s output tokens" % (role, usage.get("input_tokens"), usage.get("output_tokens")))
        except urllib.error.HTTPError as exc:
            failed += 1
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            logging.error("ERROR role=%s HTTP %s %s", role, exc.code, detail)
            print("ERROR %s: HTTP %s %s" % (role, exc.code, detail))
        except Exception as exc:  # noqa: BLE001
            failed += 1
            logging.error("ERROR role=%s %s", role, exc)
            print("ERROR %s: %s" % (role, exc))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
