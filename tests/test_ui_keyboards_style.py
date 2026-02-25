"""UI keyboard style regression tests."""

from ui import keyboards


def test_main_menu_has_expected_buttons() -> None:
    kb = keyboards.main_menu()
    texts = [btn.text for row in kb.keyboard for btn in row]

    assert texts == [
        "🏢 Компания/ИП",
        "👤 Физлицо",
        "🔎 Поиск компании",
        "🧰 Прочие инструменты",
    ]


def test_other_tools_menu_has_core_tools() -> None:
    kb = keyboards.other_tools_menu()
    texts = [btn.text for row in kb.keyboard for btn in row]

    assert "📱 Телефон" in texts
    assert "🏠 Адрес" in texts


def test_company_actions_has_scoring_button() -> None:
    kb = keyboards.company_actions("7707083893")
    texts = [btn.text for row in kb.keyboard for btn in row]

    assert "📈 Скоринг" in texts
