from aiohttp import web

from views import *


def setup_routers(app: web.Application):
    app.router.add_route('GET', '/api/v1/room_connect', room_connect)
    app.router.add_route('GET', '/api/v1/room_info', room_info)
    app.router.add_route('GET', '/api/v1/room_create', room_create)
    app.router.add_route('GET', '/api/v1/room_delete', room_delete)