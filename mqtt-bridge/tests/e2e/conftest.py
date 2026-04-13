import pytest


def pytest_configure(config):
    """Set MQTT_HOST before mqtt_bridge.bridge is imported (it reads it at module level)."""
    import os

    os.environ.setdefault("MQTT_HOST", "test-broker")


@pytest.fixture(autouse=True)
def mqtt_defaults(monkeypatch):
    """Reset module-level MQTT config to known defaults for every test."""
    monkeypatch.setattr("mqtt_bridge.bridge.MQTT_HOST", "test-broker")
    monkeypatch.setattr("mqtt_bridge.bridge.MQTT_PORT", 1883)
    monkeypatch.setattr("mqtt_bridge.bridge.MQTT_TOPIC", "home/network/status")
    monkeypatch.setattr("mqtt_bridge.bridge.MQTT_USER", None)
    monkeypatch.setattr("mqtt_bridge.bridge.MQTT_PASSWORD", None)


@pytest.fixture()
def client():
    from mqtt_bridge.bridge import app

    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
