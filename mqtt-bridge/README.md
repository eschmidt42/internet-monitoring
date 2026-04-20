# mqtt-bridge

Alertmanager webhook → MQTT bridge. Receives `POST /alert` from Alertmanager
and publishes `"down"` or `"up"` to a configured MQTT topic so mobile apps
subscribed on the LAN are notified of internet outages. Messages are not
retained; instead a background heartbeat re-publishes the last known state
every `HEARTBEAT_INTERVAL` seconds so reconnecting clients recover.

## Structure

```
mqtt-bridge/
├── src/mqtt_bridge/
│   ├── env.py        # reads configuration from environment variables
│   ├── helper.py     # mqtt_auth, publish, is_outage helpers
│   └── service.py    # Flask app (Alertmanager webhook handler)
├── tests/
│   ├── e2e/          # Flask test-client tests for the HTTP routes
│   └── unit/         # Unit tests for helper functions
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `MQTT_HOST` | *(required)* | Hostname or IP of the MQTT broker |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_TOPIC` | `home/network/status` | Topic to publish status messages to |
| `MQTT_USER` | *(none)* | MQTT username (optional) |
| `MQTT_PASSWORD` | *(none)* | MQTT password (optional) |
| `HEARTBEAT_INTERVAL` | `300` | Seconds between heartbeat re-publishes of the last known state |

## Develop

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install them
and activate the virtual environment:

```bash
uv sync
```

### Run tests

```bash
uv run pytest -n auto
```

Run only unit or e2e tests:

```bash
uv run pytest -n auto tests/unit/
uv run pytest -n auto tests/e2e/
```

Run with coverage and generate an HTML report:

```bash
uv run pytest --cov=mqtt_bridge --cov-report=html
```

The report is written to `htmlcov/index.html`. You can view it using

```bash
open htmlcov/index.html
```

### Lint and type-check

```bash
uv run ruff check .
uv run ty check
```

### Build the container image

```bash
podman compose build mqtt-bridge
```
