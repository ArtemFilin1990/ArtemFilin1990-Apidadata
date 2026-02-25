"""Application configuration loaded from environment variables."""
import logging
import os
import re

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
POLLING_MODE: bool = os.getenv("POLLING_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
DADATA_API_KEY: str = os.getenv("DADATA_API_KEY", "")
DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY", "")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
DADATA_TIMEOUT: float = float(os.getenv("DADATA_TIMEOUT", "5.0"))
TELEGRAM_STARTUP_DELAY_SECONDS: float = float(os.getenv("TELEGRAM_STARTUP_DELAY_SECONDS", "0"))

# Regex pattern for Telegram bot token validation
# Format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
_TOKEN_PATTERN = re.compile(r"^\d{8,10}:[A-Za-z0-9_-]{30,}$")


def validate() -> None:
    """Fail fast if required environment variables are missing."""
    required = ["TELEGRAM_BOT_TOKEN", "DADATA_API_KEY", "DADATA_SECRET_KEY"]
    if not POLLING_MODE:
        required.append("TELEGRAM_WEBHOOK_URL")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        msg = f"FATAL: Missing required ENV variables: {', '.join(missing)}"
        logger.critical(msg)
        raise RuntimeError(msg)

    # Validate Telegram bot token format
    if TELEGRAM_BOT_TOKEN and not _TOKEN_PATTERN.match(TELEGRAM_BOT_TOKEN):
        logger.warning(
            "TELEGRAM_BOT_TOKEN doesn't match expected format (NNNNNNNN:XXXX...). "
            "Expected format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890. "
            "If you see 'TelegramUnauthorizedError', generate a new token via @BotFather."
        )

    # Validate webhook URL format when in webhook mode
    if not POLLING_MODE and TELEGRAM_WEBHOOK_URL:
        if "/tg/" not in TELEGRAM_WEBHOOK_URL:
            logger.warning(
                "TELEGRAM_WEBHOOK_URL=%s does not contain '/tg/' path prefix. "
                "The webhook endpoint is mounted at POST /tg/<secret>, "
                "so the URL must look like https://your-domain/tg/your-secret-path",
                TELEGRAM_WEBHOOK_URL,
            )
