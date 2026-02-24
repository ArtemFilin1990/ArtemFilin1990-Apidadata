#!/usr/bin/env python3
"""
Telegram-бот для проверки контрагентов по ИНН через Dadata API.
Команды:
  /start — приветствие + меню
  /check <ИНН> — проверить контрагента
  /help — справка
Также принимает ИНН просто текстом (10 или 12 цифр).
"""
import json
import logging
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# --- Config ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DADATA_TOKEN = os.environ.get("DADATA_TOKEN")
DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not DADATA_TOKEN:
    raise RuntimeError("Set BOT_TOKEN and DADATA_TOKEN environment variables before start")

# --- Dadata API ---
def fetch_company(inn: str) -> dict | None:
    body = json.dumps({"query": inn}).encode()
    req = urllib.request.Request(
        DADATA_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {DADATA_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        logger.error(f"Dadata error: {e}")
        return None

    suggestions = data.get("suggestions", [])
    return suggestions[0] if suggestions else None


# --- Formatting ---
STATUS_MAP = {
    "ACTIVE": "✅ Действующее",
    "LIQUIDATING": "⚠️ Ликвидируется",
    "LIQUIDATED": "❌ Ликвидировано",
    "BANKRUPT": "❌ Банкротство",
    "REORGANIZING": "⚠️ Реорганизация",
}

TYPE_MAP = {
    "LEGAL": "Юридическое лицо",
    "INDIVIDUAL": "Индивидуальный предприниматель",
}


def fmt_date(ts: int | None) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts / 1000).strftime("%d.%m.%Y")


def fmt_money(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val:,.0f} ₽".replace(",", " ")


def company_age(reg_ts: int | None) -> str:
    if not reg_ts:
        return "—"
    reg = datetime.fromtimestamp(reg_ts / 1000)
    now = datetime.now()
    total_months = (now.year - reg.year) * 12 + (now.month - reg.month)
    y = total_months // 12
    m = total_months % 12
    if y == 0:
        return f"{m} мес."
    y_word = "год" if y % 10 == 1 and y % 100 != 11 else "года" if 2 <= y % 10 <= 4 and not (12 <= y % 100 <= 14) else "лет"
    if m == 0:
        return f"{y} {y_word}"
    return f"{y} {y_word} {m} мес."


def format_company(result: dict) -> str:
    d = result["data"]
    name = d.get("name", {}).get("short_with_opf", result.get("value", ""))
    full_name = d.get("name", {}).get("full_with_opf", "")
    status = STATUS_MAP.get(d.get("state", {}).get("status", ""), "❓ Неизвестно")
    org_type = TYPE_MAP.get(d.get("type", ""), d.get("type", ""))

    lines = []
    lines.append(f"🏢 <b>{escape_html(name)}</b>")
    if full_name and full_name != name:
        lines.append(f"<i>{escape_html(full_name)}</i>")
    lines.append("")
    lines.append(f"📋 <b>Статус:</b> {status}")
    lines.append(f"📂 <b>Тип:</b> {org_type}")
    lines.append("")

    # Реквизиты
    lines.append("━━━ <b>Реквизиты</b> ━━━")
    lines.append(f"<b>ИНН:</b> <code>{d.get('inn', '—')}</code>")
    if d.get("kpp"):
        lines.append(f"<b>КПП:</b> <code>{d['kpp']}</code>")
    lines.append(f"<b>ОГРН:</b> <code>{d.get('ogrn', '—')}</code>")
    if d.get("okpo"):
        lines.append(f"<b>ОКПО:</b> <code>{d['okpo']}</code>")
    if d.get("oktmo"):
        lines.append(f"<b>ОКТМО:</b> <code>{d['oktmo']}</code>")
    if d.get("okato"):
        lines.append(f"<b>ОКАТО:</b> <code>{d['okato']}</code>")
    lines.append("")

    # Адрес
    addr = (d.get("address") or {}).get("unrestricted_value") or (d.get("address") or {}).get("value")
    if addr:
        lines.append("━━━ <b>Адрес</b> ━━━")
        lines.append(f"📍 {escape_html(addr)}")
        lines.append("")

    # Руководитель
    mgmt = d.get("management")
    if mgmt:
        lines.append("━━━ <b>Руководитель</b> ━━━")
        lines.append(f"👤 {escape_html(mgmt.get('name', '—'))}")
        if mgmt.get("post"):
            lines.append(f"    <i>{escape_html(mgmt['post'])}</i>")
        lines.append("")

    # Капитал и даты
    lines.append("━━━ <b>Финансы и даты</b> ━━━")
    cap = d.get("capital")
    if cap:
        lines.append(f"💰 <b>Уставный капитал:</b> {fmt_money(cap.get('value'))}")
    reg_date = d.get("state", {}).get("registration_date")
    lines.append(f"📅 <b>Дата регистрации:</b> {fmt_date(reg_date)}")
    if reg_date:
        lines.append(f"⏳ <b>Возраст:</b> {company_age(reg_date)}")
    liq_date = d.get("state", {}).get("liquidation_date")
    if liq_date:
        lines.append(f"🚫 <b>Дата ликвидации:</b> {fmt_date(liq_date)}")
    lines.append("")

    # ОКВЭД
    okved_main = d.get("okved", "")
    okveds = d.get("okveds") or []
    if okveds:
        lines.append("━━━ <b>ОКВЭД</b> ━━━")
        for o in okveds[:5]:
            marker = "🔹" if o.get("main") else "▫️"
            lines.append(f"{marker} <code>{o['code']}</code> {escape_html(o.get('name', ''))}")
        if len(okveds) > 5:
            lines.append(f"   <i>...и ещё {len(okveds) - 5}</i>")
        lines.append("")
    elif okved_main:
        lines.append(f"<b>ОКВЭД:</b> <code>{okved_main}</code>")
        lines.append("")

    # Налоговая
    fts = (d.get("authorities") or {}).get("fts_registration")
    if fts:
        lines.append("━━━ <b>Налоговый орган</b> ━━━")
        lines.append(f"🏛 {escape_html(fts.get('name', '—'))}")
        lines.append("")

    # Контакты
    phones = d.get("phones") or []
    emails = d.get("emails") or []
    if phones or emails:
        lines.append("━━━ <b>Контакты</b> ━━━")
        for p in phones:
            lines.append(f"📞 {escape_html(p.get('value', ''))}")
        for e in emails:
            lines.append(f"📧 {escape_html(e.get('value', ''))}")
        lines.append("")

    # Филиалы
    bc = d.get("branch_count", 0)
    if bc:
        lines.append(f"🏗 <b>Филиалы:</b> {bc}")
        lines.append("")

    return "\n".join(lines)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def extract_inn(text: str) -> str | None:
    clean = re.sub(r"\D", "", text.strip())
    if len(clean) in (10, 12):
        return clean
    return None


# --- Handlers ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [["🔍 Проверить ИНН"], ["ℹ️ Справка"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    await update.message.reply_text(
        "🏢 <b>Проверка контрагентов по ИНН</b>\n\n"
        "Отправьте ИНН (10 или 12 цифр) — получите данные из ЕГРЮЛ/ЕГРИП.\n\n"
        "Или используйте команду:\n"
        "<code>/check 7707083893</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Справка</b>\n\n"
        "Бот проверяет организации и ИП по ИНН.\n"
        "Данные из ЕГРЮЛ/ЕГРИП в реальном времени.\n\n"
        "<b>Как пользоваться:</b>\n"
        "• Отправьте ИНН текстом (10 или 12 цифр)\n"
        "• Или команду: <code>/check 7707083893</code>\n\n"
        "<b>Что покажет:</b>\n"
        "• Наименование и статус\n"
        "• Реквизиты (ИНН/КПП/ОГРН/ОКПО)\n"
        "• Юридический адрес\n"
        "• Руководитель\n"
        "• Уставный капитал\n"
        "• ОКВЭД\n"
        "• Налоговый орган\n"
        "• Контакты\n\n"
        "Источник: ФНС (через DaData.ru)",
        parse_mode="HTML",
    )


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Укажите ИНН после команды:\n<code>/check 7707083893</code>",
            parse_mode="HTML",
        )
        return
    inn = extract_inn(context.args[0])
    if not inn:
        await update.message.reply_text(
            "❌ Некорректный ИНН. Нужно 10 цифр (юр. лицо) или 12 (ИП).",
            parse_mode="HTML",
        )
        return
    await do_check(update, inn)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🔍 Проверить ИНН":
        await update.message.reply_text(
            "Отправьте ИНН (10 или 12 цифр):",
            parse_mode="HTML",
        )
        return

    if text == "ℹ️ Справка":
        await cmd_help(update, context)
        return

    inn = extract_inn(text)
    if inn:
        await do_check(update, inn)
    else:
        await update.message.reply_text(
            "Не распознал ИНН. Отправьте 10 или 12 цифр.\n"
            "Пример: <code>7707083893</code>",
            parse_mode="HTML",
        )


