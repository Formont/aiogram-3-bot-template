from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    waiting_for_user_id_search = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()
    editing_broadcast = State()
    waiting_for_button = State()