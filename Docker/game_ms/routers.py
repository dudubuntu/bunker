from aiohttp import web

from views import *


def setup_routers(app: web.Application):
    app.router.add_route('POST', '/api/v1/room_connect', room_connect)
    app.router.add_route('POST', '/api/v1/room_info', room_info)
    app.router.add_route('POST', '/api/v1/room_create', room_create)
    app.router.add_route('POST', '/api/v1/room_delete', room_delete)
    
    app.router.add_route('POST', '/api/v1/player_change_nickname', player_change_username)
    app.router.add_route('POST', '/api/v1/player_kick', player_kick)
    app.router.add_route('POST', '/api/v1/player_ready', player_ready)
    app.router.add_route('POST', '/api/v1/player_get_current', player_get_current)
    app.router.add_route('POST', '/api/v1/player_open_chars', player_open_chars)
    app.router.add_route('POST', '/api/v1/player_make_vote', player_make_vote)
    
    app.router.add_route('POST', '/api/v1/game_start', game_start)
    app.router.add_route('POST', '/api/v1/game_info', game_info)
    app.router.add_route('POST', '/api/v1/game_results', game_results)
