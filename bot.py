from aiogram import Bot, Dispatcher
from app.config import TELEGRAM_TOKEN
from app.db import DbSessionMiddleware
from app.handlers import general
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(general.router)

dp.update.middleware(DbSessionMiddleware())
