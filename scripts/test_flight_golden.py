#!/usr/bin/env python3
import json
import os
import subprocess
import sys

from flight_py import simulate

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "flight_golden.json"), encoding="utf-8") as _input:
    GOLDEN = json.load(_input)


def near(actual, expected, label):
    assert abs(actual - expected) <= 1.0, "%s: got %r, want %r" % (label, actual, expected)


def mulberry32(seed):
    state = seed & 0xffffffff
    def random():
        nonlocal state
        state = (state + 0x6d2b79f5) & 0xffffffff
        value = state
        value = ((value ^ (value >> 15)) * (1 | value)) & 0xffffffff
        value = (value + (((value ^ (value >> 7)) * (61 | value)) & 0xffffffff)) ^ value
        return ((value ^ (value >> 14)) & 0xffffffff) / 4294967296
    return random


def random_cases(count):
    random = mulberry32(155)
    return [{"startX": 220 + random() * 1460, "startY": 710 + random() * 120,
             "dirX": 1 if random() < 0.5 else -1, "angleDeg": 10 + random() * 70,
             "power": 20 + random() * 80, "wind": -5 + random() * 10}
            for _ in range(count)]


for entry in GOLDEN["cases"]:
    result = simulate(entry["input"])
    assert result["hit"] == entry["result"]["hit"], entry["name"]
    near(result["landingX"], entry["result"]["landingX"], entry["name"] + " landingX")
    near(result["landingY"], entry["result"]["landingY"], entry["name"] + " landingY")
assert any(entry["result"]["hit"] == "wall" for entry in GOLDEN["cases"])
assert any(entry["result"]["hit"] == "out" for entry in GOLDEN["cases"])

inputs = random_cases(500)
runner = """'use strict'; const Flight = require('./js/flight.js'); let text = ''; process.stdin.on('data', d => text += d); process.stdin.on('end', () => { for (const line of text.trim().split('\\n')) { if (!line) continue; const r = Flight.simulate(JSON.parse(line)); console.log(JSON.stringify({landingX:r.landingX,landingY:r.landingY,hit:r.hit})); } });"""
node = subprocess.run(["node", "-e", runner], cwd=_ROOT,
                      input="\n".join(json.dumps(value, separators=(",", ":")) for value in inputs) + "\n",
                      text=True, capture_output=True, check=True)
node_results = [json.loads(line) for line in node.stdout.splitlines()]
assert len(node_results) == len(inputs)
for index, (data, js) in enumerate(zip(inputs, node_results)):
    py = simulate(data)
    assert py["hit"] == js["hit"], "cross-language hit %d" % index
    near(py["landingX"], js["landingX"], "cross-language x %d" % index)
    near(py["landingY"], js["landingY"], "cross-language y %d" % index)

wave_cases = [entry for entry in GOLDEN["cases"] if entry["input"].get("wave") is True]
assert len(wave_cases) >= 6 and all(entry["result"]["hit"] == "ground" and entry["result"]["landingY"] == 860 for entry in wave_cases), "wave goldens land exactly on the ground line"
print("PASS: %d flight goldens (%d wave), 500 Python/JS cases" % (len(GOLDEN["cases"]), len(wave_cases)))
