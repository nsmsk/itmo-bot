import time
import httpx
import pandas as pd
import openai
import asyncio
from bs4 import BeautifulSoup
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
import os


# API ключи
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация FastAPI
app = FastAPI()

# Инициализация OpenAI API
client = openai.OpenAI(api_key=OPENAI_API_KEY)

class PredictionRequest(BaseModel):
    query: str
    id: int

class PredictionResponse(BaseModel):
    id: int
    answer: Optional[int] = None
    reasoning: str
    sources: List[HttpUrl]

# Функция поиска в Google API, возвращающая DataFrame с результатами
def google_search(api_key: str, search_engine_id: str, query: str, **params) -> pd.DataFrame:
    """
    Выполняет поиск в Google API и возвращает DataFrame с результатами (только столбец links).
    """
    base_url = "https://www.googleapis.com/customsearch/v1"
    search_results = []

    # Выполняем один запрос (ограничиваем выдачу 10 результатами)
    response = httpx.get(
        base_url,
        params={
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            **params
        }
    )
    response.raise_for_status()  # Если ошибка, выбрасывает исключение
    search_results.extend(response.json().get("items", []))

    # Преобразуем в DataFrame и извлекаем только ссылки
    df = pd.json_normalize(search_results)

    if "link" not in df.columns:
        raise ValueError("Google API не вернул ссылки в результатах поиска")

    return df[["link"]]

# Функция извлечения текста из первых 3 ссылок
async def extract_text_from_url(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

    paragraphs = [p.get_text() for p in soup.find_all("p")]
    return " ".join(paragraphs[:5])  # Ограничиваемся 5 абзацами

# Функция обращения к GPT-4o-mini
def get_itmo_response(query_text: str, context: str) -> str:
    """
    Отправляет запрос к gpt-4o-mini, прося вернуть ответ в формате JSON.
    Возвращает валидный JSON-ответ.
    """

    # системный промпт с правилами
    system_prompt = (
        "Ты — помощник, который отвечает строго в формате JSON.\n"
        "Тебе даны поля:\n"
        "1) id (число)\n"
        "2) answer (число от 1 до 10 или null)\n"
        "3) reasoning (строка)\n"
        "4) sources (массив строк)\n\n"
        "Обязательно верни валидный JSON, без добавления текста вне JSON.\n"
        "Если вопрос не предполагает выбор из вариантов, верни null в answer.\n"
        "В раздел sources прикрепляй ссылки, которые даны тебе в контексте.\n"
        "В конце раздела reasoning напиши, что ответ был сгенерирован при помощи gpt-4o-mini.\n"
    )

    # Собираем промпт для пользователя
    user_prompt = (
        f"Вот запрос пользователя:\n{query_text}\n\n"
        f"Вот контекст:\n{context}\n\n"
        "Верни JSON со структурой:\n"
        "{\n"
        '  "id": <число>,\n'
        '  "answer": <число или null>,\n'
        '  "reasoning": "<строка>",\n'
        '  "sources": ["<строка>", "<строка>", ...]\n'
        "}\n\n"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return completion.choices[0].message.content


@app.post("/api/request", response_model=PredictionResponse)
async def predict(body: PredictionRequest):
    try:
        # 1. Поиск в Google API и получение DataFrame с результатами
        df = google_search(GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID, body.query)

        # 2. Извлечение первых 2 ссылок
        links = df["link"].dropna().tolist()[:2]

        # 3. Извлечение текста из этих ссылок
        texts = await asyncio.gather(*[extract_text_from_url(link) for link in links])

        # 4. Формируем контекст из полученного текста
        context = "\n".join(texts)

        # 5. Анализ через GPT-4o-mini
        response_json = get_itmo_response(body.query, context)

        # 6. Парсим ответ и возвращаем PredictionResponse
        return PredictionResponse.parse_raw(response_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
