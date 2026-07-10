import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from bot.filters.adminFilter import AdminFilter
from bot.states import BroadcastState
from bot.keyboards.builders import build_broadcast_preview_kb, build_broadcast_message_kb, build_admin_back_kb
from db import orm_queries as db

router = Router()

@router.callback_query(F.data == "admin_broadcast", AdminFilter())
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📢 Отправьте сообщение для рассылки (текст, фото, видео и т.д.):", reply_markup=build_admin_back_kb())
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()

@router.message(BroadcastState.waiting_for_message, AdminFilter())
async def broadcast_message_received(message: Message, state: FSMContext):
    # Copy message as preview
    preview_msg = await message.copy_to(message.chat.id)
    
    # Send control panel
    control_msg = await message.answer("🛠 <b>Управление рассылкой</b>\n\nВыше предпросмотр вашего сообщения. Вы можете добавить inline-кнопки.", reply_markup=build_broadcast_preview_kb(False))
    
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        preview_message_id=preview_msg.message_id,
        control_message_id=control_msg.message_id,
        buttons=[]
    )
    await state.set_state(BroadcastState.editing_broadcast)

@router.callback_query(F.data == "broadcast_add_btn", AdminFilter(), BroadcastState.editing_broadcast)
async def broadcast_add_btn_start(callback: CallbackQuery, state: FSMContext):
    msg = await callback.message.answer("Отправьте текст и ссылку для кнопки в формате:\n<code>Текст:URL</code>\n\nНапример: <code>Мой канал:https://t.me/durov</code>")
    await state.update_data(prompt_msg_id=msg.message_id)
    await state.set_state(BroadcastState.waiting_for_button)
    await callback.answer()

@router.message(BroadcastState.waiting_for_button, AdminFilter())
async def broadcast_button_received(message: Message, state: FSMContext):
    text = message.text or ""
    parts = text.split(":", 1)
    
    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    
    if len(parts) != 2 or not parts[1].startswith("http"):
        await message.answer("⚠️ Неверный формат! Нужно: <code>Текст:URL (начинается с http/https)</code>. Попробуйте еще раз или нажмите Отмена в панели управления.")
        return

    btn_text, btn_url = parts[0].strip(), parts[1].strip()
    
    buttons = data.get("buttons", [])
    buttons.append({"text": btn_text, "url": btn_url})
    
    # Cleanup prompt
    try:
        await message.delete()
        if prompt_msg_id:
            await message.bot.delete_message(message.chat.id, prompt_msg_id)
    except Exception:
        pass
    
    # Update preview message
    preview_message_id = data.get("preview_message_id")
    try:
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=preview_message_id,
            reply_markup=build_broadcast_message_kb(buttons)
        )
    except Exception:
        pass
    
    # Update control message
    control_message_id = data.get("control_message_id")
    try:
        await message.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=control_message_id,
            reply_markup=build_broadcast_preview_kb(has_buttons=len(buttons) > 0)
        )
    except Exception:
        pass
        
    await state.update_data(buttons=buttons)
    await state.set_state(BroadcastState.editing_broadcast)

@router.callback_query(F.data == "broadcast_del_btn", AdminFilter(), BroadcastState.editing_broadcast)
async def broadcast_del_btn(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    
    if buttons:
        buttons.pop()
        
        preview_message_id = data.get("preview_message_id")
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=preview_message_id,
                reply_markup=build_broadcast_message_kb(buttons)
            )
        except Exception:
            pass
            
        try:
            await callback.message.edit_reply_markup(
                reply_markup=build_broadcast_preview_kb(has_buttons=len(buttons) > 0)
            )
        except Exception:
            pass
            
        await state.update_data(buttons=buttons)
        await callback.answer("Кнопка удалена")
    else:
        await callback.answer("Нет кнопок для удаления")

@router.callback_query(F.data == "broadcast_cancel", AdminFilter())
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.", reply_markup=build_admin_back_kb())
    await callback.answer()

@router.callback_query(F.data == "broadcast_send", AdminFilter(), BroadcastState.editing_broadcast)
async def broadcast_send(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    buttons = data.get("buttons", [])
    
    await callback.message.edit_text("⏳ Рассылка запущена! Это может занять некоторое время...")
    await state.clear()
    
    users = await db.get_all_active_user_ids(session)
    reply_markup = build_broadcast_message_kb(buttons)
    
    # Run broadcast in background
    asyncio.create_task(run_broadcast(
        bot=callback.bot,
        admin_id=callback.from_user.id,
        users=users,
        from_chat_id=from_chat_id,
        message_id=message_id,
        reply_markup=reply_markup
    ))
    
    await callback.answer()

async def run_broadcast(bot, admin_id, users, from_chat_id, message_id, reply_markup):
    from db.engine import session_maker
    
    success = 0
    failed = 0
    
    async with session_maker() as session:
        for user_id in users:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    reply_markup=reply_markup
                )
                success += 1
            except TelegramForbiddenError:
                failed += 1
                await db.set_active(session, user_id, 0)
            except TelegramBadRequest:
                failed += 1
            except Exception:
                failed += 1
            
            await asyncio.sleep(0.05) # ~20 msgs per second to avoid flooding
            
    await bot.send_message(
        admin_id,
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Успешно: {success}\n"
        f"Не удалось (заблокировали бота и др.): {failed}"
    )
