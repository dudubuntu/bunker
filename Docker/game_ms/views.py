from aiohttp import web
import aiohttp_session
from sqlalchemy import select, insert, values, delete, update
from sqlalchemy.sql.expression import func as sa_func

from functools import wraps
import json
import datetime
import jwt
import logging

from db import Room, User, Player, RoomUser, RoomVote, ROOM_STATES, ROOMUSER_STATES
from utils import contains_fields_or_return_error_responce, json_content_type_required, contains_fields_or_return_error_responce, DateTimeJsonEncoder, game_sess_id_cookie_required, db_max_id, db_max_column_value_in_room


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
                else:
                    game_sess_id = request.cookies['game_sess_id']
                    response.text = json.dumps({'message': 'Successfuly connected'})
                    return response

        if not 'game_sess_id' in request.cookies or sess_is_invalid:
            game_sess_id = jwt.encode(
                payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=request.app['config']['TOKEN_EXPIRED_SECONDS'])},
                key = request.app['config']['TOKEN_APP_KEY'])
            response.set_cookie('game_sess_id', game_sess_id)

        quantity_players = (await (await conn.execute(select(Room).where(Room.id == room_id))).first())['quantity_players']
        current_quantity = (await (await conn.execute(select(sa_func.count(RoomUser.id)).where(RoomUser.room_id == room_id))).first())[0]
        if not current_quantity < quantity_players:
            #TODO изменить статус
            response.text = json.dumps({'error': {'message': 'The room is full'}})
            return response


        room_user_id = await db_max_id(conn, RoomUser, 1, True)
        player_number = await db_max_column_value_in_room(conn, RoomUser, room_id, 'player_number') + 1
        await conn.execute(insert(RoomUser, [
            {'id': room_user_id, 'username': f'user-{player_number}', 'player_number': player_number, 'state': 'in_game', 'room_id': room_id, 'aiohttp_sess_id': game_sess_id, 'info': {}}
        ]))

        # location = ''
        # raise web.HTTPFound()
        response.text = json.dumps({'message': 'Successfuly connected'})
        return response


@json_content_type_required
@contains_fields_or_return_error_responce('initiator', 'password', 'state', 'turn', 'lap', 'quantity_players', 'location')
async def room_create(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        async with conn.begin() as tr:
            logging.debug(data)
            room_id = await db_max_id(conn, Room, 1000, True)
            row = await conn.execute(insert(Room).values(id=room_id, initiator=data['initiator'], password=data['password'], state=data['state'], turn=data['turn'], lap=data['lap'], quantity_players=data['quantity_players']))

            response = web.json_response()
            game_sess_id = request.cookies.get('game_sess_id', 0)
            if not 'game_sess_id' in request.cookies:
                game_sess_id = jwt.encode(
                    payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=request.app['config']['TOKEN_EXPIRED_SECONDS'])},
                    key = request.app['config']['TOKEN_APP_KEY'])
                response.set_cookie('game_sess_id', game_sess_id)

            room_user_id = await db_max_id(conn, RoomUser, 1, True)
            row = await conn.execute(insert(RoomUser).values(id=room_user_id, username=data['initiator'], player_number=1, info={}, opened='', state=ROOMUSER_STATES['in_game'], card_opened_numbers='', room_id=room_id, aiohttp_sess_id=game_sess_id))
            
            response.text = json.dumps({'message': 'Successfully created', 'room_id': room_id})
            return response
        


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