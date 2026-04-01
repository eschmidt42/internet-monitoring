# Internet Monitoring Stack

Self-contained Podman/Docker Compose stack that monitors internet availability and alerts via MQTT push to mobile devices. Based on [internet-pi](https://github.com/geerlingguy/internet-pi/).

## Services

| Service | Port | Purpose |
|---|---|---|
| Grafana | `3000` (LAN) | Dashboard visualization |
| Prometheus | `9090` (localhost) | Metrics + alert evaluation |
| Blackbox Exporter | `9115` (localhost) | ICMP + HTTP probes |
| Alertmanager | `9093` (localhost) | Alert routing → webhook |
| Mosquitto | `1883` (LAN) | MQTT broker |
| mqtt-bridge | `5000` (localhost) | Alertmanager webhook → MQTT |

## Alerting Flow

```
Blackbox Exporter → Prometheus (evaluates alert.rules every 15s)
  → Alertmanager (fires after 2 min) → webhook → mqtt-bridge
    → Mosquitto (topic: home/network/status, payload: "down"/"up")
      → Mobile apps on LAN Wi-Fi
```

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

> Note: the MQTT credentials are not needed for now. MQTTAnalyzer had issues subscribing with credentials, so they are deactivated for now.

```bash
cp .env.example .env
```

Edit .env — set GRAFANA_ADMIN_PASSWORD, MQTT_USER, MQTT_PASSWORD. 

Create the Mosquitto password file (must match MQTT_USER / MQTT_PASSWORD in .env)

```bash
podman run --rm -it \
  -v "$(pwd)/mosquitto/config:/mosquitto/config" \
  eclipse-mosquitto:2.0.18 \
  mosquitto_passwd -c /mosquitto/config/mosquitto.passwd <MQTT_USER>
```

Or if mosquitto_passwd is installed locally:

```bash
mosquitto_passwd -c mosquitto/config/mosquitto.passwd <MQTT_USER>
```

You should then see something like:

Enter password: [paste, Enter]   ← nothing visible
Reenter password: [paste, Enter] ← nothing visible

The command will prompt for the password twice — input is not echoed, this is expected.

Verify the file was written correctly:
```bash
cat mosquitto/config/mosquitto.passwd  →  should show: <MQTT_USER>:$7$...
```

If you want to overwrite using the above podman command you may need to remove the mosquitto.passwd file, e.g. using

```bash
rm mosquitto/config/mosquitto.passwd
```

### 4. Start the stack

```bash
podman compose up -d
```

Open Grafana at http://localhost:3000 (or your Mac's LAN IP).

### 5. Mobile MQTT apps

Subscribe to `home/network/status` (or whatever you set `MQTT_TOPIC` to) on your Mac's LAN IP, port `1883`.

- **iOS**: [MQTTAnalyzer](https://github.com/philipparndt/mqtt-analyzer) (Apple App Store, tested)
- **Android**: MQTT Alert for IoT (Play Store, untested)

Payload is `"down"` when internet probes fail, `"up"` on recovery.

## Alert timing

- Probes run every **15 seconds**
- Alert fires after **2 minutes** of sustained failures
- Alerts are **silenced 22:00–07:00 Europe/Berlin** (configurable in `alertmanager/alertmanager.yml` — change the `location` field to your timezone)

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
