import unittest
import pytest
import sys, pathlib, os
import json
import aiohttp
import time


sys.path.append(pathlib.Path(__file__).parent.parent)
# sys.path.append(os.getcwd())

from utils import contains_fields_or_return_error_responce
from views import room_connect
from main import return_app


@pytest.fixture
async def create_room_return_data(aiohttp_server, aiohttp_client):
    initiator = 'admin'
    password = '1234'
    quantity_players = 4
    location = ''
    
    server = await aiohttp_server(await return_app())
    client = await aiohttp_client(server)

    response = await client.request('POST', '/api/v1/room_create', headers={'Content-Type': 'application/json'}, json={'initiator': initiator, 'password': password, 'location': location, 'quantity_players': quantity_players})
    assert response.status == 200
    data = json.loads(await response.text())
    data.update({'initiator': initiator, 'password': password, 'quantity_players': quantity_players, 'game_sess_id': data['game_sess_id'], 'players': {initiator: data['game_sess_id']}})

    return data


async def client_room_connect(client, room_data) -> dict:
    """Return dict with username and game_sess_id of the connected user
    """
    username = 'user-test'
    
    response = await client.request('POST', '/api/v1/room_connect', headers={'Content-Type': 'application/json'}, json={'room_id': room_data['room_id'], 'username': username, 'password': room_data['password']})
    assert response.status == 200
    response_data = json.loads(await response.text())

    return {'username': username, 'game_sess_id': response_data['game_sess_id']}


