"""Message formatters: take DaData data, return HTML-safe strings."""
import html
import json
from datetime import datetime
from typing import Any, Optional


# ── helpers ─────────────────────────────────────────────────────────────────

def h(value: Any) -> str:
    """HTML-escape a value converted to string; return em-dash for None/empty."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def fmt_date(ts_ms: Any) -> str:
    if ts_ms is None:
        return "—"
    try:
        return datetime.fromtimestamp(int(ts_ms) / 1000).strftime("%d.%m.%Y")
    except Exception:
        return h(ts_ms)


def fmt_money(val: Any) -> str:
    if val is None:
        return "—"
    try:
        return f"{round(float(val)):,}".replace(",", "\u00a0") + "\u00a0₽"
    except Exception:
        return h(val)


STATUS_MAP: dict[str, str] = {
    "ACTIVE": "✅ Действующее",
    "BANKRUPT": "💥 Банкротство",
    "LIQUIDATED": "🔴 Ликвидировано",
    "LIQUIDATING": "⚠️ Ликвидируется",
    "REORGANIZING": "🔄 Реорганизация",
}

TAX_SYSTEM_MAP: dict[str, str] = {
    "AUSN": "АвтоУСН",
    "USN": "УСН",
    "ENVD": "ЕНВД",
    "ESHN": "ЕСХН",
    "PSN": "ПСН",
    "NDP": "НПД",
    "ENVD_ESHN": "ЕНВД+ЕСХН",
}

INVALIDITY_CODE_MAP: dict[str, str] = {
    "COURT": "Решение суда",
    "FNS": "Решение ФНС",
    "MASS_REGISTRATION": "Массовая регистрация",
    "MASS_LEADER": "Массовый руководитель",
}


def _safe(d: Any, *keys: str, default: Any = None) -> Any:
    """Safely dig into nested dicts/None."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
    return d if d is not None else default


def chunk_text(text: str, max_len: int = 3500) -> list[str]:
    chunks: list[str] = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


# ── party formatters ─────────────────────────────────────────────────────────

def fmt_party_card(party: dict) -> str:
    """Main card for a company or IP."""
    data = party.get("data") or {}
    lines: list[str] = []

    name_d = data.get("name") or {}
    name_str = (
        name_d.get("short_with_opf")
        or name_d.get("full_with_opf")
        or party.get("value")
        or "?"
    )
    lines.append(f"<b>{h(name_str)}</b>")

    opf = _safe(data, "opf", "short")
    if opf:
        lines.append(f"ОПФ: {h(opf)}")

    state = data.get("state") or {}
    status_raw = state.get("status", "")
    status_str = STATUS_MAP.get(status_raw, status_raw)
    if status_str:
        lines.append(f"Статус: {h(status_str)}")

    reg_date = state.get("registration_date")
    if reg_date:
        lines.append(f"Дата регистрации: {fmt_date(reg_date)}")

    inn = data.get("inn") or ""
    kpp = data.get("kpp") or ""
    ogrn = data.get("ogrn") or ""
    if inn:
        lines.append(f"ИНН: <code>{h(inn)}</code>")
    if kpp:
        lines.append(f"КПП: <code>{h(kpp)}</code>")
    if ogrn:
        lines.append(f"ОГРН: <code>{h(ogrn)}</code>")

    addr = _safe(data, "address", "value")
    if addr:
        lines.append(f"Адрес: {h(addr)}")

    mgmt = data.get("management") or {}
    mgmt_name = mgmt.get("name") or ""
    mgmt_post = mgmt.get("post") or ""
    if mgmt_name:
        line = f"Руководитель: {h(mgmt_name)}"
        if mgmt_post:
            line += f" ({h(mgmt_post)})"
        lines.append(line)

    okved = data.get("okved") or ""
    if okved:
        lines.append(f"ОКВЭД: {h(okved)}")

    capital_val = _safe(data, "capital", "value")
    if capital_val is not None:
        lines.append(f"УК: {fmt_money(capital_val)}")

    finance = data.get("finance") or {}
    tax_sys = finance.get("tax_system") or ""
    if tax_sys:
        lines.append(f"Система налогообложения: {h(TAX_SYSTEM_MAP.get(tax_sys, tax_sys))}")

    if data.get("invalid"):
        lines.append("⚠️ <b>Недостоверные сведения</b>")

    return "\n".join(lines)


