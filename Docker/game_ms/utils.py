from aiohttp.abc import AbstractAccessLogger
from aiohttp import web
from functools import wraps
import json
import datetime
import jwt
import logging
from sqlalchemy import select
from sqlalchemy.sql.expression import func as sa_func
import random

from db import RoomUser
from game_help import Player


class AccessLogger(AbstractAccessLogger):

    def log(self, request, response, time):
        self.logger.info(f'[%(asctime)s] [%(process)d] [%(levelname)s] '
                         f'{request.remote} '
                         f'"{request.method} {request.path} '
                         f'done in {time}s: {response.status}')




class DateTimeJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.__str__()
        return super().default(o)



def json_content_type_required(func):
    """ """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        if not 'Content-Type' in request.headers:
            return web.json_response(status=400, data={'error': {'message': 'Content-Type required'}})
        if not request.headers['Content-Type'] == 'application/json':
            return web.json_response(status=400, data={'error': {'message': 'Content-Type must be "application/json"'}})
        
        try:
            data = await request.json()
        except json.JSONDecodeError as exc:
            return web.json_response(status=400, data={'error': {'message': 'JSON decode error. Data must be JSON formatted'}})

        return await func(request, data, *args, **kwargs)

    return wrapper


def contains_fields_or_return_error_responce(*fields):
    def wrapper1(func):
        """object contains all required fields. Else return json response with the fields"""
        @wraps(func)
        async def wrapper2(request: web.Request, data: dict, *args, **kwargs):
            assert isinstance(data, dict)
            for field in fields:
                assert isinstance(field, str)
                
            errors = list(set(fields).difference(data))
            if errors:
                return web.json_response(status=400, data={'error': {'message': 'No required fields in request', 'extra': errors}})
            else:
                return await func(request, data, *args, **kwargs)
            
        return wrapper2
    return wrapper1


def game_sess_id_cookie_required(func):
    """ """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        if not 'game_sess_id' in request.cookies:
            return web.json_response(status=403, data={'error': {'message': 'game_sess_id cookies is required.'}})
        
        return await func(request, *args, **kwargs)
    return wrapper


async def get_user_row_in_room_or_error_response(conn, room_id, game_sess_id):
    row = await (await conn.execute(select(RoomUser).where(RoomUser.room_id == room_id).where(RoomUser.game_sess_id == game_sess_id))).fetchone()
    if row is None:
        return web.json_response(status=400, data={'error': {'message': 'User not in room or room with such room_id doesn`t exist or game_sess_id is invalid.'}})
    return row


async def db_max_id(conn, Table, default, max_plus_one):
    """
    if no rows use default
    else max id of rows (max + 1 if max_plus_one)
    """
    id = (await (await conn.execute(select(sa_func.max(Table.id)))).fetchone())[0]
    if id:
        return id if not max_plus_one else id + 1
    else:
        return default


async def db_max_column_value_in_room(conn, Table, room_id, column):
    conn_res = await conn.execute(select(Table).where(Table.room_id == room_id).order_by(getattr(Table, column).desc()))
    max = (await conn_res.first())[column]
    return max


def init_game(quantity_players):
    """Return list of lists: order and chars"""
    players_list = [[], []]

    seq = [x for x in range(1, quantity_players + 1)]
    while seq:
        players_list[0].append(seq.pop(random.randint(0, len(seq) - 1)))
        players_list[1].append(Player().get_json())
    
    return players_list


def get_laps_quantity(quantity_players):
    return quantity_players // 2


def calculate_opening_quantity(quantity_players, lap, config: dict):
    """Calculate quantity open characteristics"""
    quantity_min_players, quantity_laps, quantity_total_chars = config.get('GAME_MIN_PLAYERS_QUANTITY', 4), config.get('GAME_LAPS_QUANTITY', quantity_players // 2), config.get('GAME_CHARS_QUANTITY', 11)

    assert isinstance(config, dict)
    logging.debug(f'{quantity_min_players}, {quantity_players}')
    assert quantity_min_players <= quantity_players
    assert lap > 0
    assert quantity_total_chars > 6

    if not (quantity_players >= quantity_laps + 2):
        chars_per_lap = [3, 3]
    else:
        chars_per_lap = []
        k = quantity_total_chars - 6
        i = 0
        while k > 0:
            if i == quantity_laps - 1:
                i = 0
            if len(chars_per_lap) < quantity_laps:
                chars_per_lap.append(1)
            else:
                chars_per_lap[i] += 1
                i += 1
            k -= 1

    return chars_per_lap[lap - 1]