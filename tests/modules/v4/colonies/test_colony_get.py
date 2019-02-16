import pytest
from flask import Flask

from config import API_DB_CONFIG
from tests.modules.v4.helpers import make_user, make_colony

versions = ['v4']
markets = API_DB_CONFIG


class TestColoniesGet:
    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_get_colony(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/colonies/{}'.format(version, market, colony_id)

        result = client.get(url, mimetype='application/json')
        assert result.status_code == 200
        assert result.json

        client_expects = {'BaseName', 'FactionName', 'Planet', 'OwnerID', 'OwnerType', 'Hash'}
        got = set(result.json.keys())

        assert client_expects.issubset(got)
