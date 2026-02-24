"""Format DaData responses into Telegram HTML messages."""

from dadata_bot.utils.masking import mask_phone, mask_passport_series, mask_passport_number


# ------------------------------------------------------------------ #
#  QC human-readable labels                                          #
# ------------------------------------------------------------------ #
QC_PHONE = {
    "0": "✅ Телефон распознан уверенно",
    "1": "⚠️ Телефон распознан с допущениями",
    "2": "❌ Телефон не распознан",
    "3": "⚠️ Телефон пустой",
}

QC_PASSPORT = {
    "0": "✅ Серия/номер распознаны",
    "1": "⚠️ Серия/номер не распознаны",
    "2": "❌ Паспорт недействителен",
    "10": "✅ Паспорт действителен",
}

QC_VEHICLE = {
    "0": "✅ Распознано уверенно",
    "1": "⚠️ Распознано с допущениями",
    "2": "❌ Не распознано",
}

STATUS_MAP = {
    "ACTIVE": "✅ Действует",
    "LIQUIDATING": "⚠️ В процессе ликвидации",
    "LIQUIDATED": "❌ Ликвидировано",
    "BANKRUPT": "❌ Банкротство",
    "REORGANIZING": "⚠️ Реорганизация",
}


def _val(v, default="—"):
    return v if v else default


# ------------------------------------------------------------------ #
#  Company                                                            #
# ------------------------------------------------------------------ #
def format_company_summary(data: dict) -> str:
    if not data or not data.get("suggestions"):
        return "Информация о компании не найдена."
    c = data["suggestions"][0]["data"]

    name = _val(c.get("name", {}).get("full_with_opf")
                or c.get("name", {}).get("short_with_opf"))
    status_code = c.get("state", {}).get("status", "")
    status = STATUS_MAP.get(status_code, status_code)
    inn = _val(c.get("inn"))
    kpp = _val(c.get("kpp"))
    ogrn = _val(c.get("ogrn"))
    mgr_name = _val(c.get("management", {}).get("name"))
    mgr_post = c.get("management", {}).get("post", "")
    address = _val(c.get("address", {}).get("value"))
    okved = _val(c.get("okved"))
    okved_name = c.get("okved_name", "")
    employees = _val(c.get("employee_count"))

    # Признаки недостоверности
    invalid = []
    if c.get("invalid"):
        for key, label in [
            ("address", "адрес"), ("management", "руководитель"),
            ("founders", "учредители"),
        ]:
            if c["invalid"].get(key):
                invalid.append(label)

    lines = [
        f"<b>{name}</b>",
        f"Статус: {status}",
        f"ИНН/КПП: {inn}/{kpp}" if kpp != "—" else f"ИНН: {inn}",
        f"ОГРН: {ogrn}",
        f"Руководитель: {mgr_name}" + (f" ({mgr_post})" if mgr_post else ""),
        f"Адрес: {address}",
        f"ОКВЭД: {okved}" + (f" — {okved_name}" if okved_name else ""),
        f"Численность: {employees}",
    ]
    if invalid:
        lines.append(f"⚠️ Недостоверность: {', '.join(invalid)}")
    else:
        lines.append("Признаки недостоверности: отсутствуют")

    return "\n".join(lines)


def format_company_details(data: dict) -> str:
    if not data or not data.get("suggestions"):
        return "Подробная информация не найдена."
    c = data["suggestions"][0]["data"]

    full_name = _val(c.get("name", {}).get("full_with_opf"))
    short_name = _val(c.get("name", {}).get("short_with_opf"))
    inn = _val(c.get("inn"))
    kpp = _val(c.get("kpp"))
    ogrn = _val(c.get("ogrn"))
    okpo = _val(c.get("okpo"))
    okato = _val(c.get("okato"))
    oktmo = _val(c.get("oktmo"))
    okogu = _val(c.get("okogu"))
    okfs = _val(c.get("okfs"))
    okved = _val(c.get("okved"))
    okved_name = _val(c.get("okved_name"))
    address = _val(c.get("address", {}).get("value"))
    status_code = c.get("state", {}).get("status", "")
    status = STATUS_MAP.get(status_code, status_code)
    reg_date = _val(c.get("state", {}).get("registration_date"))
    mgr_name = _val(c.get("management", {}).get("name"))
    mgr_post = _val(c.get("management", {}).get("post"))
    founders = ", ".join(
        f.get("name", "?") for f in (c.get("founders") or [])
    ) or "—"
    branch_count = c.get("branch_count", 0)

    return (
        f"<b>Подробная информация</b>\n"
        f"Полное: {full_name}\n"
        f"Краткое: {short_name}\n"
        f"ИНН: {inn} | КПП: {kpp}\n"
        f"ОГРН: {ogrn}\n"
        f"ОКПО: {okpo} | ОКАТО: {okato}\n"
        f"ОКТМО: {oktmo} | ОКОГУ: {okogu} | ОКФС: {okfs}\n"
        f"ОКВЭД: {okved} — {okved_name}\n"
        f"Адрес: {address}\n"
        f"Статус: {status}\n"
        f"Дата регистрации: {reg_date}\n"
        f"Руководитель: {mgr_name} ({mgr_post})\n"
        f"Учредители: {founders}\n"
        f"Филиалов: {branch_count}"
    )


