"""F16: rooms of dropped sockets are held for the seat grace (60 s): one address with 40 connects/min holds 40 rooms; 5 addresses fill MAX_ROOMS=200.
Run: python3 -B scripts/redteam_probes/probe_rooms_fill.py   (scaled: max_rooms=20, trust_proxy with 1 spoofed address, 40 connects/min)"""
import os
import asyncio, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h import H, run, verdict
async def main():
    async with H(max_rooms=20, trust_proxy=True, max_connects_per_min=40, max_per_addr=8) as h:
        for i in range(20):
            c = await h.open(headers={"CF-Connecting-IP": "203.0.113.9"})
            await c.send(type="create_room", seat="red")
            await c.close()
        other = await h.open(headers={"CF-Connecting-IP": "198.51.100.1"})
        await other.send(type="create_room", seat="red")
        verdict("F16 one address fills every room slot with dropped sockets", "server_busy" in other.errors(),
                "rooms=%d, connected=%d, honest client errors=%s" % (len(h.relay.rooms), h.relay.connections, other.errors()),
                "rooms per address capped (or a room without a connected seat does not count / is dropped sooner)")
run(main())
