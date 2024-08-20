from typing import Any, Awaitable, Callable, Coroutine, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

class DBMiddleware(BaseMiddleware):
    def __init__(self,  session_pool: async_sessionmaker) -> None:
        self.session_pool = session_pool
    
    async def __call__(self, 
                 handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], 
                 event: TelegramObject, 
                 data: Dict[str, Any]) -> Coroutine[Any, Any, Any]:
        async with self.session_pool() as session:
            data['session'] = session
            return await handler(event, data)