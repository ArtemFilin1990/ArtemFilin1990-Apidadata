"""Tests for the Telegram webhook endpoint."""
import importlib
import json
import os
import sys
from threading import Event

# Set required ENV vars before any app imports so validate() passes.
_ENV_DEFAULTS = {
    "TELEGRAM_BOT_TOKEN": "0000000000:test_placeholder_token_for_tests",
    "TELEGRAM_WEBHOOK_URL": "https://example.com/tg/test-secret-path",
    "DADATA_API_KEY": "test_api_key",
    "DADATA_SECRET_KEY": "test_secret_key",
    "POLLING_MODE": "0",
}
for _k, _v in _ENV_DEFAULTS.items():
    os.environ[_k] = _v

from unittest.mock import MagicMock, patch  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


_START_UPDATE = {
    "update_id": 1001,
    "message": {
        "message_id": 1,
        "from": {"id": 42, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 42, "type": "private"},
        "date": 1700000000,
        "text": "/start",
    },
}

_TEXT_UPDATE = {
    "update_id": 1002,
    "message": {
        "message_id": 2,
        "from": {"id": 42, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 42, "type": "private"},
        "date": 1700000001,
        "text": "hello",
    },
}


def _set_webhook_env() -> None:
    for key, value in _ENV_DEFAULTS.items():
        os.environ[key] = value


def _reload_app_with_mock():
    """Reload app and tg_bot modules, inject a mock bot, return (app_module, mock_bot)."""
    _set_webhook_env()
    sys.modules.pop("app", None)
    sys.modules.pop("config", None)
    sys.modules.pop("tg_bot", None)

    mock_bot = MagicMock()
    mock_bot.set_webhook.return_value = None
    mock_bot.remove_webhook.return_value = None

    # Import tg_bot first and inject mock before app imports it
    tg_bot_mod = importlib.import_module("tg_bot")
    tg_bot_mod.set_bot(mock_bot)

    app_module = importlib.import_module("app")
    return app_module, mock_bot


def test_webhook_returns_200_for_start_command() -> None:
    """/tg/webhook must return 200 for a valid /start update."""
    app_module, mock_bot = _reload_app_with_mock()
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/tg/test-secret-path",
            content=json.dumps(_START_UPDATE),
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 200


def test_webhook_returns_200_for_text_message() -> None:
    """/tg/webhook must return 200 for a plain text message."""
    app_module, mock_bot = _reload_app_with_mock()
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/tg/test-secret-path",
            content=json.dumps(_TEXT_UPDATE),
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 200


def test_webhook_calls_process_new_updates() -> None:
    """process_new_updates must be called with the parsed update."""
    app_module, mock_bot = _reload_app_with_mock()
    called = Event()

    def _side_effect(updates: list) -> None:
        called.set()

    mock_bot.process_new_updates.side_effect = _side_effect

    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        client.post(
            "/tg/test-secret-path",
            content=json.dumps(_START_UPDATE),
            headers={"Content-Type": "application/json"},
        )
        assert called.wait(timeout=2.0), "process_new_updates was not called within 2 s"

    mock_bot.process_new_updates.assert_called_once()
    updates_arg = mock_bot.process_new_updates.call_args[0][0]
    assert len(updates_arg) == 1
    assert updates_arg[0].update_id == 1001


def test_lifespan_sets_webhook() -> None:
    """Startup must call set_webhook with the configured URL."""
    import time
    app_module, mock_bot = _reload_app_with_mock()
    with TestClient(app_module.app, raise_server_exceptions=False):
        # Give the daemon thread a moment to run
        time.sleep(0.5)

    mock_bot.set_webhook.assert_called_once_with(url="https://example.com/tg/test-secret-path")
