# research

## availabilty pings / monitoring

> I want to brainstorm something. I want to measure the internet availability from my home network. More concretely, I want to create a time series that contains information I can use to visualize when internet was not available, e.g. via using `ping` every second or so to one or more web adresses. Hence I'm contemplating to write a python cron job that does that and dumps data into some data base and visualize that with some web GUI. Ideally all three being contained in docker containers wired up with docker-compose. Are there any critical flaws I should be aware of now before building this up? If no, what would be your recommendations?
Your idea to monitor internet availability using `ping` and visualize it via a Docker-based stack is solid and well-aligned with existing solutions. Many users have implemented similar setups to track connectivity, latency, and outages—especially to provide evidence to ISPs about reliability issues [^1]. Below are key recommendations and potential pitfalls to consider before building your system.

### ✅ Recommended Architecture
The most common and effective pattern involves:

- **Ping Monitoring**: A Python (or shell) script that periodically pings one or more hosts (e.g., `8.8.8.8`, `1.1.1.1`, or `google.com`) and logs results (latency, success/failure) [^3][^4].
- **Storage**: Use **InfluxDB** or **Prometheus** for time-series data. InfluxDB is user-friendly with Grafana; Prometheus is powerful with exporters [^4][^5].
- **Visualization**: **Grafana** is the standard for dashboards, offering real-time graphs of uptime, latency, and packet loss [^1][^8].
- **Containerization**: **Docker Compose** is ideal for wiring these components together cleanly [^2][^5].

Several open-source projects provide ready-to-use templates:

