# Руководство по устранению проблем развертывания

Этот документ описывает типичные проблемы при развертывании бота и способы их решения.

## Проблема 1: Ошибка "can't open file '/app/app.py'"

### Причина
Чаще всего проблема в структуре артефакта: проект попадает в контейнер с лишней верхней папкой (например, `/app/Apidadata-main/app.py`), поэтому файла по пути `/app/app.py` нет.

### Решение

В данном репозитории **app.py уже существует** и является правильной точкой входа для FastAPI-приложения, но важно, чтобы файл лежал именно в `/app/app.py`.

Проверочная структура в контейнере:
```
/app/app.py
/app/server.py
/app/web.py
/app/config.py
/app/tg_bot.py
/app/services/...
/app/ui/...
```

#### Для Amvera
1. Убедитесь, что деплой выполняется из корня GitHub-репозитория (без дополнительной вложенной директории).
2. Если используете zip, перепакуйте архив так, чтобы внутри не было верхней папки `Apidadata-main/`.
3. Проверьте `amvera.yml`:
```yaml
run:
  scriptName: app.py
  main: app.py
```

Файл `app.py` теперь может запускаться напрямую через uvicorn (в `if __name__ == "__main__"`), поэтому для Amvera рекомендуется `scriptName: app.py`.

#### Для других платформ (Vercel, Render, Railway и т.д.)

**Вариант 1: Использование app.py (рекомендуется)**
```bash
python app.py
```

**Вариант 2: Прямой запуск через uvicorn**
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Вариант 3: Для Procfile (Heroku, Render)**
```
web: python app.py
```

### Структура проекта
```
.
├── app.py          # FastAPI приложение с webhook endpoint
├── server.py       # Entrypoint для Amvera (запускает uvicorn)
├── tg_bot.py       # Логика Telegram бота и обработчики
├── config.py       # Конфигурация и валидация ENV переменных
└── ...
```

## Проблема 2: TelegramUnauthorizedError (401 Unauthorized)

### Причина
Токен бота неверный, отозван или в неправильном формате.

### Решение

1. **Сгенерируйте новый токен через @BotFather:**
   - Откройте @BotFather в Telegram
   - Отправьте команду `/mybots`
   - Выберите своего бота
   - Нажмите "API Token"
   - Нажмите "Revoke current token" (если необходимо)
   - Скопируйте новый токен

2. **Формат токена должен быть:**
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
   ```
   - Числовая часть (8-10 цифр)
   - Двоеточие
   - Буквенно-цифровая часть (30+ символов)

3. **Обновите переменную окружения:**
   ```bash
   TELEGRAM_BOT_TOKEN=ваш_новый_токен
   ```

4. **Перезапустите приложение**

### Проверка токена
Вы можете проверить токен вручную:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

Если токен верный, вы получите информацию о боте. Если нет - ошибку 401.

## Проблема 3: Webhook не получает обновления

### Причина
Неправильно настроен webhook URL или Telegram не может достучаться до сервера.

### Решение

1. **Проверьте формат TELEGRAM_WEBHOOK_URL:**
   ```
   https://your-domain.com/tg/your-secret-path
   ```

   ⚠️ **Важно:** URL должен содержать `/tg/` в пути!

2. **Проверьте текущий webhook:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
   ```

3. **Удалите старый webhook:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook"
   ```

4. **Установите новый webhook:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-domain.com/tg/your-secret-path"
   ```

5. **Проверьте, что сервер доступен:**
   ```bash
   curl https://your-domain.com/health
   ```

   Должен вернуть: `{"status":"ok","mode":"webhook","webhook_path":"/tg/your-secret-path"}`

### Альтернатива: Polling режим

Если webhook временно недоступен, используйте polling:
```bash
POLLING_MODE=1
```

⚠️ **Внимание:** Polling не рекомендуется для production, так как требует постоянного соединения.

## Проблема 4: Ошибки валидации конфигурации

### Причина
Отсутствуют обязательные переменные окружения.

### Решение

1. **Скопируйте .env.example в .env:**
   ```bash
   cp .env.example .env
   ```

2. **Заполните все обязательные переменные:**

   **Обязательные для всех режимов:**
   - `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
   - `DADATA_API_KEY` - API ключ DaData
   - `DADATA_SECRET_KEY` - секретный ключ DaData

   **Обязательные для webhook режима (по умолчанию):**
   - `TELEGRAM_WEBHOOK_URL` - URL для webhook

   **Опциональные:**
   - `POLLING_MODE=1` - для polling режима
   - `LOG_LEVEL=INFO` - уровень логирования
   - `DADATA_TIMEOUT=5.0` - таймаут запросов к DaData
   - `PORT=8000` - порт сервера

3. **Проверка конфигурации:**

   При старте приложение вызывает `config.validate()`, которая проверяет:
   - Наличие всех обязательных переменных
   - Формат токена Telegram
   - Формат webhook URL (должен содержать `/tg/`)

## Проблема 5: Ошибки при запросах к DaData API

### Причина
Неверные или отсутствующие API ключи DaData.

### Решение

1. **Получите ключи:**
   - Зарегистрируйтесь на https://dadata.ru
   - Перейдите в https://dadata.ru/profile/#info
   - Скопируйте "API key" и "Secret key"

2. **Установите переменные:**
   ```bash
   DADATA_API_KEY=ваш_api_ключ
   DADATA_SECRET_KEY=ваш_секретный_ключ
   ```

3. **Проверьте лимиты:**
   - У DaData есть лимиты на количество запросов
   - Проверьте баланс и тарифный план

## Проверка работоспособности

### 1. Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env и заполните все значения

# Запуск в polling режиме (для разработки)
export POLLING_MODE=1
python app.py

# Запуск в webhook режиме (для production)
export POLLING_MODE=0
export TELEGRAM_WEBHOOK_URL=https://your-domain.com/tg/secret
python app.py
```

### 2. Проверка endpoints

```bash
# Health check
curl http://localhost:8000/health

# Должен вернуть:
# {"status":"ok","mode":"polling|webhook","webhook_path":"..."}
```

### 3. Проверка логов

При старте вы должны увидеть:
```
INFO:app:Telegram mode: webhook|polling
INFO:tg_bot:TeleBot instance created successfully
INFO:app:Webhook URL: https://***:***/tg/***  # (токен замаскирован)
```

Если видите WARNING или ERROR - проверьте конфигурацию.

## Дополнительные ресурсы

- [Документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Документация DaData API](https://dadata.ru/api/)
- [README проекта](./README.md)
- [Инструкция по деплою на Amvera](./README_DEPLOY_AMVERA.md)

## Получение помощи

Если проблема не решена:

1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения установлены правильно
3. Проверьте формат токена и webhook URL
4. Используйте skill "error-hunter-fixer-2.skill" для автоматического поиска и исправления ошибок
5. Создайте issue в репозитории с подробным описанием проблемы и логами
