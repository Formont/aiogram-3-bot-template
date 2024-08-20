from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.filters import AdminFilter
from db import orm_queries as db
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    await db.add_user(session, message.from_user.id)
    await message.answer("Hello")

@router.message(Command("admin"), AdminFilter())
async def cmd_start(message: Message, session: AsyncSession):
    await message.answer("Hello, admin!")