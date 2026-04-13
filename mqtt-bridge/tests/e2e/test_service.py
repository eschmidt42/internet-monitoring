"""Unit tests for mqtt_bridge.service."""

from unittest.mock import patch

# ---------------------------------------------------------------------------
# /healthz
# ---------------------------------------------------------------------------


class TestHealthz:
    def test_returns_200_with_ok_status(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /alert – request validation
# ---------------------------------------------------------------------------


class TestAlertValidation:
    def test_non_json_body_returns_400(self, client):
        resp = client.post("/alert", data="not json", content_type="text/plain")
        assert resp.status_code == 400
        assert "valid JSON" in resp.get_json()["error"]

    def test_json_array_returns_400(self, client):
        resp = client.post("/alert", json=[])
        assert resp.status_code == 400
        assert "JSON object" in resp.get_json()["error"]

    def test_missing_alerts_key_returns_400(self, client):
        resp = client.post("/alert", json={})
        assert resp.status_code == 400
        assert "alerts" in resp.get_json()["error"]

    def test_alerts_not_a_list_returns_400(self, client):
        resp = client.post("/alert", json={"alerts": "firing"})
        assert resp.status_code == 400
        assert "'alerts' must be a list" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# /alert – payload classification
# ---------------------------------------------------------------------------


class TestAlertPayload:
    """Tests for the 'up'/'down' payload logic."""

    def _post(self, client, alerts):
        with patch("mqtt_bridge.helper.paho_publish.single"):
            return client.post("/alert", json={"alerts": alerts})

    def test_empty_alerts_publishes_up(self, client):
        resp = self._post(client, [])
        assert resp.status_code == 200
        assert resp.get_json()["published"] == "up"

    def test_internet_down_firing_publishes_down(self, client):
        alerts = [{"status": "firing", "labels": {"alertname": "InternetDown"}}]
        resp = self._post(client, alerts)
        assert resp.get_json()["published"] == "down"

    def test_critical_severity_firing_publishes_down(self, client):
        alerts = [{"status": "firing", "labels": {"severity": "critical"}}]
        resp = self._post(client, alerts)
        assert resp.get_json()["published"] == "down"

    def test_internet_down_resolved_publishes_up(self, client):
        alerts = [{"status": "resolved", "labels": {"alertname": "InternetDown"}}]
        resp = self._post(client, alerts)
        assert resp.get_json()["published"] == "up"

    def test_warning_alert_publishes_up(self, client):
        # HighLatency is firing but neither InternetDown nor critical – informational only.
        alerts = [
            {
                "status": "firing",
                "labels": {"alertname": "HighLatency", "severity": "warning"},
            }
        ]
        resp = self._post(client, alerts)
        assert resp.get_json()["published"] == "up"

    def test_any_outage_in_mixed_list_publishes_down(self, client):
        alerts = [
            {"status": "resolved", "labels": {"alertname": "InternetDown"}},
            {"status": "firing", "labels": {"alertname": "InternetDown"}},
        ]
        resp = self._post(client, alerts)
        assert resp.get_json()["published"] == "down"

    def test_mqtt_failure_returns_502(self, client):
        alerts = [{"status": "firing", "labels": {"alertname": "InternetDown"}}]
        with patch(
            "mqtt_bridge.helper.paho_publish.single",
            side_effect=Exception("connection refused"),
        ):
            resp = client.post("/alert", json={"alerts": alerts})
        assert resp.status_code == 502
        assert "connection refused" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# /alert – MQTT publish call
# ---------------------------------------------------------------------------


class TestMqttPublish:
    def test_publishes_with_correct_arguments(self, client):
        alerts = [{"status": "firing", "labels": {"alertname": "InternetDown"}}]
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_pub:
            client.post("/alert", json={"alerts": alerts})

        mock_pub.assert_called_once_with(
            topic="home/network/status",
            payload="down",
            hostname="test-broker",
            port=1883,
            auth=None,
            retain=True,
        )

    def test_publishes_with_auth_when_credentials_set(self, client, monkeypatch):
        monkeypatch.setattr("mqtt_bridge.service.MQTT_USER", "alice")
        monkeypatch.setattr("mqtt_bridge.service.MQTT_PASSWORD", "secret")

        alerts = [{"status": "firing", "labels": {"alertname": "InternetDown"}}]
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_pub:
            client.post("/alert", json={"alerts": alerts})

        _, kwargs = mock_pub.call_args
        assert kwargs["auth"] == {"username": "alice", "password": "secret"}

    def test_no_auth_when_only_user_set(self, client, monkeypatch):
        monkeypatch.setattr("mqtt_bridge.service.MQTT_USER", "alice")
        # MQTT_PASSWORD remains None (set by autouse fixture)

        alerts = [{"status": "firing", "labels": {"alertname": "InternetDown"}}]
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_pub:
            client.post("/alert", json={"alerts": alerts})

        _, kwargs = mock_pub.call_args
        assert kwargs["auth"] is None
