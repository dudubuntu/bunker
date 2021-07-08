from aiohttp import web
from sqlalchemy import select

from functools import wraps
import json


from db import Room, User, Player
from utils import contains_fields_or_return_error_responce


# def is_authenticated(func):
#     def wrapper(request: web.Request, *args, **kwargs):
#         sess_id = request.cookies['sessionid']
#         res = func(request, *args, **kwargs)
#         return res
#     return wrapper
# def is_authenticated(request: web.Request):


async def room_connect(request: web.Request):
    data = request.json()
    await contains_fields_or_return_error_responce(data, 'room_id')

    async with request.app['db'].acquire() as conn:
        pass

    return web.json_response({'message': 'You`ve been connected to the room.'})
    