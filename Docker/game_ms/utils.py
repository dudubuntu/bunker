from aiohttp import web
from functools import wraps


def contains_fields_or_return_error_responce(obj: dict, *fields: str):
    """object contains all required fields. Else return json response with the fields"""
    assert isinstance(obj, dict)
    for field in fields:
        assert isinstance(field, str)
        
    errors = list(set(fields).difference(obj))
    if errors:
        return web.json_response(status=400, data={'error': {'message': 'No required fields in request', 'extra': errors}})


def json_content_type_required(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not 'Content-Type' in request.headers:
            return web.json_response(status=400, data={'error': {'message': 'Content-Type required'}})
        if not request.headers['Content-Type'] == 'application/json':
            return web.json_response(status=400, data={'error': {'message': 'Content-Type must be "application/json"'}})
        return func(request, *args, **kwargs)
    return wrapper