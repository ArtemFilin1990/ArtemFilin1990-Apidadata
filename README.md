# DaData MAX — Telegram-бот

Telegram-бот для проверки юрлиц/ИП по ИНН/ОГРН и валидации персональных данных (телефон, паспорт РФ, авто) через [DaData API](https://dadata.ru/api/).

## Возможности

| Функция | API DaData | Описание |
| ------- | --------- | -------- |
| 🔎 Проверить ИНН | `findById/party` | Карточка юрлица/ИП: название, статус, руководитель, адрес, ОКВЭД, численность, недостоверность |
| 📄 Подробно | `findById/party` | Расширенная карточка (ОКПО, ОКАТО, ОКТМО, учредители и т.д.) |
| 🏢 Филиалы | `findById/party` (BRANCH) | Список филиалов компании |
| 🔗 Аффилированность | `findAffiliated/party` | Связанные юрлица по ИНН руководителя/учредителей |
| 📍 Адрес | `findById/address` | Детализация адреса по ФИАС |
| 🏦 Банк | `findById/bank` | Информация о банке по БИК |
| 📱 Телефон | `clean/phone` | Нормализация, оператор, регион, часовой пояс |
| 🪪 Паспорт РФ | `clean/passport` | Проверка серии/номера, статус действительности |
| 🚗 Авто | `clean/vehicle` | Распознавание марки/модели из строки |

## Безопасность и приватность

- Бот **не добывает** чужие данные — только проверяет то, что ввёл пользователь.
- В логах и кэше **не хранится** полный телефон/паспорт: только маска + SHA-256 хэш.
- В выдаче телефон и паспорт показываются **маскированно**.

## Структура проекта

```text
.
├── app.py                        # FastAPI-приложение (/health + Telegram webhook)
├── tg_bot.py                     # Инициализация бота и обработчики сообщений
├── config.py                     # Чтение/валидация ENV
├── services/                     # Клиент DaData, кэш, утилиты ИНН
├── ui/                           # Форматирование ответов и клавиатуры
├── tests/                        # Unit/smoke тесты
├── requirements.txt
└── .env.example
```

## Установка и запуск

### 1. Клонируйте / скопируйте проект

### 2. Создайте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

Скопируйте `.env.example` → `.env` и заполните:

```dotenv
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
DADATA_API_KEY=ваш_api_key
DADATA_SECRET_KEY=ваш_secret_key
TELEGRAM_WEBHOOK_URL=https://your-domain.example/tg/your-secret-path
```

- `TELEGRAM_BOT_TOKEN` — получите у [@BotFather](https://t.me/BotFather)
- `DADATA_API_KEY` и `DADATA_SECRET_KEY` — в [личном кабинете DaData](https://dadata.ru/profile/)

> **Важно:** Clean-методы (телефон/паспорт/авто) требуют `X-Secret` и ходят на `cleaner.dadata.ru`. Убедитесь, что `DADATA_SECRET_KEY` указан.

### 5. Запустите приложение

```bash
python server.py
```

- Приложение работает в режиме webhook и должно быть запущено как HTTP-сервис.

### Fallback-режим polling (если webhook недоступен)

Если бот не отвечает из-за проблем с публичным webhook URL, можно временно включить polling:

```dotenv
POLLING_MODE=1
```

В этом режиме `TELEGRAM_WEBHOOK_URL` не обязателен, а бот получает апдейты через long polling.

## Деплой на Amvera

1. Добавьте переменные окружения в настройках проекта Amvera:
   - `TELEGRAM_BOT_TOKEN`
   - `DADATA_API_KEY`
   - `DADATA_SECRET_KEY`

2. Используйте `requirements.txt` для автоматической установки зависимостей.

Подробную инструкцию смотрите в [README_DEPLOY_AMVERA.md](./README_DEPLOY_AMVERA.md).

## Устранение проблем деплоя

Если возникли проблемы при развертывании бота (ошибки с точкой входа, токеном, webhook и т.д.), смотрите подробное руководство:

📖 **[DEPLOYMENT_TROUBLESHOOTING.md](./DEPLOYMENT_TROUBLESHOOTING.md)**

Типичные проблемы:
- ❌ `can't open file '/app/app.py'` — неверная точка входа
- ❌ `TelegramUnauthorizedError` — неверный или отозванный токен
- ❌ Webhook не получает обновления — неправильный URL
- ❌ Отсутствующие переменные окружения

## Кэширование

| Тип данных | TTL | Ключ кэша |
| --------- | --- | --------- |
| Карточка компании | 7 дней | `company:{query}` |
| Аффилированность | 7 дней | `aff:{inn}` |
| Clean (телефон/паспорт/авто) | 24 часа | `clean:{type}:{sha256(input)}` |

## Rate-limit

- Token bucket: 10 RPS к DaData API
- На 429/5xx: экспоненциальный backoff (0.5s → 1s → 2s), макс. 3 попытки

## API-эндпоинты

| Метод | URL | Назначение |
| ----- | --- | --------- |
| `findById/party` | `suggestions.dadata.ru/...` | Карточка юрлица/ИП |
| `findAffiliated/party` | `suggestions.dadata.ru/...` | Аффилированные лица |
| `findById/address` | `suggestions.dadata.ru/...` | Детализация адреса |
| `findById/bank` | `suggestions.dadata.ru/...` | Информация о банке |
| `clean/phone` | `cleaner.dadata.ru/api/v1/clean/phone` | Нормализация телефона |
| `clean/passport` | `cleaner.dadata.ru/api/v1/clean/passport` | Проверка паспорта |
| `clean/vehicle` | `cleaner.dadata.ru/api/v1/clean/vehicle` | Распознавание авто |
