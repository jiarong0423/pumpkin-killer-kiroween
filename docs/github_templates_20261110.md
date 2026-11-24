# Templates and references found for the room-code relay, deterministic play and MCP multiplayer (2026-11-10)

Method: three web searches (the `gh` command could not reach GitHub from the sandbox: certificate error). The results are search snippets. I did NOT open the repositories: licences, maintenance, star counts and code quality are UNVERIFIED. Check each one before copying anything.

## 1. Invitation-code rooms and a tiny relay (owner decisions 9, 11, 12)
| Reference | What it is | Fit |
|---|---|---|
| [p5.multiplayer](https://github.com/L05/p5.multiplayer/blob/master) | Node server, the client names a room id in the URL (a join-by-code flow), Socket.IO | closest to "random invitation code"; Socket.IO is heavier than needed |
| [Railway "nodejs websocket game server" / "server multiplayer game template"](https://railway.com/deploy/nodejs-websocket-game-server) | stateless WebSocket relay with rooms; players get an id; messages are relayed to the room | matches "the cloud only forwards"; written in TypeScript with msgpack |
| [room.io](https://github.com/oni0nknight/room.io) | small room layer for Node | not read |
| [Colyseus](https://docs.colyseus.io/) (see also its [custom room id recipe](https://docs.colyseus.io/recipes) and [lobby](https://docs.colyseus.io/room/built-in/lobby)) | self-hosted Node framework, MIT, rooms, matchmaking, turn-based demo | works on Contabo/Coolify as a Node process, BUT it is server-authoritative with synced state: more than we decided (endpoints compute) |
| [A Dumb Relay (devlog)](https://multitap-site.pages.dev/devlog/2026-01-03-a-dumb-relay) | a game-agnostic relay that accepts inputs, orders them, broadcasts them | exactly the relay idea of decision 9 |

## 2. Deterministic play on every device (decision 9)
| Reference | What it is | Fit |
|---|---|---|
| [NetplayJS](https://www.npmjs.com/package/netplayjs) | browser multiplayer with WebRTC signalling, rollback/prediction | a different style (rollback), useful for the determinism rules |
| [FangDash how it works](https://mrdemonwolf.github.io/fangdash/docs/multiplayer/how-it-works) | server sends a random seed to every player, mulberry32 PRNG | the same seed and PRNG we already use in `js/particles.js` |
| [Deterministic Lockstep in Networked Games (paper)](https://hdms.bsz-bw.de/files/7106/Deterministic_Lockstep_in_Networked_Games.pdf) and [lockstep.io](https://www.npmjs.com/package/lockstep.io) | the rules: no unseeded randomness, same processing order, no float differences across platforms | checklist for the rules module and its golden-vector tests |

## 3. MCP and games (decision 10: MCP is only a channel)
| Reference | What it is | Fit |
|---|---|---|
| [github-samples/turn-based-game-mcp](https://awesome.ecosyste.ms/projects/github.com%2Fgithub-samples%2Fturn-based-game-mcp) | Next.js + MCP server that acts as the AI opponent (single-player) | shape of tools for a turn-based game |
| [mcp-arena](https://glama.ai/mcp/servers/pkronstrom/mcp-arena) | arena where agents call `join_game`, `move_unit`, `get_my_state` | good tool names; fog-of-war per agent |
| [Silicon Pantheon](https://glama.ai/mcp/servers/egqadmrxi9) and [Tic-Tac-Toe MCP](https://glama.ai/mcp/servers/mh8o3w2qe3) | server is the sole authority of the state; agents send moves only | the opposite of decision 10; use only for message shapes |
| [account-link MCP Multiplayer](https://lobehub.com/en/mcp/account-link-mcp-multiplayer) | agents in separate sessions share channels, bot codes are verified | the "shared channel" idea; check the trust model |
| [antics-mcp](https://mcpservers.org/servers/antics-gg/antics-mcp) | deploys a web game to a playable multiplayer URL with rooms | not read |
| (found in a listing, not opened) two Claude Code sessions playing tic-tac-toe through one shared server, each woken on its turn by a push | the turn notification idea: an agent is told when it is its turn | needed for agent seats |

## 4. What I recommend (nothing is built)
1. Hand-roll a tiny relay with the `ws` package on Node (one file, rooms in memory, random 6-character codes, message size and rate limits, room expiry, `/health`). It is what decisions 9, 11 and 12 describe and fits a Dockerfile on Coolify. Do not adopt Colyseus unless the owner wants authoritative state.
2. The relay stamps each action with a sequence number and broadcasts it; the shared seed is created when the room is created; every device runs the deterministic rules module.
3. Copy the TOOL NAMES and the "your turn" notification idea from mcp-arena, not their authority model.
4. Next step if the owner agrees: a Kiro task that reads the three or four repos that look best (licence first), then writes the relay spec and tests; the main line builds and verifies it.
