#!/usr/bin/env python3
"""Offline Bedrock gateway tests. No boto3, network, or credentials are used."""
import contextlib
import datetime as dt
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("pk_ai_gateway_bedrock_test", ROOT / "scripts" / "pk_ai_gateway.py")
assert SPEC and SPEC.loader
GATEWAY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GATEWAY
SPEC.loader.exec_module(GATEWAY)

AIM_FIELDS = {"own_hero_id": "wizard", "own_position": 280, "enemy_position": 1560, "enemy_hp": 85,
              "wind": -1.5, "weather": "clear", "fence_hp": 100, "round_number": 4}
PICK_CANDIDATES = [
    {"id": 11, "kind": "throw", "aim": {"angle": 54, "power": 70}, "predicted_distance_px": 1200},
    {"id": 12, "kind": "move", "predicted_distance_px": 108},
    {"id": 13, "kind": "defend", "predicted_distance_px": 0},
]


@contextlib.contextmanager
def patched_environ(values):
    old = os.environ.copy()
    os.environ.update(values)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


class FakeBedrockClient:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0) if self.responses else {"output": {"message": {"content": [{"text": '{"angle":54,"power":70}'}]}}, "usage": {"inputTokens": 10, "outputTokens": 5}}
        if isinstance(response, Exception):
            raise response
        return response


class ClientError(Exception):
    def __init__(self, code):
        self.response = {"Error": {"Code": code}}