def fmt_taxes(party: dict) -> str:
    data = party.get("data") or {}
    lines = ["<b>🧾 Налоги</b>"]

    auth = data.get("authorities") or {}
    fts_reg = auth.get("fts_registration") or {}
    if fts_reg:
        fts_reg_label = h(fts_reg.get("name") or fts_reg.get("code") or "")
        fts_reg_code = h(fts_reg.get("code") or "")
        lines.append(f"ИФНС регистрации: {fts_reg_label} ({fts_reg_code})")
        if fts_reg.get("address"):
            lines.append(f"Адрес ИФНС: {h(fts_reg.get('address'))}")

    fts_rep = auth.get("fts_report") or {}
    if fts_rep:
        fts_rep_label = h(fts_rep.get("name") or fts_rep.get("code") or "")
        fts_rep_code = h(fts_rep.get("code") or "")
        lines.append(f"ИФНС отчётности: {fts_rep_label} ({fts_rep_code})")

    finance = data.get("finance") or {}
    tax_sys = finance.get("tax_system") or ""
    if tax_sys:
        lines.append(f"Система налогообложения: {h(TAX_SYSTEM_MAP.get(tax_sys, tax_sys))}")

    year = finance.get("year")
    if year:
        lines.append(f"Отчётный год: {h(year)}")

    debt = finance.get("debt")
    penalty = finance.get("penalty")
    if debt is not None:
        lines.append(f"Недоимка: {fmt_money(debt)}")
    if penalty is not None:
        lines.append(f"Штрафы: {fmt_money(penalty)}")

    if len(lines) == 1:
        lines.append("Нет данных о налогах.")

    return "\n".join(lines)


def fmt_debts(party: dict) -> str:
    data = party.get("data") or {}
    finance = data.get("finance") or {}
    lines = ["<b>💸 Долги (данные DaData)</b>"]

    debt = finance.get("debt")
    penalty = finance.get("penalty")
    year = finance.get("year")

    if debt is not None:
        lines.append(f"Недоимка: {fmt_money(debt)}")
    if penalty is not None:
        lines.append(f"Штрафы: {fmt_money(penalty)}")
    if year:
        lines.append(f"За {h(year)} год")

    lines.append("")
    lines.append("ℹ️ ФССП не подключено — исполнительные производства не отображаются.")

    if debt is None and penalty is None:
        lines.insert(1, "Нет данных о задолженностях.")

    return "\n".join(lines)


def _extract_invalidity_decisions(invalidity: Any) -> list[str]:
    """Return list of COURT invalidity decision strings from an invalidity block."""
    results: list[str] = []
    if not isinstance(invalidity, dict):
        return results
    if invalidity.get("code") == "COURT":
        decision = invalidity.get("decision") or {}
        num = decision.get("number") or ""
        date = decision.get("date") or ""
        organ = decision.get("organ") or ""
        parts = [p for p in [organ, num, date] if p]
        results.append(" / ".join(h(p) for p in parts) if parts else "Решение суда (детали не указаны)")
    return results


def fmt_courts(party: dict) -> str:
    data = party.get("data") or {}
    lines = ["<b>⚖️ Суды (решения о недостоверности)</b>"]
    decisions: list[str] = []

    # address invalidity
    addr_inv = _safe(data, "address", "invalidity")
    decisions.extend(_extract_invalidity_decisions(addr_inv))

    # founders invalidity
    for f in data.get("founders") or []:
        decisions.extend(_extract_invalidity_decisions(f.get("invalidity")))

    # managers invalidity
    for m in data.get("managers") or []:
        decisions.extend(_extract_invalidity_decisions(m.get("invalidity")))

    if decisions:
        for d in decisions:
            lines.append(f"• {d}")
    else:
        lines.append("Нет решений суда по недостоверности (или данные не предоставлены DaData).")

    return "\n".join(lines)


