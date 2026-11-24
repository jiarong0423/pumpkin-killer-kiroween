# Task 192 result — Kiro usage document

## What changed

- `docs/KIRO_USAGE_20261116.md` is now a 119-line evidence record. It distinguishes recorded Kiro CLI and desktop-app use from unrecorded Kiro Web and Crew use; documents specs, steering, custom agents, hooks, MCP, seeded properties, golden vectors, the balance simulator, third-party tools, and roles.
- The document replaces broad claims with paths, commit identifiers, task results, and explicit limits on what the repository proves.
- `docs/kiro_192_result.md` records this task's evidence and verification commands.

## Commands run and output tails

```text
git log --oneline
```

Exit code: 0. The final output line was:

```text
6eaaa6e Initial skeleton: MIT license, Kiro steering and core throw loop spec
```

```text
git log --format='%h %s' --all -- shared/determinism_golden.json docs/kiro_179_result.md docs/kiro_181_result.md docs/kiro_187_result.md | head -80
```

Exit code: 0. Output:

```text
6f1c21a Coin toss, AI levels, agent seat (Kiro 189); wind arrow back without a number; steady yellow ring under the active unit; page-parse test
8068913 Kiro 178 (ui-polish: scale-aware canvas text, plates with avatar and status chips, wind arrow, compact cards), 180 (asset pipeline: steering, spec, checker, manifest, hook), 181 (property triage), 182 (relay client, join-time and reconnect scripts); verified with the full test suite; relay client kept out of the service-worker precache
461f0a4 Kiro 179 outputs (property tests found 4 failures, kept failing on purpose), briefs 181 triage and 182 relay client
a835958 Determinism contract (Kiro 173, verified): seeded wind, start positions, dice, supply drop, bounce count and nun pick in JavaScript and Python with 988 shared golden vectors; avatar and hunchback Colab queue
```

```text
node scripts/test_properties.js
```

Exit code: 0. Last lines:

```text
ok   - all balance pairings finish without numerical dominance (2016 matches)
test_properties: all 6 properties passed
```

```text
node scripts/test_determinism.js && python3 -B scripts/test_determinism_golden.py
```

Exit code: 0. Last lines:

```text
test_determinism.js: 10000 seed property cases passed
test_determinism_golden.py: 1040 golden vectors passed
test_determinism_golden.py: 10000 seed property cases passed
```

```text
node scripts/test_sim_balance.js
```

Exit code: 0. Last line:

```text
test_sim_balance: all 29 tests passed
```

```text
wc -l docs/KIRO_USAGE_20261116.md && git diff --check -- docs/KIRO_USAGE_20261116.md
```

Exit code: 0. Output:

```text
119 docs/KIRO_USAGE_20261116.md
```

`git diff --check` produced no output.

## Claims not verified and removed or limited

- No repository record proves Kiro Web use. The document says "not used."
- No `docs/crew_*_result.md` exists. The document says Kiro Crew was not used.
- The previous general statement that all configured hooks had run was removed. The only recorded IDE save event used a predecessor hook; the preload stale result was a manual dry run. The remaining current hooks are described as configured without a recorded catch.
- The route log for task 173 proves only that a task completed. No surviving result file proves the reported-but-missing golden-vector incident. The document limits the claim to the current shared file, its tests, and commit `a835958`.
- The previous unqualified attribution that Kiro wrote the engine, MCP server, relay, rule modules, deployment files, and UI polish was replaced with task-file attribution. The document separately identifies main-line wiring and verification records.
- The desktop IDE attempt to call the MCP server failed, so the document does not claim a successful IDE MCP call. The recorded `pk-player` match is identified as main-line verified evidence instead.

Main-line re-verification and any `docs/kiro_verified.json` update remain outside this task.
