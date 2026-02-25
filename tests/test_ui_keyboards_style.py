"""UI keyboard style regression tests."""

from ui import keyboards


def test_main_menu_has_expected_buttons() -> None:
    kb = keyboards.main_menu()
    texts = [btn.text for row in kb.keyboard for btn in row]

    assert texts == [
        "🏢 ООО по ИНН",
        "🧑‍💼 ИП по ИНН",
        "👤 Физлицо по ИНН",
        "🔎 Поиск компании",
        "🧰 Прочие инструменты",
    ]


def test_other_tools_menu_has_core_tools() -> None:
    kb = keyboards.other_tools_menu()
    texts = [btn.text for row in kb.keyboard for btn in row]

    assert "📱 Телефон" in texts
    assert "🏠 Адрес" in texts