def fmt_affiliated(results: list[dict]) -> str:
    lines = ["<b>🔗 Связанные компании</b>"]
    if not results:
        lines.append("Связанные компании не найдены (или недоступно для текущего тарифа).")
        return "\n".join(lines)
    for item in results[:20]:
        name = item.get("value") or ""
        inn = _safe(item, "data", "inn") or ""
        status_raw = _safe(item, "data", "state", "status") or ""
        status = STATUS_MAP.get(status_raw, status_raw)
        row = h(name)
        if inn:
            row += f" <code>{h(inn)}</code>"
        if status:
            row += f" [{h(status)}]"
        lines.append(f"• {row}")
    return "\n".join(lines)


def fmt_founders(party: dict) -> str:
    data = party.get("data") or {}
    founders = data.get("founders") or []
    lines = ["<b>👥 Учредители</b>"]
    if not founders:
        lines.append("Нет данных об учредителях.")
        return "\n".join(lines)
    for f in founders[:30]:
        name = f.get("name") or f.get("fio") or "?"
        inn = f.get("inn") or ""
        share_val = _safe(f, "share", "value")
        share_type = _safe(f, "share", "type") or ""
        inv_code = _safe(f, "invalidity", "code") or ""

        row = h(name)
        if inn:
            row += f" <code>{h(inn)}</code>"
        if share_val is not None:
            row += f" {fmt_money(share_val)}"
        if inv_code:
            row += f" ⚠️{h(INVALIDITY_CODE_MAP.get(inv_code, inv_code))}"
        lines.append(f"• {row}")
    return "\n".join(lines)


def fmt_managers(party: dict) -> str:
    data = party.get("data") or {}
    managers = data.get("managers") or []
    lines = ["<b>🧑‍💼 Руководители</b>"]
    if not managers:
        mgmt = data.get("management") or {}
        mgmt_name = mgmt.get("name") or ""
        if mgmt_name:
            lines.append(f"• {h(mgmt_name)} — {h(mgmt.get('post') or '')}")
        else:
            lines.append("Нет данных о руководителях.")
        return "\n".join(lines)
    for m in managers[:30]:
        name = m.get("name") or m.get("fio") or "?"
        inn = m.get("inn") or ""
        post = m.get("post") or ""
        inv_code = _safe(m, "invalidity", "code") or ""

        row = h(name)
        if post:
            row += f" — {h(post)}"
        if inn:
            row += f" <code>{h(inn)}</code>"
        if inv_code:
            row += f" ⚠️{h(INVALIDITY_CODE_MAP.get(inv_code, inv_code))}"
        lines.append(f"• {row}")
    return "\n".join(lines)


def fmt_finance(party: dict) -> str:
    data = party.get("data") or {}
    finance = data.get("finance") or {}
    lines = ["<b>📊 Финансы</b>"]

    year = finance.get("year")
    if year:
        lines.append(f"Отчётный год: {h(year)}")

    for field, label in [
        ("income", "Доход"),
        ("revenue", "Выручка"),
        ("expense", "Расходы"),
        ("debt", "Недоимка"),
        ("penalty", "Штрафы"),
    ]:
        val = finance.get(field)
        if val is not None:
            lines.append(f"{label}: {fmt_money(val)}")

    if len(lines) == 1:
        lines.append("Финансовые данные недоступны.")

    return "\n".join(lines)


def fmt_licenses(party: dict) -> str:
    data = party.get("data") or {}
    licenses = data.get("licenses") or []
    lines = ["<b>🪪 Лицензии</b>"]
    if not licenses:
        lines.append("Лицензии не найдены.")
        return "\n".join(lines)
    for lic in licenses:
        series = lic.get("series") or ""
        number = lic.get("number") or ""
        issue_date = lic.get("issue_date") or ""
        authority = lic.get("issue_authority") or ""
        parts = [p for p in [series, number, issue_date, authority] if p]
        lines.append(f"• {' | '.join(h(p) for p in parts)}")
    return "\n".join(lines)


