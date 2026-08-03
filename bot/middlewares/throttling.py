from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        """
        :param rate_limit: Delay in seconds between requests
        """
        self.rate_limit = rate_limit
        self.caches: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            
        if user_id:
            now = time.time()
            last_time = self.caches.get(user_id)
            if last_time and (now - last_time) < self.rate_limit:
                # User is spamming
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer("Слишком быстро! Не спешите.", show_alert=False)
                    except Exception:
                        pass
                return None # Drop the update
            
            # Update last action time
            self.caches[user_id] = now
            
        return await handler(event, data)
