from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Проверить ИНН"), KeyboardButton(text="👤 Проверить данные")],
        [KeyboardButton(text="🏠 Старт"), KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите действие...",
)
