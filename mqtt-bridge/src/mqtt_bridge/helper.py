import logging
from collections.abc import Mapping
from typing import TypedDict, cast

import paho.mqtt.publish as paho_publish

logger = logging.getLogger(__name__)


class AuthParameter(TypedDict, total=False):
    username: str
    password: str | None


def mqtt_auth(*, user: str | None, password: str | None) -> AuthParameter | None:
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
    auth = mqtt_auth(user=user, password=password)
    paho_publish.single(
        topic=topic,
        payload=payload,
        hostname=host,
        port=port,
        auth=auth,  # ty: ignore
        retain=True,
    )
    logger.info("Published '%s' to %s", payload, topic)


# Only treat connectivity-loss alerts as "down"; warnings (e.g. HighLatency)
# are informational and should not trigger an outage notification.
def is_outage(alert: Mapping[str, object]) -> bool:

    labels = alert.get("labels", {})

    if not isinstance(labels, dict):
        return False

    labels_map = cast(Mapping[str, object], labels)

    return alert.get("status") == "firing" and (
        labels_map.get("alertname") == "InternetDown"
        or labels_map.get("severity") == "critical"
    )
