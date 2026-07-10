from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.adminFilter import AdminFilter
from bot.keyboards.builders import build_admin_dashboard_kb, build_admin_users_kb, build_admin_back_kb, build_admin_user_card_kb
from bot.states import AdminState
from db import orm_queries as db

router = Router()

@router.message(Command("admin"), AdminFilter())
async def admin_dashboard(message: Message, session: AsyncSession):
    stats = await db.get_admin_stats(session)
    
    total_users = stats['total_users']
    new_users = stats['new_users_today']
    
    text = (
        f"🛠 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей всего: {total_users} (+{new_users} за сутки)\n"
    )
    
    await message.answer(text, reply_markup=build_admin_dashboard_kb())

@router.callback_query(F.data == "admin_back_to_main", AdminFilter())
async def admin_back_to_main(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    stats = await db.get_admin_stats(session)
    
    total_users = stats['total_users']
    new_users = stats['new_users_today']

    
    text = (
        f"🛠 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей всего: {total_users} (+{new_users} за сутки)\n"
        f"Выбери раздел для управления:"
    )
    
    await callback.message.edit_text(text, reply_markup=build_admin_dashboard_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_users", AdminFilter())
async def admin_users_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    stats = await db.get_admin_users_stats(session)
    
    text = (
        f"👥 <b>Управление пользователями</b>\n\n"
        f"Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"Новых за сегодня: <b>{stats['new_users_today']}</b>\n"
        f"Новых за неделю: <b>{stats['new_users_week']}</b>\n"
        f"Активных (не заблокировали бота): <b>{stats['active_users']}</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=build_admin_users_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_user_search", AdminFilter())
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введите ID пользователя для поиска:", reply_markup=build_admin_back_kb())
    await state.set_state(AdminState.waiting_for_user_id_search)
    await callback.answer()

@router.message(AdminState.waiting_for_user_id_search, AdminFilter())
async def process_user_search(message: Message, session: AsyncSession, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ ID должен быть числом.", reply_markup=build_admin_back_kb())
        return

    user = await db.get_user(session, user_id)
    if user:
        if user.is_blocked:
            status = "Заблокирован 🚫"
        else:
            status = "Активен" if user.active else "Бот остановлен/удален"
        
        try:
            chat = await message.bot.get_chat(user_id)
            name_parts = []
            if chat.first_name:
                name_parts.append(chat.first_name)
            if chat.last_name:
                name_parts.append(chat.last_name)
            full_name = " ".join(name_parts) if name_parts else "Нет имени"
            username_str = f"@{chat.username}" if chat.username else "Нет"
        except Exception:
            full_name = "Неизвестно"
            username_str = "Неизвестно"

        text = (
            f"🪪 <b>Карточка пользователя</b>\n\n"
            f"ID: <b>{user.user_id}</b>\n"
            f"Имя: <b>{full_name}</b>\n"
            f"Username: <b>{username_str}</b>\n"
            f"Статус: <b>{status}</b>\n"
            f"Дата регистрации: {user.created_at}"
        )
        await message.answer(text, reply_markup=build_admin_user_card_kb(user.user_id, user.is_blocked))
    else:
        await message.answer("Пользователь не найден.", reply_markup=build_admin_back_kb())
    await state.clear()

@router.callback_query(F.data.startswith("admin_action_block_"), AdminFilter())
async def admin_action_block(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split("_")[-1])
    await db.set_blocked(session, user_id, True)
    
    # Reload user and text
    user = await db.get_user(session, user_id)
    status = "Заблокирован 🚫"
    try:
        chat = await callback.message.bot.get_chat(user_id)
        name_parts = []
        if chat.first_name:
            name_parts.append(chat.first_name)
        if chat.last_name:
            name_parts.append(chat.last_name)
        full_name = " ".join(name_parts) if name_parts else "Нет имени"
        username_str = f"@{chat.username}" if chat.username else "Нет"
    except Exception:
        full_name = "Неизвестно"
        username_str = "Неизвестно"

    text = (
        f"🪪 <b>Карточка пользователя</b>\n\n"
        f"ID: <b>{user.user_id}</b>\n"
        f"Имя: <b>{full_name}</b>\n"
        f"Username: <b>{username_str}</b>\n"
        f"Статус: <b>{status}</b>\n"
        f"Дата регистрации: {user.created_at}"
    )
    await callback.message.edit_text(text, reply_markup=build_admin_user_card_kb(user.user_id, True))
    await callback.answer("🚫 Пользователь заблокирован")

@router.callback_query(F.data.startswith("admin_action_unblock_"), AdminFilter())
async def admin_action_unblock(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split("_")[-1])
    await db.set_blocked(session, user_id, False)
    
    # Reload user and text
    user = await db.get_user(session, user_id)
    status = "Активен" if user.active else "Бот остановлен/удален"
    try:
        chat = await callback.message.bot.get_chat(user_id)
        name_parts = []
        if chat.first_name:
            name_parts.append(chat.first_name)
        if chat.last_name:
            name_parts.append(chat.last_name)
        full_name = " ".join(name_parts) if name_parts else "Нет имени"
        username_str = f"@{chat.username}" if chat.username else "Нет"
    except Exception:
        full_name = "Неизвестно"
        username_str = "Неизвестно"

    text = (
        f"🪪 <b>Карточка пользователя</b>\n\n"
        f"ID: <b>{user.user_id}</b>\n"
        f"Имя: <b>{full_name}</b>\n"
        f"Username: <b>{username_str}</b>\n"
        f"Дата регистрации: {user.created_at}"
    )
    await callback.message.edit_text(text, reply_markup=build_admin_user_card_kb(user.user_id, False))
    await callback.answer("✅ Пользователь разблокирован")