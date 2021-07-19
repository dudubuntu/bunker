from aiohttp import web
import aiohttp_session
from sqlalchemy import select, insert, values, delete, update
from sqlalchemy.sql.expression import func as sa_func

from functools import wraps
import json
import datetime
import jwt
import logging
import random

from db import Room, User, Player, RoomUser, RoomVote, ROOM_STATES, ROOMUSER_STATES, ROOMVOTE_STATES
from utils import contains_fields_or_return_error_responce, json_content_type_required, contains_fields_or_return_error_responce, DateTimeJsonEncoder, game_sess_id_cookie_required, db_max_id, db_max_column_value_in_room, get_user_row_in_room_or_error_response, init_game, calculate_opening_quantity, voting_to_kick
from game_help import DATA


@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'password')
async def room_connect(request: web.Request, data: dict):
    """
    Request {"room_id": 1234}
    Response {'message': 'Connection is allowed'} status=200

    Exceptions
    {"error": {"message": "", extra: ["", ""]}} status=400
    """

    #TODO добавить проверку на статус комнаты - впускать только в статусе waiting

    async with request.app['db'].acquire() as conn:
        room_row = await (await conn.execute(select(Room).where(Room.id == data['room_id']).where(Room.password == data['password']))).fetchone()
        if not room_row:
            return web.json_response(status=400, data={'error': {'message': 'No such room with the provided room_id and password.'}})
        
        room_id = room_row['id']

        response = web.json_response()
        sess_is_invalid = False
        user_already_in_room = False

        if 'game_sess_id' in request.cookies:
            user_row = await (await conn.execute(select(RoomUser).where(RoomUser.game_sess_id == request.cookies['game_sess_id']).where(RoomUser.room_id == room_id))).fetchone()

            if not user_row:
                response.del_cookie('game_sess_id')
                sess_is_invalid = True
            else:
                if user_row['state'] == 'kicked':
                    response.text = json.dumps({'error': {'message': 'User have been kicked'}})
                    # response.status = 403         изменить логику смены статуса
                    return response
                else:
                    game_sess_id = request.cookies['game_sess_id']
                    user_already_in_room = True

        if not 'game_sess_id' in request.cookies or sess_is_invalid:
            game_sess_id = jwt.encode(
                payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=request.app['config']['TOKEN_EXPIRED_SECONDS'])},
                key = request.app['config']['TOKEN_APP_KEY'])
            response.set_cookie('game_sess_id', game_sess_id)

        user_left = False
        if user_already_in_room:
            user_row = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_id).where(RoomUser.game_sess_id == request.cookies['game_sess_id']))).fetchone()
            if user_row['state'] in ('ready', 'not_ready'):
                response.text = json.dumps({'message': 'Successfuly connected'})
                return response
            elif user_row['state'] in ('left'):
                user_left = True

        quantity_players = (await (await conn.execute(select(Room).where(Room.id == room_id))).first())['quantity_players']
        current_quantity = (await (await conn.execute(select(sa_func.count(RoomUser.id)).where(RoomUser.room_id == room_id).where(RoomUser.state != ROOMUSER_STATES['kicked']).where(RoomUser.state != ROOMUSER_STATES['left']))).first())[0]
        if not current_quantity < quantity_players:
            #TODO изменить статус
            response.text = json.dumps({'error': {'message': 'The room is full'}})
            return response

        if user_left:
            state = ROOMUSER_STATES['ready'] if room_row['initiator'] == user_row['username'] else ROOMUSER_STATES['not_ready']
            result = await conn.execute(update(RoomUser).values(state=state).where(RoomUser.room_id == data['room_id']).where(RoomUser.game_sess_id == request.cookies['game_sess_id']))
            if result.rowcount == 0:
                return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})
        else:
            room_user_id = await db_max_id(conn, RoomUser, 1, True)
            player_number = await db_max_column_value_in_room(conn, RoomUser, room_id, 'player_number') + 1
            await conn.execute(insert(RoomUser, [
                {'id': room_user_id, 'username': f'user-{player_number}', 'player_number': player_number, 'state': 'not_ready', 'room_id': room_id, 'game_sess_id': game_sess_id, 'info': {}, 'opened': '', 'card_opened_numbers': ''}
            ]))

        #TODO добавлять ли редирект?
        # location = ''
        # raise web.HTTPFound()
        response.text = json.dumps({'message': 'Successfuly connected'})
        return response


