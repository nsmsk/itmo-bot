# ITMO-Bot

## Описание
**ITMO-Bot** — это FastAPI-сервис, развернутый на платформе **Railway.app**, который позволяет обрабатывать вопросы и предоставлять подробные ответы, используя модель GPT-4.0-mini и предоставленные источники данных.

---

## Запуск локально

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/nsmsk/itmo-bot.git
   cd itmo-bot
   ```

2. **Создайте и настройте файл `.env`:**
   В корне проекта создайте файл `.env` со следующим содержимым:
   ```env
   OPENAI_API_KEY=ваш_ключ_от_OpenAI
   GOOGLE_API_KEY=ваш_ключ_от_Google
   GOOGLE_SEARCH_ENGINE_ID=ваш_ID_поисковой_системы
   ```

3. **Соберите и запустите контейнер:**
   ```bash
   docker-compose up --build
   ```

4. **Откройте локальный сервер:**
   Перейдите по адресу [http://localhost:8080](http://localhost:8080) для доступа к API.

---

## Развертывание на Railway

1. **Импортируйте репозиторий в Railway:**
   - Зайдите на [Railway.app](https://railway.app) и подключите ваш GitHub.
   - Выберите репозиторий `itmo-bot`.

2. **Настройте переменные окружения:**
   Во вкладке **Variables** добавьте:
   ```
   OPENAI_API_KEY=ваш_ключ_от_OpenAI
   GOOGLE_API_KEY=ваш_ключ_от_Google
   GOOGLE_SEARCH_ENGINE_ID=ваш_ID_поисковой_системы
   ```

3. **Expose service:**
   - Перейдите в **Settings** → **Networking**.
   - Нажмите "Generate Domain" для создания публичного URL.

4. **Сервис будет доступен по вашему публичному URL:**
   ```
   https://itmo-bot-production.up.railway.app
   ```

---

## Примеры запросов

### 1. **POST /api/request**
Отправьте POST-запрос на эндпоинт `/api/request`.

Пример через `curl`:
```bash
curl -X POST 'https://itmo-bot-production.up.railway.app/api/request' \
-H 'Content-Type: application/json' \
-d '{
    "query": "Когда был основан ИТМО?",
    "id": 1
}'
```

Пример ответа:
```json
{
  "id": 1,
  "answer": 1,
  "reasoning": "Университет ИТМО был основан в 1900 году в Санкт-Петербурге, что делает его одним из старейших учебных заведений в России. Этот факт подтверждается историей учебного заведения, восходящей к 26 марта 1900 года.",
  "sources": [
    "https://science.itmo.ru/",
    "https://edu.itmo.ru/"
  ]
}
```

---

## Стек технологий
- Python
- FastAPI
- Docker
- Railway
- OpenAI API
- Google Custom Search API

---

## TODO
- [ ] Добавить больше эндпоинтов.
- [ ] Улучшить обработку ошибок.
- [ ] Настроить более подробное логирование.
