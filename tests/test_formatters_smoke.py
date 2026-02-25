"""Smoke tests for formatters: no crashes on sparse data, HTML escaping."""
import html

from ui.formatters import (
    fmt_affiliated,
    fmt_balance,
    fmt_bank,
    fmt_contacts,
    fmt_courts,
    fmt_daily_stats,
    fmt_debts,
    fmt_docs,
    fmt_email_clean,
    fmt_finance,
    fmt_founders,
    fmt_geolocate,
    fmt_iplocate,
    fmt_licenses,
    fmt_managers,
    fmt_name_clean,
    fmt_party_card,
    fmt_passport_clean,
    fmt_person_inn,
    fmt_suggest_address,
    fmt_suggest_party,
    fmt_taxes,
    fmt_vehicle_clean,
    h,
)


def _minimal_party(inn: str = "7707083893", type_: str = "LEGAL") -> dict:
    return {
        "value": "ООО Тест",
        "data": {
            "type": type_,
            "inn": inn,
            "name": {"short_with_opf": "ООО <Test>"},
        },
    }


# ── h() escaping ──────────────────────────────────────────────────────────────

def test_h_escapes_html():
    assert h("<script>") == "&lt;script&gt;"
    assert h("Tom & Jerry") == "Tom &amp; Jerry"
    assert h(None) == "—"
    assert h("") == "—"


# ── fmt_party_card ────────────────────────────────────────────────────────────

def test_fmt_party_card_minimal_no_crash():
    result = fmt_party_card(_minimal_party())
    assert isinstance(result, str)
    assert len(result) > 0


def test_fmt_party_card_empty_data_no_crash():
    result = fmt_party_card({})
    assert isinstance(result, str)


def test_fmt_party_card_html_escaped():
    party = _minimal_party()
    party["data"]["name"]["short_with_opf"] = "<b>Evil</b>"
    result = fmt_party_card(party)
    assert "<b>Evil</b>" not in result
    assert "&lt;b&gt;" in result


def test_fmt_party_card_no_crash_with_full_data():
    party = {
        "value": "ООО Полный",
        "data": {
            "type": "LEGAL",
            "inn": "7707083893",
            "kpp": "770701001",
            "ogrn": "1027700132195",
            "name": {"short_with_opf": "ООО Полный", "full_with_opf": "Общество Полное"},
            "opf": {"short": "ООО"},
            "state": {"status": "ACTIVE", "registration_date": 978307200000},
            "address": {"value": "г. Москва"},
            "management": {"name": "Иванов И.И.", "post": "Директор"},
            "okved": "62.01",
            "capital": {"value": 10000},
            "invalid": False,
            "finance": {
                "tax_system": "USN",
                "debt": 0,
                "penalty": 0,
                "year": 2022,
                "income": 1_000_000,
            },
        },
    }
    result = fmt_party_card(party)
    assert "ООО Полный" in result
    assert "✅" in result


# ── action formatters ─────────────────────────────────────────────────────────

def test_fmt_taxes_no_crash():
    assert isinstance(fmt_taxes(_minimal_party()), str)


def test_fmt_debts_no_crash():
    result = fmt_debts(_minimal_party())
    assert isinstance(result, str)
    assert "ФССП" in result


def test_fmt_courts_no_court_decisions():
    result = fmt_courts(_minimal_party())
    assert isinstance(result, str)
    assert "Нет решений" in result


def test_fmt_courts_with_court_invalidity():
    party = _minimal_party()
    party["data"]["address"] = {
        "value": "г. Москва",
        "invalidity": {
            "code": "COURT",
            "decision": {"number": "А40-12345/2020", "date": "01.01.2020", "organ": "АС г. Москвы"},
        },
    }
    result = fmt_courts(party)
    assert "А40-12345/2020" in result


def test_fmt_affiliated_empty():
    result = fmt_affiliated([])
    assert "не найдены" in result.lower() or "недоступно" in result.lower()


def test_fmt_affiliated_list():
    items = [{"value": "ООО Связь", "data": {"inn": "1234567890", "state": {"status": "ACTIVE"}}}]
    result = fmt_affiliated(items)
    assert "ООО Связь" in result


def test_fmt_founders_empty():
    assert isinstance(fmt_founders(_minimal_party()), str)


def test_fmt_managers_fallback_to_management():
    party = _minimal_party()
    party["data"]["management"] = {"name": "Петров П.П.", "post": "CEO"}
    result = fmt_managers(party)
    assert "Петров П.П." in result


