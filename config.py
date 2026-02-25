"""Application configuration loaded from environment variables."""
import logging
import os

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
POLLING_MODE: bool = os.getenv("POLLING_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
DADATA_API_KEY: str = os.getenv("DADATA_API_KEY", "")
DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY", "")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
DADATA_TIMEOUT: float = float(os.getenv("DADATA_TIMEOUT", "5.0"))


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

    # Validate webhook URL format when in webhook mode
    if not POLLING_MODE and TELEGRAM_WEBHOOK_URL:
        if "/tg/" not in TELEGRAM_WEBHOOK_URL:
            logger.warning(
                "TELEGRAM_WEBHOOK_URL=%s does not contain '/tg/' path prefix. "
                "The webhook endpoint is mounted at POST /tg/<secret>, "
                "so the URL must look like https://your-domain/tg/your-secret-path",
                TELEGRAM_WEBHOOK_URL,
            )
