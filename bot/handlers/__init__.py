from aiogram import Router

def setup_routers():
    from . import cmds, actions

    router = Router()
    
    router.include_router(cmds.router)
    router.include_router(actions.router)

    return router