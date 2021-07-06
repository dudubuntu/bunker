from aiohttp import web


from .routers import setup_routers
from .config import APP_CONFIG
from .db import init_pg, close_pg


def init_app():
    app = web.Application()

    app['config'] = APP_CONFIG

    setup_routers(app)

    app.on_startup.append(init_pg)
    app.on_shutdown(close_pg)

    return app


if __name__ == '__main__':
    app = init_app()
    web.run_app(app, host='localhost', port=8001)