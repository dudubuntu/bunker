from aiohttp import web


def contains_fields_or_return_error_responce(obj: dict, *fields: str):
    """object contains all required fields. Else return json response with the fields"""
    assert isinstance(obj, dict)
    for field in fields:
        assert isinstance(field, str)
        
    errors = list(set(fields).difference(obj))
    if errors:
        return web.json_response(status=400, data={'errors': [{'message': 'No required fields in request', 'extra': errors}]})