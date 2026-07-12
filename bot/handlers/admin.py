from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.adminFilter import AdminFilter
from bot.keyboards.builders import build_admin_dashboard_kb, build_admin_users_kb, build_admin_back_kb, build_admin_user_card_kb, build_admin_sponsors_kb, build_admin_sponsor_view_kb
from bot.states.userStates import AdminState, AdminSponsorState
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

@router.callback_query(F.data == "admin_sponsors", AdminFilter())
async def admin_sponsors_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    sponsors = await db.get_active_sponsors(session)
    text = f"🤝 <b>Управление спонсорами (ОП)</b>\n\nАктивных спонсоров: {len(sponsors)}"
    await callback.message.edit_text(text, reply_markup=build_admin_sponsors_kb(sponsors))
    await callback.answer()

@router.callback_query(F.data == "admin_sponsor_add", AdminFilter())
async def admin_sponsor_add_start(callback: CallbackQuery, state: FSMContext):
    text = (
        "➕ <b>Добавление спонсора</b>\n\n"
        "1️⃣ Добавьте этого бота в администраторы канала (с правом создания пригласительных ссылок).\n"
        "2️⃣ Отправьте мне ID канала (например, -1001234567890) или перешлите любое сообщение из канала."
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_sponsors"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(AdminSponsorState.waiting_for_channel)
    await callback.answer()

@router.message(AdminSponsorState.waiting_for_channel, AdminFilter())
async def admin_sponsor_channel_process(message: Message, state: FSMContext):
    channel_id = None
    
    if message.forward_from_chat and message.forward_from_chat.type == "channel":
        channel_id = message.forward_from_chat.id
    else:
        try:
            channel_id = int(message.text.strip())
        except Exception:
            pass
            
    if not channel_id:
        await message.answer("⚠️ Не удалось определить ID канала. Попробуйте еще раз.")
        return
        
    # Check bot permissions
    try:
        chat = await message.bot.get_chat(channel_id)
        bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
        if not bot_member.can_invite_users:
            await message.answer(f"⚠️ У бота нет права приглашать пользователей в канале {chat.title}.")
            return
            
        await state.update_data(channel_id=channel_id, channel_title=chat.title)
        await message.answer(f"✅ Канал <b>{chat.title}</b> найден.\n\nВведите желаемое количество подписчиков (цель):")
        await state.set_state(AdminSponsorState.waiting_for_target_subs)
    except Exception as e:
        await message.answer("⚠️ Ошибка проверки канала. Бот является админом там? Убедитесь в этом и в правильности ID.")

@router.message(AdminSponsorState.waiting_for_target_subs, AdminFilter())
async def admin_sponsor_subs_process(message: Message, session: AsyncSession, state: FSMContext):
    try:
        target_subs = int(message.text.strip())
        if target_subs <= 0:
            raise ValueError
    except Exception:
        await message.answer("⚠️ Введите положительное число.")
        return
        
    data = await state.get_data()
    channel_id = data['channel_id']
    channel_title = data['channel_title']
    
    try:
        # Generate invite link
        invite = await message.bot.create_chat_invite_link(chat_id=channel_id, name="ОП Бот", creates_join_request=False)
        
        await db.add_sponsor(session, channel_id, channel_title, target_subs, invite.invite_link)
        await message.answer(f"✅ Спонсор успешно добавлен!\nЦель: {target_subs} подписчиков.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при создании ссылки-приглашения: {e}")
        
    await state.clear()
    
    # Show menu again
    sponsors = await db.get_active_sponsors(session)
    await message.answer(f"🤝 <b>Управление спонсорами (ОП)</b>\n\nАктивных спонсоров: {len(sponsors)}", reply_markup=build_admin_sponsors_kb(sponsors))

@router.callback_query(F.data.startswith("admin_sponsor_view_"), AdminFilter())
async def admin_sponsor_view(callback: CallbackQuery, session: AsyncSession):
    sponsor_id = int(callback.data.split("_")[-1])
    sponsor = await db.get_sponsor(session, sponsor_id)
    if not sponsor:
        await callback.answer("⚠️ Спонсор не найден", show_alert=True)
        return
        
    text = (
        f"📢 <b>Спонсор ID {sponsor.id}</b>\n\n"
        f"Канал ID: <code>{sponsor.channel_id}</code>\n"
        f"Прогресс: <b>{sponsor.current_subs} / {sponsor.target_subs}</b>\n"
        f"Ссылка: {sponsor.invite_link}\n"
        f"Статус: {'Активен' if sponsor.is_active else 'Выполнен'}"
    )
    await callback.message.edit_text(text, reply_markup=build_admin_sponsor_view_kb(sponsor.id))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_sponsor_del_"), AdminFilter())
async def admin_sponsor_del(callback: CallbackQuery, session: AsyncSession):
    sponsor_id = int(callback.data.split("_")[-1])
    await db.delete_sponsor(session, sponsor_id)
    await callback.answer("✅ Спонсор удален!", show_alert=True)
    
    sponsors = await db.get_active_sponsors(session)
    text = f"🤝 <b>Управление спонсорами (ОП)</b>\n\nАктивных спонсоров: {len(sponsors)}"
    await callback.message.edit_text(text, reply_markup=build_admin_sponsors_kb(sponsors))