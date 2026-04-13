import logging
from typing import TypedDict

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
