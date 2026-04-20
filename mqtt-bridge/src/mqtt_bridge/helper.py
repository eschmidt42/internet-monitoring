import logging
from collections.abc import Mapping
from typing import TypedDict, cast

import paho.mqtt.publish as paho_publish

logger = logging.getLogger(__name__)


class AuthParameter(TypedDict, total=False):
    username: str
    password: str | None


def mqtt_auth(*, user: str | None, password: str | None) -> AuthParameter | None:
    """Build a paho auth dict if credentials are provided.

    Args:
        user (str | None): MQTT username, or None to skip authentication.
        password (str | None): MQTT password, or None to skip authentication.

    Returns:
        AuthParameter | None: A dict with ``username`` and ``password`` keys if
            both are provided, otherwise None.
    """
    if user and password:
        return {"username": user, "password": password}
    return None


def publish(
    payload: str,
    *,
    user: str | None,
    password: str | None,
    topic: str,
    host: str,
    port: int,
) -> None:
    """Publish an MQTT message, with optional authentication.

    Args:
        payload (str): The message payload to publish.
        user (str | None): MQTT username, or None to connect without authentication.
        password (str | None): MQTT password, or None to connect without authentication.
        topic (str): MQTT topic to publish to.
        host (str): Hostname or IP address of the MQTT broker.
        port (int): Port number of the MQTT broker.
    """
    auth = mqtt_auth(user=user, password=password)
    paho_publish.single(
        topic=topic,
        payload=payload,
        hostname=host,
        port=port,
        auth=auth,  # ty: ignore
        retain=False,
    )
    logger.info("Published '%s' to %s", payload, topic)


def is_outage(alert: Mapping[str, object]) -> bool:
    """Return True if the alert represents an active outage.

    Only connectivity-loss alerts (``InternetDown`` alertname or ``critical``
    severity) count as outages. Informational warnings such as ``HighLatency``
    are ignored.

    Args:
        alert (Mapping[str, object]): Alertmanager alert payload, expected to
            contain ``status`` and a nested ``labels`` mapping.

    Returns:
        bool: True if the alert is firing and matches an outage condition,
            False otherwise.
    """
    labels = alert.get("labels", {})

    if not isinstance(labels, dict):
        return False

    labels_map = cast(Mapping[str, object], labels)

    return alert.get("status") == "firing" and (
        labels_map.get("alertname") == "InternetDown"
        or labels_map.get("severity") == "critical"
    )
