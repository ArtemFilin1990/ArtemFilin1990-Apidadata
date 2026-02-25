"""Menu flow tests for Telegram bot handlers."""

import importlib
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock


_ENV_DEFAULTS = {
    "TELEGRAM_BOT_TOKEN": "0000000000:test_placeholder_token_for_tests",
    "TELEGRAM_WEBHOOK_URL": "https://example.com/tg/test-secret-path",
    "DADATA_API_KEY": "test_api_key",
    "DADATA_SECRET_KEY": "test_secret_key",
}


def _reload_tg_bot():
    for key, value in _ENV_DEFAULTS.items():
        os.environ[key] = value
    sys.modules.pop("tg_bot", None)
    sys.modules.pop("config", None)
    mod = importlib.import_module("tg_bot")
    # Inject a mock bot so handlers don't hit the real Telegram API
    mock = MagicMock()
    mod.set_bot(mock)
    return mod


def test_start_sends_main_menu() -> None:
    tg_bot = _reload_tg_bot()

    message = SimpleNamespace(chat=SimpleNamespace(id=123))
    tg_bot.handle_start(message)

    tg_bot.get_bot().send_message.assert_called_once()
    args, kwargs = tg_bot.get_bot().send_message.call_args
    assert args[0] == 123
    assert "Выберите действие" in args[1]
    assert kwargs["reply_markup"].to_dict() == tg_bot.keyboards.main_menu().to_dict()


def test_main_callback_returns_main_menu() -> None:
    tg_bot = _reload_tg_bot()

    call = SimpleNamespace(
        id="cb-1",
        data="m:main",
        message=SimpleNamespace(chat=SimpleNamespace(id=777)),
    )

    tg_bot.handle_menu(call)

    tg_bot.get_bot().send_message.assert_called_once()
    args, kwargs = tg_bot.get_bot().send_message.call_args
    assert args[0] == 777
    assert "Главное меню" in args[1]
    assert kwargs["reply_markup"].to_dict() == tg_bot.keyboards.main_menu().to_dict()
    tg_bot.get_bot().answer_callback_query.assert_called_once_with("cb-1")


def test_other_callback_opens_tools_menu() -> None:
    tg_bot = _reload_tg_bot()

    call = SimpleNamespace(
        id="cb-2",
        data="m:other",
        message=SimpleNamespace(chat=SimpleNamespace(id=777)),
    )

    tg_bot.handle_menu(call)

    tg_bot.get_bot().send_message.assert_called_once()
    args, kwargs = tg_bot.get_bot().send_message.call_args
    assert args[0] == 777
    assert args[1] == "Выберите инструмент:"
    assert kwargs["reply_markup"].to_dict() == tg_bot.keyboards.other_tools_menu().to_dict()
    tg_bot.get_bot().answer_callback_query.assert_called_once_with("cb-2")


def test_ooo_flow_uses_legal_type_and_main_branch() -> None:
    tg_bot = _reload_tg_bot()

    call = SimpleNamespace(
        id="cb-3",
        data="m:ooo",
        message=SimpleNamespace(chat=SimpleNamespace(id=999)),
    )
    tg_bot.handle_menu(call)

    tg_bot.ds.find_party = MagicMock(return_value={"data": {"inn": "7707083893"}})
    tg_bot.handle_text(SimpleNamespace(chat=SimpleNamespace(id=999), text="7707083893"))

    tg_bot.ds.find_party.assert_called_once_with(
        "7707083893",
        type="LEGAL",
        branch_type="MAIN",
    )


def test_npd_tool_validates_12_digit_inn() -> None:
    tg_bot = _reload_tg_bot()
    tg_bot._set_state(555, "tool", "npd")

    tg_bot.handle_text(SimpleNamespace(chat=SimpleNamespace(id=555), text="7707083893"))

    tg_bot.get_bot().send_message.assert_called()
    args, _ = tg_bot.get_bot().send_message.call_args
    assert "12 цифр" in args[1]
