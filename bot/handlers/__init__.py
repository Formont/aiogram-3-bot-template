from aiogram import Router

def setup_routers():
    from . import cmds

    router = Router()
    
    router.include_router(cmds.router)

    return router