async def do_check(update: Update, inn: str):
    msg = await update.message.reply_text("🔄 Проверяю ИНН...")

    result = fetch_company(inn)

    if result is None:
        await msg.edit_text(
            f"❌ Организация с ИНН <code>{inn}</code> не найдена в ЕГРЮЛ/ЕГРИП.",
            parse_mode="HTML",
        )
        return

    text = format_company(result)

    # Кнопки под результатом
    d = result["data"]
    buttons = []
    addr = (d.get("address") or {}).get("data") or {}
    if addr.get("geo_lat") and addr.get("geo_lon"):
        map_url = f"https://yandex.ru/maps/?pt={addr['geo_lon']},{addr['geo_lat']}&z=16&l=map"
        buttons.append([InlineKeyboardButton("📍 На карте", url=map_url)])

    buttons.append([InlineKeyboardButton("🔄 Новый запрос", callback_data="new_search")])

    try:
        await msg.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
        )
    except Exception:
        # Если сообщение слишком длинное — разбиваем
        chunks = split_message(text, 4000)
        await msg.edit_text(chunks[0], parse_mode="HTML")
        for chunk in chunks[1:]:
            await update.message.reply_text(
                chunk,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons) if chunk == chunks[-1] else None,
            )


def split_message(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Ищем перенос строки ближе к max_len
        idx = text.rfind("\n", 0, max_len)
        if idx == -1:
            idx = max_len
        chunks.append(text[:idx])
        text = text[idx:].lstrip("\n")
    return chunks


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "new_search":
        await query.message.reply_text(
            "Отправьте ИНН (10 или 12 цифр):",
            parse_mode="HTML",
        )


# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started. Polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
