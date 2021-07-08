import unittest
import pytest
import sys, os
import json
from aiohttp import web


sys.path.append(os.getcwd())
print(os.getcwd())

from utils import contains_fields_or_return_error_responce


class TestUtils:
    @pytest.mark.parametrize("obj, fields, expected_result", [
        pytest.param({'room_id': 12345}, ['room_id'], None, id='common'),
        pytest.param({'room_id': 12345, 'something_else': 12345}, ['room_id'], None, id='common_and_something')
    ])
    def test_contains_fields_or_return_error_responce_return_none(self, obj, fields, expected_result):
        result = contains_fields_or_return_error_responce(obj, *fields)
        assert result == expected_result
    
    @pytest.mark.parametrize("obj, fields, expected_status, expected_data", [
        pytest.param({'room_id': 12345, 'something_else': 12345}, ['room_id', 'no_such_field'], 400, {'error': {'message': 'No required fields in request', 'extra': ['no_such_field']}},  id='no_such_field'),
        pytest.param({}, ['room_id'], 400, {'error': {'message': 'No required fields in request', 'extra': ['room_id']}},  id='empty_obj'),
    ])
    def test_contains_fields_or_return_error_responce_return_error_response(self, obj, fields, expected_status, expected_data):
        result = contains_fields_or_return_error_responce(obj, *fields)
        assert result.status == expected_status
        assert json.loads(result.text) == expected_data