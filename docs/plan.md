# Internet Monitoring — Implementation Plan

## Problem Statement

Build a self-contained Podman (Docker Compose compatible) stack on macOS that:
- Monitors internet availability via ICMP ping and HTTP probes
- Visualizes uptime/latency in a Grafana dashboard
- Alerts on the local network (LAN/Wi-Fi) via both Grafana alerting and MQTT push to iOS and Android devices
- Alert fires after 2 minutes of detected outage

## Starting Point (deleted with the `feat/building-stuff` branch)

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
- Port bindings in compose can expose selected services to the Mac's LAN IP (Podman Desktop handles host-port forwarding from the VM)
- macOS firewall must allow ports 1883 (Mosquitto) and, optionally, 3000 (Grafana) for access from other LAN devices; keep Prometheus (9090) and Alertmanager (9093) internal to the compose network or bound to `127.0.0.1` if host-only access is needed

## ICMP / NET_RAW Requirements

Blackbox Exporter uses raw ICMP sockets for ping probes. Unprivileged containers cannot send ICMP by default — this is especially common under Podman rootless and will cause false "internet down" alerts.

**Required in `docker-compose.yml`** for the `blackbox` service:
```yaml
cap_add:
  - NET_RAW
```

**Podman rootless on macOS (Podman Desktop):** `cap_add: NET_RAW` alone may not be sufficient because the Podman VM's kernel restricts unprivileged ICMP. Two options (in order of preference):

1. **Set `ping_group_range` in the Podman VM** (one-time, survives restarts if added to `/etc/sysctl.d/`):
   ```bash
   podman machine ssh
   sudo sysctl -w net.ipv4.ping_group_range="0 2147483647"
   ```
2. **Run the blackbox container as root** by adding `user: root` to the service in compose — simpler but less hardened.

Fallback if neither is acceptable: replace ICMP probes with HTTP(S) probes targeting a known connectivity endpoint such as `https://www.gstatic.com/generate_204`, or use a blackbox `tcp_connect` probe (for example to `8.8.8.8:53`) if only reachability is required (less reliable than ICMP but requires no extra capabilities).

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
5. **Mosquitto**: username/password auth via `mosquitto_passwd` (password file `.gitignore`'d); `allow_anonymous false`; credentials passed to `mqtt-bridge` and mobile apps via env vars. Bind to all interfaces (LAN reachable).
6. **Grafana**: port 3000, pre-provisioned dashboard from internet-pi

## Implementation Checklist

1. Write `docker-compose.yml` (all 6 services)
2. Adapt `prometheus/prometheus.yml` from internet-pi (remove speedtest, add pinghosts)
3. Write `prometheus/pinghosts.yml`
4. Adapt `prometheus/alert.rules` (internet outage rule, remove high_load)
5. Write `alertmanager/alertmanager.yml` (route alerts to webhook; add `mute_time_intervals` for quiet hours, default 22:00–07:00)
6. Write `mosquitto/config/mosquitto.conf` with `allow_anonymous false`, `password_file` pointing to `mosquitto.passwd`; add `mosquitto/config/mosquitto.passwd` to `.gitignore`; document one-time setup step: `mosquitto_passwd -c mosquitto/config/mosquitto.passwd <username>`
7. Write `mqtt-bridge/bridge.py`, `Dockerfile`, `requirements.txt`; pass `MQTT_USER` and `MQTT_PASSWORD` as env vars in compose
8. Copy/adapt Grafana provisioning files from internet-pi
9.  Copy/adapt Blackbox Exporter config from internet-pi
10. Verify `podman compose up` brings everything up cleanly
11. Test Mosquitto reachable from LAN
