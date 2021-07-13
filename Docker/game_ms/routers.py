from aiohttp import web

from views import *


def setup_routers(app: web.Application):
    app.router.add_route('GET', '/api/v1/room_connect', room_connect)
    app.router.add_route('GET', '/api/v1/room_info', room_info)
    app.router.add_route('GET', '/api/v1/room_create', room_create)
    app.router.add_route('GET', '/api/v1/room_delete', room_delete)
    
    app.router.add_route('GET', '/api/v1/player_change_nickname', player_change_username)
    app.router.add_route('GET', '/api/v1/player_kick', player_kick)
    app.router.add_route('GET', '/api/v1/player_ready', player_ready)
    
    app.router.add_route('GET', '/api/v1/game_start', game_start)