def format_branches(data: dict) -> str:
    if not data or not data.get("suggestions"):
        return "Филиалы не найдены."
    lines = ["<b>Филиалы компании:</b>"]
    for item in data["suggestions"]:
        b = item["data"]
        name = _val(b.get("name", {}).get("short_with_opf")
                    or b.get("name", {}).get("full_with_opf"))
        inn = _val(b.get("inn"))
        addr = _val(b.get("address", {}).get("value"))
        lines.append(f"• {name}\n  ИНН: {inn}\n  Адрес: {addr}")
    return "\n".join(lines) if len(lines) > 1 else "Филиалы не найдены."


def format_affiliated(data: dict) -> str:
    if not data or not data.get("suggestions"):
        return "Аффилированные лица не найдены."
    lines = ["<b>Аффилированные лица:</b>"]
    for item in data["suggestions"]:
        p = item["data"]
        name = _val(p.get("name", {}).get("full_with_opf")
                    or p.get("name", {}).get("short_with_opf"))
        inn = _val(p.get("inn"))
        status_code = p.get("state", {}).get("status", "")
        status = STATUS_MAP.get(status_code, status_code)
        lines.append(f"• {name}\n  ИНН: {inn} | {status}")
    return "\n".join(lines)


def format_address(data: dict) -> str:
    if not data or not data.get("suggestions"):
        return "Информация об адресе не найдена."
    a = data["suggestions"][0]["data"]
    return (
        f"<b>Адрес:</b>\n"
        f"Полный: {_val(a.get('result') or a.get('value'))}\n"
        f"Регион: {_val(a.get('region_with_type'))}\n"
        f"Город: {_val(a.get('city_with_type'))}\n"
        f"Улица: {_val(a.get('street_with_type'))}\n"
        f"Дом: {_val(a.get('house'))}\n"
        f"ФИАС: {_val(a.get('fias_id'))}\n"
        f"КЛАДР: {_val(a.get('kladr_id'))}"
    )


def format_bank(data: dict) -> str:
    if not data or not data.get("suggestions"):
        return "Информация о банке не найдена."
    b = data["suggestions"][0]["data"]
    return (
        f"<b>Банк:</b>\n"
        f"Название: {_val(b.get('name', {}).get('payment'))}\n"
        f"БИК: {_val(b.get('bic'))}\n"
        f"Корр. счёт: {_val(b.get('correspondent_account'))}\n"
        f"Адрес: {_val(b.get('address', {}).get('value'))}"
    )


# ------------------------------------------------------------------ #
#  Clean data formatters                                              #
# ------------------------------------------------------------------ #
def format_phone(data: list | None) -> str:
    if not data or not data[0]:
        return "Информация о телефоне не найдена."
    p = data[0]
    masked = mask_phone(p.get("phone"))
    qc = str(p.get("qc", ""))
    qc_label = QC_PHONE.get(qc, qc)
    return (
        f"<b>Проверка телефона:</b>\n"
        f"Номер: {masked}\n"
        f"Страна: {_val(p.get('country'))}\n"
        f"Регион: {_val(p.get('region'))}\n"
        f"Город: {_val(p.get('city'))}\n"
        f"Оператор: {_val(p.get('provider'))}\n"
        f"Часовой пояс: {_val(p.get('timezone'))}\n"
        f"Качество: {qc_label}"
    )


def format_passport(data: list | None) -> str:
    if not data or not data[0]:
        return "Информация о паспорте не найдена."
    p = data[0]
    series = mask_passport_series(p.get("series"))
    number = mask_passport_number(p.get("number"))
    qc = str(p.get("qc", ""))
    qc_label = QC_PASSPORT.get(qc, qc)
    return (
        f"<b>Проверка паспорта РФ:</b>\n"
        f"Серия: {series}\n"
        f"Номер: {number}\n"
        f"Качество: {qc_label}"
    )


def format_vehicle(data: list | None) -> str:
    if not data or not data[0]:
        return "Информация об авто не найдена."
    v = data[0]
    qc = str(v.get("qc", ""))
    qc_label = QC_VEHICLE.get(qc, qc)
    return (
        f"<b>Проверка авто:</b>\n"
        f"Марка: {_val(v.get('brand'))}\n"
        f"Модель: {_val(v.get('model'))}\n"
        f"Качество: {qc_label}"
    )
