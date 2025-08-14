from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


from aiogram import BaseMiddleware

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async for session in get_db():
            data['session'] = session
            return await handler(event, data)
