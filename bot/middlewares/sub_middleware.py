from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from db import orm_queries as db
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.builders import build_sub_check_kb
from aiogram.fsm.context import FSMContext
from bot.states.userStates import ChangeNameState

class SubCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # We only check Message and CallbackQuery
        user_id = None
        bot = data.get("bot")
        
        if isinstance(event, Message):
            user_id = event.from_user.id
            text = event.text
            if text and text.startswith("/admin"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data.startswith("admin_") or event.data.startswith("sub_verify_check"):
                return await handler(event, data)
                
        if not user_id:
            return await handler(event, data)
            
        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)
            
        # Ensure user is added to DB even if they hit the subscription wall
        await db.add_user(session, user_id, event.from_user.username or event.from_user.first_name)
        
        user = await db.get_user(session, user_id)
        
        sponsors = await db.get_active_sponsors(session)
        if sponsors:
            unsubscribed_sponsors = []
            for sponsor in sponsors:
                try:
                    member = await bot.get_chat_member(chat_id=sponsor.channel_id, user_id=user_id)
                    if member.status in ['left', 'kicked', 'restricted']:
                        unsubscribed_sponsors.append(sponsor)
                except Exception as e:
                    # If bot is not in the channel or user hasn't started the bot, skip or count as unsubscribed.
                    # It's better to assume unsubscribed if we can't fetch, or maybe log the error.
                    unsubscribed_sponsors.append(sponsor)
                    
            if unsubscribed_sponsors:
                text = "⚠️ <b>Для использования бота необходимо подписаться на каналы наших спонсоров:</b>"
                kb = build_sub_check_kb(unsubscribed_sponsors)
                
                if isinstance(event, Message):
                    await event.answer(text, reply_markup=kb)
                elif isinstance(event, CallbackQuery):
                    await event.message.answer(text, reply_markup=kb)
                    await event.answer()
                return

        state: FSMContext = data.get("state")
        current_state = await state.get_state() if state else None
        
        if user and (not user.name or len(user.name) < 5) and current_state != ChangeNameState.waiting_for_name.state:
            text = "⚠️ Ваше имя слишком короткое или уже занято.\nПожалуйста, отправьте мне новое уникальное имя (от 5 до 30 символов) для игры. В дальнейшем вы сможете изменить его в Профиле."
            if state:
                await state.set_state(ChangeNameState.waiting_for_name)
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text)
                await event.answer()
            return
            
        return await handler(event, data)
