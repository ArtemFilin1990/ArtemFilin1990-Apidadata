"""Inline and reply keyboards for Telegram bot menus."""
from __future__ import annotations

"""Keyboard definitions for the Telegram bot UI.

This module attempts to import ``telebot.types`` to construct inline
keyboards compatible with the Telegram Bot API.  If the optional
``telebot`` dependency is not installed (for example, during unit
testing), fallback classes implementing a minimal subset of the
``telebot.types`` interface are defined.  These simple classes provide
``InlineKeyboardMarkup`` and ``InlineKeyboardButton`` objects with
attributes ``keyboard``, ``text`` and ``callback_data`` sufficient for
tests that inspect the structure of reply markups.  They do not
implement full Telegram API functionality but allow the UI functions
defined below to execute without raising ``ImportError``.
"""

# Attempt to import the real telebot types
try:
    from telebot import types  # type: ignore
except Exception:
    # Define minimal fallback classes to emulate telebot types
    class _FallbackInlineKeyboardButton:
        def __init__(self, text: str, callback_data: str) -> None:
            self.text = text
            self.callback_data = callback_data

        def to_dict(self) -> dict[str, str]:
            return {"text": self.text, "callback_data": self.callback_data}

    class _FallbackInlineKeyboardMarkup:
        def __init__(self, row_width: int = 2) -> None:
            self.row_width = row_width
            self.keyboard: list[list[_FallbackInlineKeyboardButton]] = []

        def add(self, *buttons: _FallbackInlineKeyboardButton) -> None:
            """Add a row of buttons to the keyboard."""
            self.keyboard.append(list(buttons))

        # Provide a similar interface as telebot types for iteration
        def to_dict(self) -> dict[str, list[list[dict[str, str]]]]:
            return {
                "inline_keyboard": [[btn.to_dict() for btn in row] for row in self.keyboard]
            }

    class types:  # type: ignore
        """Namespace containing fallback keyboard classes."""

        InlineKeyboardButton = _FallbackInlineKeyboardButton
        InlineKeyboardMarkup = _FallbackInlineKeyboardMarkup


def main_menu() -> Any:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🏢 ООО по ИНН", callback_data="m:ooo"),
        types.InlineKeyboardButton("🧑‍💼 ИП по ИНН", callback_data="m:ip"),
    )
    kb.add(
        types.InlineKeyboardButton("👤 Физлицо по ИНН", callback_data="m:person"),
        types.InlineKeyboardButton("🔎 Поиск компании", callback_data="m:search"),
    )
    kb.add(
        types.InlineKeyboardButton("🧰 Прочие инструменты", callback_data="m:other"),
    )
    return kb


def other_tools_menu() -> Any:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📱 Телефон", callback_data="t:phone"),
        types.InlineKeyboardButton("🚗 Авто", callback_data="t:auto"),
    )
    kb.add(
        types.InlineKeyboardButton("📧 Email", callback_data="t:email"),
        types.InlineKeyboardButton("🏠 Адрес", callback_data="t:address"),
    )
    kb.add(
        types.InlineKeyboardButton("🏦 Банк", callback_data="t:bank"),
        types.InlineKeyboardButton("🪪 Паспорт", callback_data="t:passport"),
    )
    kb.add(
        types.InlineKeyboardButton("👤 ФИО", callback_data="t:fio"),
        types.InlineKeyboardButton("🌍 IP", callback_data="t:iplocate"),
    )
    kb.add(
        types.InlineKeyboardButton("📍 Координаты", callback_data="t:geolocate"),
        types.InlineKeyboardButton("🧭 Подсказки адреса", callback_data="t:suggest_address"),
    )
    kb.add(types.InlineKeyboardButton("⬅️ Главное меню", callback_data="m:main"))
    return kb


def company_actions(inn: str) -> Any:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📈 Скоринг", callback_data=f"c:score:{inn}"),
        types.InlineKeyboardButton("💸 Налоги", callback_data=f"c:tax:{inn}"),
    )
    kb.add(
        types.InlineKeyboardButton("⚖️ Суды", callback_data=f"c:court:{inn}"),
        types.InlineKeyboardButton("📉 Долги", callback_data=f"c:debt:{inn}"),
    )
    kb.add(
        types.InlineKeyboardButton("🔗 Аффилированность", callback_data=f"c:aff:{inn}"),
        types.InlineKeyboardButton("➕ Дополнительно", callback_data=f"c:more:{inn}"),
    )
    return kb


def company_more(inn: str) -> Any:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👥 Учредители", callback_data=f"c:founders:{inn}"),
        types.InlineKeyboardButton("🧑‍💼 Руководители", callback_data=f"c:managers:{inn}"),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Финансы", callback_data=f"c:finance:{inn}"),
        types.InlineKeyboardButton("🪪 Лицензии", callback_data=f"c:licenses:{inn}"),
    )
    kb.add(
        types.InlineKeyboardButton("☎️ Контакты", callback_data=f"c:contacts:{inn}"),
        types.InlineKeyboardButton("📄 Документы", callback_data=f"c:docs:{inn}"),
    )
    kb.add(
        types.InlineKeyboardButton("{ } JSON", callback_data=f"c:json:{inn}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data=f"c:back:{inn}"),
    )
    return kb
