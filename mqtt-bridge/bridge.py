"""
Alertmanager webhook → MQTT bridge.

Receives POST /alert from Alertmanager and publishes a message to the
configured MQTT topic so mobile apps subscribed on the LAN are notified.

Payload published:
  "down"    — when one or more alerts are firing
  "up"      — when all alerts have resolved
"""

import os
import logging
from flask import Flask, request, jsonify
import paho.mqtt.publish as publish

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "home/network/status")
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")


def _mqtt_auth():
    if MQTT_USER and MQTT_PASSWORD:
        return {"username": MQTT_USER, "password": MQTT_PASSWORD}
    return None


def _publish(payload: str):
    auth = _mqtt_auth()
    publish.single(
        topic=MQTT_TOPIC,
        payload=payload,
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        auth=auth,
        retain=True,
    )
    logger.info("Published '%s' to %s", payload, MQTT_TOPIC)


@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json(force=True, silent=True) or {}
    alerts = data.get("alerts", [])

    # Only treat connectivity-loss alerts as "down"; warnings (e.g. HighLatency)
    # are informational and should not trigger an outage notification.
    def _is_outage(alert):
        labels = alert.get("labels", {})
        return (
            alert.get("status") == "firing"
            and (
                labels.get("alertname") == "InternetDown"
                or labels.get("severity") == "critical"
            )
        )

    payload = "down" if any(_is_outage(a) for a in alerts) else "up"

    try:
        _publish(payload)
    except Exception as exc:
        logger.error("MQTT publish failed: %s", exc)
        return jsonify({"error": str(exc)}), 502

    return jsonify({"status": "ok", "published": payload}), 200


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
