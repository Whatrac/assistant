import uvicorn
from fastapi import FastAPI, Request
from aiogram import types
from app.bot import bot, dp
from app.config import HOST, PORT, WEBHOOK_URL
from app.handlers.general import set_bot_commands
from app.scheduler import Scheduler
from app.db import engine, Base
import asyncio
from aiogram.types import Update

app = FastAPI()



@app.on_event("startup")
async def on_startup():
    # Создаём таблицы (sqlite, postgresql и т.п.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    await set_bot_commands(bot)
    # Запускаем шедулер
    loop = asyncio.get_event_loop()
    sched = Scheduler(bot, loop=loop)
    sched.start()
    print("Бот запущен!")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
