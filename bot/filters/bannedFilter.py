from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from db import orm_queries as db

class NotBannedFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, session: AsyncSession) -> bool:
        user_id = event.from_user.id
        user = await db.get_user(session, user_id)
        if user and user.is_blocked:
            if isinstance(event, Message):
                await event.answer("🚫 Вы заблокированы администрацией и не можете использовать бота.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Вы заблокированы администрацией.", show_alert=True)
            return False
        return True
