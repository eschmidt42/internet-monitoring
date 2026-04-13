import pytest


def pytest_configure(config):
    """Set MQTT_HOST before mqtt_bridge.service is imported (it reads it at module level)."""
    import os

    os.environ.setdefault("MQTT_HOST", "test-broker")


@pytest.fixture(autouse=True)
def mqtt_defaults(monkeypatch: pytest.MonkeyPatch):
    """Reset module-level MQTT config to known defaults for every test."""
    monkeypatch.setattr("mqtt_bridge.service.MQTT_HOST", "test-broker")
    monkeypatch.setattr("mqtt_bridge.service.MQTT_PORT", 1883)
    monkeypatch.setattr("mqtt_bridge.service.MQTT_TOPIC", "home/network/status")
    monkeypatch.setattr("mqtt_bridge.service.MQTT_USER", None)
    monkeypatch.setattr("mqtt_bridge.service.MQTT_PASSWORD", None)


@pytest.fixture()
def client():
    from mqtt_bridge.service import app

    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
