#!/usr/bin/env python3
"""Loopback-only, template-constrained AI gateway with provider and spend guards."""
import collections
import datetime as dt
import html
import json
import logging
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import signal
import sys
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

BODY_LIMIT = 4096
OUTPUT_LIMIT = 160
REQUEST_WINDOW_SECONDS = 3
REQUEST_HOURLY_LIMIT = 30
UPSTREAM_TIMEOUT_SECONDS = 6
ANGLE_MIN = 25
ANGLE_MAX = 80
POWER_MIN = 15
POWER_MAX = 115
DEFAULT_DAILY_CAP = 200
DEFAULT_DAILY_USD = 1.00
DEFAULT_TOTAL_USD = 20.00
DEFAULT_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
LOG = logging.getLogger("pk_ai_gateway")


class ConfigurationError(ValueError):
    """Raised when a required owner-selected gateway setting is absent."""


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(name: str) -> Dict[str, Any]:
    config_dir = Path(os.getenv("PK_AI_CONFIG_DIR", str(project_root() / "shared")))
    with (config_dir / name).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ConfigurationError("AI configuration must be an object")
    return value


def selected_backend() -> str:
    configured = os.getenv("PK_AI_BACKEND", "").strip().lower()
    if configured in ("bedrock", "gemini"):
        return configured
    if configured:
        raise ConfigurationError("PK AI gateway refuses to start: PK_AI_BACKEND must be bedrock or gemini")
    return "bedrock" if os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") else "gemini"


def load_model_config(backend: Optional[str] = None) -> Dict[str, Any]:
    backend = backend or selected_backend()
    config = load_json("ai_models.json")
    # Pre-Bedrock files used a top-level default and allowed list. Read them so
    # an owner can migrate configuration without a code or request-body change.
    provider = config.get(backend)
    if provider is None and backend == "gemini":
        provider = {"default": config.get("default"), "allowed": config.get("allowed")}
    if not isinstance(provider, dict):
        raise ConfigurationError("PK AI gateway refuses to start: shared/ai_models.json has no %s section" % backend)
    default = provider.get("default")
    allowed = provider.get("allowed")
    if not isinstance(default, str) or not default:
        raise ConfigurationError("PK AI gateway refuses to start: shared/ai_models.json %s.default is not set" % backend)
    if (not isinstance(allowed, list) or not allowed or any(not isinstance(model, str) or not model for model in allowed)
            or default not in allowed):
        raise ConfigurationError("PK AI gateway refuses to start: %s.allowed must include the default model" % backend)
    return {"default": default, "allowed": list(allowed)}


def load_prompt_config() -> Dict[str, Dict[str, Any]]:
    prompts = load_json("ai_prompts.json")
    if not prompts:
        raise ConfigurationError("PK AI gateway refuses to start: no prompt templates configured")
    for kind, template in prompts.items():
        if not isinstance(kind, str) or not isinstance(template, dict):
            raise ConfigurationError("PK AI gateway refuses to start: invalid prompt template")
        if (not isinstance(template.get("fields"), list)
                or any(not isinstance(field, str) for field in template["fields"])
                or not isinstance(template.get("instruction"), str)):
            raise ConfigurationError("PK AI gateway refuses to start: invalid prompt template")
    return prompts


def configured_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value >= 0 else default


def configured_usd(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value >= 0 else default


def configured_price(name: str) -> Optional[float]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        price = float(raw)
    except ValueError:
        return None
    return price if price >= 0 else None


def clean_model_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = html.unescape(value).strip()
    value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]*>", "", value).strip()
    return value[:OUTPUT_LIMIT]


def extract_gemini_text(payload: Any) -> str:
    try:
        return clean_model_text(payload["candidates"][0]["content"]["parts"][0]["text"])
    except (KeyError, IndexError, TypeError):
        return ""


def extract_bedrock_text(payload: Any) -> str:
    try:
        parts = payload["output"]["message"]["content"]
    except (KeyError, TypeError):
        return ""
    if not isinstance(parts, list):
        return ""
    return clean_model_text("".join(part.get("text", "") for part in parts if isinstance(part, dict)))


def extract_usage(payload: Any, backend: str) -> Tuple[int, int]:
    usage = payload.get("usage") if backend == "bedrock" and isinstance(payload, dict) else None
    if backend == "gemini" and isinstance(payload, dict):
        usage = payload.get("usageMetadata")
    if not isinstance(usage, dict):
        return 0, 0
    input_tokens = usage.get("inputTokens", usage.get("promptTokenCount", 0))
    output_tokens = usage.get("outputTokens", usage.get("candidatesTokenCount", 0))
    return (input_tokens if isinstance(input_tokens, int) and input_tokens >= 0 else 0,
            output_tokens if isinstance(output_tokens, int) and output_tokens >= 0 else 0)


