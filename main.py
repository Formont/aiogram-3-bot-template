from aiogram import Bot, Dispatcher

from bot.middlewares import DBMiddleware
from bot.handlers import setup_routers
from db.engine import session_maker, create_tables
from config import TOKEN
import asyncio

bot = Bot(TOKEN)
dp = Dispatcher()

async def on_startup():
    await create_tables()
    print("Bot has been started")
    
async def main():
    dp.startup.register(on_startup)
    dp.update.middleware(DBMiddleware(session_maker))
    dp.include_router(setup_routers())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
