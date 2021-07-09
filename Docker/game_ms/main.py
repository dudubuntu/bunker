from aiohttp import web
import aiohttp_cors
import aiohttp_session

from routers import setup_routers
from config import APP_CONFIG
from db_helpers import init_pg, close_pg


def cors_configurate(app: web.Application):
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
    })

    for route in list(app.router.routes()):
        cors.add(route)


async def init_app():
    app = web.Application()

    app['config'] = APP_CONFIG

    setup_routers(app)

    cors_configurate(app)

    aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())

    app.on_startup.append(init_pg)
    app.on_shutdown.append(close_pg)

    return app