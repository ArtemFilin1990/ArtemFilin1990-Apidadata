"""Telegram bot setup and handlers."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import telebot

import config
from services import dadata_service as ds
from services.inn_utils import normalize_inn, validate_inn
from ui import formatters
from ui import keyboards

logger = logging.getLogger(__name__)

TELEGRAM_STARTUP_DELAY_SECONDS = float(os.getenv("TELEGRAM_STARTUP_DELAY_SECONDS", "0"))
if TELEGRAM_STARTUP_DELAY_SECONDS > 0:
    time.sleep(TELEGRAM_STARTUP_DELAY_SECONDS)

# --- Deferred bot creation ---------------------------------------------------
# pyTelegramBotAPI validates the token at construction time.  When the module is
# imported during test collection or before environment variables are set the
# token may still be empty, which raises ``ValueError``.  We therefore create
# the bot lazily: the first call to ``get_bot()`` builds the real instance and
# all subsequent calls return the cached one.

_bot: telebot.TeleBot | None = None
_handlers_registered: bool = False


def get_bot() -> telebot.TeleBot:
    """Return the TeleBot singleton, creating it on first call."""
    global _bot, _handlers_registered
    if _bot is None:
        token = config.TELEGRAM_BOT_TOKEN
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set — cannot create TeleBot instance"
            )
        _bot = telebot.TeleBot(token, parse_mode="HTML")
        logger.info("TeleBot instance created successfully")
    if not _handlers_registered:
        _register_handlers(_bot)
        _handlers_registered = True
    return _bot


def set_bot(instance: Any) -> None:
    """Replace the bot singleton (used by tests to inject a mock)."""
    global _bot, _handlers_registered
    _bot = instance
    _handlers_registered = False


# Module-level ``bot`` attribute for backward compatibility.
# ``app.py`` does ``from tg_bot import bot``.
# Tests do ``tg_bot.bot.send_message = MagicMock()`` or ``patch("tg_bot.bot", ...)``.
# We use a module-level property via __getattr__/__setattr__ on the module isn't
# possible in Python, so we use a simple proxy object instead.

class _BotProxy:
    """Transparent proxy that forwards attribute access to the lazily created
    ``TeleBot`` instance.  Supports attribute assignment so tests can do
    ``tg_bot.bot.send_message = MagicMock()``."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_bot(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(get_bot(), name, value)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<_BotProxy wrapping {_bot!r}>"


bot = _BotProxy()  # type: ignore[assignment]

_user_state: dict[int, tuple[str, str]] = {}


def _set_state(chat_id: int, kind: str | None, value: str | None = None) -> None:
    if kind is None:
        _user_state.pop(chat_id, None)
    else:
        _user_state[chat_id] = (kind, value or "")


def _send_chunks(chat_id: int, text: str, reply_markup: Any | None = None) -> None:
    chunks = formatters.chunk_text(text)
    for idx, chunk in enumerate(chunks):
        get_bot().send_message(chat_id, chunk, reply_markup=reply_markup if idx == 0 else None)


def _safe_party(inn: str, type_filter: str | None = None) -> dict | None:
    try:
        return ds.find_party(inn, type=type_filter)
    except Exception:
        logger.exception("find_party failed for %s", inn)
        return None


def _safe_affiliated(inn: str) -> list[dict]:
    try:
        return ds.find_affiliated(inn)
    except Exception:
        logger.exception("find_affiliated failed for %s", inn)
        return []


# ---------------------------------------------------------------------------
#  Handler functions
# ---------------------------------------------------------------------------

def _handle_start(message: telebot.types.Message) -> None:
    _set_state(message.chat.id, None)
    get_bot().send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=keyboards.main_menu(),
    )


