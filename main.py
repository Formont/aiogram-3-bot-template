from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.middlewares import DBMiddleware
from bot.handlers import setup_routers
from db.engine import session_maker, create_tables

from bot.utils.payments.client import cp
from config import TOKEN
import asyncio

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
cp._kwargs["bot"] = bot
crypto_polling_task = None

async def on_startup():
    global crypto_polling_task
    await create_tables()
    crypto_polling_task = asyncio.create_task(cp.start_polling())
    print("Bot has been started")

async def on_shutdown():
    if crypto_polling_task and not crypto_polling_task.done():
        await cp.stop_polling()
        await crypto_polling_task
    
async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DBMiddleware(session_maker))
    dp.include_router(setup_routers())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
