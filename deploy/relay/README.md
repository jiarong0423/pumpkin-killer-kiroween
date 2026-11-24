# Pumpkin Killer relay

The owner deploys this relay. It only keeps live room codes and forwarded messages in memory.

## Environment

- `HOST`: bind address. The image sets `0.0.0.0`; local runs default to `127.0.0.1`.
- `PORT`: listening port, default `8765`.
- `PK_RELAY_ORIGINS`: comma-separated browser Origin allowlist. Empty accepts only localhost browser origins; native local clients have no Origin.
- `PK_RELAY_LOG_LEVEL`: Python log level, default `WARNING`.

Build from the repository root:

```sh
docker build -f deploy/relay/Dockerfile -t pumpkin-killer-relay .
```

For Coolify, create a separate service from this Dockerfile. Set `PORT` to the exposed Coolify port and keep `HOST=0.0.0.0`. Configure Traefik to route WebSocket upgrades at `/ws` to the service and allow the deployed page origin in `PK_RELAY_ORIGINS`.

Coolify should check `GET /health`; it returns `200 OK` with `ok`. After the owner deploys, check the health URL, create and join a room through `/ws`, and verify a reverse-proxy WebSocket connection forwards an action.
