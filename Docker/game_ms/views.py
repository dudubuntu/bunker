from aiohttp import web
import aiohttp_session
from sqlalchemy import select, insert, values, delete, update
from sqlalchemy.sql.expression import func as sa_func

from functools import wraps
import json
import datetime
import jwt
import uuid
import logging
import random

from db import Room, User, Player, RoomUser, RoomVote, ROOM_STATES, ROOMUSER_STATES, ROOMVOTE_STATES
from utils import contains_fields_or_return_error_responce, json_content_type_required, contains_fields_or_return_error_responce, DateTimeJsonEncoder, game_sess_id_cookie_required, db_max_id, db_max_column_value_in_room, get_user_row_in_room_or_error_response, init_game, calculate_opening_quantity, voting_to_kick, get_laps_quantity
from game_help import DATA


@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def room_fill_players(request: web.Request, data: dict):
    """
    Наполнить комнату тестовыми игроками
    """

    #TODO добавить проверку на статус комнаты - впускать только в статусе waiting

    async with request.app['db'].acquire() as conn:
        room_row = await (await conn.execute(select(Room).where(Room.id == data['room_id']))).fetchone()
        if not room_row:
            return web.json_response(status=400, data={'error': {'message': 'No such room with the provided room_id.'}})
        if room_row['state'] != ROOM_STATES['waiting']:
            return web.json_response(status=400, data={'error': {'message': 'You are able only to add users to games with "waiting" state.'}})

        roomusers_rows = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_row['id']).filter((RoomUser.state == 'ready') | (RoomUser.state == 'not_ready')))).fetchall()
        async with conn.begin() as tr:
            room_user_id = await db_max_id(conn, RoomUser, 1, True)
            for i in range(len(roomusers_rows) + 1, room_row['quantity_players'] + 1):
                game_sess_id = str(uuid.uuid1())
                await conn.execute(insert(RoomUser, [
                    {'id': room_user_id, 'username': f'user-{i}', 'player_number': 0, 'state': 'ready', 'room_id': room_row['id'], 'game_sess_id': game_sess_id, 'info': {}, 'opened': '', 'card_opened_numbers': ''}
                ]))
                room_user_id += 1

        return web.json_response(status=200, data={'message': 'Successfuly filled'})