@json_content_type_required
@contains_fields_or_return_error_responce('initiator', 'password', 'quantity_players', 'location')
async def room_create(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        async with conn.begin() as tr:
            logging.debug(data)
            room_id = await db_max_id(conn, Room, 1000, True)
            row = await conn.execute(insert(Room).values(id=room_id, initiator=data['initiator'], password=data['password'], state=ROOM_STATES['waiting'], turn=1, lap=1, quantity_players=data['quantity_players']))

            response = web.json_response()
            game_sess_id = request.cookies.get('game_sess_id', 0)
            if not 'game_sess_id' in request.cookies:
                game_sess_id = jwt.encode(
                    payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=request.app['config']['TOKEN_EXPIRED_SECONDS'])},
                    key = request.app['config']['TOKEN_APP_KEY'])
                response.set_cookie('game_sess_id', game_sess_id)

            room_user_id = await db_max_id(conn, RoomUser, 1, True)
            row = await conn.execute(insert(RoomUser).values(id=room_user_id, username=data['initiator'], player_number=1, info={}, opened='', state=ROOMUSER_STATES['ready'], card_opened_numbers='', room_id=room_id, game_sess_id=game_sess_id))
            
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
        

        #TODO добавить в ответ поле connected
        room_users = await (await conn.execute(select(RoomUser.username, RoomUser.state).where(RoomUser.room_id == data['room_id']))).fetchall()
        logging.debug(room_users)
        connected = []
        for user_row in room_users:
            user = dict(zip(user_row, user_row.values()))
            connected.append(user)

        data = dict(zip(row, row.values()))
        data.update({'connected': connected})
    return web.json_response(status=200, text=DateTimeJsonEncoder().encode(data))


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def room_delete(request: web.Request, data:dict):
    room_id = data['room_id']
    async with request.app['db'].acquire() as conn:
        row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(row, web.Response):
            return row

        username = row.get('username')
        logging.debug(username)
        async with conn.begin() as tr:
            result = await conn.execute(delete(Room).where(Room.id == room_id).where(Room.initiator == username))
            if result.rowcount == 0:
                return web.json_response(status=403, data={'error': {'message': 'You are not the room initiator'}})            

            await conn.execute(delete(RoomUser).where(RoomUser.room_id == data['room_id']))
            await conn.execute(delete(RoomVote).where(RoomVote.room_id == data['room_id']))

    return web.json_response(status=200, data={'message': 'Room was deleted'})


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'new_username')
async def player_change_username(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        if data['new_username'] == user_row['username']:
            return web.json_response(status=400, data={'error': {'message': 'New username is the same with the old one.'}})

        is_owner = False
        room = await (await conn.execute(select(Room).where(Room.id == data['room_id']))).fetchone()
        if room['initiator'] == user_row['username']:
            is_owner = True

        result = await (await conn.execute(select(RoomUser.username).where(RoomUser.room_id == data['room_id']).where(RoomUser.username == data['new_username']))).fetchall()
        if result:
            return web.json_response(status=400, data={'error': {'message': 'This username is already in room.'}})

        async with conn.begin() as tr:
            result = await conn.execute(update(RoomUser).values(username=data['new_username']).where(RoomUser.id == user_row['id']))
            if result.rowcount == 0:
                return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})
            
            if is_owner:
                result = await conn.execute(update(Room).values(initiator=data['new_username']).where(Room.id == data['room_id']))
                if result.rowcount == 0:
                    return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})
        
        return web.json_response(status=200, data={'error': {'message': 'Username was changed'}})


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'aim_username')
async def player_kick(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        if data['aim_username'] == user_row['username']:
            result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['left']).where(RoomUser.id == user_row['id']))
            if result.rowcount == 0:
                return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})
            return web.json_response(status=200, data={'error': {'message': 'You were successfuly left.'}})

        room_row = await (await conn.execute(select(Room).where(Room.id == data['room_id']))).fetchone()
        if user_row['username'] != room_row['initiator']:
            return web.json_response(status=403, data={'error': {'message': 'You have no priveleges to do this.'}})

        result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['kicked']).where(RoomUser.room_id == data['room_id']).where(RoomUser.username == data['aim_username']))
        if result.rowcount == 0:
            return web.json_response(status=500, data={'error': {'message': 'There is no user with the provider username.'}})

        #TODO Добавить транзакцию на проверку: если в комнате нет хотя бы одного пользователя в статусе не kicked, left то удалить комнату

        return web.json_response(status=200, data={'error': {'message': f'User {data["aim_username"]} was successfully kicked.'}})


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def player_ready(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['ready']).where(RoomUser.room_id == data['room_id']).where(RoomUser.game_sess_id == request.cookies['game_sess_id']))
        if result.rowcount == 0:
            return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})

        return web.json_response(status=200, data={'message': 'You`re ready!'})


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def game_start(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        room_row = await (await conn.execute(select(Room).where(Room.id == data['room_id']))).fetchone()
        if user_row['username'] != room_row['initiator']:
            return web.json_response(status=403, data={'error': {'message': 'You have no priveleges to do this.'}})
        if room_row['state'] != ROOM_STATES['waiting']:
            return web.json_response(status=400, data={'error': {'message': 'The game is already started'}})

        roomusers_rows = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_row['id']).where(RoomUser.state == ROOMUSER_STATES['ready']))).fetchall()
        order_chars_list = [*init_game(len(roomusers_rows))]

        async with conn.begin() as tr:
            await conn.execute(update(RoomUser).values(player_number=0, state=ROOMUSER_STATES['left']).where(RoomUser.room_id == room_row['id']).where(RoomUser.state != ROOMUSER_STATES['ready']))
            
            i = 0
            for roomuser, order_number, char in zip(roomusers_rows, *order_chars_list):
                result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['in_game'], player_number=order_number, info=char).where(RoomUser.room_id == room_row['id']).where(RoomUser.game_sess_id == roomuser['game_sess_id']))
                i += 1

            await conn.execute(update(Room).values(state=ROOM_STATES['opening']).where(Room.id == room_row['id']))

            if i < request.app['config']['GAME_MIN_PLAYERS_QUANTITY']:
                await tr.rollback()
                return web.json_response(status=400, data={'error': {'message': 'Not enough users to start the game'}})

        return web.json_response(status=200, data={'message': 'The game is started'})


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def game_info(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row
            
        room_row = await (await conn.execute(select(Room).where(Room.id == data['room_id']))).fetchone()
        users_rows = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == data['room_id']).where(RoomUser.state == ROOMUSER_STATES['in_game']))).fetchall()

        data = {
            'room_id': room_row['id'],
            'state': room_row['state'],
            'turn': room_row['turn'],
            #TODO добавлять ли настройку столько кругов играть
            'opening_quantity': calculate_opening_quantity(room_row['quantity_players'], room_row['lap'], request.app['config']),
            'quantity_players': room_row['quantity_players'],
            'players': [
                {
                    'player_number': player['player_number'],
                    'username': player['username'],
                    'state': player['state'],
                    'info': {
                        char: player['info'][char] for char in player['opened'].strip().split(',')
                    } if len(player['opened'].strip()) != 0 else {},
                } for player in users_rows]
        }
        return web.json_response(status=200, data=data)


@game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def player_get_current(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        data = {
            'room_id': user_row['room_id'],
            'username': user_row['username'],
            'player_number': user_row['player_number'],
            'info': user_row['info'],
            'opened': user_row['opened'],
            'card_opened_numbers': user_row['card_opened_numbers'],
            'state': user_row['state'],
        }
        return web.json_response(status=200, data=data)