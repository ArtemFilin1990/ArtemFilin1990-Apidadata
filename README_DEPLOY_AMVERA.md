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

## 3) Настройте ENV в Amvera

Минимально:
- `TELEGRAM_BOT_TOKEN`
- `DADATA_API_KEY`
- `DADATA_SECRET_KEY`
- `TELEGRAM_WEBHOOK_URL=https://<your-domain>/tg/<secret-path>`

Опционально для временного fallback:
- `POLLING_MODE=1` — если webhook временно недоступен.

## 4) Настройте run.scriptName

Основной режим (рекомендуется):
- `run.scriptName = server.py`

Это запускает `uvicorn` и корректно поднимает HTTP webhook-сервис.

Аварийное восстановление при неправильной точке входа:
- если в логах ошибка вида `can't open file '/app/app.py'`, значит Amvera пытается запустить несуществующий файл;
- временно переключите `run.scriptName = bot.py`, чтобы убрать цикл падений;
- затем верните `run.scriptName = server.py` после проверки, что в корне есть `app.py` и `server.py`.

## 5) Установите webhook Telegram

Удалить старый webhook:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/deleteWebhook"
```

Установить новый webhook:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<your-domain>/tg/<secret-path>"
```

## 6) Диагностика типовых ошибок

### `can't open file '/app/app.py'`
Причина: неверный `run.scriptName` в Amvera.

Решение:
1. Срочно поставить `bot.py` (стабилизация старта),
2. Затем переключить обратно на `server.py` для webhook-режима.

### `TelegramUnauthorizedError`
Причина: недействительный/отозванный токен.

Решение:
1. В BotFather выполнить revoke и получить новый токен,
2. Обновить `TELEGRAM_BOT_TOKEN` в ENV Amvera,
3. Перезапустить сервис.
