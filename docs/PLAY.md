# Play Pumpkin Killer locally

This ZIP contains the playable web page, its referenced assets, shared game data,
the Python practice engine and MCP server, local launch scripts, and the MIT licence.
It also includes a `SHA256SUMS.txt` manifest for every payload file. The manifest
itself is excluded because a file cannot contain its own final checksum.

## Computer play

You need Python 3.10 or later. If `python3 --version` (macOS/Linux) or
`py -3 --version` (Windows) does not show Python 3.10 or later, install Python
from https://www.python.org/downloads/ and run the command again.

- **macOS or Linux:** unzip the package, open a terminal in the unzipped folder,
  then run `(not published)`.
- **Windows:** unzip the package, then double-click `start_game.bat`.

The scripts start a local server on `127.0.0.1` and open the game in your default
browser. Keep the terminal or command window open while playing. You can set a
different local port with `PK_PORT` before starting the macOS/Linux script.

## Agent seat

Run `./start_agent.sh red` on macOS/Linux or `start_agent.bat red` on Windows.
Replace `red` with `white`, `spectator`, or `referee` as needed. The script starts
the local stdio MCP server for that seat; connect your MCP-capable agent to its
standard input and output.

The invitation relay is not built or deployed yet. Once it exists, install its optional client dependency with `python3 -m pip install websockets`, then a connected agent command will use this shape: `start_agent.sh red <relay-url> <invitation-code>`. A friend will enter the same invitation code in the future room interface.

## Phone play and privacy

The ZIP is for computers. To play on a phone, open the hosted page in a browser.
A hosted address does not exist yet. Nothing in this package sends data anywhere.
The future relay will send only its room messages between participants.

Pumpkin Killer is provided under the MIT License. See `LICENSE` in this ZIP.