def fmt_contacts(party: dict) -> str:
    data = party.get("data") or {}
    phones = data.get("phones") or []
    emails = data.get("emails") or []
    lines = ["<b>📞 Контакты</b>"]

    if phones:
        lines.append("Телефоны:")
        for p in phones:
            src = _safe(p, "data", "source") or p.get("value") or ""
            if src:
                lines.append(f"  • {h(src)}")
    if emails:
        lines.append("Email:")
        for e in emails:
            src = _safe(e, "data", "source") or e.get("value") or ""
            if src:
                lines.append(f"  • {h(src)}")

    if not phones and not emails:
        lines.append("Контакты не найдены в данных DaData.")

    return "\n".join(lines)


def fmt_docs(party: dict) -> str:
    data = party.get("data") or {}
    documents = data.get("documents") or {}
    lines = ["<b>📄 Документы</b>"]
    if not documents:
        lines.append("Документы не найдены.")
        return "\n".join(lines)
    if isinstance(documents, dict):
        for doc_name, doc_data in documents.items():
            if not isinstance(doc_data, dict):
                continue
            series = doc_data.get("series") or ""
            number = doc_data.get("number") or ""
            issue_date = doc_data.get("issue_date") or ""
            parts = [p for p in [series, number, issue_date] if p]
            suffix = " | ".join(h(p) for p in parts) if parts else "—"
            lines.append(f"• {h(doc_name)}: {suffix}")
    return "\n".join(lines)


def fmt_party_json(party: dict) -> str:
    """Return pretty-printed JSON string for file export."""
    return json.dumps(party, ensure_ascii=False, indent=2)


# ── person ───────────────────────────────────────────────────────────────────

def fmt_person_inn(inn: str, fns_unit: Optional[dict]) -> str:
    valid = len(inn) == 12
    fns_code = inn[:4] if len(inn) >= 4 else "—"
    fns_name = None
    if fns_unit:
        fns_name = (
            (fns_unit.get("data") or {}).get("name")
            or fns_unit.get("value")
        )

    lines = [
        "<b>🧍 Физлицо — проверка ИНН</b>",
        f"ИНН: <code>{h(inn)}</code>",
        f"Валидность: {'✅ корректный' if valid else '❌ некорректный'}",
        f"Код ИФНС: <code>{h(fns_code)}</code>",
    ]
    if fns_name:
        lines.append(f"ИФНС: {h(fns_name)}")
    return "\n".join(lines)


# ── «Прочее» clean formatters ────────────────────────────────────────────────

def fmt_email_clean(result: Optional[dict]) -> str:
    if not result:
        return "Результат не получен."
    lines = ["<b>📧 Email</b>"]
    qc = result.get("qc")
    qc_map = {0: "✅ Корректный", 1: "⚠️ Некорректный", 2: "❓ Не определено"}
    lines.append(f"Email: {h(result.get('source') or '')}")
    lines.append(f"Статус: {h(qc_map.get(qc, str(qc)))}")
    if result.get("local"):
        lines.append(f"Локальная часть: {h(result.get('local'))}")
    if result.get("domain"):
        lines.append(f"Домен: {h(result.get('domain'))}")
    if result.get("type"):
        lines.append(f"Тип: {h(result.get('type'))}")
    return "\n".join(lines)


def fmt_phone_clean(result: Optional[dict]) -> str:
    if not result:
        return "Результат не получен."
    lines = ["<b>📱 Телефон</b>"]
    lines.append(f"Исходный: {h(result.get('source') or '')}")
    phone = result.get("phone") or result.get("result") or ""
    if phone:
        lines.append(f"Нормализованный: <code>{h(phone)}</code>")
    region = (result.get("data") or {}).get("region") or result.get("region") or ""
    if region:
        lines.append(f"Регион: {h(region)}")
    provider = (result.get("data") or {}).get("provider") or result.get("provider") or ""
    if provider:
        lines.append(f"Оператор: {h(provider)}")
    qc = result.get("qc")
    qc_map = {0: "✅ Корректный", 1: "⚠️ Некорректный", 3: "❓ Не определено"}
    if qc is not None:
        lines.append(f"Статус: {h(qc_map.get(qc, str(qc)))}")
    return "\n".join(lines)


