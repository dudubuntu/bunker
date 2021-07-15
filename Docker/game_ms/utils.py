from aiohttp.abc import AbstractAccessLogger
from aiohttp import web
from functools import wraps
import json
import datetime
import jwt
from sqlalchemy import select
from sqlalchemy.sql.expression import func as sa_func


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