"""Application configuration loaded from environment variables."""
import logging
import os
import re

TELEGRAM_TOKEN_RE = re.compile(r"\d+:[A-Za-z0-9_-]{20,}")
TRUTHY_VALUES = {"1", "true", "yes", "on"}

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
POLLING_MODE: bool = os.getenv("POLLING_MODE", "0").strip().lower() in TRUTHY_VALUES
DADATA_API_KEY: str = os.getenv("DADATA_API_KEY", "")
DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY", "")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
DADATA_TIMEOUT: float = float(os.getenv("DADATA_TIMEOUT", "5.0"))


def _env(name: str) -> str:
    """Return normalized environment variable value."""
    return os.getenv(name, "").strip()


def validate() -> None:
    """Fail fast if required environment variables are missing."""
    polling_mode = _env("POLLING_MODE").lower() in TRUTHY_VALUES
    token = _env("TELEGRAM_BOT_TOKEN")
    webhook_url = _env("TELEGRAM_WEBHOOK_URL")

    required_values = {
        "TELEGRAM_BOT_TOKEN": token,
        "DADATA_API_KEY": _env("DADATA_API_KEY"),
        "DADATA_SECRET_KEY": _env("DADATA_SECRET_KEY"),
    }
    if not polling_mode:
        required_values["TELEGRAM_WEBHOOK_URL"] = webhook_url

    missing = [name for name, value in required_values.items() if not value]
    if missing:
        msg = f"FATAL: Missing required ENV variables: {', '.join(missing)}"
        logger.critical(msg)
        raise RuntimeError(msg)

    # Warn early about suspicious Telegram token format to simplify troubleshooting.
    if not TELEGRAM_TOKEN_RE.fullmatch(token):
        logger.warning(
            "TELEGRAM_BOT_TOKEN doesn't match expected format '<digits>:<token>'"
        )

    # Validate webhook URL format when in webhook mode
    if not polling_mode and "/tg/" not in webhook_url:
        logger.warning(
            "TELEGRAM_WEBHOOK_URL=%s does not contain '/tg/' path prefix. "
            "The webhook endpoint is mounted at POST /tg/<secret>, "
            "so the URL must look like https://your-domain/tg/your-secret-path",
            webhook_url,
        )