def fmt_address_clean(result: Optional[dict]) -> str:
    if not result:
        return "Результат не получен."
    lines = ["<b>📍 Адрес</b>"]
    source = result.get("source") or result.get("unparsed_parts") or ""
    if source:
        lines.append(f"Исходный: {h(source)}")
    result_str = result.get("result") or ""
    if result_str:
        lines.append(f"Нормализованный: {h(result_str)}")
    postal = result.get("postal_code") or ""
    if postal:
        lines.append(f"Индекс: {h(postal)}")
    region = result.get("region_with_type") or result.get("region") or ""
    if region:
        lines.append(f"Регион: {h(region)}")
    city = result.get("city_with_type") or result.get("city") or ""
    if city:
        lines.append(f"Город: {h(city)}")
    street = result.get("street_with_type") or ""
    if street:
        lines.append(f"Улица: {h(street)}")
    qc = result.get("qc")
    qc_map = {0: "✅ Точный адрес", 1: "⚠️ Несколько вариантов", 2: "❌ Не найден", 3: "❓ Мусор"}
    if qc is not None:
        lines.append(f"Качество: {h(qc_map.get(qc, str(qc)))}")
    return "\n".join(lines)


def fmt_vehicle_clean(result: Optional[dict]) -> str:
    if not result:
        return "Результат не получен."
    lines = ["<b>🚗 Авто (марка / модель)</b>"]
    lines.append(f"Исходный: {h(result.get('source') or '')}")
    res = result.get("result") or ""
    if res:
        lines.append(f"Нормализованный: {h(res)}")
    brand = result.get("brand") or ""
    model = result.get("model") or ""
    if brand:
        lines.append(f"Марка: {h(brand)}")
    if model:
        lines.append(f"Модель: {h(model)}")
    qc = result.get("qc")
    qc_map = {0: "✅ Найдено", 1: "⚠️ Не найдено"}
    if qc is not None:
        lines.append(f"Статус: {h(qc_map.get(qc, str(qc)))}")
    return "\n".join(lines)


def fmt_name_clean(result: Optional[dict]) -> str:
    if not result:
        return "Результат не получен."
    lines = ["<b>👤 ФИО</b>"]
    lines.append(f"Исходное: {h(result.get('source') or '')}")
    res = result.get("result") or ""
    if res:
        lines.append(f"Результат: {h(res)}")
    surname = result.get("surname") or ""
    name = result.get("name") or ""
    patronymic = result.get("patronymic") or ""
    if surname:
        lines.append(f"Фамилия: {h(surname)}")
    if name:
        lines.append(f"Имя: {h(name)}")
    if patronymic:
        lines.append(f"Отчество: {h(patronymic)}")
    gender = result.get("gender") or ""
    if gender:
        gender_map = {"М": "Мужской", "Ж": "Женский"}
        lines.append(f"Пол: {h(gender_map.get(gender, gender))}")
    qc = result.get("qc")
    qc_map = {0: "✅ Распознано", 1: "⚠️ Неоднозначно", 2: "❌ Не распознано"}
    if qc is not None:
        lines.append(f"Качество: {h(qc_map.get(qc, str(qc)))}")
    return "\n".join(lines)


def fmt_passport_clean(result: Optional[dict]) -> str:
    if not result:
        return "Результат не получен."
    lines = ["<b>🛂 Паспорт</b>"]
    lines.append(f"Исходный: {h(result.get('source') or '')}")
    series = result.get("series") or ""
    number = result.get("number") or ""
    if series:
        lines.append(f"Серия: {h(series)}")
    if number:
        lines.append(f"Номер: {h(number)}")
    qc = result.get("qc")
    qc_map = {0: "✅ Корректный", 1: "⚠️ Некорректный", 10: "❌ Не распознан"}
    if qc is not None:
        lines.append(f"Статус: {h(qc_map.get(qc, str(qc)))}")
    return "\n".join(lines)


