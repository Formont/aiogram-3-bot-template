from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_admin_dashboard_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Управление юзерами", callback_data="admin_users")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Массовая рассылка", callback_data="admin_broadcast")
    )
    return builder.as_markup()

def build_admin_users_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_user_search"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_main"))
    return builder.as_markup()

def build_admin_back_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users"))
    return builder.as_markup()

def build_admin_user_card_kb(user_id: int, is_blocked: bool):
    builder = InlineKeyboardBuilder()
    if is_blocked:
        builder.row(InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_action_unblock_{user_id}"))
    else:
        builder.row(InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_action_block_{user_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users"))
    return builder.as_markup()

def build_broadcast_preview_kb(has_buttons: bool):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить кнопку", callback_data="broadcast_add_btn"))
    if has_buttons:
        builder.row(InlineKeyboardButton(text="🗑 Удалить последнюю кнопку", callback_data="broadcast_del_btn"))
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel"),
        InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_send")
    )
    return builder.as_markup()

def build_broadcast_message_kb(buttons_list: list):
    builder = InlineKeyboardBuilder()
    for btn in buttons_list:
        builder.row(InlineKeyboardButton(text=btn['text'], url=btn['url']))
    return builder.as_markup()
