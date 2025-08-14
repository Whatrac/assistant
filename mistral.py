import os
import random
import httpx
from app.config import MISTRAL_API_KEY

async def call_mistral(prompt: str) -> str | None:
    if not MISTRAL_API_KEY:
        return None
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
    payload = {
        "model": "mistral-small",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        j = r.json()
        try:
            return j["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

def fallback_morning_exercise():
    arr = [
        "3 минуты растяжки: наклоны и вращения",
        "5 минут лёгкой зарядки: приседания и отжимания",
        "Йога: 5 поз на 7 минут",
    ]
    return random.choice(arr)

def fallback_motivation():
    arr = [
        "Каждый шаг — это прогресс. Продолжай!",
        "Маленькие привычки решают большие цели.",
        "Улыбнись — ты делаешь отличную работу.",
    ]
    return random.choice(arr)

def fallback_question_of_day():
    arr = [
        "Что сегодня тебя вдохновило утром?",
        "Какая одна маленькая цель на сегодня?",
        "Что хочешь сделать иначе сегодня?",
    ]
    return random.choice(arr)
