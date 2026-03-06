"""Telegram bot handlers — menus, FSM, callbacks."""

import json

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from dadata_bot.keyboards.reply_keyboards import main_menu_keyboard
from dadata_bot.keyboards.inline_keyboards import (
    get_check_data_keyboard,
    get_company_card_keyboard,
    get_check_again_keyboard,
)
from dadata_bot.services.dadata_service import DaDataService
from dadata_bot.utils.text_formatter import (
    format_company_summary,
    format_company_details,
    format_branches,
    format_affiliated,
    format_address,
    format_bank,
    format_phone,
    format_passport,
    format_vehicle,
)
from dadata_bot.utils.validators import is_valid_inn_ogrn, is_valid_phone, is_valid_passport, is_valid_vehicle
from dadata_bot.utils.masking import mask_phone as _mask_phone, sha256

router = Router()

# Telegram message length limit
TG_MAX_LEN = 4096


class Form(StatesGroup):
    waiting_for_inn = State()
    waiting_for_phone = State()
    waiting_for_passport = State()
    waiting_for_vehicle = State()


# ------------------------------------------------------------------ #
#  Reply-menu handlers                                                #
# ------------------------------------------------------------------ #
@router.message(CommandStart())
@router.message(F.text == "🏠 Старт")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я помогу получить информацию о компаниях (ИНН/ОГРН) "
        "и проверить телефон, паспорт РФ или авто через DaData.\n\n"
        "Выберите действие кнопками ниже.",
        reply_markup=main_menu_keyboard,
    )


@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "<b>Что умеет бот:</b>\n"
        "🍏 <b>Проверить ИНН</b> — карточка юрлица/ИП по ИНН или ОГРН.\n"
        "🍎 <b>Проверить данные</b> — валидация телефона, паспорта РФ, авто.\n\n"
        "Бот <b>не хранит</b> и <b>не передаёт</b> ваши персональные данные третьим лицам.",
        reply_markup=main_menu_keyboard,
    )


# ------------------------------------------------------------------ #
#  ИНН / ОГРН                                                        #
# ------------------------------------------------------------------ #
@router.message(F.text == "🔎 Проверить ИНН")
async def ask_inn(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_for_inn)
    await message.answer("Введите ИНН (10/12) или ОГРН (13/15). Только цифры.")


@router.message(Form.waiting_for_inn)
async def process_inn(message: Message, state: FSMContext, dadata_service: DaDataService):
    query = message.text.strip()
    if not is_valid_inn_ogrn(query):
        await message.answer(
            "Некорректный формат. Введите ИНН (10 или 12 цифр) или ОГРН (13 или 15 цифр)."
        )
        return

    await message.answer("🔍 Ищу информацию…")
    try:
        data = await dadata_service.find_party_by_id(query)

        if data and data.get("suggestions"):
            # Store data in FSM for inline-button callbacks
            await state.update_data(company_data=data, company_query=query)
            summary = format_company_summary(data)
            await message.answer(summary, reply_markup=get_company_card_keyboard(query))
        else:
            await message.answer("По данному ИНН/ОГРН ничего не найдено.")
    except Exception:
        logger.exception("Error processing INN/OGRN query=%s", query)
        await message.answer("Произошла ошибка при запросе данных. Попробуйте позже.")
    finally:
        await state.set_state(None)