AIM_FIELDS = {"own_hero_id", "own_position", "enemy_position", "enemy_hp", "wind", "weather", "fence_hp", "round_number"}
PICK_BASE_FIELDS = AIM_FIELDS | {"candidates"}


def valid_aim_fields(fields: Dict[str, Any]) -> bool:
    if set(fields) != AIM_FIELDS:
        return False
    numbers = ("own_position", "enemy_position", "wind")
    integers = ("enemy_hp", "fence_hp", "round_number")
    return (isinstance(fields["own_hero_id"], str) and bool(fields["own_hero_id"])
            and isinstance(fields["weather"], str) and bool(fields["weather"])
            and all(isinstance(fields[name], (int, float)) and not isinstance(fields[name], bool) for name in numbers)
            and all(isinstance(fields[name], int) and not isinstance(fields[name], bool) for name in integers))


def valid_pick_fields(fields: Dict[str, Any]) -> bool:
    if set(fields) != PICK_BASE_FIELDS or not valid_aim_fields({key: value for key, value in fields.items() if key != "candidates"}):
        return False
    candidates = fields["candidates"]
    if not isinstance(candidates, list) or not 3 <= len(candidates) <= 6:
        return False
    ids = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) - {"id", "kind", "aim", "predicted_distance_px"}:
            return False
        candidate_id = candidate.get("id")
        if (not isinstance(candidate_id, int) or isinstance(candidate_id, bool) or candidate_id in ids
                or not isinstance(candidate.get("kind"), str) or not candidate["kind"]
                or not isinstance(candidate.get("predicted_distance_px"), (int, float))
                or isinstance(candidate["predicted_distance_px"], bool)):
            return False
        aim = candidate.get("aim")
        if aim is not None and (not isinstance(aim, dict) or set(aim) != {"angle", "power"}
                                or not isinstance(aim["angle"], int) or isinstance(aim["angle"], bool)
                                or not isinstance(aim["power"], int) or isinstance(aim["power"], bool)
                                or not ANGLE_MIN <= aim["angle"] <= ANGLE_MAX
                                or not POWER_MIN <= aim["power"] <= POWER_MAX):
            return False
        ids.add(candidate_id)
    return True


def validate_fields(kind: str, fields: Any, template: Dict[str, Any]) -> bool:
    if not isinstance(fields, dict) or set(fields) != set(template["fields"]):
        return False
    return valid_aim_fields(fields) if kind == "aim" else valid_pick_fields(fields) if kind == "pick" else False


