import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, and_

from aiogram import Bot

from app.db import AsyncSessionLocal
from app.handlers.qutoes import get_random_quote
from app.models import Run, User
from app.mistral import (
    call_mistral,
    fallback_morning_exercise,
    fallback_motivation,
    fallback_question_of_day,
)

log = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, bot, loop=None):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.loop = loop or asyncio.get_event_loop()

    def start(self):
        # Добавляем задачи в планировщик с корректной обёрткой для async функций
        self.scheduler.add_job(
            self._async_job_wrapper(self.send_motivation),
            "interval",
            hours=3,
            next_run_time=datetime.utcnow(),
            id="motivation_job",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._async_job_wrapper(self.send_evening_question),
            CronTrigger(hour=18, minute=0),
            id="evening_question_job",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._async_job_wrapper(self.send_weekly_summary),
            CronTrigger(day_of_week="sun", hour=18, minute=0),
            id="weekly_summary_job",
            replace_existing=True,
        )

        # Запуск планировщика
        self.scheduler.start()
        log.info("Scheduler started with jobs: %s", self.scheduler.get_jobs())

    def _async_job_wrapper(self, coro_func):
        def sync_wrapper():
            asyncio.run_coroutine_threadsafe(self._run_and_log_errors(coro_func), self.loop)
        return sync_wrapper

    async def _run_and_log_errors(self, coro_func):
        try:
            await coro_func()
        except Exception as e:
            log.error(f"Ошибка в планировщике: {e}")

    async def get_all_chat_ids(self) -> list[int]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.chat_id).where(User.chat_id.isnot(None))
            )
            chat_ids = [row[0] for row in result.all()]
        return chat_ids

    async def send_to_all_users(self, text: str):
        chat_ids = await self.get_all_chat_ids()
        for chat_id in chat_ids:
            try:
                await self.bot.send_message(chat_id, text)
            except Exception as e:
                log.error(f"Не удалось отправить сообщение пользователю {chat_id}: {e}")

    async def safe_call_mistral(self, prompt: str, fallback: str) -> str:
        try:
            res = await call_mistral(prompt)
            return res or fallback
        except Exception as e:
            log.error(f"Mistral error: {e}")
            return fallback

    async def send_motivation(self):
        text = get_random_quote()
        await self.send_to_all_users(text)

    async def send_evening_question(self):
        await self.send_to_all_users("Как прошёл твой день? Поделишься парой слов?")

    async def send_weekly_summary(self):
        async with AsyncSessionLocal() as session:
            today = datetime.utcnow().date()
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)

            result = await session.execute(
                select(Run).where(
                    and_(
                        Run.created_at >= datetime.combine(last_monday, datetime.min.time()),
                        Run.created_at <= datetime.combine(last_sunday, datetime.max.time()),
                    )
                )
            )
            runs = result.scalars().all()

        total_runs = len(runs)
        total_km = sum(r.distance_km for r in runs)
        total_cal = sum(r.calories for r in runs)

        summary = (
            f"Пробежек: {total_runs}\n"
            f"Дистанция: {total_km:.2f} км\n"
            f"Калорий: {total_cal}"
        )
        advice = await self.safe_call_mistral(
            f"Weekly summary:\n{summary}\nДай короткий дружелюбный совет на русском (2 строки).",
            "Попробуй поставить небольшую цель на следующую неделю и отслеживать её ежедневно.",
        )

        await self.send_to_all_users(f"Еженедельная сводка:\n{summary}\n\nСовет:\n{advice}")

    async def send_morning_routine_to_user(self, chat_id: int):
        exercise = await self.safe_call_mistral(
            "Дай короткий комплекс утренней зарядки (1 предложение, по-русски).",
            fallback_morning_exercise(),
        )
        question = await self.safe_call_mistral(
            "Дай креативный вопрос для утра (1 предложение, по-русски).",
            fallback_question_of_day(),
        )
        try:
            await self.bot.send_message(
                chat_id,
                f"Доброе утро! Зарядка на сегодня: {exercise}\nВопрос дня: {question}",
            )
        except Exception as e:
            log.error(f"Не удалось отправить утреннее сообщение {chat_id}: {e}")