@pytest.fixture
async def create_game_return_data(aiohttp_server, aiohttp_client, create_room_return_data):
    server = await aiohttp_server(await return_app())
    client = await aiohttp_client(server)

    response = await client.request('POST', '/api/v1/room_fill_players', headers={'Content-Type': 'application/json'}, json={'room_id': create_room_return_data['room_id'], 'debug': True})
    assert response.status == 200
    create_room_return_data['players'].update(json.loads(await response.text())['players'])

    response = await client.request('POST', '/api/v1/game_start', headers={'Content-Type': 'application/json'}, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': create_room_return_data['game_sess_id']})
    assert response.status == 200

    return create_room_return_data


# class TestUtils:

#     @pytest.mark.parametrize("method, url", [
#         pytest.param('POST', '/api/v1/room_connect', id='room_fill_players'),
#         pytest.param('POST', '/api/v1/room_connect', id='room_create'),
#         pytest.param('POST', '/api/v1/room_connect', id='room_info'),
#         pytest.param('POST', '/api/v1/room_connect', id='room_delete'),
#         pytest.param('POST', '/api/v1/room_connect', id='player_change_username'),
#         pytest.param('POST', '/api/v1/room_connect', id='player_kick'),
#         pytest.param('POST', '/api/v1/room_connect', id='player_ready'),
#         pytest.param('POST', '/api/v1/room_connect', id='game_start'),
#         pytest.param('POST', '/api/v1/room_connect', id='game_info'),
#         pytest.param('POST', '/api/v1/room_connect', id='player_get_current'),
#         pytest.param('POST', '/api/v1/room_connect', id='player_open_chars'),
#         pytest.param('POST', '/api/v1/room_connect', id='player_make_vote'),
#         pytest.param('POST', '/api/v1/room_connect', id='game_votes_info'),
#         pytest.param('POST', '/api/v1/room_connect', id='game_game_results'),
#     ])
#     async def test_json_content_type_required(self, method, url, aiohttp_server, aiohttp_client):
#         server = await aiohttp_server(await return_app())
#         client = await aiohttp_client(server)

#         response = await client.request(method, url, headers={'Content-Type': 'plain/text'}, json={})
#         assert response.status == 400
#         assert json.loads(await response.text()) == {'error': {'message': 'Content-Type must be "application/json"'}}

#         response = await client.request(method, url, headers={'Content-Type': 'application/json'}, data='')
#         assert response.status == 400
#         assert json.loads(await response.text()) == {'error': {'message': 'JSON decode error. Data must be JSON formatted'}}


#     @pytest.mark.parametrize("method, url, headers, fields", [
#         pytest.param(
#             'POST', '/api/v1/room_fill_players', {'Content-Type': 'application/json'}, ['room_id'], id = 'room_fill_players'
#         ),
#         pytest.param(
#             'POST', '/api/v1/room_connect', {'Content-Type': 'application/json'}, ['room_id', 'password', 'username'], id = 'room_connect'
#         ),
#         pytest.param(
#             'POST', '/api/v1/room_create', {'Content-Type': 'application/json'}, ['initiator', 'password', 'quantity_players', 'location'], id = 'room_create'
#         ),
#         pytest.param(
#             'POST', '/api/v1/room_info', {'Content-Type': 'application/json'}, ['room_id'], id = 'room_info'
#         ),
#         pytest.param(
#             'POST', '/api/v1/room_delete', {'Content-Type': 'application/json'}, ['room_id'], id = 'room_delete'
#         ),
#         pytest.param(
#             'POST', '/api/v1/player_change_username', {'Content-Type': 'application/json'}, ['room_id', 'new_username'], id = 'player_change_username'
#         ),
#         pytest.param(
#             'POST', '/api/v1/player_kick', {'Content-Type': 'application/json'}, ['room_id', 'aim_username'], id = 'player_kick'
#         ),
#         pytest.param(
#             'POST', '/api/v1/player_ready', {'Content-Type': 'application/json'}, ['room_id'], id = 'player_ready'
#         ),
#         pytest.param(
#             'POST', '/api/v1/player_get_current', {'Content-Type': 'application/json'}, ['room_id'], id = 'player_get_current'
#         ),
#         pytest.param(
#             'POST', '/api/v1/player_open_chars', {'Content-Type': 'application/json'}, ['room_id', 'open'], id = 'player_open_chars'
#         ),
#         pytest.param(
#             'POST', '/api/v1/player_make_vote', {'Content-Type': 'application/json'}, ['room_id', 'votes'], id = 'player_make_vote'
#         ),
#         pytest.param(
#             'POST', '/api/v1/game_start', {'Content-Type': 'application/json'}, ['room_id'], id = 'game_start'
#         ),
#         pytest.param(
#             'POST', '/api/v1/game_info', {'Content-Type': 'application/json'}, ['room_id'], id = 'game_info'
#         ),
#         pytest.param(
#             'POST', '/api/v1/game_votes_info', {'Content-Type': 'application/json'}, ['room_id'], id = 'game_votes_info'
#         ),
#         pytest.param(
#             'POST', '/api/v1/game_results', {'Content-Type': 'application/json'}, ['room_id'], id = 'game_results'
#         ),
#     ])
#     async def test_contains_fields_or_return_error_responce(self, method, url, headers, fields, aiohttp_server, aiohttp_client):
#         server = await aiohttp_server(await return_app())
#         client = await aiohttp_client(server)
#         result_template = {'error': {'message': 'No required fields in request', 'extra': []}}

#         for field in fields:
#             result_template['error']['extra'] = [field]
#             request_fields = fields.copy()
#             request_fields.remove(field)

#             response = await client.request(method, url, headers=headers, json={}.fromkeys(request_fields, ''))
#             assert response.status == 400
#             assert json.loads(await response.text()) == result_template

#     async def test_get_user_row_in_room_or_error_response()



# class TestRoomApiTemp:
#     OWNER_NAME = 'admin'
#     PASSWORD = '1234'
#     room_id = 1020
#     players = {}


#     @pytest.mark.parametrize("data, expected_status, expected_fields", [
#         pytest.param({'initiator': OWNER_NAME, 'password': PASSWORD, 'quantity_players': 4, 'location': ''}, 200, ['message', 'room_id', 'game_sess_id', 'password']),
#     ])
#     async def test_room_create(self, data, expected_status, expected_fields, aiohttp_server, aiohttp_client):
#         method, url, headers = 'POST', '/api/v1/room_create', {'Content-Type': 'application/json'}

#         server = await aiohttp_server(await return_app())
#         client = await aiohttp_client(server)

#         response = await client.request(method, url, headers=headers, json=data)
#         response_data = json.loads(await response.text())
#         assert response.status == expected_status
#         for field in expected_fields:
#             assert field in response_data

#         self.players[self.OWNER_NAME] = response_data['game_sess_id']
#         self.room_id = response_data['room_id']
#         self.password = response_data['password']


#     @pytest.mark.parametrize("data, expected_status, expected_fields, expected_result", [
#         pytest.param({'room_id': room_id, 'password': PASSWORD, 'username': 'user-1'}, 200, ['message', 'game_sess_id'], None, id='Successfuly connected'),
#         pytest.param({'room_id': -1, 'password': PASSWORD, 'username': 'user-1'}, 400, ['error'], {'error': {'message': 'No such room with the provided room_id and password.'}}, id='invalid_room_id'),
#         pytest.param({'room_id': room_id, 'password': '###', 'username': 'user-1'}, 400, ['error'], {'error': {'message': 'No such room with the provided room_id and password.'}}, id='invalid_password'),
#         pytest.param({'room_id': 1000, 'password': PASSWORD, 'username': 'user-1'}, 400, ['error'], {'error': {'message': 'You are unable to connect to started or finished game.'}}, id='finished_game_error'),
#     ])
#     async def test_room_connect(self, data, expected_status, expected_fields, expected_result, aiohttp_server, aiohttp_client):
#         method, url, headers = 'POST', '/api/v1/room_connect', {'Content-Type': 'application/json'}
#         server = await aiohttp_server(await return_app())
#         client = await aiohttp_client(server)

#         response = await client.request(method, url, headers=headers, json=data)
#         response_data = json.loads(await response.text())
#         assert response.status == expected_status
#         if expected_result:
#             assert response_data == expected_result
#         if expected_fields:
#             for field in expected_fields:
#                 assert field in response_data
        
#         if expected_status == 200:
#             self.players[data['username']] = response_data['game_sess_id']


#     @pytest.mark.parametrize("data, expected_status, expected_fields, expected_result", [
#         pytest.param({'room_id': -1}, 400, ['error'], {'error': {'message': 'Room is not exist.'}}, id='Room is not exist'),
#         pytest.param({'room_id': room_id}, 200, ['id', 'initiator', 'quantity_players', 'state', 'connected'], None, id='success'),
#     ])
#     async def test_room_info(self, data, expected_status, expected_fields, expected_result, aiohttp_server, aiohttp_client):
#         method, url, headers = 'POST', '/api/v1/room_info', {'Content-Type': 'application/json'}
#         server = await aiohttp_server(await return_app())
#         client = await aiohttp_client(server)

#         response = await client.request(method, url, headers=headers, json=data)
#         response_data = json.loads(await response.text())
#         if expected_fields:
#             for field in expected_fields:
#                 assert field in response_data
#         if expected_result:
#             assert response_data == expected_result
#         else:
#             print(response_data)
#             for conn_player_obj in response_data['connected']:
#                 assert 'username' in conn_player_obj
#                 assert 'state' in conn_player_obj


#     @pytest.mark.parametrize("expected_status, is_owner, expected_fields, expected_result", [
#         pytest.param(403, False, ['error'], {'error': {'message': 'You are not the room initiator'}}, id='No rules'),
#         pytest.param(200, True, ['message'], {'message': 'Room was deleted'}, id='success'),
#     ])
#     async def test_room_delete(self, expected_status, is_owner, expected_fields, expected_result, aiohttp_server, aiohttp_client):
#         method, url, headers = 'POST', '/api/v1/room_delete', {'Content-Type': 'application/json'}
#         server = await aiohttp_server(await return_app())
#         client = await aiohttp_client(server)

#         response = await client.request(method, '/api/v1/room_create', headers=headers, json={'initiator': self.OWNER_NAME, 'password': self.PASSWORD, 'quantity_players': 4, 'location': ''})
#         response_data = json.loads(await response.text())

#         time.sleep(1)
#         response_cl = await client.request(method, '/api/v1/room_connect', headers=headers, json={'username': 'user-1', 'password': self.PASSWORD, 'room_id': response_data['room_id']})
#         response_data_cl = json.loads(await response_cl.text())

#         response = await client.request(method, url, headers=headers, json={'room_id': response_data['room_id'], 'game_sess_id': response_data['game_sess_id'] if is_owner else response_data_cl['game_sess_id']})
#         response_data = json.loads(await response.text())

#         if expected_result:
#             assert response_data == expected_result
#         if expected_fields:
#             for field in expected_fields:
#                 assert field in response_data



class TestPlayerApiTemp:
    # async def player_change_username

    # player kick

    async def test_player_ready(self, aiohttp_client, aiohttp_server, create_room_return_data):
        method, url, headers = 'POST', '/api/v1/player_ready', {'Content-Type': 'application/json'}
        server = await aiohttp_server(await return_app())
        client = await aiohttp_client(server)

        cl_data = {
            'username': 'user_test',
        }
        response = await client.request(method, '/api/v1/room_connect', headers=headers, json={'username': cl_data['username'], 'password': create_room_return_data['password'], 'room_id': create_room_return_data['room_id']})
        response_conn_data = json.loads(await response.text())
        cl_data.update({'game_sess_id': response_conn_data['game_sess_id']})

        response = await client.request(method, url, headers=headers, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': response_conn_data['game_sess_id']})
        response_data = json.loads(await response.text())

        assert response.status == 200
        assert response_data == {'message': 'You`re ready!'}


    @pytest.mark.parametrize("expected_status, expected_fields_dict, expected_result, kwargs", [
        pytest.param(200, {'room_id': int, 'username': str, 'player_number': int, 'info': dict, 'opened': list, 'card_opened_numbers': list, 'state': str, 'is_owner': bool}, None, None, id='success'),
    ])
    async def test_player_get_current(self, expected_status, expected_fields_dict, expected_result, kwargs, aiohttp_client, aiohttp_server, create_game_return_data):
        method, url, headers = 'POST', '/api/v1/player_get_current', {'Content-Type': 'application/json'}
        server = await aiohttp_server(await return_app())
        client = await aiohttp_client(server)

        response = await client.request(method, url, headers=headers, json={'room_id': create_game_return_data['room_id'], 'game_sess_id': create_game_return_data['game_sess_id']})
        response_data = json.loads(await response.text())
        assert response.status == expected_status
        if expected_fields_dict:
            for field, value in expected_fields_dict.items():
                if value in (int, bool, str, dict, list):
                    try:
                        value(response_data[field])
                    except (ValueError, TypeError) as exc:
                        raise AssertionError(exc)
                else:
                    assert response_data[field] == value
        if expected_result:
            assert response_data == expected_result


    @pytest.mark.parametrize("expected_status, open_chars, expected_fields_dict, expected_result, kwargs", [
        pytest.param(400, '', {'error': dict}, {'error': {'message': 'Currently it is not your turn.'}}, {'not_your_turn': True}, id='not_your_turn'),
        pytest.param(400, '', {'error': dict}, {'error': {'message': 'The game is currrently in waiting state.'}}, {'game_not_started': True}, id='game_not_started'),
    ])
    async def test_player_open_chars(self, expected_status, open_chars, expected_fields_dict, expected_result, kwargs, aiohttp_client, aiohttp_server, create_game_return_data, create_room_return_data):
        method, url, headers = 'POST', '/api/v1/player_open_chars', {'Content-Type': 'application/json'}
        server = await aiohttp_server(await return_app())
        client = await aiohttp_client(server)


        if kwargs.get('game_not_started', 0) == True:
            response = await client.request(method, '/api/v1/game_info', headers=headers, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': create_room_return_data['game_sess_id']})
            response_data = json.loads(await response.text())
            print(response_data)
        else:
            game_info = json.loads(await (await client.request(method, '/api/v1/game_info', headers=headers, json={'room_id': create_game_return_data['room_id'], 'game_sess_id': create_game_return_data['game_sess_id']})).text())
            for user_data in game_info['players']:
                if user_data['player_number'] != game_info['turn']:
                    if kwargs.get('not_your_turn', 0) == True:
                        response = await client.request(method, url, headers=headers, json={'room_id': create_game_return_data['room_id'], 'game_sess_id': create_game_return_data['players'][user_data['username']], 'open': open_chars})
                        response_data = json.loads(await response.text())
                        break
                
                    
        
        assert response.status == expected_status
        if expected_fields_dict:
            for field, value in expected_fields_dict.items():
                if value in (int, bool, str, dict, list):
                    try:
                        value(response_data[field])
                    except (ValueError, TypeError) as exc:
                        raise AssertionError(exc)
                else:
                    assert response_data[field] == value
        if expected_result:
            assert response_data == expected_result



class TestGameApiTemp:

    @pytest.mark.parametrize("expected_status, expected_fields, expected_result, kwargs", [
        pytest.param(403, ['error'], {'error': {'message': 'You have no priveleges to do this.'}}, {'is_owner': False}, id='not_owner'),
        pytest.param(400, ['error'], {'error': {'message': 'Not enough users to start the game'}}, {'fill_room': False}, id='not_enough_users'),
        pytest.param(200, ['message'], {'message': 'The game is started'}, {}, id='success'),
        pytest.param(400, ['error'], {'error': {'message': 'The game is already started'}}, {'started_game': True}, id='started_game'),
    ])
    async def test_game_start(self, expected_status, expected_fields, expected_result, kwargs, aiohttp_client, aiohttp_server, create_room_return_data):
        method, url, headers = 'POST', '/api/v1/game_start', {'Content-Type': 'application/json'}
        server = await aiohttp_server(await return_app())
        client = await aiohttp_client(server)

        if kwargs.get('is_owner', 1) == False:
            client_data = await client_room_connect(client, create_room_return_data)
            response = await client.request(method, url, headers=headers, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': client_data['game_sess_id']})
            response_data = json.loads(await response.text())
        else:
            if kwargs.get('fill_room', 1) == False:
                response = await client.request(method, url, headers=headers, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': create_room_return_data['game_sess_id']})
                response_data = json.loads(await response.text())
            else:
                response_fill = await client.request(method, 'api/v1/room_fill_players', headers=headers, json={'room_id': create_room_return_data['room_id']})
                assert response_fill.status == 200

                response = await client.request(method, url, headers=headers, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': create_room_return_data['game_sess_id']})
                response_data = json.loads(await response.text())

                if kwargs.get('started_game', 0) == True:
                    response = await client.request(method, url, headers=headers, json={'room_id': create_room_return_data['room_id'], 'game_sess_id': create_room_return_data['game_sess_id']})
                    response_data = json.loads(await response.text())
        
        assert response.status == expected_status
        if expected_fields:
            for field in expected_fields:
                assert field in response_data
        if expected_result:
            assert response_data == expected_result


    @pytest.mark.parametrize("expected_status, expected_fields, expected_result, kwargs", [
        pytest.param(200, ['id', 'initiator', 'state', 'lap', 'turn', 'opening_quantity', 'quantity_players', 'players'], None, None, id='success'),
    ])
    async def test_game_info(self, expected_status, expected_fields, expected_result, kwargs, aiohttp_client, aiohttp_server, create_game_return_data):
        method, url, headers = 'POST', '/api/v1/game_info', {'Content-Type': 'application/json'}
        server = await aiohttp_server(await return_app())
        client = await aiohttp_client(server)

        response = await client.request(method, url, headers=headers, json={'room_id': create_game_return_data['room_id'], 'game_sess_id': create_game_return_data['game_sess_id']})
        response_data = json.loads(await response.text())
        assert response.status == expected_status
        if expected_fields:
            for field in expected_fields:
                assert field in response_data
        if expected_result:
            assert response_data == expected_result


    