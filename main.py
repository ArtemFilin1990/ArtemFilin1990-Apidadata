import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from loguru import logger

from dadata_bot.services.dadata_service import DaDataService

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dadata_service = DaDataService()
    dp["dadata_service"] = dadata_service

    from dadata_bot.handlers.user_handlers import router as user_router
    dp.include_router(user_router)

    logger.info("Starting bot...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await dadata_service.close_session()


if __name__ == "__main__":
    logger.add("bot.log", rotation="500 MB")
    asyncio.run(main())
