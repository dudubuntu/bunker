from aiohttp import web
import aiohttp_session
from sqlalchemy import select, insert, values, delete, update

from functools import wraps
import json
import datetime
import jwt


from db import Room, User, Player, RoomUser, RoomVote, ROOM_STATES, ROOMUSER_STATES
from utils import contains_fields_or_return_error_responce, json_content_type_required, contains_fields_or_return_error_responce, DateTimeJsonEncoder, game_sess_id_cookie_required


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

    room_id = None
    async with request.app['db'].acquire() as conn:
        conn_result = await conn.execute(select(Room).where(Room.id == data['room_id']).where(Room.password == data['password']))    #, Room.password == data['password']))
        row = await conn_result.fetchone()
        if not row:
            return web.json_response(status=400, data={'error': {'message': 'No such room with the provided room_id and password.'}})
        
        room_id = row['id']

    response = web.json_response()
    sess_is_invalid = False

    if 'game_sess_id' in request.cookies:
        async with request.app['db'].acquire() as conn:
            conn_result = await conn.execute(
                select(RoomUser)\
                .where(RoomUser.aiohttp_sess_id == request.cookies['game_sess_id'])\
                .where(RoomUser.room_id == room_id)
            )
            row = await conn_result.fetchone()

            if not row:
                response.del_cookie('game_sess_id')
                sess_is_invalid = True
            else:
                if row['state'] == 'kicked':
                    response.text = json.dumps({'error': {'message': 'User have been kicked'}})
                    # response.status = 403         изменить логику смены статуса
                    return response

    if not 'game_sess_id' in request.cookies or sess_is_invalid:
        token = jwt.encode(
            payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=request.app['config']['TOKEN_EXPIRED_SECONDS'])},
            key = request.app['config']['TOKEN_APP_KEY'])
        response.set_cookie('game_sess_id', token)

        async with request.app['db'].acquire() as conn:
            roomuser = await conn.execute(insert(RoomUser, [
                {'id': 1, 'username': 'random', 'player_number': 1, 'state': 'in_game', 'room_id': room_id, 'aiohttp_sess_id': token}
            ]))

    # location = ''
    # raise web.HTTPFound()
    response.text = json.dumps({'message': 'Successfuly connected'})
    return response


@json_content_type_required
@contains_fields_or_return_error_responce('initiator', 'password', 'state', 'turn', 'lap', 'players_quantity', 'location')
async def room_create(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        room = await conn.execute(insert(Room).values(id=1000, initiator='admin', password='', state=ROOM_STATES['waiting'], turn=1, lap=1, quantity_players=1, created=datetime.datetime.now(), updated=datetime.datetime.now()))
        # room_player = await conn.execute(insert(RoomUser).values(id=1, username=room.initiator, player_number=1, info={}, opened='', state=ROOMUSER_STATES['in_game'], card_opened_numbers='1', room_id=room.id, user_id=1))
        # print(room_player)
        
    return web.json_response(status=200, data={'message': 'Room was created'})


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def room_info(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        conn_result = await conn.execute(select(Room).where(Room.id == data['room_id']))
        row = await conn_result.fetchone()
        if not row:
            return web.json_response(status=400, data={'error': {'message': 'Room is not exist.'}})
        
        data = {}
        data.update(zip(row, row.values()))

    return web.json_response(status=200, text=DateTimeJsonEncoder().encode(data))


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'nickname')
async def room_delete(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        await conn.execute(delete(Room).where(Room.id == data['room_id']).where(Room.initiator == data['nickname']))

    return web.json_response(status=200, data={'message': 'Room was deleted'})