#!/usr/bin/env python3
"""Minimal command-line and test client for the local Pumpkin Killer room relay."""
import argparse
import asyncio
import json
from typing import Any, Dict, Optional

import websockets


class RelayClient:
    def __init__(self, url: str, code: Optional[str], seat: str, *, solo: bool = False,
                 scene: str = "graveyard") -> None:
        self.url = url
        self.code = code
        self.seat = seat
        self.solo = solo
        self.scene = scene
        self.socket: Any = None

    async def connect(self) -> Dict[str, Any]:
        self.socket = await websockets.connect(self.url, max_size=16 * 1024)
        if self.code:
            await self.send({"type": "join", "code": self.code, "seat": self.seat,
                             "client_version": "pk-relay-client"})
        else:
            await self.send({"type": "create_room", "seat": self.seat,
                             "solo": self.solo, "scene": self.scene,
                             "client_version": "pk-relay-client"})
        return await self.receive()

    async def send(self, message: Dict[str, Any]) -> None:
        if self.socket is None:
            raise RuntimeError("client is not connected")
        await self.socket.send(json.dumps(message, separators=(",", ":")))

    async def receive(self) -> Dict[str, Any]:
        if self.socket is None:
            raise RuntimeError("client is not connected")
        return json.loads(await self.socket.recv())

    async def close(self) -> None:
        if self.socket is not None:
            await self.socket.close()
            self.socket = None


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Join or create a Pumpkin Killer relay room.")
    parser.add_argument("--url", default="ws://127.0.0.1:8765/ws")
    parser.add_argument("--code", help="Invitation code. Omit to create a room.")
    parser.add_argument("--seat", required=True, choices=("red", "white", "spectator"))
    parser.add_argument("--solo", action="store_true",
                        help="start a practice room after its single player is ready")
    parser.add_argument("--scene", default="graveyard",
                        choices=("graveyard", "church", "school", "belltower"),
                        help="scene id for a room you create")
    args = parser.parse_args()
    client = RelayClient(args.url, args.code, args.seat, solo=args.solo, scene=args.scene)
    try:
        first = await client.connect()
        print(json.dumps(first, ensure_ascii=False))
        while True:
            print(json.dumps(await client.receive(), ensure_ascii=False))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(_main())
