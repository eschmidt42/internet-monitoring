"""Unit tests for mqtt_bridge.helper."""

from unittest.mock import MagicMock, patch

from mqtt_bridge.helper import mqtt_auth, publish

# ---------------------------------------------------------------------------
# mqtt_auth
# ---------------------------------------------------------------------------


class TestMqttAuth:
    def test_returns_auth_dict_when_both_credentials_provided(self) -> None:
        result = mqtt_auth(user="alice", password="secret")
        assert result == {"username": "alice", "password": "secret"}

    def test_returns_none_when_user_is_none(self) -> None:
        assert mqtt_auth(user=None, password="secret") is None

    def test_returns_none_when_password_is_none(self) -> None:
        assert mqtt_auth(user="alice", password=None) is None

    def test_returns_none_when_both_are_none(self) -> None:
        assert mqtt_auth(user=None, password=None) is None

    def test_returns_none_when_user_is_empty_string(self) -> None:
        assert mqtt_auth(user="", password="secret") is None

    def test_returns_none_when_password_is_empty_string(self) -> None:
        assert mqtt_auth(user="alice", password="") is None


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------


class TestPublish:
    def _publish(
        self,
        mock_single: MagicMock,
        *,
        payload: str = "up",
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        publish(
            payload,
            user=user,
            password=password,
            topic="home/network/status",
            host="broker",
            port=1883,
        )

    def test_calls_paho_single_with_correct_arguments(self) -> None:
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_single:
            self._publish(mock_single, payload="down")

        mock_single.assert_called_once_with(
            topic="home/network/status",
            payload="down",
            hostname="broker",
            port=1883,
            auth=None,
            retain=True,
        )

    def test_passes_auth_when_credentials_provided(self) -> None:
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_single:
            self._publish(mock_single, user="alice", password="secret")

        _, kwargs = mock_single.call_args
        assert kwargs["auth"] == {"username": "alice", "password": "secret"}

    def test_passes_no_auth_when_credentials_absent(self) -> None:
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_single:
            self._publish(mock_single)

        _, kwargs = mock_single.call_args
        assert kwargs["auth"] is None

    def test_retain_is_always_true(self) -> None:
        with patch("mqtt_bridge.helper.paho_publish.single") as mock_single:
            self._publish(mock_single)

        _, kwargs = mock_single.call_args
        assert kwargs["retain"] is True
