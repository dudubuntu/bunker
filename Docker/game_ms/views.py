from aiohttp import web

import json


def room_connect(request: web.Request):
    return web.Response(body=json.dumps({'message': 'You`ve been connected to the room.'}))