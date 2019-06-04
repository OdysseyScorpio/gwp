import json

import fakeredis
import pytest
from flask import Flask
from flask import g

from config import API_DB_CONFIG
from lib.db import get_redis_database_connection
from lib.gwpcc import consts
from tests.modules.v4.helpers import make_user, make_colony

versions = ['v4']
markets = API_DB_CONFIG


class TestColoniesPut:
    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_colony_simple(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/colonies/{}'.format(version, market, colony_id)

        colony_metadata = {
            'BaseName'    : 'TestBase',
            'FactionName' : 'TestFaction',
            'Planet'      : 'TestPlanet',
            'OwnerType'   : 'Steam',
            'OwnerID'     : user_id,
            'LastGameTick': 1,
            'HasSpawned'  : False
        }

        result = client.put(url, data=json.dumps(colony_metadata), mimetype='application/json')
        assert result.status_code == 200
        assert result.json
        assert result.json['Hash'] == colony_id

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_colony_ban_normal(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony_metadata = {
            'BaseName'    : 'TestBase',
            'FactionName' : 'TestFaction',
            'Planet'      : 'TestPlanet',
            'OwnerType'   : 'Normal',
            'OwnerID'     : user_id,
            'LastGameTick': 1,
            'HasSpawned'  : False
        }

        url = '/{}/{}/colonies/create'.format(version, market)

        result = client.put(url, data=json.dumps(colony_metadata), mimetype='application/json')

        colony_id = result.json['Hash']

        url = '/{}/{}/colonies/{}'.format(version, market, colony_id)

        colony_metadata = {
            'BaseName'    : 'TestBase',
            'FactionName' : 'TestFaction',
            'Planet'      : 'TestPlanet',
            'OwnerType'   : 'Normal',
            'OwnerID'     : user_id,
            'LastGameTick': 1,
            'HasSpawned'  : True
        }

        result = client.put(url, data=json.dumps(colony_metadata), mimetype='application/json')
        assert result.status_code == 200

        # Check the the user is in the moderation queue.
        redis = g._database
        assert redis.sismember(consts.KEY_USER_NORMAL_ID_MODERATE_SET, user_id)

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_colony_ban_steam(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/colonies/{}'.format(version, market, colony_id)

        colony_metadata = {
            'BaseName'    : 'TestBase',
            'FactionName' : 'TestFaction',
            'Planet'      : 'TestPlanet',
            'OwnerType'   : 'Steam',
            'OwnerID'     : user_id,
            'LastGameTick': 1,
            'HasSpawned'  : True
        }

        result = client.put(url, data=json.dumps(colony_metadata), mimetype='application/json')
        assert result.status_code == 200

        # Check the the user is in the moderation queue.
        redis = g._database
        assert redis.sismember(consts.KEY_USER_STEAM_ID_MODERATE_SET, user_id)

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_colony_mismatched_id(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/colonies/{}'.format(version, market, colony_id)

        colony_metadata = {
            'BaseName'    : 'TestBase',
            'FactionName' : 'TestFaction',
            'Planet'      : 'TestPlanet',
            'OwnerType'   : 'Steam',
            'OwnerID'     : '1111111111111111111111111111111111111111',
            'LastGameTick': 1,
            'HasSpawned'  : False
        }

        result = client.put(url, data=json.dumps(colony_metadata), mimetype='application/json')
        assert result.status_code == 201
        assert result.json
        assert result.json['Hash'] != colony_id