class MutableDay:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class BedrockBackendCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Path(self.tmp.name, "config")
        self.config.mkdir()
        (self.config / "ai_prompts.json").write_text((ROOT / "shared" / "ai_prompts.json").read_text(), encoding="utf-8")
        self.write_models()
        self.env = patched_environ({"PK_AI_CONFIG_DIR": str(self.config), "PK_AI_STATE_DIR": str(Path(self.tmp.name, "state")),
                                    "PK_AI_BACKEND": "bedrock", "PK_AI_DAILY_CAP": "200",
                                    "PK_AI_DAILY_USD": "1.00", "PK_AI_TOTAL_USD": "20.00",
                                    "PK_AI_PRICE_IN_PER_M": "1", "PK_AI_PRICE_OUT_PER_M": "1",
                                    "AWS_SECRET_ACCESS_KEY": "CANARY_KEY"})
        self.env.__enter__()

    def tearDown(self):
        self.env.__exit__(None, None, None)
        self.tmp.cleanup()

    def write_models(self, default="owner-model"):
        (self.config / "ai_models.json").write_text(json.dumps({"bedrock": {"default": default, "allowed": [default]},
                                                                  "gemini": {"default": None, "allowed": []}}), encoding="utf-8")

    def state(self, client=None, day=None):
        return GATEWAY.GatewayState(GATEWAY.load_model_config("bedrock"), GATEWAY.load_prompt_config(),
                                    GATEWAY.BedrockBackend(client or FakeBedrockClient()), day or dt.date.today)

    @staticmethod
    def response(text, incoming=10, outgoing=5):
        return {"output": {"message": {"content": [{"text": text}]}},
                "usage": {"inputTokens": incoming, "outputTokens": outgoing}}

    def test_converse_uses_default_model_fixed_system_and_settings(self):
        client = FakeBedrockClient([self.response('{"angle":54,"power":70}')])
        state = self.state(client)
        answer, outcome = GATEWAY.gateway_request(state, "aim", AIM_FIELDS)
        self.assertEqual((outcome, answer), ("ok", {"angle": 54, "power": 70}))
        call = client.calls[0]
        self.assertEqual(call["modelId"], "owner-model")
        self.assertEqual(call["inferenceConfig"], {"maxTokens": 60, "temperature": 0.2})
        self.assertEqual(call["system"][0]["text"], state.prompts["aim"]["instruction"])
        self.assertNotIn("owner-model", call["messages"][0]["content"][0]["text"])

    def test_invalid_pick_id_is_unavailable(self):
        client = FakeBedrockClient([self.response('{"pick":999}')])
        fields = dict(AIM_FIELDS, candidates=PICK_CANDIDATES)
        answer, outcome = GATEWAY.gateway_request(self.state(client), "pick", fields)
        self.assertEqual((answer, outcome), (None, "unavailable"))

    def test_throttle_retries_once_then_returns_unavailable(self):
        client = FakeBedrockClient([ClientError("ThrottlingException"), ClientError("ThrottlingException")])
        answer, outcome = GATEWAY.gateway_request(self.state(client), "aim", AIM_FIELDS)
        self.assertEqual((answer, outcome), (None, "unavailable"))
        self.assertEqual(len(client.calls), 2)

    def test_daily_request_cap_stops_second_call(self):
        os.environ["PK_AI_DAILY_CAP"] = "1"
        client = FakeBedrockClient()
        state = self.state(client)
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS)[1], "ok")
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS), (None, "unavailable"))
        self.assertEqual(len(client.calls), 1)

    def test_daily_money_cap_stops_later_call(self):
        os.environ["PK_AI_DAILY_USD"] = "0.50"
        client = FakeBedrockClient([self.response('{"angle":54,"power":70}', 1_000_000, 0)])
        state = self.state(client)
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS)[1], "ok")
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS), (None, "unavailable"))
        self.assertEqual(len(client.calls), 1)

    def test_total_money_cap_stops_later_call(self):
        os.environ["PK_AI_DAILY_USD"] = "100"
        os.environ["PK_AI_TOTAL_USD"] = "0.50"
        client = FakeBedrockClient([self.response('{"angle":54,"power":70}', 1_000_000, 0)])
        state = self.state(client)
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS)[1], "ok")
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS), (None, "unavailable"))
        self.assertEqual(len(client.calls), 1)

    def test_utc_day_rollover_and_counter_survive_restart(self):
        day = MutableDay(dt.date(2026, 11, 16))
        client = FakeBedrockClient([self.response('{"angle":54,"power":70}', 100, 0)])
        state = self.state(client, day)
        self.assertEqual(GATEWAY.gateway_request(state, "aim", AIM_FIELDS)[1], "ok")
        restarted = self.state(FakeBedrockClient(), day)
        self.assertEqual(restarted.requests_today, 1)
        self.assertEqual(restarted.spent_today_usd, 0.0001)
        day.value = dt.date(2026, 11, 17)
        self.assertEqual(restarted.health()["requests_today"], 0)
        self.assertEqual(restarted.health()["spent_today_usd"], 0.0)
        self.assertEqual(restarted.spent_total_usd, 0.0001)

    def test_health_and_logs_never_include_canary_data(self):
        client = FakeBedrockClient([self.response("CANARY_ANSWER")])
        state = self.state(client)
        server = GATEWAY.GatewayServer(("127.0.0.1", 0), state)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        GATEWAY.LOG.addHandler(handler)
        try:
            fields = dict(AIM_FIELDS, weather="CANARY_PROMPT")
            request = Request("http://127.0.0.1:%d/ai" % server.server_port,
                              data=json.dumps({"prompt_kind": "aim", "fields": fields}).encode(), method="POST",
                              headers={"Content-Type": "application/json", "X-Forwarded-For": "test-client"})
            with self.assertRaises(HTTPError) as raised:
                urlopen(request, timeout=2)
            self.assertEqual(raised.exception.code, 503)
            health = json.loads(urlopen("http://127.0.0.1:%d/ai/health" % server.server_port, timeout=2).read())
        finally:
            GATEWAY.LOG.removeHandler(handler)
            server.shutdown()
            server.server_close()
        self.assertEqual(set(health), {"configured", "backend", "model", "slots", "requests_today", "cap_today", "spent_today_usd"})
        for canary in ("CANARY_PROMPT", "CANARY_ANSWER", "CANARY_KEY"):
            self.assertNotIn(canary, json.dumps(health))
            self.assertNotIn(canary, stream.getvalue())


if __name__ == "__main__":
    unittest.main()
