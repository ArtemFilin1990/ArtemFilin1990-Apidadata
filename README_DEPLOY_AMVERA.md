# Деплой на Amvera — DaData Telegram bot

Документ синхронизирован с текущим кодом репозитория:
- HTTP-приложение — `FastAPI` (`app.py`),
- старт в Amvera — через `app.py` (читает `PORT`, запускает `uvicorn`),
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

## 4) Проверьте структуру файлов в контейнере (критично)

Причина ошибки `can't open file '/app/app.py'` часто не в `run.scriptName`, а в том, что проект попал в контейнер с лишней вложенной папкой (например, `/app/Apidadata-main/app.py` вместо `/app/app.py`).

В рабочем варианте после распаковки должно быть так:

```text
/app/app.py
/app/server.py
/app/web.py
/app/config.py
/app/tg_bot.py
/app/services/...
/app/ui/...
```

Что проверить:
- если деплой из GitHub-репозитория — используйте корень репозитория (в этом репо файлы уже лежат корректно в корне);
- если деплой из zip/артефакта — перепакуйте архив без верхней папки `Apidadata-main/`, чтобы файлы лежали сразу в корне архива.

## 5) Настройте run.scriptName

Основной режим (рекомендуется):
- `run.scriptName = app.py`

Это запускает `uvicorn` и корректно поднимает HTTP webhook-сервис.

Если в логах ошибка вида `can't open file '/app/app.py'`, сначала проверьте структуру файлов в контейнере (пункт выше). Переключение entrypoint не исправит проблему, если `app.py` отсутствует по пути `/app/app.py`.

## 6) Установите webhook Telegram

Удалить старый webhook:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/deleteWebhook"
```

Установить новый webhook:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<your-domain>/tg/<secret-path>"
```

## 7) Диагностика типовых ошибок

### `can't open file '/app/app.py'`
Причина: в контейнер попал архив с вложенной папкой (например, `Apidadata-main/`), и `app.py` оказался не по пути `/app/app.py`.

Решение:
1. Перепроверьте источник деплоя (лучше из GitHub-репозитория напрямую),
2. Если деплой из zip — перепакуйте без верхней папки,
3. Убедитесь, что в контейнере есть `/app/app.py` (и опционально `/app/server.py`),
4. Используйте `run.scriptName = app.py`.

### `TelegramUnauthorizedError`
Причина: недействительный/отозванный токен.

Решение:
1. В BotFather выполнить revoke и получить новый токен,
2. Обновить `TELEGRAM_BOT_TOKEN` в ENV Amvera,
3. Перезапустить сервис.