@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'password', 'username')
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
        if room_row['state'] != ROOM_STATES['waiting']:
            return web.json_response(status=400, data={'error': {'message': 'You are unable to connect to started or finished game.'}})
        room_id = room_row['id']

        response = web.json_response()
        game_sess_id = str(uuid.uuid1())
        room_user_id = await db_max_id(conn, RoomUser, 1, True)
        await conn.execute(insert(RoomUser, [
            {'id': room_user_id, 'username': data['username'], 'player_number': 0, 'state': 'not_ready', 'room_id': room_id, 'game_sess_id': game_sess_id, 'info': {}, 'opened': '', 'card_opened_numbers': ''}
        ]))
        response.text = json.dumps({'message': 'Successfuly connected', 'game_sess_id': game_sess_id})
        return response

        # response = web.json_response()
        # sess_is_invalid = False
        # user_already_in_room = False

        # if 'game_sess_id' in request.cookies:
        #     user_row = await (await conn.execute(select(RoomUser).where(RoomUser.game_sess_id == request.cookies['game_sess_id']).where(RoomUser.room_id == room_id))).fetchone()

        #     if not user_row:
        #         response.del_cookie('game_sess_id')
        #         sess_is_invalid = True
        #     else:
        #         if user_row['state'] == 'kicked':
        #             response.text = json.dumps({'error': {'message': 'User have been kicked'}})
        #             # response.status = 403         изменить логику смены статуса
        #             return response
        #         else:
        #             game_sess_id = request.cookies['game_sess_id']
        #             user_already_in_room = True

        # if not 'game_sess_id' in request.cookies or sess_is_invalid:
        #     game_sess_id = jwt.encode(
        #         payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=request.app['config']['TOKEN_EXPIRED_SECONDS'])},
        #         key = request.app['config']['TOKEN_APP_KEY'])
        #     response.set_cookie('game_sess_id', game_sess_id)

        # user_left = False
        # if user_already_in_room:
        #     user_row = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_id).where(RoomUser.game_sess_id == request.cookies['game_sess_id']))).fetchone()
        #     if user_row['state'] in ('ready', 'not_ready'):
        #         response.text = json.dumps({'message': 'Successfuly connected'})
        #         return response
        #     elif user_row['state'] in ('left'):
        #         user_left = True

        # quantity_players = (await (await conn.execute(select(Room).where(Room.id == room_id))).first())['quantity_players']
        # current_quantity = (await (await conn.execute(select(sa_func.count(RoomUser.id)).where(RoomUser.room_id == room_id).where(RoomUser.state != ROOMUSER_STATES['kicked']).where(RoomUser.state != ROOMUSER_STATES['left']))).first())[0]
        # if not current_quantity < quantity_players:
        #     #TODO изменить статус
        #     response.text = json.dumps({'error': {'message': 'The room is full'}})
        #     return response

        # if user_left:
        #     state = ROOMUSER_STATES['ready'] if room_row['initiator'] == user_row['username'] else ROOMUSER_STATES['not_ready']
        #     result = await conn.execute(update(RoomUser).values(state=state).where(RoomUser.room_id == data['room_id']).where(RoomUser.game_sess_id == request.cookies['game_sess_id']))
        #     if result.rowcount == 0:
        #         return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})
        # else:
        #     room_user_id = await db_max_id(conn, RoomUser, 1, True)
            
        #     result = await (await conn.execute(select(RoomUser.username).where(RoomUser.room_id == data['room_id']).where(RoomUser.username == data['username']))).fetchall()
        #     if result:
        #         return web.json_response(status=400, data={'error': {'message': 'This username is already in room.'}})

        #     await conn.execute(insert(RoomUser, [
        #         {'id': room_user_id, 'username': data['username'], 'player_number': 0, 'state': 'not_ready', 'room_id': room_id, 'game_sess_id': game_sess_id, 'info': {}, 'opened': '', 'card_opened_numbers': ''}
        #     ]))

        # response.text = json.dumps({'message': 'Successfuly connected'})
        # return response


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
                game_sess_id = str(uuid.uuid1())
                response.set_cookie('game_sess_id', game_sess_id)

            room_user_id = await db_max_id(conn, RoomUser, 1, True)
            row = await conn.execute(insert(RoomUser).values(id=room_user_id, username=data['initiator'], player_number=1, info={}, opened='', state=ROOMUSER_STATES['ready'], card_opened_numbers='', room_id=room_id, game_sess_id=game_sess_id))
            
        response.text = json.dumps({'message': 'Successfully created', 'room_id': room_id, 'password': data['password'], 'game_sess_id': game_sess_id})
        return response  


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def room_info(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        conn_result = await conn.execute(select(Room).where(Room.id == data['room_id']))
        row = await conn_result.fetchone()
        if not row:
            return web.json_response(status=400, data={'error': {'message': 'Room is not exist.'}})
        
        room_users = await (await conn.execute(select(RoomUser.username, RoomUser.state).where(RoomUser.room_id == data['room_id']))).fetchall()
        logging.debug(room_users)
        connected = []
        for user_row in room_users:
            user = dict(zip(user_row, user_row.values()))
            connected.append(user)

        data = dict(zip(row, row.values()))
        data.update({'connected': connected})
    return web.json_response(status=200, text=DateTimeJsonEncoder().encode(data))


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def room_delete(request: web.Request, data:dict):
    room_id = data['room_id']
    async with request.app['db'].acquire() as conn:
        # row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
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


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'new_username')
async def player_change_username(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
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
            
            if is_owner:
                result = await conn.execute(update(Room).values(initiator=data['new_username']).where(Room.id == data['room_id']))
        
        return web.json_response(status=200, data={'error': {'message': 'Username was changed'}})


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'aim_username')
async def player_kick(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
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
            return web.json_response(status=400, data={'error': {'message': 'There is no user with the provider username.'}})

        #TODO Добавить транзакцию на проверку: если в комнате нет хотя бы одного пользователя в статусе не kicked, left то удалить комнату

        return web.json_response(status=200, data={'message': f'User {data["aim_username"]} was successfully kicked.'})


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def player_ready(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        # result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['ready']).where(RoomUser.room_id == data['room_id']).where(RoomUser.game_sess_id == request.cookies['game_sess_id']))
        result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['ready']).where(RoomUser.room_id == data['room_id']).where(RoomUser.game_sess_id == data['game_sess_id']))
        if result.rowcount == 0:
            return web.json_response(status=500, data={'error': {'message': 'Something went wrong.'}})

        return web.json_response(status=200, data={'message': 'You`re ready!'})


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def game_start(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
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
            #TODO добавить в where не только != ready, но и kicked
            await conn.execute(update(RoomUser).values(player_number=0, state=ROOMUSER_STATES['left']).where(RoomUser.room_id == room_row['id']).where(RoomUser.state != ROOMUSER_STATES['ready']))
            
            actual_players_quantity = 0
            for roomuser, order_number, char in zip(roomusers_rows, *order_chars_list):
                result = await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['in_game'], player_number=order_number, info=char).where(RoomUser.room_id == room_row['id']).where(RoomUser.game_sess_id == roomuser['game_sess_id']))
                actual_players_quantity += 1

            await conn.execute(update(Room).values(state=ROOM_STATES['opening']).where(Room.id == room_row['id']))

            if actual_players_quantity < request.app['config']['GAME_MIN_PLAYERS_QUANTITY']:
                await tr.rollback()
                return web.json_response(status=400, data={'error': {'message': 'Not enough users to start the game'}})

        return web.json_response(status=200, data={'message': 'The game is started'})


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def game_info(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row
            
        room_row = await (await conn.execute(select(Room).where(Room.id == data['room_id']))).fetchone()
        users_rows = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == data['room_id']).where(RoomUser.state == ROOMUSER_STATES['in_game']))).fetchall()

        data = {
            'id': room_row['id'],
            'initiator': room_row['initiator'],
            'state': room_row['state'],
            'lap': room_row['lap'],
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


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def player_get_current(request: web.Request, data:dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        room_row = await (await conn.execute(select(Room).where(Room.id == user_row['room_id']))).fetchone()

        data = {
            'room_id': user_row['room_id'],
            'username': user_row['username'],
            'player_number': user_row['player_number'],
            'info': user_row['info'],
            'opened': user_row['opened'],
            'card_opened_numbers': user_row['card_opened_numbers'],
            'state': user_row['state'],
            'is_owner': True if room_row['initiator'] == user_row['username'] else False
        }
        return web.json_response(status=200, data=data)


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'open')
async def player_open_chars(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        room_row = await (await conn.execute(select(Room).where(Room.id == user_row['room_id']))).fetchone()
        if user_row['player_number'] != room_row['turn']:
            return web.json_response(status=400, data={'error': {'message': 'Currently it is not your turn.'}})
        if room_row['state'] != ROOM_STATES['opening']:
            return web.json_response(status=400, data={'error': {'message': f'The game is currrently in {room_row["state"]} state.'}})
        
        roomusers_rows = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_row['id']).where(RoomUser.state == ROOMUSER_STATES['in_game']).order_by(RoomUser.player_number))).fetchall()

        try:
            isinstance(data['open'], list)
        except TypeError:
            return web.json_response(status=400, data={'error': {'message': '"open" must be an array object'}})

        opened = user_row['opened'].strip().split(',')
        for open in data['open']:
            if not open in opened:
                opened.append(open)
        opened = ','.join(opened)[1:] if ','.join(opened)[0] == ',' else ','.join(opened)
        lap, turn, state = room_row['lap'], room_row['turn'], room_row['state']

        async with conn.begin():
            await conn.execute(update(RoomUser).values(opened=opened).where(RoomUser.room_id == room_row['id']).where(RoomUser.game_sess_id == user_row['game_sess_id']))

            if turn == roomusers_rows[-1]['player_number']:
                await conn.execute(insert(RoomVote).values(lap=lap, state=ROOMVOTE_STATES['waiting_first_time'], extra={'first_lap': {}}, room_id=room_row['id'], result=None))
                state = ROOM_STATES['voting']
            else:
                for i in range(len(roomusers_rows)):
                    if roomusers_rows[i]['player_number'] == turn:
                        turn = roomusers_rows[i + 1]['player_number']
                        break
            await conn.execute(update(Room).values(turn=turn, state=state).where(Room.id == room_row['id']))

        return web.json_response(status=200, data={'message': 'Successfully opened.'})


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id', 'votes')
async def player_make_vote(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        room_row = await (await conn.execute(select(Room).where(Room.id == user_row['room_id']))).fetchone()
        if room_row['state'] != ROOM_STATES['voting']:
            return web.json_response(status=400, data={'error': {'message': 'Voting is over'}})
        if user_row['username'] in data['votes']:
            return web.json_response(status=400, data={'error': {'message': 'You can`t vote for yourself.'}})

        roomvote_row = await (await conn.execute(select(RoomVote).where(RoomVote.room_id == user_row['room_id']).where(RoomVote.lap == room_row['lap']))).fetchone()
        roomuser_row = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_row['id']).where(RoomUser.state == ROOMUSER_STATES['in_game']))).fetchall()
        state, result, extra = roomvote_row['state'], roomvote_row['result'], roomvote_row['extra']

        if state == ROOMVOTE_STATES['waiting_first_time']:
            if user_row['username'] in extra['first_lap']:
                return web.json_response(status=400, data={'error': {'message': 'You`ve already voted.'}})

            extra['first_lap'].update({user_row['username']: data['votes']})

            if len(extra['first_lap']) == len(roomuser_row):
                votes = []
                for user_votes in extra['first_lap'].values():
                    for vote in user_votes:
                        votes.append(vote)

                result = voting_to_kick(votes)
                if len(result) != 1:
                    state = ROOMVOTE_STATES['waiting_second_time']
                    extra['second_lap'] = {}
                else:
                    state = ROOMVOTE_STATES['done']

        elif state == ROOMVOTE_STATES['waiting_second_time']:
            if user_row['username'] in extra['second_lap']:
                return web.json_response(status=400, data={'error': {'message': 'You`ve already voted.'}})

            if user_row['username'] in result:
                return web.json_response(status=400, data={'error': {'message': 'You are unable to vote because the voting is against you'}})

            extra['second_lap'].update({user_row['username']: data['votes']})

            if len(extra['second_lap']) == len(roomuser_row) - len(result):
                votes = []
                for user_votes in extra['second_lap'].values():
                    for vote in user_votes:
                        votes.append(vote)

                result = voting_to_kick(votes)
                if len(result) != 1:
                    result = None
                    
                state = ROOMVOTE_STATES['done']

        async with conn.begin():
            #TODO переделать result в JSON
            await conn.execute(update(RoomVote).values(state=state, result=result if result else None, extra=extra).where(RoomVote.room_id == room_row['id']).where(RoomVote.lap == room_row['lap']))

            if state == ROOMVOTE_STATES['done']:
                if result:
                    for username in result.keys():
                        await conn.execute(update(RoomUser).values(state=ROOMUSER_STATES['kicked_by_vote']).where(RoomUser.room_id == room_row['id']).where(RoomUser.username == username))
                if room_row['lap'] == get_laps_quantity(room_row['quantity_players']):
                    await conn.execute(update(Room).values(state=ROOM_STATES['finished'], closed=datetime.datetime.utcnow()))
                else:
                    await conn.execute(update(Room).values(state=ROOM_STATES['opening'], lap=room_row['lap'] + 1, turn=1).where(Room.id == room_row['id']))

        return web.json_response(status=200, data={"message": "Successfuly voted."})


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def game_votes_info(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        room_row = await (await conn.execute(select(Room).wehere(Room.id == user_row['room_id']))).fetchone()
        roomvote_row = await (await conn.execute(select(RoomVote).wehere(RoomVote.user_id == user_row['room_id']).where(RoomVote.lap == room_row['lap']))).fetchone()

        data = {
            'room_id': room_row['id'],
            'lap': room_row['lap'],
            'state': roomvote_row['state'],
            'extra': roomvote_row['extra']['fist_lap'] if not 'second_lap' in roomvote_row['extra'] else room_row['extra']['second_lap'],
            'result': roomvote_row['result']
        }

        return web.json_response(status=200, data=data)


# @game_sess_id_cookie_required
@json_content_type_required
@contains_fields_or_return_error_responce('room_id')
async def game_results(request: web.Request, data: dict):
    async with request.app['db'].acquire() as conn:
        # user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], request.cookies['game_sess_id'])
        user_row = await get_user_row_in_room_or_error_response(conn, data['room_id'], data['game_sess_id'])
        if isinstance(user_row, web.Response):
            return user_row

        room_row = await (await conn.execute(select(Room).where(Room.id == user_row['room_id']))).fetchone()
        roomusers_rows = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_row['id']))).fetchall()
        roomvotes_rows = await (await conn.execute(select(RoomVote).where(RoomVote.room_id == room_row['id']))).fetchall()
        if room_row['state'] != 'finished':
            return web.json_response(status=400, data={'error': {'message': 'The game is not finished.'}})
        else:
            data = DateTimeJsonEncoder().encode({
                'room_id': room_row['id'],
                'created': room_row['created'],
                'closed': room_row['closed'],
                'room_users': [
                    [user['player_number'], user['id'], user['info'], user['state']] for user in roomusers_rows
                ],
                'votes': [
                    [vote['lap'], vote['state'], vote['extra'], vote['result']] for vote in roomvotes_rows
                ]
            })
            return web.json_response(status=200, text=data)