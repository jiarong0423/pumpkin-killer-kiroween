#!/usr/bin/env python3
"""Tests for static deployment file validation."""

import json
import tempfile
import unittest
from pathlib import Path

from check_deploy_files import validate


class DeployFilesTest(unittest.TestCase):
    def write_valid_files(self, root: Path) -> tuple[Path, Path, Path]:
        docker = root / "Dockerfile"
        nginx = root / "nginx.conf"
        manifest = root / "manifest.webmanifest"
        manifest.write_text(json.dumps({"icons": [{"src": "icons/icon-192.png"}]}), encoding="utf-8")
        docker.write_text(
            "COPY sw.js /usr/share/nginx/html/sw.js\n"
            "COPY manifest.webmanifest /usr/share/nginx/html/manifest.webmanifest\n"
            "COPY icons/icon-192.png /usr/share/nginx/html/icons/icon-192.png\n"
            "RUN sed '1,/^types {/d;/^}/d' /etc/nginx/mime.types > /etc/nginx/pk_mime_body.types\n",
            encoding="utf-8",
        )
        nginx.write_text(
            "types {\n include /etc/nginx/pk_mime_body.types;\n}\n"
            "location = /sw.js {\n default_type application/javascript;\n"
            " add_header Cache-Control \"no-cache\";\n}\n"
            "location /assets/ {\n add_header Cache-Control \"public, max-age=31536000, immutable\";\n}\n",
            encoding="utf-8",
        )
        return docker, nginx, manifest

    def test_repository_files_are_valid(self):
        validate()

    def test_rejects_missing_manifest_icon_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            docker, nginx, manifest = self.write_valid_files(Path(temporary))
            manifest.write_text(json.dumps({"icons": [{"src": "icons/missing.png"}]}), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "missing.png"):
                validate(docker, nginx, manifest)

    def test_rejects_types_block_without_default_types(self):
        with tempfile.TemporaryDirectory() as temporary:
            docker, nginx, manifest = self.write_valid_files(Path(temporary))
            nginx.write_text(nginx.read_text(encoding="utf-8").replace(
                "include /etc/nginx/pk_mime_body.types;", "application/font-woff2 woff2;"
            ), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "pk_mime_body"):
                validate(docker, nginx, manifest)


if __name__ == "__main__":
    unittest.main()
