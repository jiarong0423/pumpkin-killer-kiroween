# AI level sweep — 2026-11-15

Command: `python3 -B scripts/sweep_agent_levels.py --throws 400 --seeds 101 202 303 404 505 606 707 808`

Each level has 400 total throws split over the human-vs-agent and agent-vs-agent MCP modes and seeds 101, 202, 303, 404, 505, 606, 707, 808. Each action uses only the six published MCP tools. Landing error is absolute horizontal error; the two error columns average the first and second halves of each seeded match.

| level | throws | hits | hit rate | mean landing error, first half | mean landing error, second half | 95% hit-rate interval |
|---|---:|---:|---:|---:|---:|---:|
| easy | 400 | 45 | 11.2% | 404.5 px | 398.8 px | 8.5%–14.7% |
| normal | 400 | 117 | 29.2% | 241.3 px | 119.6 px | 25.0%–33.9% |
| hard | 400 | 209 | 52.2% | 222.8 px | 59.6 px | 47.4%–57.1% |

The 95% interval is the Wilson interval for the observed hit rate.
