import asyncio
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from basic.handlers import router
# from administrate.admin import router_admin
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties

from config import API_TOKEN


logging.basicConfig(level=logging.INFO)



bot = Bot(token=API_TOKEN, session=AiohttpSession(), default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())



dp.include_router(router)


async def on_startup():
    logging.info("Бот запущен")

async def on_shutdown():
    await dp.storage.close()
    await bot.close()
    logging.info("Бот остановлен")

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
