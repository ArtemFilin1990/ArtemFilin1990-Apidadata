"""FastAPI app: webhook endpoint, health check, startup lifecycle."""
from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from threading import Thread
from urllib.parse import urlparse

# The Telegram bot API library is optional in some environments. Import it
# lazily and fall back to ``None`` if it isn't installed so that the module
# can still be imported for testing utility functions (e.g. ``mask_token``)
try:
    import telebot  # type: ignore
except Exception:
    telebot = None  # type: ignore
from fastapi import FastAPI, Request, Response
import uvicorn

import config
from services.dadata_service import close_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

executor: ThreadPoolExecutor | None = None
_polling_thread: Thread | None = None

_TOKEN_RE = re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}")


def mask_token(text: str) -> str:
    return _TOKEN_RE.sub("***:***", text)


def _configure_webhook() -> None:
    from tg_bot import get_bot  # noqa: PLC0415 – intentional late import after validate()

    try:
        real_bot = get_bot()
        real_bot.remove_webhook()
        real_bot.set_webhook(url=config.TELEGRAM_WEBHOOK_URL)
        logger.info("Webhook set to %s", mask_token(config.TELEGRAM_WEBHOOK_URL))
    except Exception:
        logger.exception("Failed to set Telegram webhook")


def _run_polling() -> None:
    from tg_bot import get_bot  # noqa: PLC0415 – intentional late import after validate()

    try:
        real_bot = get_bot()
        real_bot.remove_webhook()
        real_bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
    except Exception:
        logger.exception("Telegram polling stopped unexpectedly")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    global executor, _polling_thread

    config.validate()
    executor = ThreadPoolExecutor(max_workers=4)
    if config.POLLING_MODE:
        logger.info("Telegram mode: polling")
        _polling_thread = Thread(target=_run_polling, daemon=True)
        _polling_thread.start()
    else:
        logger.info("Telegram mode: webhook")
        logger.info(
            "Webhook URL: %s", mask_token(config.TELEGRAM_WEBHOOK_URL)
        )
        Thread(target=_configure_webhook, daemon=True).start()

    yield

    if executor is not None:
        executor.shutdown(wait=False)
        executor = None

    if config.POLLING_MODE:
        try:
            from tg_bot import get_bot  # noqa: PLC0415

            get_bot().stop_polling()
        except Exception:
            logger.exception("Failed to stop polling")
        _polling_thread = None

    close_client()
    logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    webhook_path = urlparse(config.TELEGRAM_WEBHOOK_URL).path if config.TELEGRAM_WEBHOOK_URL else ""
    mode = "polling" if config.POLLING_MODE else "webhook"
    return {
        "status": "ok",
        "mode": mode,
        "webhook_path": webhook_path,
    }


@app.post("/tg/{secret_path:path}")
async def telegram_webhook(secret_path: str, request: Request) -> Response:
    if config.POLLING_MODE:
        logger.warning("Received webhook request while in polling mode — returning 409")
        return Response(status_code=409)

    expected_path = urlparse(config.TELEGRAM_WEBHOOK_URL).path
    actual_path = f"/tg/{secret_path}"
    if actual_path != expected_path:
        logger.warning(
            "Webhook path mismatch: received %s, expected %s",
            actual_path,
            expected_path,
        )
        return Response(status_code=404)

    body = await request.body()
    # Parse the incoming update.  If the optional telebot dependency is
    # available, use its Update parser; otherwise fall back to decoding the
    # JSON into a simple namespace exposing an ``update_id`` attribute.
    try:
        if telebot is not None:
            update = telebot.types.Update.de_json(body.decode("utf-8"))  # type: ignore[attr-defined]
        else:
            # Import JSON lazily so the module can be imported without it at
            # module import time (json is part of stdlib and always available)
            import json as _json  # noqa: WPS433
            data: Any = _json.loads(body.decode("utf-8"))  # type: ignore[no-untyped-call]
            # Use SimpleNamespace so attributes can be accessed with dot syntax
            from types import SimpleNamespace  # noqa: WPS433

            update = SimpleNamespace(**data)
    except Exception:
        logger.exception("Failed to parse Telegram update")
        return Response(status_code=400)

    # Acquire the bot instance (may be a mock in test environments)
    from tg_bot import get_bot  # noqa: PLC0415

    bot_instance = None
    try:
        bot_instance = get_bot()
    except Exception:
        logger.exception("Failed to obtain bot instance")

    if bot_instance is None:
        logger.error("Bot instance is None — cannot process update")
    elif executor is not None:
        try:
            # process_new_updates expects a list of Update objects
            bot_instance.process_new_updates([update])  # type: ignore[attr-defined]
        except Exception:
            logger.exception("Failed to submit update to executor")
    else:
        logger.error("Executor is None — cannot process update")
    return Response(status_code=200)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
