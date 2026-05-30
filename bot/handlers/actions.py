from aiogram import Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.types import ChatMemberUpdated

from sqlalchemy.ext.asyncio import AsyncSession
from db import orm_queries as db

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def member_blocked_bot(event: ChatMemberUpdated, session: AsyncSession):
    await db.set_active(session, event.from_user.id, 0)

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def member_unblocked_bot(event: ChatMemberUpdated, session: AsyncSession):
    await db.set_active(session, event.from_user.id)