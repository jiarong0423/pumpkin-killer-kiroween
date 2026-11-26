#!/bin/sh
# The relay remains loopback-only; nginx is the sole public listener.
set -eu

: "${PK_ALLOWED_ORIGINS:=}"
export PK_RELAY_ORIGINS="$PK_ALLOWED_ORIGINS"
if [ -z "$PK_ALLOWED_ORIGINS" ]; then
    echo "ERROR: PK_ALLOWED_ORIGINS is empty. The relay then accepts browsers on localhost only and every real player gets 403; the hosted MCP accepts any browser Origin. Set it to the public https address." >&2
fi
export HOST=127.0.0.1
export PORT=8765
: "${PK_AI_HOST:=127.0.0.1}"
: "${PK_AI_PORT:=8766}"
export PK_AI_HOST PK_AI_PORT
: "${PK_MCP_HOST:=127.0.0.1}"
: "${PK_MCP_PORT:=8767}"
: "${PK_MCP_RELAY_URL:=ws://127.0.0.1:8765/ws}"
: "${PK_MCP_PAGE_JUDGE:=auto}"
: "${PK_MCP_MAX_PAGE_JUDGES:=10}"
export PK_MCP_HOST PK_MCP_PORT PK_MCP_RELAY_URL PK_MCP_PAGE_JUDGE PK_MCP_MAX_PAGE_JUDGES
# The hosted MCP gateway names the remote client behind each seat so the relay counts seats per client, not all as 127.0.0.1.
# A fresh random token per start (never written to a file); unless one is supplied, only the two local processes know it.
: "${PK_RELAY_GATEWAY_TOKEN:=$(python3 -c 'import secrets; print(secrets.token_hex(16))')}"
export PK_RELAY_GATEWAY_TOKEN

python3 /app/pk_relay.py &
relay_pid=$!
mcp_pid=
if [ -f /app/scripts/pk_mcp_http.py ]; then
    python3 -B /app/scripts/pk_mcp_http.py &
    mcp_pid=$!
fi
gateway_pid=

# Money guard: the gateway counts dollars only when both prices are set. Without them the dollar caps (PK_AI_DAILY_USD, PK_AI_TOTAL_USD) would
# be blind and only the call cap would hold, so the AI gateway is not started at all (the game keeps its built-in opponents).
ai_allowed=1
if [ -z "${PK_AI_PRICE_IN_PER_M:-}" ] || [ -z "${PK_AI_PRICE_OUT_PER_M:-}" ]; then
    ai_allowed=0
fi
if [ "$ai_allowed" = "0" ] && { [ -n "${AWS_REGION:-}" ] || [ -n "${AWS_DEFAULT_REGION:-}" ] || [ -n "${PK_GEMINI_KEYS:-}" ] || [ "${PK_AI_BACKEND:-}" = "bedrock" ]; }; then
    echo "ERROR: AI credentials are set but PK_AI_PRICE_IN_PER_M or PK_AI_PRICE_OUT_PER_M is missing. The AI gateway is NOT started (its dollar caps would not count). Set both prices from the official price page to enable it." >&2
fi

# Bedrock uses the standard AWS environment or a workload role, never a key file.
backend="${PK_AI_BACKEND:-}"
if [ "$ai_allowed" = "0" ]; then
    :
elif [ "$backend" = "bedrock" ] || { [ -z "$backend" ] && { [ -n "${AWS_REGION:-}" ] || [ -n "${AWS_DEFAULT_REGION:-}" ]; }; }; then
    python3 /app/scripts/pk_ai_gateway.py &
    gateway_pid=$!
elif [ "$backend" = "gemini" ] || [ -z "$backend" ]; then
    if [ -n "${PK_GEMINI_KEYS:-}" ]; then
        python3 /app/scripts/pk_ai_gateway.py &
        gateway_pid=$!
    fi
fi

stop() {
    if [ -n "${watch_pid:-}" ]; then
        kill "$watch_pid" 2>/dev/null || true
    fi
    kill "$relay_pid" 2>/dev/null || true
    if [ -n "$mcp_pid" ]; then
        kill "$mcp_pid" 2>/dev/null || true
    fi
    if [ -n "$gateway_pid" ]; then
        kill "$gateway_pid" 2>/dev/null || true
    fi
    wait "$relay_pid" 2>/dev/null || true
    if [ -n "$mcp_pid" ]; then
        wait "$mcp_pid" 2>/dev/null || true
    fi
    if [ -n "$gateway_pid" ]; then
        wait "$gateway_pid" 2>/dev/null || true
    fi
}

trap 'stop; exit 0' INT TERM

nginx -g 'daemon off;' &
nginx_pid=$!
# If the relay or the MCP process dies, stop nginx too so the container exits non-zero and Coolify restarts it
# (otherwise the page keeps loading while rooms or /mcp silently fail).
(
    while kill -0 "$relay_pid" 2>/dev/null && { [ -z "$mcp_pid" ] || kill -0 "$mcp_pid" 2>/dev/null; }; do
        sleep 5
    done
    echo "ERROR: the relay or MCP process stopped; stopping the container so it restarts" >&2
    kill "$nginx_pid" 2>/dev/null || true
) &
watch_pid=$!
wait "$nginx_pid" || status=$?
stop
exit "${status:-0}"
