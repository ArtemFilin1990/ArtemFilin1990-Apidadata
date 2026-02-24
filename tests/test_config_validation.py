"""Test config validation, especially token format checking."""
import os
import pytest
from unittest import mock


def test_validate_missing_required_vars():
    """Validate raises RuntimeError if required vars are missing."""
    with mock.patch.dict(os.environ, {}, clear=True):
        import config
        with pytest.raises(RuntimeError, match="Missing required ENV variables"):
            config.validate()


def test_validate_token_format_warning(caplog):
    """Validate warns if TELEGRAM_BOT_TOKEN has wrong format."""
    env = {
        "TELEGRAM_BOT_TOKEN": "invalid_token_format",
        "DADATA_API_KEY": "test_key",
        "DADATA_SECRET_KEY": "test_secret",
        "POLLING_MODE": "1",
    }
    with mock.patch.dict(os.environ, env, clear=True):
        # Force reload of config module to pick up new env vars
        import importlib
        import config
        importlib.reload(config)

        caplog.clear()
        config.validate()

        # Check that warning was logged
        assert any(
            "doesn't match expected format" in record.message
            for record in caplog.records
        ), "Expected token format warning not found in logs"


def test_validate_valid_token_format():
    """Validate doesn't warn if token has correct format."""
    env = {
        "TELEGRAM_BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
        "DADATA_API_KEY": "test_key",
        "DADATA_SECRET_KEY": "test_secret",
        "POLLING_MODE": "1",
    }
    with mock.patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)

        # Should not raise any exception
        config.validate()


def test_validate_webhook_url_format_warning(caplog):
    """Validate warns if webhook URL doesn't contain /tg/."""
    env = {
        "TELEGRAM_BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
        "TELEGRAM_WEBHOOK_URL": "https://example.com/webhook",  # Missing /tg/
        "DADATA_API_KEY": "test_key",
        "DADATA_SECRET_KEY": "test_secret",
        "POLLING_MODE": "0",  # webhook mode
    }
    with mock.patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)

        caplog.clear()
        config.validate()

        # Check that warning was logged
        assert any(
            "does not contain '/tg/'" in record.message
            for record in caplog.records
        ), "Expected webhook URL format warning not found in logs"


def test_validate_webhook_url_correct_format():
    """Validate doesn't warn if webhook URL contains /tg/."""
    env = {
        "TELEGRAM_BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
        "TELEGRAM_WEBHOOK_URL": "https://example.com/tg/secret",
        "DADATA_API_KEY": "test_key",
        "DADATA_SECRET_KEY": "test_secret",
        "POLLING_MODE": "0",
    }
    with mock.patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)

        # Should not raise any exception
        config.validate()


def test_validate_polling_mode_no_webhook_required():
    """In polling mode, TELEGRAM_WEBHOOK_URL is not required."""
    env = {
        "TELEGRAM_BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
        "DADATA_API_KEY": "test_key",
        "DADATA_SECRET_KEY": "test_secret",
        "POLLING_MODE": "1",
        # No TELEGRAM_WEBHOOK_URL
    }
    with mock.patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)

        # Should not raise any exception
        config.validate()