def _handle_menu(call: telebot.types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    action = call.data.split(":", 1)[1]
    _set_state(chat_id, None)

    if action == "main":
        get_bot().send_message(
            chat_id,
            "Главное меню:",
            reply_markup=keyboards.main_menu(),
        )
    elif action in {"ooo", "ip"}:
        prompt = "Введите ИНН или ОГРН компании." if action == "ooo" else "Введите ИНН/ОГРНИП для ИП."
        _set_state(chat_id, "party", action)
        get_bot().send_message(chat_id, prompt)
    elif action == "person":
        _set_state(chat_id, "person", "")
        get_bot().send_message(chat_id, "Введите ИНН физлица (12 цифр).")
    elif action == "search":
        _set_state(chat_id, "search", "")
        get_bot().send_message(chat_id, "Введите название компании для поиска.")
    elif action == "other":
        get_bot().send_message(chat_id, "Выберите инструмент:", reply_markup=keyboards.other_tools_menu())

    get_bot().answer_callback_query(call.id)


def _handle_tool_prompt(call: telebot.types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    tool = call.data.split(":", 1)[1]
    _set_state(chat_id, "tool", tool)

    prompts = {
        "phone": "Введите телефон в свободном формате.",
        "auto": "Введите марку и модель авто (например, форд фокус).",
        "email": "Введите email.",
        "address": "Введите адрес строкой.",
        "bank": "Введите БИК, ИНН или название банка.",
        "fio": "Введите ФИО целиком.",
        "passport": "Введите серию и номер паспорта РФ.",
        "iplocate": "Введите IP-адрес.",
        "geolocate": "Введите координаты 'lat,lon' (через запятую).",
        "suggest_address": "Введите начало адреса для подсказок.",
    }
    get_bot().send_message(chat_id, prompts.get(tool, "Введите запрос."))
    get_bot().answer_callback_query(call.id)


def _handle_company_action(call: telebot.types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    _, action, inn = call.data.split(":", 2)
    party = _safe_party(inn)
    if party is None:
        get_bot().answer_callback_query(call.id, "Не найдено")
        return

    if action == "tax":
        text = formatters.fmt_taxes(party)
    elif action == "debt":
        text = formatters.fmt_debts(party)
    elif action == "court":
        text = formatters.fmt_courts(party)
    elif action == "aff":
        text = formatters.fmt_affiliated(_safe_affiliated(inn))
    elif action == "more":
        get_bot().send_message(chat_id, "Дополнительно:", reply_markup=keyboards.company_more(inn))
        get_bot().answer_callback_query(call.id)
        return
    elif action == "founders":
        text = formatters.fmt_founders(party)
    elif action == "managers":
        text = formatters.fmt_managers(party)
    elif action == "finance":
        text = formatters.fmt_finance(party)
    elif action == "licenses":
        text = formatters.fmt_licenses(party)
    elif action == "contacts":
        text = formatters.fmt_contacts(party)
    elif action == "docs":
        text = formatters.fmt_docs(party)
    elif action == "json":
        text = f"<pre>{formatters.h(json.dumps(party, ensure_ascii=False, indent=2))}</pre>"
    elif action == "back":
        get_bot().send_message(chat_id, "Действия:", reply_markup=keyboards.company_actions(inn))
        get_bot().answer_callback_query(call.id)
        return
    else:
        text = "Неизвестное действие."

    _send_chunks(chat_id, text)
    get_bot().answer_callback_query(call.id)


def _format_party_response(party: dict) -> tuple[str, Any]:
    inn = (party.get("data") or {}).get("inn") or ""
    keyboard = keyboards.company_actions(inn) if inn else None
    return formatters.fmt_party_card(party), keyboard


def _handle_text(message: telebot.types.Message) -> None:
    chat_id = message.chat.id
    text = (message.text or "").strip()
    state = _user_state.get(chat_id)

    if state and state[0] == "party":
        type_filter = "LEGAL" if state[1] == "ooo" else "INDIVIDUAL"
        inn = normalize_inn(text)
        if not validate_inn(inn):
            get_bot().send_message(chat_id, "Некорректный ИНН/ОГРН.")
            return
        party = _safe_party(inn, type_filter=type_filter)
        if party:
            body, keyboard = _format_party_response(party)
            _send_chunks(chat_id, body, reply_markup=keyboard)
        else:
            get_bot().send_message(chat_id, "Не найдено в DaData.")
        _set_state(chat_id, None)
        return

    if state and state[0] == "person":
        inn = normalize_inn(text)
        if not validate_inn(inn):
            get_bot().send_message(chat_id, "Некорректный ИНН.")
            return
        fns_unit = ds.find_fns_unit(inn[:4]) if len(inn) >= 4 else None
        get_bot().send_message(chat_id, formatters.fmt_person_inn(inn, fns_unit))
        _set_state(chat_id, None)
        return

    if state and state[0] == "search":
        try:
            results = ds.suggest_party(text)
        except Exception:
            logger.exception("suggest_party failed for %s", text)
            get_bot().send_message(chat_id, "Сервис DaData временно недоступен. Попробуйте позже.")
            _set_state(chat_id, None)
            return
        _send_chunks(chat_id, formatters.fmt_suggest_party(results))
        _set_state(chat_id, None)
        return

    if state and state[0] == "tool":
        tool = state[1]
        try:
            if tool == "phone":
                res = ds.clean_resource("phone", text)
                reply = formatters.fmt_phone_clean(res)
            elif tool == "auto":
                res = ds.clean_resource("vehicle", text)
                reply = formatters.fmt_vehicle_clean(res)
            elif tool == "email":
                res = ds.clean_resource("email", text)
                reply = formatters.fmt_email_clean(res)
            elif tool == "address":
                res = ds.clean_resource("address", text)
                reply = formatters.fmt_address_clean(res)
            elif tool == "bank":
                reply = formatters.fmt_bank(ds.find_bank(text))
            elif tool == "fio":
                res = ds.clean_name(text)
                reply = formatters.fmt_name_clean(res)
            elif tool == "passport":
                res = ds.clean_passport(text)
                reply = formatters.fmt_passport_clean(res)
            elif tool == "iplocate":
                reply = formatters.fmt_iplocate(ds.iplocate(text))
            elif tool == "geolocate":
                parts = [p.strip() for p in text.replace(",", " ").split()]
                reply = "Введите координаты в формате lat,lon."
                if len(parts) >= 2:
                    try:
                        lat, lon = float(parts[0]), float(parts[1])
                        reply = formatters.fmt_geolocate(ds.geolocate_address(lat, lon))
                    except Exception:
                        reply = "Некорректные координаты."
            elif tool == "suggest_address":
                reply = formatters.fmt_suggest_address(ds.suggest_address(text))
            else:
                reply = "Неизвестный инструмент."
        except Exception:
            logger.exception("tool handler failed for %s", tool)
            reply = "Сервис DaData временно недоступен. Попробуйте позже."

        _send_chunks(chat_id, reply)
        _set_state(chat_id, None)
        return

    inn = normalize_inn(text)
    if validate_inn(inn):
        party = _safe_party(inn)
        if party:
            body, keyboard = _format_party_response(party)
            _send_chunks(chat_id, body, reply_markup=keyboard)
        else:
            get_bot().send_message(chat_id, "Не найдено в DaData.")
    else:
        get_bot().send_message(chat_id, "Я понимаю ИНН/ОГРН или команды /start, /help.")


# ---------------------------------------------------------------------------
#  Register all handlers on a TeleBot instance
# ---------------------------------------------------------------------------

def _register_handlers(b: telebot.TeleBot) -> None:
    b.message_handler(commands=["start", "help"])(_handle_start)
    b.callback_query_handler(func=lambda call: call.data.startswith("m:"))(_handle_menu)
    b.callback_query_handler(func=lambda call: call.data.startswith("t:"))(_handle_tool_prompt)
    b.callback_query_handler(func=lambda call: call.data.startswith("c:"))(_handle_company_action)
    b.message_handler(func=lambda message: True)(_handle_text)


# Expose handler functions under their original names for tests
handle_start = _handle_start
handle_menu = _handle_menu
handle_tool_prompt = _handle_tool_prompt
handle_company_action = _handle_company_action
handle_text = _handle_text
