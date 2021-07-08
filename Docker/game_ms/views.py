from aiohttp import web
from sqlalchemy import select

from functools import wraps
import json


from db import Room, User, Player
from utils import contains_fields_or_return_error_responce, json_content_type_required


# def is_authenticated(func):
#     def wrapper(request: web.Request, *args, **kwargs):
#         sess_id = request.cookies['sessionid']
#         res = func(request, *args, **kwargs)
#         return res
#     return wrapper
# def is_authenticated(request: web.Request):


@json_content_type_required
async def room_connect(request: web.Request):
    """
    Request {"room_id": 1234}
    Response {'message': 'Connection is allowed'} status=200

    Exceptions
    {"error": {"message": "", extra: ["", ""]}} status=400
    """
    try:
        data = await request.json()
    except json.JSONDecodeError as exc:
        return web.json_response(status=400, data={'error': {'message': 'JSON decode error. Data must be JSON formatted'}})

    result = contains_fields_or_return_error_responce(data, 'room_id', 'password')
    if result is not None:
        return result

    async with request.app['db'].acquire() as conn:
        results = conn.execute(select(Room).where(Room.id == data['room_id']))    #, Room.password == data['password']))
        if not results:
            web.json_response(status=400, data={'error': {'message': 'No such room with the provided room_id and password.'}})

    # location = ''
    # raise web.HTTPFound()
    return web.json_response(status=200, data={'message': 'Connection is allowed'})
    