from aiogram import Router
from bot.filters import NotBannedFilter

def setup_routers():
    from . import cmds, actions, admin, broadcast

    router = Router()
    
    router.message.filter(NotBannedFilter())
    router.callback_query.filter(NotBannedFilter())

    router.include_router(cmds.router)
    router.include_router(actions.router)
    router.include_router(admin.router)
    router.include_router(broadcast.router)

    return router