# ------------------------------------------------------------------ #
#  Проверить данные (inline menu)                                     #
# ------------------------------------------------------------------ #
@router.message(F.text == "👤 Проверить данные")
async def ask_check_data(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Что хотите проверить?", reply_markup=get_check_data_keyboard())


# -- Телефон -------------------------------------------------------- #
@router.callback_query(F.data == "check_phone")
async def cb_check_phone(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Введите телефон (как есть).")
    await state.set_state(Form.waiting_for_phone)
    await cb.answer()


@router.message(Form.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext, dadata_service: DaDataService):
    raw = message.text.strip()
    if not is_valid_phone(raw):
        await message.answer("Некорректный формат телефона. Попробуйте ещё раз.")
        return

    logger.info(f"clean/phone request hash={sha256(raw)}")
    await message.answer("📱 Проверяю телефон…")
    try:
        data = await dadata_service.clean_phone(raw)
        if data:
            await message.answer(format_phone(data), reply_markup=get_check_again_keyboard("phone"))
        else:
            await message.answer("Не удалось проверить телефон. Попробуйте позже.")
    except Exception:
        logger.exception("Error processing phone raw=%s", sha256(raw))
        await message.answer("Произошла ошибка при запросе данных. Попробуйте позже.")
    finally:
        await state.set_state(None)


# -- Паспорт -------------------------------------------------------- #
@router.callback_query(F.data == "check_passport")
async def cb_check_passport(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Введите серию и номер паспорта РФ (например, 4509 235857).")
    await state.set_state(Form.waiting_for_passport)
    await cb.answer()


@router.message(Form.waiting_for_passport)
async def process_passport(message: Message, state: FSMContext, dadata_service: DaDataService):
    raw = message.text.strip()
    if not is_valid_passport(raw):
        await message.answer("Некорректный формат. Введите 4 цифры серии и 6 цифр номера (например, 4509 235857).")
        return

    logger.info(f"clean/passport request hash={sha256(raw)}")
    await message.answer("🪪 Проверяю паспорт…")
    try:
        data = await dadata_service.clean_passport(raw)
        if data:
            await message.answer(format_passport(data), reply_markup=get_check_again_keyboard("passport"))
        else:
            await message.answer("Не удалось проверить паспорт. Попробуйте позже.")
    except Exception:
        logger.exception("Error processing passport hash=%s", sha256(raw))
        await message.answer("Произошла ошибка при запросе данных. Попробуйте позже.")
    finally:
        await state.set_state(None)


# -- Авто ----------------------------------------------------------- #
@router.callback_query(F.data == "check_vehicle")
async def cb_check_vehicle(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Введите авто строкой (например, форд фокус).")
    await state.set_state(Form.waiting_for_vehicle)
    await cb.answer()


@router.message(Form.waiting_for_vehicle)
async def process_vehicle(message: Message, state: FSMContext, dadata_service: DaDataService):
    raw = message.text.strip()
    if not is_valid_vehicle(raw):
        await message.answer("Слишком короткий запрос. Введите марку и модель авто.")
        return

    await message.answer("🚗 Проверяю авто…")
    try:
        data = await dadata_service.clean_vehicle(raw)
        if data:
            await message.answer(format_vehicle(data), reply_markup=get_check_again_keyboard("vehicle"))
        else:
            await message.answer("Не удалось проверить авто. Попробуйте позже.")
    except Exception:
        logger.exception("Error processing vehicle raw=%s", raw)
        await message.answer("Произошла ошибка при запросе данных. Попробуйте позже.")
    finally:
        await state.set_state(None)


# ------------------------------------------------------------------ #
#  «Проверить ещё» callbacks                                         #
# ------------------------------------------------------------------ #
@router.callback_query(F.data.startswith("again_"))
async def cb_again(cb: CallbackQuery, state: FSMContext):
    dtype = cb.data.removeprefix("again_")
    if dtype == "phone":
        await cb.message.answer("Введите телефон (как есть).")
        await state.set_state(Form.waiting_for_phone)
    elif dtype == "passport":
        await cb.message.answer("Введите серию и номер паспорта РФ (например, 4509 235857).")
        await state.set_state(Form.waiting_for_passport)
    elif dtype == "vehicle":
        await cb.message.answer("Введите авто строкой (например, форд фокус).")
        await state.set_state(Form.waiting_for_vehicle)
    await cb.answer()


# ------------------------------------------------------------------ #
#  «Назад» — возврат в главное меню                                   #
# ------------------------------------------------------------------ #
@router.callback_query(F.data == "back_main")
async def cb_back_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(
        "Выберите действие кнопками ниже.",
        reply_markup=main_menu_keyboard,
    )
    await cb.answer()


# ------------------------------------------------------------------ #
#  Company card inline callbacks                                      #
# ------------------------------------------------------------------ #
@router.callback_query(F.data.startswith("co_"))
async def cb_company(cb: CallbackQuery, state: FSMContext, dadata_service: DaDataService):
    parts = cb.data.split(":", 1)
    action = parts[0]  # e.g. "co_details"
    query = parts[1] if len(parts) > 1 else ""

    user_data = await state.get_data()
    company_data = user_data.get("company_data")

    if not company_data or not company_data.get("suggestions"):
        await cb.answer("Данные компании не найдены. Выполните поиск ИНН/ОГРН заново.", show_alert=True)
        return

    c = company_data["suggestions"][0]["data"]
    inn = c.get("inn", query)
    response_text = ""

    if action == "co_details":
        response_text = format_company_details(company_data)

    elif action == "co_branches":
        data = await dadata_service.find_branches(inn)
        response_text = format_branches(data)

    elif action == "co_affil":
        affiliated_inns: set[str] = set()
        mgr_inn = c.get("management", {}).get("inn")
        if mgr_inn:
            affiliated_inns.add(mgr_inn)
        for f in c.get("founders") or []:
            if f.get("inn"):
                affiliated_inns.add(f["inn"])
        if affiliated_inns:
            data = await dadata_service.find_affiliated_multi(list(affiliated_inns), limit=3)
            response_text = format_affiliated(data)
        else:
            response_text = "ИНН связанных лиц не найдены в карточке компании."

    elif action == "co_address":
        fias_id = c.get("address", {}).get("data", {}).get("fias_id")
        if fias_id:
            data = await dadata_service.find_address_by_id(fias_id)
            response_text = format_address(data)
        else:
            response_text = "FIAS ID адреса не найден в карточке."

    elif action == "co_bank":
        # DaData party response doesn't include bank BIC directly;
        # prompt user or try INN-based lookup
        response_text = (
            "В карточке компании нет данных о банке.\n"
            "Для поиска банка используйте его БИК или ИНН через 🍏 Проверить ИНН."
        )

    elif action == "co_json":
        raw = json.dumps(company_data, indent=2, ensure_ascii=False)
        if len(raw) > TG_MAX_LEN - 20:
            # Split into chunks
            chunks = [raw[i:i + TG_MAX_LEN - 20] for i in range(0, len(raw), TG_MAX_LEN - 20)]
            for chunk in chunks:
                await cb.message.answer(f"<pre>{chunk}</pre>")
            await cb.answer()
            return
        response_text = f"<pre>{raw}</pre>"

    else:
        response_text = "Неизвестное действие."

    if response_text:
        # Truncate if too long
        if len(response_text) > TG_MAX_LEN:
            response_text = response_text[: TG_MAX_LEN - 30] + "\n\n<i>…обрезано</i>"
        await cb.message.answer(response_text, reply_markup=get_company_card_keyboard(query))
    await cb.answer()
