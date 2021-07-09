from aiohttp import web
from functools import wraps
import json
import datetime
import jwt


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