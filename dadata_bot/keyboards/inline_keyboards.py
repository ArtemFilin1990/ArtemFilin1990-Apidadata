from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_check_data_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Телефон", callback_data="check_phone")],
        [InlineKeyboardButton(text="🪪 Паспорт РФ", callback_data="check_passport")],
        [InlineKeyboardButton(text="🚗 Авто (марка/модель)", callback_data="check_vehicle")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def get_company_card_keyboard(query: str) -> InlineKeyboardMarkup:
    """Inline buttons under company summary. `query` is INN/OGRN for callbacks."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Подробно", callback_data=f"co_details:{query}"),
            InlineKeyboardButton(text="🏢 Филиалы", callback_data=f"co_branches:{query}"),
        ],
        [
            InlineKeyboardButton(text="🔗 Аффилированность", callback_data=f"co_affil:{query}"),
            InlineKeyboardButton(text="📍 Адрес", callback_data=f"co_address:{query}"),
        ],
        [
            InlineKeyboardButton(text="🏦 Банк", callback_data=f"co_bank:{query}"),
            InlineKeyboardButton(text="📄 Полный JSON", callback_data=f"co_json:{query}"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])


def get_check_again_keyboard(data_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Проверить ещё", callback_data=f"again_{data_type}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
    ])