def fmt_suggest_party(results: list[dict]) -> str:
    lines = ["<b>🔍 Результаты поиска</b>"]
    if not results:
        lines.append("Ничего не найдено.")
        return "\n".join(lines)
    for i, item in enumerate(results[:10], 1):
        name = item.get("value") or "?"
        data = item.get("data") or {}
        inn = data.get("inn") or ""
        status_raw = _safe(data, "state", "status") or ""
        status = STATUS_MAP.get(status_raw, status_raw)
        row = f"{i}. <b>{h(name)}</b>"
        if inn:
            row += f"\n   ИНН: <code>{h(inn)}</code>"
        if status:
            row += f" [{h(status)}]"
        addr = _safe(data, "address", "value") or ""
        if addr:
            row += f"\n   {h(addr)}"
        lines.append(row)
    return "\n".join(lines)


def fmt_suggest_address(results: list[dict]) -> str:
    lines = ["<b>📍 Подсказки адресов</b>"]
    if not results:
        lines.append("Ничего не найдено.")
        return "\n".join(lines)
    for i, item in enumerate(results[:10], 1):
        value = item.get("value") or "?"
        lines.append(f"{i}. {h(value)}")
    return "\n".join(lines)


def fmt_geolocate(results: list[dict]) -> str:
    lines = ["<b>📍 Обратное геокодирование</b>"]
    if not results:
        lines.append("Адреса не найдены.")
        return "\n".join(lines)
    for i, item in enumerate(results[:10], 1):
        value = item.get("value") or "?"
        lines.append(f"{i}. {h(value)}")
    return "\n".join(lines)


def fmt_iplocate(result: Optional[dict]) -> str:
    if not result:
        return "Город по IP не определён."
    lines = ["<b>🌐 GeoIP</b>"]
    value = result.get("value") or ""
    if value:
        lines.append(f"Город: {h(value)}")
    data = result.get("data") or {}
    postal_code = data.get("postal_code") or ""
    if postal_code:
        lines.append(f"Индекс: {h(postal_code)}")
    country = data.get("country") or ""
    if country:
        lines.append(f"Страна: {h(country)}")
    return "\n".join(lines)


def fmt_balance(balance: Optional[float]) -> str:
    if balance is None:
        return "Не удалось получить баланс."
    return f"<b>💰 Баланс DaData</b>\n{fmt_money(balance)}"


def fmt_daily_stats(stats: Optional[dict]) -> str:
    if not stats:
        return "Не удалось получить статистику."
    lines = ["<b>📊 Статистика DaData</b>"]
    date = stats.get("date") or ""
    if date:
        lines.append(f"Дата: {h(date)}")
    services = stats.get("services") or {}
    if services:
        lines.append("<b>Использовано:</b>")
        for svc, cnt in services.items():
            lines.append(f"  • {h(svc)}: {h(cnt)}")
    remaining = stats.get("remaining") or {}
    if remaining:
        lines.append("<b>Осталось:</b>")
        for svc, cnt in remaining.items():
            lines.append(f"  • {h(svc)}: {h(cnt)}")
    return "\n".join(lines)


def fmt_bank(result: Optional[dict]) -> str:
    if not result:
        return "Банк не найден."
    data = result.get("data") or {}
    lines = ["<b>🏦 Банк</b>"]
    name = result.get("value") or (data.get("name") or {}).get("payment") or ""
    if name:
        lines.append(f"Название: {h(name)}")
    bic = data.get("bic") or ""
    if bic:
        lines.append(f"БИК: <code>{h(bic)}</code>")
    inn = data.get("inn") or ""
    if inn:
        lines.append(f"ИНН: <code>{h(inn)}</code>")
    corr = data.get("correspondent_account") or ""
    if corr:
        lines.append(f"Корр. счёт: <code>{h(corr)}</code>")
    address = (data.get("address") or {}).get("value") or ""
    if address:
        lines.append(f"Адрес: {h(address)}")
    status = (data.get("state") or {}).get("status") or ""
    if status:
        lines.append(f"Статус: {h(STATUS_MAP.get(status, status))}")
    return "\n".join(lines)
