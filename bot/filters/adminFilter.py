from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from config import ADMINS

class AdminFilter(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        if hasattr(event, "from_user") and getattr(event, "from_user", None):
            return event.from_user.id in ADMINS
        return False