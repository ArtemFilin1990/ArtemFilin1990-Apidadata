# Деплой на Amvera — DaData Telegram bot

Документ синхронизирован с текущим кодом репозитория:
- HTTP-приложение — `FastAPI` (`app.py`),
- старт в Amvera — через `server.py` (читает `PORT`, запускает `uvicorn`),
- режимы бота: `webhook` (по умолчанию) и `polling` (`POLLING_MODE=1`).

## 1) Подготовьте ключи и токены

Нужны:
- `TELEGRAM_BOT_TOKEN` (BotFather),
- `DADATA_API_KEY`,
- `DADATA_SECRET_KEY`.

> В текущем коде переменные `FNS_LOGIN`/`FNS_PASSWORD` не используются, добавлять их не нужно.

## 2) Локально подготовьте проект

```bash
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env`:

Удалить webhook:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/deleteWebhook"
```

Установить webhook:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<your-domain>/tg/<secret-path>"
``