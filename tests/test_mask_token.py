"""Tests for token masking utility."""
import os

# Set required ENV vars before any app imports so validate() passes.
_ENV_DEFAULTS = {
    "TELEGRAM_BOT_TOKEN": "0000000000:test_placeholder_token_for_tests",
    "TELEGRAM_WEBHOOK_URL": "https://example.com/tg/",
    "DADATA_API_KEY": "test_api_key",
    "DADATA_SECRET_KEY": "test_secret_key",
}
for _k, _v in _ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

from app import mask_token  # noqa: E402


def test_mask_token_replaces_bot_token() -> None:
    url = "https://api.ewerest.ru/tg/1234567890:ABCDEFGHIJ_klmnopqrstuvwxyz12345"
    assert "1234567890" not in mask_token(url)
    assert mask_token(url) == "https://api.ewerest.ru/tg/***"


def test_mask_token_preserves_plain_text() -> None:
    text = "https://api.ewerest.ru/tg/"
    assert mask_token(text) == text


def test_mask_token_hides_webhook_secret_path() -> None:
    text = "https://api.ewerest.ru/tg/super-secret-path"
    assert mask_token(text) == "https://api.ewerest.ru/tg/***"


def test_mask_token_empty_string() -> None:
    assert mask_token("") == ""