def validate_answer(kind: str, text: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        answer = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(answer, dict):
        return None
    if kind == "aim":
        angle, power = answer.get("angle"), answer.get("power")
        if (set(answer) != {"angle", "power"} or isinstance(angle, bool) or isinstance(power, bool)
                or not isinstance(angle, int) or not isinstance(power, int)
                or not ANGLE_MIN <= angle <= ANGLE_MAX or not POWER_MIN <= power <= POWER_MAX):
            return None
        return {"angle": angle, "power": power}
    if kind == "pick":
        choice = answer.get("pick")
        candidate_ids = {candidate["id"] for candidate in fields["candidates"]}
        return {"pick": choice} if set(answer) == {"pick"} and choice in candidate_ids else None
    return None


def gateway_prompt(template: Dict[str, Any], fields: Dict[str, Any]) -> str:
    return template["instruction"] + "\nPublic game data: " + json.dumps(fields, separators=(",", ":"), ensure_ascii=False)


class GeminiBackend:
    name = "gemini"

    def call(self, model: str, system: str, user: str) -> Tuple[int, str, int, int]:
        key = os.getenv("PK_GEMINI_KEYS", "").split(",")[0].strip()
        if not key:
            return 0, "", 0, 0
        endpoint = os.getenv("PK_GEMINI_ENDPOINT", DEFAULT_GEMINI_ENDPOINT).format(model=quote(model, safe=""))
        body = json.dumps({"contents": [{"role": "user", "parts": [{"text": user}]}],
                           "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}},
                          separators=(",", ":")).encode("utf-8")
        request = Request(endpoint, data=body, method="POST", headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urlopen(request, timeout=UPSTREAM_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
                incoming, outgoing = extract_usage(payload, self.name)
                return response.getcode(), extract_gemini_text(payload), incoming, outgoing
        except HTTPError as error:
            return error.code, "", 0, 0
        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError):
            return 0, "", 0, 0

    def configured(self) -> bool:
        return bool(os.getenv("PK_GEMINI_KEYS", "").strip())

    def slots(self) -> int:
        return len([key for key in os.getenv("PK_GEMINI_KEYS", "").split(",") if key.strip()])


class BedrockBackend:
    name = "bedrock"

    def __init__(self, client: Any = None) -> None:
        if client is not None:
            self.client = client
            return
        try:
            import boto3
            from botocore.config import Config
        except ImportError as error:
            raise ConfigurationError("PK AI gateway refuses to start: boto3 is required for the Bedrock backend") from error
        self.client = boto3.client("bedrock-runtime", config=Config(connect_timeout=UPSTREAM_TIMEOUT_SECONDS,
                                                                      read_timeout=UPSTREAM_TIMEOUT_SECONDS,
                                                                      retries={"total_max_attempts": 1, "mode": "standard"}))

    def call(self, model: str, system: str, user: str) -> Tuple[int, str, int, int]:
        try:
            payload = self.client.converse(modelId=model, system=[{"text": system}],
                                           messages=[{"role": "user", "content": [{"text": user}]}],
                                           inferenceConfig={"maxTokens": 60, "temperature": 0.2})
            incoming, outgoing = extract_usage(payload, self.name)
            return 200, extract_bedrock_text(payload), incoming, outgoing
        except Exception as error:  # boto exception classes are intentionally not imported at module load.
            code = ""
            response = getattr(error, "response", None)
            if isinstance(response, dict):
                code = str(response.get("Error", {}).get("Code", ""))
            return (429 if code in {"ThrottlingException", "TooManyRequestsException"} else 0), "", 0, 0

    def configured(self) -> bool:
        return True

    def slots(self) -> int:
        return 1


class GatewayState:
    def __init__(self, models: Dict[str, Any], prompts: Dict[str, Dict[str, Any]], backend: Any,
                 date_provider: Callable[[], dt.date] = dt.date.today) -> None:
        self.default_model = models["default"]
        self.prompts = prompts
        self.backend = backend
        self.date_provider = date_provider
        self.client_requests: Dict[str, collections.deque] = {}
        self.lock = threading.Lock()
        self.state_dir = Path(os.getenv("PK_AI_STATE_DIR", "/tmp/pk_ai"))
        self.counter_path = self.state_dir / "counters.json"
        self.day = self.date_provider().isoformat()
        self.requests_today = 0
        self.spent_today_usd = 0.0
        self.spent_total_usd = 0.0
        self._load_counters()

    def _load_counters(self) -> None:
        try:
            stored = json.loads(self.counter_path.read_text(encoding="utf-8"))
            if not isinstance(stored, dict):
                return
            self.day = str(stored.get("day", self.day))
            self.requests_today = max(0, int(stored.get("requests_today", 0)))
            self.spent_today_usd = max(0.0, float(stored.get("spent_today_usd", 0)))
            self.spent_total_usd = max(0.0, float(stored.get("spent_total_usd", 0)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return
        self._roll_day_locked()

    def _save_counters_locked(self) -> None:
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = self.counter_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"day": self.day, "requests_today": self.requests_today,
                                         "spent_today_usd": self.spent_today_usd,
                                         "spent_total_usd": self.spent_total_usd}, separators=(",", ":")), encoding="utf-8")
        temporary.replace(self.counter_path)

    def _roll_day_locked(self) -> None:
        today = self.date_provider().isoformat()
        if self.day != today:
            self.day = today
            self.requests_today = 0
            self.spent_today_usd = 0.0
            self._save_counters_locked()

    def health(self) -> Dict[str, Any]:
        with self.lock:
            self._roll_day_locked()
            return {"configured": self.backend.configured(), "backend": self.backend.name,
                    "model": self.default_model, "slots": self.backend.slots(),
                    "requests_today": self.requests_today, "cap_today": configured_int("PK_AI_DAILY_CAP", DEFAULT_DAILY_CAP),
                    "spent_today_usd": round(self.spent_today_usd, 8)}

    def accept_client_request(self, client: str) -> bool:
        now = time.monotonic()
        with self.lock:
            entries = self.client_requests.setdefault(client, collections.deque())
            while entries and now - entries[0] >= 3600:
                entries.popleft()
            if sum(1 for stamp in entries if now - stamp < REQUEST_WINDOW_SECONDS) >= 1 or len(entries) >= REQUEST_HOURLY_LIMIT:
                return False
            entries.append(now)
            return True

    def reserve_call(self) -> bool:
        with self.lock:
            self._roll_day_locked()
            if (self.requests_today >= configured_int("PK_AI_DAILY_CAP", DEFAULT_DAILY_CAP)
                    or self.spent_today_usd >= configured_usd("PK_AI_DAILY_USD", DEFAULT_DAILY_USD)
                    or self.spent_total_usd >= configured_usd("PK_AI_TOTAL_USD", DEFAULT_TOTAL_USD)):
                return False
            self.requests_today += 1
            self._save_counters_locked()
            return True

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        incoming = configured_price("PK_AI_PRICE_IN_PER_M")
        outgoing = configured_price("PK_AI_PRICE_OUT_PER_M")
        if incoming is None or outgoing is None:
            return
        amount = input_tokens * incoming / 1_000_000 + output_tokens * outgoing / 1_000_000
        with self.lock:
            self._roll_day_locked()
            self.spent_today_usd += amount
            self.spent_total_usd += amount
            self._save_counters_locked()


def gateway_request(state: GatewayState, kind: str, fields: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
    if not state.reserve_call():
        return None, "unavailable"
    template = state.prompts[kind]
    user = "Public game data: " + json.dumps(fields, separators=(",", ":"), ensure_ascii=False)
    for attempt in range(2):
        status, text, input_tokens, output_tokens = state.backend.call(state.default_model, template["instruction"], user)
        state.record_usage(input_tokens, output_tokens)
        if status != 429 or attempt:
            break
    if status != 200:
        return None, "unavailable"
    answer = validate_answer(kind, text, fields)
    return (answer, "ok") if answer is not None else (None, "unavailable")


class GatewayHandler(BaseHTTPRequestHandler):
    server: "GatewayServer"
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def client_id(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "")
        return forwarded.split(",", 1)[0].strip() if self.client_address[0] in ("127.0.0.1", "::1") and forwarded else self.client_address[0]

    def send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self.send_json(HTTPStatus.OK, self.server.state.health()) if self.path == "/ai/health" else self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "reason": "not_found"})

    def do_POST(self) -> None:
        status, response = HTTPStatus.BAD_REQUEST, {"ok": False, "reason": "invalid_request"}
        if self.path != "/ai":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "reason": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            length = BODY_LIMIT + 1
        if 0 <= length <= BODY_LIMIT:
            try:
                request = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                request = None
            if isinstance(request, dict) and set(request) == {"prompt_kind", "fields"} and isinstance(request.get("prompt_kind"), str):
                kind = request["prompt_kind"]
                template = self.server.state.prompts.get(kind)
                if template and validate_fields(kind, request["fields"], template):
                    if self.server.state.accept_client_request(self.client_id()):
                        answer, outcome = gateway_request(self.server.state, kind, request["fields"])
                        if outcome == "ok" and answer is not None:
                            status, response = HTTPStatus.OK, {"ok": True, "result": answer}
                        else:
                            status, response = HTTPStatus.SERVICE_UNAVAILABLE, {"ok": False, "reason": "unavailable"}
                    else:
                        status, response = HTTPStatus.TOO_MANY_REQUESTS, {"ok": False, "reason": "unavailable"}
        elif length > BODY_LIMIT:
            status, response = HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "reason": "invalid_request"}
        LOG.info("ai_call status=%s backend=%s model=%s", int(status), self.server.state.backend.name, self.server.state.default_model)
        self.send_json(status, response)


class GatewayServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: Tuple[str, int], state: GatewayState) -> None:
        self.state = state
        super().__init__(address, GatewayHandler)


def create_state(*, backend_client: Any = None, date_provider: Callable[[], dt.date] = dt.date.today) -> GatewayState:
    backend_name = selected_backend()
    models = load_model_config(backend_name)
    backend = BedrockBackend(backend_client) if backend_name == "bedrock" else GeminiBackend()
    return GatewayState(models, load_prompt_config(), backend, date_provider)


def run() -> None:
    try:
        state = create_state()
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
    if configured_price("PK_AI_PRICE_IN_PER_M") is None or configured_price("PK_AI_PRICE_OUT_PER_M") is None:
        LOG.warning("WARNING ai money prices are unset; request caps remain active but spend is not counted")
    logging.basicConfig(level=os.getenv("PK_AI_LOG_LEVEL", "INFO"), format="%(message)s")
    server = GatewayServer((os.getenv("PK_AI_HOST", "127.0.0.1"), int(os.getenv("PK_AI_PORT", "8766"))), state)
    def stop(_: int, __: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
