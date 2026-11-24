#!/usr/bin/env python3
"""The repository's Coolify deploy files hold every rule of check_coolify_deploy.py, and the checker really catches each problem."""
import shutil
import tempfile
import unittest
from pathlib import Path

import check_coolify_deploy as chk


class CoolifyDeployTests(unittest.TestCase):
    def copy_tree(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "deploy").mkdir()
        for name in ("Dockerfile.coolify", "entrypoint.sh", "nginx.conf"):
            shutil.copy(chk.ROOT / "deploy" / name, tmp / "deploy" / name)
        shutil.copy(chk.ROOT / "requirements.txt", tmp / "requirements.txt")
        if (chk.ROOT / ".dockerignore").exists():
            shutil.copy(chk.ROOT / ".dockerignore", tmp / ".dockerignore")
        return tmp

    def test_repository_holds_every_rule(self):
        self.assertEqual(chk.validate(), [])

    def test_missing_gateway_copy_is_caught(self):
        tmp = self.copy_tree()
        path = tmp / "deploy" / "Dockerfile.coolify"
        path.write_text("\n".join(l for l in path.read_text().splitlines() if "pk_ai_gateway" not in l) + "\n")
        self.assertTrue(any("pk_ai_gateway" in p for p in chk.validate(tmp)))

    def test_forgeable_forwarded_for_is_caught(self):
        tmp = self.copy_tree()
        path = tmp / "deploy" / "nginx.conf"
        path.write_text(path.read_text().replace("X-Forwarded-For $remote_addr", "X-Forwarded-For $proxy_add_x_forwarded_for"))
        self.assertTrue(any("/ai" in p and "X-Forwarded-For" in p for p in chk.validate(tmp)))

    def test_gateway_without_price_guard_is_caught(self):
        tmp = self.copy_tree()
        path = tmp / "deploy" / "entrypoint.sh"
        path.write_text(path.read_text().replace("PK_AI_PRICE_IN_PER_M", "PK_AI_PRICE_X"))
        self.assertTrue(any("PK_AI_PRICE" in p for p in chk.validate(tmp)))

    def test_unpinned_websockets_is_caught(self):
        tmp = self.copy_tree()
        (tmp / "requirements.txt").write_text("websockets>=15\n")
        self.assertTrue(any("websockets" in p for p in chk.validate(tmp)))

    def test_missing_real_ip_and_limits_are_caught(self):
        tmp = self.copy_tree()
        path = tmp / "deploy" / "nginx.conf"
        text = path.read_text()
        for needle in ("real_ip_header", "limit_req_zone", "limit_conn_zone", "client_header_timeout"):
            path.write_text("\n".join(l for l in text.splitlines() if needle not in l) + "\n")
            problems = chk.validate(tmp)
            self.assertTrue(any(needle.split("_")[0] in p or needle in p for p in problems), (needle, problems))

    def test_trusting_every_address_for_real_ip_is_caught(self):
        tmp = self.copy_tree()
        path = tmp / "deploy" / "nginx.conf"
        path.write_text(path.read_text().replace("set_real_ip_from 172.16.0.0/12;", "set_real_ip_from 0.0.0.0/0;"))
        self.assertTrue(any("never trust every address" in p for p in chk.validate(tmp)))


if __name__ == "__main__":
    unittest.main()
