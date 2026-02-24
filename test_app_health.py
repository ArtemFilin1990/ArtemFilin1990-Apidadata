"""Smoke test: FastAPI /health endpoint."""
import importlib
import os
import sys

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

from unittest.mock import MagicMock  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


def _reload_app_with_mock():
    """Reload app and tg_bot modules, inject a mock bot, return (app_module, mock_bot)."""
    for key, value in _ENV_DEFAULTS.items():
        os.environ[key] = value
    sys.modules.pop("app", None)
    sys.modules.pop("config", None)
    sys.modules.pop("tg_bot", None)

    mock_bot = MagicMock()
    mock_bot.set_webhook.return_value = None
    mock_bot.remove_webhook.return_value = None
    mock_bot.infinity_polling.return_value = None
    mock_bot.stop_polling.return_value = None

    tg_bot_mod = importlib.import_module("tg_bot")
    tg_bot_mod.set_bot(mock_bot)

    app_module = importlib.import_module("app")
    return app_module, mock_bot


def test_health_ok() -> None:
    """GET /health must return 200 with {status: ok}."""
    app_module, mock_bot = _reload_app_with_mock()
    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "webhook"
    assert "webhook_path" in data


def test_health_polling_mode_without_webhook_url() -> None:
    """GET /health must return polling mode when POLLING_MODE=1 and webhook URL is optional."""
    old_polling_mode = os.environ.get("POLLING_MODE")
    old_webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")

    try:
        # Set polling env BEFORE reload so config picks them up
        os.environ["POLLING_MODE"] = "1"
        os.environ["TELEGRAM_WEBHOOK_URL"] = ""

        sys.modules.pop("app", None)
        sys.modules.pop("config", None)
        sys.modules.pop("tg_bot", None)

        mock_bot = MagicMock()
        mock_bot.infinity_polling.return_value = None
        mock_bot.stop_polling.return_value = None
        mock_bot.remove_webhook.return_value = None

        tg_bot_mod = importlib.import_module("tg_bot")
        tg_bot_mod.set_bot(mock_bot)

        app_module = importlib.import_module("app")
        with TestClient(app_module.app, raise_server_exceptions=False) as client:
            response = client.get("/health")
    finally:
        if old_polling_mode is None:
            os.environ.pop("POLLING_MODE", None)
        else:
            os.environ["POLLING_MODE"] = old_polling_mode
        if old_webhook_url is None:
            os.environ.pop("TELEGRAM_WEBHOOK_URL", None)
        else:
            os.environ["TELEGRAM_WEBHOOK_URL"] = old_webhook_url

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "polling"
