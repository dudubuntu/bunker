from aiohttp import web
from sqlalchemy import select, insert, values, delete

from functools import wraps
import json
import datetime


from db import Room, User, Player, RoomUser, RoomVote, ROOM_STATES, ROOMUSER_STATES
from utils import contains_fields_or_return_error_responce, json_content_type_required, contains_fields_or_return_error_responce


# def is_authenticated(func):
#     def wrapper(request: web.Request, *args, **kwargs):
#         sess_id = request.cookies['sessionid']
#         res = func(request, *args, **kwargs)
#         return res
#     return wrapper
# def is_authenticated(request: web.Request):


@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'password')
async def room_connect(request: web.Request, data: dict):
    """
    Request {"room_id": 1234}
    Response {'message': 'Connection is allowed'} status=200

    Exceptions
    {"error": {"message": "", extra: ["", ""]}} status=400
    """

    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(select(Room).where(Room.id == data['room_id']))    #, Room.password == data['password']))
        results = await cursor.fetchall()
        if not results:
            return web.json_response(status=400, data={'error': {'message': 'No such room with the provided room_id and password.'}})

    # location = ''
    # raise web.HTTPFound()
    return web.json_response(status=200, data={'message': 'Connection is allowed'})


@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def room_info(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(select(Room).where(Room.id == data['room_id']))
        result = await cursor.fetchone()
        if not result:
            return web.json_response(status=400, data={'error': {'message': 'Room is not exist.'}})

    return web.json_response(status=200, data={'str': str(result)})


@json_content_type_required
@contains_fields_or_return_error_responce('initiator', 'password', 'state', 'turn', 'lap', 'players_quantity', 'location')
async def room_create(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        room = await conn.execute(insert(Room).values(id=1000, initiator='admin', password='', state=ROOM_STATES['waiting'], turn=1, lap=1, quantity_players=1, created=datetime.datetime.now(), updated=datetime.datetime.now()))
        # print(dir(room))
        # print(await room.scalar())
        # room_player = await conn.execute(insert(RoomUser).values(id=1, username=room.initiator, player_number=1, info={}, opened='', state=ROOMUSER_STATES['in_game'], card_opened_numbers='1', room_id=room.id, user_id=1))
        # print(room_player)
        

    return web.json_response(status=200, data={'message': 'Room was created'})


@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'nickname')
async def room_delete(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        await conn.execute(delete(Room).where(Room.id == data['room_id']).where(Room.initiator == data['nickname']))

    return web.json_response(status=200, data={'message': 'Room was deleted'})