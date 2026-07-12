from aiogram import Router, F
from aiogram.types import CallbackQuery, ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from sqlalchemy.ext.asyncio import AsyncSession
from db import orm_queries as db

router = Router()

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def new_chat_member(update: ChatMemberUpdated, session: AsyncSession):
    try:
        channel_id = update.chat.id
        sponsor = await db.get_active_sponsor_by_channel(session, channel_id)
        
        if sponsor:
            # Сравниваем ссылку
            if update.invite_link and update.invite_link.invite_link == sponsor.invite_link:
                user_id = update.from_user.id
                await db.check_user_sponsor_reward(session, user_id, sponsor.id)
    except Exception as e:
        print(f"Error tracking invite link: {e}")

@router.callback_query(F.data == "sub_verify_check")
async def verify_subscription(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.fromuser.id if hasattr(callback, 'fromuser') else callback.from_user.id
    sponsors = await db.get_active_sponsors(session)
    
    if not sponsors:
        await callback.message.delete()
        await callback.answer("✅ Нет активных спонсоров. Доступ разрешен!", show_alert=True)
        return
        
    unsubscribed = False
    for sponsor in sponsors:
        try:
            member = await callback.bot.get_chat_member(chat_id=sponsor.channel_id, user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                unsubscribed = True
                break
        except Exception:
            unsubscribed = True
            break
            
    if unsubscribed:
        await callback.answer("❌ Вы подписались не на все каналы!", show_alert=True)
    else:
        await callback.message.delete()
        await callback.answer("✅ Подписка подтверждена! Доступ разрешен.", show_alert=True)
