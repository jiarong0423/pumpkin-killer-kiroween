#!/usr/bin/env python3
"""Offline test: the preload block in index.html matches the imgList, every linked file exists, and no link is duplicated."""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
assert "<!-- PRELOAD-BEGIN -->" in html and "<!-- PRELOAD-END -->" in html, "preload block missing"
links = re.findall(r'<link rel="preload" as="image" href="([^"]+)">', html)
assert links, "no preload links"
assert len(links) == len(set(links)), "duplicate preload link"
for p in links:
    assert os.path.exists(os.path.join(ROOT, p)), "missing file " + p
r = subprocess.run([sys.executable, "-B", os.path.join(ROOT, "scripts", "make_preload_links.py")], capture_output=True, text=True)
assert r.returncode == 0, "block is stale: " + r.stdout[-200:]
print("test_preload_links: OK (%d links)" % len(links))
