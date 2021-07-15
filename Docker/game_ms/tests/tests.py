import unittest
import pytest
import sys, pathlib, os
import json
import aiohttp


sys.path.append(pathlib.Path(__file__).parent.parent)
# sys.path.append(os.getcwd())

from utils import contains_fields_or_return_error_responce
from views import room_connect
from main import return_app


# class TestUtils:
#     @pytest.mark.parametrize("obj, fields, expected_result", [
#         pytest.param({'room_id': 12345}, ['room_id'], None, id='common'),
#         pytest.param({'room_id': 12345, 'something_else': 12345}, ['room_id'], None, id='common_and_something')
#     ])
#     def test_contains_fields_or_return_error_responce_return_none(self, obj, fields, expected_result):
#         result = contains_fields_or_return_error_responce(obj, *fields)
#         assert result == expected_result
    
#     @pytest.mark.parametrize("obj, fields, expected_status, expected_data", [
#         pytest.param({'room_id': 12345, 'something_else': 12345}, ['room_id', 'no_such_field'], 400, {'error': {'message': 'No required fields in request', 'extra': ['no_such_field']}},  id='no_such_field'),
#         pytest.param({}, ['room_id'], 400, {'error': {'message': 'No required fields in request', 'extra': ['room_id']}},  id='empty_obj'),
#     ])
#     def test_contains_fields_or_return_error_responce_return_error_response(self, obj, fields, expected_status, expected_data):
#         result = contains_fields_or_return_error_responce(obj, *fields)
#         assert result.status == expected_status
#         assert json.loads(result.text) == expected_data


class TestRoomApi:

    @pytest.mark.parametrize("method, url, headers, expected_status, expected_result", [
        pytest.param(
            'GET', '/api/v1/room_connect', {}, 400, {'error': {'message': 'Content-Type required'}}, id = 'no_headers'
        ),
        pytest.param(
            'GET', '/api/v1/room_connect', {'Content-Type': 'application/json'}, 400, {'error': {'message': 'Content-Type must be "application/json"'}}, id = 'wrong_content_type'
        ),
    ])
    async def test_room_connect(self, method, url, headers, expected_status, expected_result, aiohttp_server, aiohttp_client):
        server = await aiohttp_server(return_app)
        client = await aiohttp_client(server)

        response = await client.request(method, url, headers=headers)
        assert response.status == expected_status
        assert json.loads(response.text) == expected_result