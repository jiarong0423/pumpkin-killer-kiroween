#!/usr/bin/env python3
"""Offline regression tests for shared gateway constraints."""
import contextlib
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("pk_ai_gateway", ROOT / "scripts" / "pk_ai_gateway.py")
assert SPEC and SPEC.loader
GATEWAY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GATEWAY
SPEC.loader.exec_module(GATEWAY)

AIM_FIELDS = {"own_hero_id": "wizard", "own_position": 280, "enemy_position": 1560, "enemy_hp": 85,
              "wind": -1.5, "weather": "clear", "fence_hp": 100, "round_number": 4}


@contextlib.contextmanager
def patched_environ(values):
    old = os.environ.copy()
    os.environ.clear()
    os.environ.update(old)
    os.environ.update(values)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


class FakeBackend:
    name = "fake"

    def __init__(self, response='{"angle":54,"power":70}'):
        self.response = response
        self.calls = []

    def call(self, model, system, user):
        self.calls.append((model, system, user))
        return 200, self.response, 0, 0

    def configured(self):
        return True

    def slots(self):
        return 1


class GatewayConfigurationCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Path(self.tmp.name, "config")
        self.config.mkdir()
        Path(self.config, "ai_prompts.json").write_text((ROOT / "shared" / "ai_prompts.json").read_text(), encoding="utf-8")
        self.env = patched_environ({"PK_AI_CONFIG_DIR": str(self.config), "PK_AI_STATE_DIR": str(Path(self.tmp.name, "state")),
                                    "PK_AI_BACKEND": "bedrock"})
        self.env.__enter__()

    def tearDown(self):
        self.env.__exit__(None, None, None)
        self.tmp.cleanup()

    def write_models(self, default="model-owner-selected"):
        Path(self.config, "ai_models.json").write_text(json.dumps({"bedrock": {"default": default, "allowed": [default]},
                                                                      "gemini": {"default": None, "allowed": []}}), encoding="utf-8")

    def test_null_default_refuses_start_with_file_name(self):
        self.write_models(None)
        with self.assertRaisesRegex(GATEWAY.ConfigurationError, r"shared/ai_models\.json bedrock\.default is not set"):
            GATEWAY.load_model_config("bedrock")

    def test_request_uses_only_owner_default_model(self):
        self.write_models()
        backend = FakeBackend()
        state = GATEWAY.GatewayState(GATEWAY.load_model_config("bedrock"), GATEWAY.load_prompt_config(), backend)
        answer, outcome = GATEWAY.gateway_request(state, "aim", AIM_FIELDS)
        self.assertEqual((outcome, answer), ("ok", {"angle": 54, "power": 70}))
        self.assertEqual([call[0] for call in backend.calls], ["model-owner-selected"])

    def test_legacy_gemini_model_fields_remain_readable(self):
        Path(self.config, "ai_models.json").write_text(json.dumps({"default": "legacy-model", "allowed": ["legacy-model"]}), encoding="utf-8")
        self.assertEqual(GATEWAY.load_model_config("gemini"), {"default": "legacy-model", "allowed": ["legacy-model"]})

    def test_invalid_pick_fields_are_rejected_before_backend(self):
        self.write_models()
        candidates = [{"id": 1, "kind": "throw", "aim": {"angle": 54, "power": 70}, "predicted_distance_px": 1000},
                      {"id": 2, "kind": "move", "predicted_distance_px": 120},
                      {"id": 3, "kind": "defend", "predicted_distance_px": 0}]
        fields = dict(AIM_FIELDS, candidates=candidates)
        self.assertTrue(GATEWAY.valid_pick_fields(fields))
        fields["candidates"] = candidates[:2]
        self.assertFalse(GATEWAY.valid_pick_fields(fields))

    def test_power_115_accepted_and_116_rejected_for_pick_and_aim(self):
        self.write_models()
        candidates = [{"id": 1, "kind": "throw", "aim": {"angle": 54, "power": 115}, "predicted_distance_px": 1500},
                      {"id": 2, "kind": "move", "predicted_distance_px": 120},
                      {"id": 3, "kind": "defend", "predicted_distance_px": 0}]
        fields = dict(AIM_FIELDS, candidates=candidates)
        self.assertTrue(GATEWAY.valid_pick_fields(fields))
        candidates[0] = {"id": 1, "kind": "throw", "aim": {"angle": 54, "power": 116}, "predicted_distance_px": 1500}
        self.assertFalse(GATEWAY.valid_pick_fields(fields))
        self.assertEqual(GATEWAY.validate_answer("aim", '{"angle":45,"power":115}', AIM_FIELDS), {"angle": 45, "power": 115})
        self.assertIsNone(GATEWAY.validate_answer("aim", '{"angle":45,"power":116}', AIM_FIELDS))


if __name__ == "__main__":
    unittest.main()
