import logging

import paho.mqtt.publish as paho_publish

logger = logging.getLogger(__name__)


def mqtt_auth(*, user, password):
    if user and password:
        return {"username": user, "password": password}
    return None


def publish(payload: str, *, user, password, topic, host, port):
    auth = mqtt_auth(user=user, password=password)
    paho_publish.single(
        topic=topic,
        payload=payload,
        hostname=host,
        port=port,
        auth=auth,
        retain=True,
    )
    logger.info("Published '%s' to %s", payload, topic)
