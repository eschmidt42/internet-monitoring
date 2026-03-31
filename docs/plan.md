# Internet Monitoring — Implementation Plan

## Problem Statement

Build a self-contained Podman (Docker Compose compatible) stack on macOS that:
- Monitors internet availability via ICMP ping and HTTP probes
- Visualizes uptime/latency in a Grafana dashboard
- Alerts on the local network (LAN/Wi-Fi) via both Grafana alerting and MQTT push to iOS and Android devices
- Alert fires after 2 minutes of detected outage

## Starting Point

`internet-pi/internet-monitoring/` contains provisioned configs for:
- Prometheus (scrape config, alert rules)
- Blackbox Exporter (probe modules)
- Grafana (dashboards + datasource provisioning)

No `docker-compose.yml` exists yet (upstream uses Ansible). No MQTT, Alertmanager, or bridge service.

## Target Stack

| Service | Purpose |
|---|---|
| `prometheus` | Metrics collection + alert rule evaluation |
| `blackbox` | ICMP + HTTP probes (via Prometheus) |
| `alertmanager` | Alert routing → webhook |
| `grafana` | Dashboard visualization + Grafana-native alerts |
| `mosquitto` | MQTT broker, exposed on LAN (port 1883) |
| `mqtt-bridge` | Small Python container: receives Alertmanager webhook → publishes to Mosquitto |

Speedtest is excluded.

## File Layout (target state)

```
internet-monitoring/           ← working compose root (new)
  docker-compose.yml
  prometheus/
    prometheus.yml             ← adapted from internet-pi
    alert.rules                ← adapted from internet-pi
    pinghosts.yml              ← ping targets config
  grafana/
    provisioning/
      dashboards/
        dashboard.yml
        internet-connection.json  ← from internet-pi
      datasources/
        datasource.yml
  blackbox/
    config/
      blackbox.yml             ← from internet-pi
  alertmanager/
    alertmanager.yml           ← new
  mosquitto/
    config/
      mosquitto.conf           ← new
  mqtt-bridge/
    Dockerfile
    bridge.py                  ← Flask webhook → paho-mqtt
    requirements.txt
```

The internet-pi subtree is reference only; we produce a clean `internet-monitoring/` directory at the repo root.

## Podman on macOS

- Use **Podman Desktop** (installs `podman machine`, provides Docker-socket compatibility)
- Use `docker compose` CLI pointed at the Podman socket — or `podman compose`
- Port bindings in compose expose services to Mac's LAN IP (Podman Desktop handles host-port forwarding from the VM)
- macOS firewall must allow ports 1883, 3000 (Grafana), 9090, 9093

## Alerting Flow

```
Blackbox Exporter → Prometheus (evaluates alert.rules every 15s)
  → Alertmanager (fires after 2 min) → webhook → mqtt-bridge
    → Mosquitto (topic: home/network/status, payload: "down"/"up")
      → Mobile apps on LAN Wi-Fi
```

Grafana also gets its own alert rules on the same Prometheus datasource (as backup / dashboard-integrated).

## Mobile App Recommendations

- **Android**: MQTT Alert for IoT (Play Store) — triggers phone notification from MQTT topic
- **iOS**: MQTT Alert (App Store) or RadioShuttle MQTT Push Client (works even when app is backgrounded)
- Both connect to MacBook's LAN IP on port 1883, subscribe to `home/network/status`

## Key Configuration Decisions

1. **Ping targets**: `8.8.8.8`, `1.1.1.1`, `google.com` (configurable in `pinghosts.yml`)
2. **Scrape interval**: 15s (blackbox), alert fires after 2 min sustained
3. **Alertmanager webhook**: calls `http://mqtt-bridge:5000/alert`
4. **Alert quiet hours**: Alertmanager `mute_time_intervals` silences MQTT/webhook alerts at night (22:00–07:00); configurable in `alertmanager.yml`
5. **Mosquitto**: anonymous access, bind to all interfaces (LAN reachable)
6. **Grafana**: port 3000, pre-provisioned dashboard from internet-pi

## Implementation Checklist

1. Create `internet-monitoring/` directory structure at repo root
2. Write `docker-compose.yml` (all 6 services)
3. Adapt `prometheus/prometheus.yml` from internet-pi (remove speedtest, add pinghosts)
4. Write `prometheus/pinghosts.yml`
5. Adapt `prometheus/alert.rules` (internet outage rule, remove high_load)
6. Write `alertmanager/alertmanager.yml` (route alerts to webhook; add `mute_time_intervals` for quiet hours, default 22:00–07:00)
7. Write `mosquitto/config/mosquitto.conf`
8. Write `mqtt-bridge/bridge.py`, `Dockerfile`, `requirements.txt`
9. Copy/adapt Grafana provisioning files from internet-pi
10. Copy/adapt Blackbox Exporter config from internet-pi
11. Verify `podman compose up` brings everything up cleanly
12. Test Mosquitto reachable from LAN
