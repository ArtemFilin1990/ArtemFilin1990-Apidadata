"""Inline and reply keyboards for Telegram bot menus."""
from __future__ import annotations

from telebot import types


def main_menu() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🏢 Компания/ИП", callback_data="m:ooo"),
        types.InlineKeyboardButton("👤 Физлицо", callback_data="m:person"),
    )
    kb.add(
        types.InlineKeyboardButton("🔎 Поиск компании", callback_data="m:search"),
        types.InlineKeyboardButton("🧰 Прочие инструменты", callback_data="m:other"),
    )
    return kb


def other_tools_menu() -> types.InlineKeyboardMarkup:
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


def company_actions(inn: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💸 Налоги", callback_data=f"c:tax:{inn}"),
        types.InlineKeyboardButton("⚖️ Суды", callback_data=f"c:court:{inn}"),
    )
    kb.add(
        types.InlineKeyboardButton("📉 Долги", callback_data=f"c:debt:{inn}"),
        types.InlineKeyboardButton("🔗 Аффилированность", callback_data=f"c:aff:{inn}"),
    )
    kb.add(types.InlineKeyboardButton("➕ Дополнительно", callback_data=f"c:more:{inn}"))
    return kb


def company_more(inn: str) -> types.InlineKeyboardMarkup:
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
