# Internet Monitoring Stack

Self-contained Podman/Docker Compose stack that monitors internet availability and alerts via MQTT push to mobile devices.

## Services

| Service | Port | Purpose |
|---|---|---|
| Grafana | `3000` (LAN) | Dashboard visualization |
| Prometheus | `9090` (localhost) | Metrics + alert evaluation |
| Blackbox Exporter | `9115` (localhost) | ICMP + HTTP probes |
| Alertmanager | `9093` (localhost) | Alert routing → webhook |
| Mosquitto | `1883` (LAN) | MQTT broker |
| mqtt-bridge | `5000` (localhost) | Alertmanager webhook → MQTT |

## Quick Start

### 1. Prerequisites

- [Podman Desktop](https://podman-desktop.io/) (macOS) — provides `podman machine` + Docker socket
- `podman compose` or `docker-compose` CLI

### 2. ICMP / Ping support (Podman rootless, one-time)

```bash
podman machine ssh
sudo sysctl -w net.ipv4.ping_group_range="0 2147483647"
# To persist across reboots:
echo "net.ipv4.ping_group_range = 0 2147483647" | sudo tee /etc/sysctl.d/99-ping.conf
exit
```

### 3. Configure credentials

```bash
cp .env.example .env
# Edit .env — set GRAFANA_ADMIN_PASSWORD, MQTT_USER, MQTT_PASSWORD

# Create the Mosquitto password file (must match MQTT_USER / MQTT_PASSWORD in .env)
podman run --rm -it eclipse-mosquitto mosquitto_passwd -c /dev/stdout <MQTT_USER> > mosquitto/config/mosquitto.passwd
# Or if mosquitto_passwd is installed locally:
mosquitto_passwd -c mosquitto/config/mosquitto.passwd <MQTT_USER>
```

### 4. Start the stack

```bash
podman compose up -d
```

Open Grafana at http://localhost:3000 (or your Mac's LAN IP).

### 5. Mobile MQTT apps

Subscribe to `home/network/status` (or whatever you set `MQTT_TOPIC` to) on your Mac's LAN IP, port `1883`.

- **iOS**: MQTT Alert (App Store) or RadioShuttle MQTT Push Client
- **Android**: MQTT Alert for IoT (Play Store)

Payload is `"down"` when internet probes fail, `"up"` on recovery.

## Alert timing

- Probes run every **15 seconds**
- Alert fires after **2 minutes** of sustained failures
- Alerts are **silenced 22:00–07:00** (configurable in `alertmanager/alertmanager.yml`)

## Ping targets

Edit `prometheus/pinghosts.yml` — format is `"host;label"`:

```yaml
- targets:
    - "8.8.8.8;Google DNS"
    - "1.1.1.1;Cloudflare DNS"
    - "google.com;google.com"
```

## Directory structure

```
docker-compose.yml
.env.example
prometheus/
  prometheus.yml
  alert.rules
  pinghosts.yml
alertmanager/
  alertmanager.yml
blackbox/config/
  blackbox.yml
grafana/provisioning/
  datasources/datasource.yml
  dashboards/dashboard.yml
  dashboards/internet-connection.json
mosquitto/config/
  mosquitto.conf
  mosquitto.passwd  ← gitignored, create manually
mqtt-bridge/
  Dockerfile
  bridge.py
  requirements.txt
```