def test_fmt_finance_no_data():
    result = fmt_finance(_minimal_party())
    assert "недоступны" in result.lower()


def test_fmt_licenses_empty():
    assert "не найдены" in fmt_licenses(_minimal_party()).lower()


def test_fmt_contacts_empty():
    assert isinstance(fmt_contacts(_minimal_party()), str)


def test_fmt_docs_empty():
    assert "не найдены" in fmt_docs(_minimal_party()).lower()


# ── person formatter ──────────────────────────────────────────────────────────

def test_fmt_person_inn_no_fns_unit():
    result = fmt_person_inn("500100732259", None)
    assert "500100732259" in result
    assert "✅" in result


# ── clean formatters ──────────────────────────────────────────────────────────

def test_fmt_email_clean_none():
    assert isinstance(fmt_email_clean(None), str)


def test_fmt_email_clean_with_data():
    result = fmt_email_clean({"source": "test@example.com", "qc": 0, "local": "test", "domain": "example.com"})
    assert "test@example.com" in result


def test_fmt_vehicle_clean_none():
    assert isinstance(fmt_vehicle_clean(None), str)


def test_fmt_bank_none():
    result = fmt_bank(None)
    assert isinstance(result, str)
    assert "не найден" in result.lower()


# ── new formatters: name, passport ───────────────────────────────────────────

def test_fmt_name_clean_none():
    assert isinstance(fmt_name_clean(None), str)


def test_fmt_name_clean_with_data():
    result = fmt_name_clean({
        "source": "Срегей владимерович иванов",
        "result": "Иванов Сергей Владимирович",
        "surname": "Иванов",
        "name": "Сергей",
        "patronymic": "Владимирович",
        "gender": "М",
        "qc": 1,
    })
    assert "Иванов" in result
    assert "Сергей" in result
    assert "Мужской" in result


def test_fmt_passport_clean_none():
    assert isinstance(fmt_passport_clean(None), str)


def test_fmt_passport_clean_with_data():
    result = fmt_passport_clean({
        "source": "4509 235857",
        "series": "45 09",
        "number": "235857",
        "qc": 0,
    })
    assert "45 09" in result
    assert "235857" in result
    assert "✅" in result


# ── suggest party ────────────────────────────────────────────────────────────

def test_fmt_suggest_party_empty():
    result = fmt_suggest_party([])
    assert "не найдено" in result.lower()


def test_fmt_suggest_party_with_data():
    items = [
        {
            "value": "ПАО СБЕРБАНК",
            "data": {
                "inn": "7707083893",
                "state": {"status": "ACTIVE"},
                "address": {"value": "г. Москва"},
            },
        }
    ]
    result = fmt_suggest_party(items)
    assert "СБЕРБАНК" in result
    assert "7707083893" in result


# ── suggest address ──────────────────────────────────────────────────────────

def test_fmt_suggest_address_empty():
    result = fmt_suggest_address([])
    assert "не найдено" in result.lower()


def test_fmt_suggest_address_with_data():
    items = [{"value": "г Москва, ул Сухонская, д 11"}]
    result = fmt_suggest_address(items)
    assert "Сухонская" in result


# ── geolocate ────────────────────────────────────────────────────────────────

def test_fmt_geolocate_empty():
    result = fmt_geolocate([])
    assert "не найдены" in result.lower()


def test_fmt_geolocate_with_data():
    items = [{"value": "г Москва, ул Сухонская, д 11"}]
    result = fmt_geolocate(items)
    assert "Сухонская" in result


# ── iplocate ─────────────────────────────────────────────────────────────────

def test_fmt_iplocate_none():
    result = fmt_iplocate(None)
    assert "не определён" in result.lower()


def test_fmt_iplocate_with_data():
    result = fmt_iplocate({"value": "г Краснодар", "data": {"postal_code": "350000", "country": "Россия"}})
    assert "Краснодар" in result
    assert "350000" in result


# ── balance & stats ──────────────────────────────────────────────────────────

def test_fmt_balance_none():
    result = fmt_balance(None)
    assert "не удалось" in result.lower()


def test_fmt_balance_with_value():
    result = fmt_balance(150.0)
    assert "Баланс" in result


def test_fmt_daily_stats_none():
    result = fmt_daily_stats(None)
    assert "не удалось" in result.lower()


def test_fmt_daily_stats_with_data():
    result = fmt_daily_stats({
        "date": "2024-10-10",
        "services": {"clean": 200, "suggestions": 15000},
        "remaining": {"clean": 800},
    })
    assert "2024-10-10" in result
    assert "clean" in result
