import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./assistant.db")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 3465))
MORNING_TIME = os.getenv("MORNING_TIME", "07:00")