| Project | Tools Used | Features |
|--------|------------|----------|
| [raynigon/ping-monitor](https://github.com/raynigon/ping-monitor) | Python, InfluxDB, Grafana | Simple ping logging and visualization [^4] |
| [bmateusz/ping-monitor](https://github.com/bmateusz/ping-monitor) | Prometheus, Grafana | ISP dispute-focused dashboard [^1] |
| [geerlingguy/internet-monitoring](https://github.com/geerlingguy/internet-monitoring) | Prometheus, Grafana, Blackbox Exporter | Full monitoring stack with speedtests [^2] |
| [famesjranko/docker-network-monitor-dash](https://github.com/famesjranko/docker-network-monitor-dash) | Python, SQLite, Grafana | Lightweight, logs success rate and latency [^3] |

### ⚠️ Critical Flaws and Considerations

1. **Ping Overhead and Rate Limits**:
   - Pinging every second is aggressive and may trigger rate limiting (especially with ICMP). Consider 5–10 second intervals instead [^7].
   - Use multiple targets (e.g., `8.8.8.8`, `1.1.1.1`, `google.com`) to avoid false positives from a single host being down.

2. **Python Cron vs Long-Running Container**:
   - A cron job adds overhead and complexity (missed runs, logging). Prefer a **long-running Python container** with a loop (e.g., `while True: ping(); sleep(5)`) for reliability [^4][^6].

3. **Clock Drift & Uptime Tracking**:
   - If your host reboots, ensure your containers restart automatically (`restart: unless-stopped` in Docker).
   - Consider logging timestamps in UTC to avoid local clock issues.

4. **Database Choice**:
   - **InfluxDB** is optimized for time-series and integrates seamlessly with Grafana.
   - Avoid SQLite for high-frequency writes unless the interval is >10s [^3].

5. **Visualization**:
   - Grafana dashboards can show:
     - Uptime percentage (via `up` metric)
     - Latency trends
     - Packet loss over time
     - Outage detection (e.g., >30s downtime)

6. **Alternative: Blackbox Exporter**
   - Instead of writing your own ping script, consider **Prometheus Blackbox Exporter**, which supports ICMP ping, HTTP checks, and TLS expiry [^2][^5].

### 🔧 Suggested Stack
```yaml
# docker-compose.yml (simplified)
services:
  ping-monitor:
    build: ./ping-script
    restart: unless-stopped

  influxdb:
    image: influxdb:alpine
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    restart: unless-stopped
```

### ✅ Final Recommendations
- Start with a proven template (e.g., [geerlingguy/internet-monitoring](https://github.com/geerlingguy/internet-monitoring)) and customize it [^2].
- Use Blackbox Exporter or a lightweight Python script with exponential backoff on errors.
- Visualize in Grafana with alerts for prolonged outages.
- Log to InfluxDB for scalability and retention policies.
- Avoid pinging faster than every 5 seconds to prevent noise and throttling.

This approach will give you a robust, maintainable system for tracking and proving internet reliability issues.

[^1]: [GitHub - bmateusz/ping-monitor: A Docker-based network monitoring ...](https://github.com/bmateusz/ping-monitor) (22%)
[^2]: [GitHub - geerlingguy/internet-monitoring: Monitor your network and ...](https://github.com/geerlingguy/internet-monitoring) (20%)
[^3]: [GitHub - famesjranko/docker-network-monitor-dash: Monitors internet ...](https://github.com/famesjranko/docker-network-monitor-dash) (16%)
[^4]: [raynigon/ping-monitor: Simple Setup to Monitor Ping Responses](https://github.com/raynigon/ping-monitor) (15%)
[^5]: [GitHub - thomaschaplin/internet-monitoring: Monitor your network and ...](https://github.com/thomaschaplin/internet-monitoring) (10%)
[^6]: [A docker container for monitoring connections using ping and ... - GitHub](https://github.com/ManuelWiese/connectivity-monitor) (7%)
[^7]: [Measuring internet consistency with speedtest.net, plotly and docker](https://medium.com/@metahertz/measuring-internet-consistency-with-speedtest-net-plotly-and-docker-95f30a132574) (6%)
[^8]: [Easy speedtest + network monitor based on docker-compose - GitHub](https://github.com/jamesjarvis/network-monitor) (4%)

## alerting

> What would I need to consider when I wanted to add some sort of alerting, e.g. when the internet access is down. The alerting should work over the local network / wifi.

Adding local network alerting for internet outages is feasible but comes with important constraints and design considerations, especially when relying solely on local infrastructure. Below are key factors to consider and practical recommendations:

### ⚠️ Critical Constraints

1. **Alert Delivery Requires an Independent Path**:
   - If the internet is down, cloud-based notification services (e.g., email, push via Firebase, Telegram bots) won’t work unless your phone is on cellular.
   - For local-only alerts, you need a system that operates **independently of internet connectivity** but still reaches your devices [^1].

2. **Device Availability**:
   - Your alerting host (e.g., a Raspberry Pi or server) must remain powered and connected to the local network.
   - Use a UPS to ensure it stays online during brief outages or power fluctuations [^6].

### ✅ Recommended Alerting Strategies

| Method | How It Works | Pros | Cons |
|-------|-------------|------|------|
| **Local Push via Home Assistant or Node-RED** | Use a self-hosted automation platform to detect outages and send local push notifications (e.g., via mobile app or local HTTP call) [^2][^4]. | Works offline; integrates with smart home devices | Requires setup and maintenance |
| **Network-Wide Ping Monitoring** | Run a service on your LAN that pings external IPs. If ping fails, trigger a local alert (e.g., sound, LED, or message to local devices) [^3]. | Simple to implement; low overhead | May generate false positives |
| **Local Messaging (e.g., MQTT + Mobile App)** | Use MQTT broker (e.g., Mosquitto) on your LAN. When outage detected, publish alert to a topic. A local app (e.g., MQTT Dashboard on phone) receives it over Wi-Fi [^1]. | Fully offline-capable; real-time | Requires user to install apps |
| **Router-Based Alerts** | Some routers (e.g., UniFi, TP-Link) support outage alerts via email or app notifications [^7][^8]. | Built-in; easy to configure | Limited flexibility; may depend on internet for delivery |

### 🛠 Implementation Tips

- **Use a Reliable Monitoring Script**: Extend your existing `ping` script to check connectivity and publish to MQTT or trigger a local webhook.
- **Leverage Existing Tools**:
  - **Home Assistant**: Can detect internet loss and send local notifications to mobile app even when internet is down (using local push) [^2].
  - **Node-RED**: Flow-based tool ideal for routing outage events to multiple local outputs.
  - **Prometheus + Alertmanager**: If already using Prometheus, configure Alertmanager to send alerts via local webhooks or MQTT.
- **Fallback Alerts**: If internet is restored after an outage, send a "back online" notification to confirm recovery [^5].

### 📱 Example: Local Alert via MQTT

1. Run Mosquitto broker in Docker.
2. Modify your Python ping script to publish `"down"` or `"up"` to `home/network/status`.
3. Install MQTT Dashboard app on your phone (connected to same Wi-Fi).
4. Configure app to listen to the topic and show pop-up or sound.

This setup works entirely without internet and is ideal for local awareness.

### ✅ Summary
To implement effective local alerting:
- Ensure your monitoring system is resilient (UPS, local power).
- Use local messaging (MQTT, Home Assistant) for true offline alerts.
- Avoid reliance on cloud services for critical outage notifications.
- Test failover and recovery alerts thoroughly.

With these strategies, you can build a reliable, self-contained alerting system that works even when the internet is down.

[^1]: [How to monitor home network & get alerts if internet connection goes ...](https://www.reddit.com/r/selfhosted/comments/16e8sz5/how_to_monitor_home_network_get_alerts_if/) (30%)
[^2]: [How would I log actions that occur during an internet outage and send ...](https://community.home-assistant.io/t/how-would-i-log-actions-that-occur-during-an-internet-outage-and-send-notifications-to-my-mobile-once-internet-is-back-up/70755) (16%)
[^3]: [Best way to be alerted of a power outage. : r/HomeNetworking](https://www.reddit.com/r/HomeNetworking/comments/1bkna6y/best_way_to_be_alerted_of_a_power_outage/) (15%)
[^4]: [Is there a way to get a message or a notification every time my home ...](https://www.reddit.com/r/homeautomation/comments/t54hdv/is_there_a_way_to_get_a_message_or_a_notification/) (12%)
[^5]: [How do I track internet downtime? - Home Assistant Community](https://community.home-assistant.io/t/how-do-i-track-internet-downtime/411988) (10%)
[^6]: [Notification when internet is down : r/homeautomation - Reddit](https://www.reddit.com/r/homeautomation/comments/163ivr5/notification_when_internet_is_down/) (7%)
[^7]: [How to configure Connection Alerts on Tether... | TP-Link Deutschland](https://www.tp-link.com/ch/support/faq/2916/) (7%)
[^8]: [How can I setup alerts for when internet is down?](https://community.ui.com/questions/How-can-I-setup-alerts-for-when-internet-is-down/1b883a07-5c72-42ef-a2f6-593035210698) (3%)

## mqtt apps

> Fascinating. Are there android and ios MQTT apps that I could use for the alerting in this sort of setup?

Yes, there are several reliable MQTT client apps available for both Android and iOS that can be used for local network alerting in your internet monitoring setup. These apps can receive messages from your local MQTT broker (e.g., Mosquitto) over Wi-Fi, even when the internet is down, making them ideal for offline alerting.

### 🔹 Recommended Apps

#### **Android**

- **[MQTT Alert for IoT](https://play.google.com/store/apps/details?id=gigiosoft.MQTTAlert&hl=en)** [^2]
  - Lightweight app designed specifically for triggering phone notifications based on MQTT messages (e.g., door open, temperature change).
  - Supports persistent connections and background operation.

- **[MQTT Client – IoT & Automation](https://play.google.com/store/apps/details?id=com.shan.livemq&hl=en-US)** [^1]
  - Feature-rich client for advanced users and automation.
  - Allows subscription to topics, message logging, and notification triggers.

- **[MQTT Dash](https://play.google.com/store/apps/details?id=net.routix.mqttdash&hl=de)** [^3]
  - Designed for smart home and IoT monitoring.
  - Displays real-time data and can trigger alerts; supports secure connections (TLS) and authentication.

#### **iOS**

- **[RadioShuttle MQTT Push Client](https://github.com/RadioShuttle/MQTTPushClient_iOS)** [^4][^6]
  - Allows receiving MQTT messages as push notifications via Apple’s Push Notification service (APNs).
  - Works with a public relay server (radioshuttle.de), which connects to your local MQTT broker and forwards messages securely.
  - Notifications arrive within seconds, even if the app is not running.
  - Web interface for dashboard-style monitoring [^5].

- **Alternative: Use Home Assistant App**
  - If you’re using Home Assistant as part of your stack, its iOS app can receive local push notifications without internet when connected to the same network (via local push proxy).

### 🛠 Setup Tips

- Ensure your MQTT broker (e.g., Mosquitto) is accessible on the local network.
- Use retained messages for critical alerts so the app receives them immediately upon reconnect.
- Configure your ping monitor to publish to a topic like `home/network/status` with payload `down` or `up`.
- For iOS, if you prefer fully local operation without cloud relays, consider running a local web-based dashboard with WebSocket support and using a browser-based MQTT client.

These apps provide a robust foundation for receiving real-time, local-network-based alerts without relying on internet connectivity.

[^1]: [MQTT Client– IoT & Automation - Apps on Google Play](https://play.google.com/store/apps/details?id=com.shan.livemq&hl=en-US) (25%)
[^2]: [MQTT Alert for IOT - Apps on Google Play](https://play.google.com/store/apps/details?id=gigiosoft.MQTTAlert&hl=en) (23%)
[^3]: [MQTT Dash (IoT, Smart Home) – Apps bei Google Play](https://play.google.com/store/apps/details?id=net.routix.mqttdash&hl=de) (21%)
[^4]: [RadioShuttle MQTT Push Client app for iOS - GitHub](https://github.com/RadioShuttle/MQTTPushClient_iOS) (12%)
[^5]: [MQTT Push Client (App) | RadioShuttle Network Protocol](https://www.radioshuttle.de/en/mqtt-en/mqtt-push-client-app/) (11%)
[^6]: [MQTTPushClient_iOS/README.md at master - GitHub](https://github.com/RadioShuttle/MQTTPushClient_iOS/blob/master/README.md) (8%)

## network accessibility of mqtt broker when running on macos

> Assuming I'm running the docker containers on my MacBook, including the MQTT broker, could I make that accessible on the local network?

Yes, you can make your Docker containers—including an MQTT broker—accessible on the local network when running on your MacBook, but it requires specific configuration due to how Docker Desktop for macOS operates.

### 🔧 Why It’s Not Automatic
Docker on macOS runs inside a lightweight virtual machine (VM), which means:
- Container ports are not directly exposed to the host or local network by default.
- Even with `ports` mapping in `docker-compose.yml`, the service may only be reachable from the host (MacBook) itself, not other devices on the LAN [^1][^3].

### ✅ Solutions to Enable LAN Access

#### 1. **Port Forwarding via `docker-compose.yml`**
Ensure your MQTT broker (e.g., Mosquitto) exposes its port to the host:
```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
      - "9001:9001" # WebSockets (optional)
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
```
Then, other devices can connect to your MacBook’s **local IP** (e.g., `192.168.1.100:1883`) [^2].

#### 2. **Enable Host Network Access**
Use `host.docker.internal` in your config if the broker needs to reference the host. For example, in Mosquitto config:
```
listener 1883
bind_address 0.0.0.0
```
This allows binding to all interfaces, including those reachable over LAN.

#### 3. **Use `socat` for Advanced Forwarding** [^5]
If direct port mapping doesn’t work, use `socat` to forward traffic from the host to the Docker VM:
```bash
socat TCP-LISTEN:1883,fork,reuseaddr TCP:host.docker.internal:1883 &
```
Run this on the host (Mac) to forward incoming LAN connections to the container.

#### 4. **Use `docker-mac-net-connect` for Full Network Bridging** [^4]
This tool leverages WireGuard to bridge the Docker VM network with the host, making containers directly reachable on the LAN. It’s more complex but offers full network integration.

### 📱 Testing Connectivity
From another device on the same Wi-Fi:
```bash
mosquitto_sub -h <your-macbook-ip> -t "home/network/status" -v
```
If you receive messages, your setup is working.

### ⚠️ Notes
- Your MacBook must be powered on and connected to the network.
- Disable macOS firewall for the port if blocking occurs (System Settings > Privacy & Security > Firewall).
- Avoid using `--net=host`—it’s not supported on Docker Desktop for Mac [^1].

With proper port exposure and networking setup, your MQTT broker will be accessible to Android/iOS apps on the local network—even during internet outages.

[^1]: [Docker on macOS: How to Expose Container Ports to Host Machine (Fix for ...](https://www.codegenes.net/blog/docker-macosx-expose-container-ports-to-host-machine/) (31%)
[^2]: [How to make MQTT broker docker image accessible to devices in LAN?](https://stackoverflow.com/questions/64810427/how-to-make-mqtt-broker-docker-image-accessible-to-devices-in-lan) (22%)
[^3]: [Access from Local Network](https://forums.docker.com/t/access-from-local-network/133079) (20%)
[^4]: [Making Your Docker Network Reachable In MacOS](https://medium.com/@tylerauerbeck/making-your-docker-network-reachable-in-osx-e68f998f8249) (16%)
[^5]: [Using socat to enable LAN access to Docker ports on a Mac](https://medium.com/@nitride_speeder.9o/using-socat-to-enable-lan-access-to-docker-ports-on-a-mac-afbdde047779) (11%)


## Todos

- [ ] try https://github.com/geerlingguy/internet-pi/tree/master/internet-monitoring - seems like it could already be the solution - with some tweaks
- [ ] add mqtt / mobile app notification