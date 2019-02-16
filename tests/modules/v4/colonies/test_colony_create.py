import json

import pytest
from flask import Flask

from config import API_DB_CONFIG
from tests.modules.v4.helpers import make_user

versions = ['v4']
markets = API_DB_CONFIG


class TestColoniesCreate:
    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_create_basic_normal_user(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony = {'BaseName': 'TestBase',
                  'FactionName': 'TestFaction',
                  'Planet': 'TestPlanet',
                  'OwnerType': 'Normal',
                  'OwnerID': user_id,
                  'LastGameTick': 0}

        url = '/{}/{}/colonies/create'.format(version, market)

        result = client.put(url, data=json.dumps(colony), mimetype='application/json')
        assert result.status_code == 201
        assert result.json
        assert 'Hash' in result.json
        assert len(result.json['Hash']) == 40

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_create_basic_steam_user(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony = {'BaseName': 'TestBase',
                  'FactionName': 'TestFaction',
                  'Planet': 'TestPlanet',
                  'OwnerType': 'Steam',
                  'OwnerID': user_id,
                  'LastGameTick': 0}

        url = '/{}/{}/colonies/create'.format(version, market)

        result = client.put(url, data=json.dumps(colony), mimetype='application/json')
        assert result.status_code == 201
        assert result.json
        assert 'Hash' in result.json
        assert len(result.json['Hash']) == 40

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_create_basic_unknown_user(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony = {'BaseName': 'TestBase',
                  'FactionName': 'TestFaction',
                  'Planet': 'TestPlanet',
                  'OwnerType': 'Unknown',
                  'OwnerID': user_id,
                  'LastGameTick': 0}

        url = '/{}/{}/colonies/create'.format(version, market)

        result = client.put(url, data=json.dumps(colony), mimetype='application/json')
        assert result.status_code == 400
