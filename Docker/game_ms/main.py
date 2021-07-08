from aiohttp import web


from routers import setup_routers
from config import APP_CONFIG
from db_helpers import init_pg, close_pg


async def my_web_app():
    app = web.Application()

    app['config'] = APP_CONFIG

    setup_routers(app)

    app.on_startup.append(init_pg)
    app.on_shutdown.append(close_pg)

    return app


# web.run_app(app, host='localhost', port=8001)