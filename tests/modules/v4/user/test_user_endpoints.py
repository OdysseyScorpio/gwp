import pytest
from flask import Flask

from config import API_DB_CONFIG

versions = ['v4']
markets = API_DB_CONFIG


class TestUser:

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_get_create(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '{}/{}/user/create'.format(version, market)

        result = client.get(url)
        assert result.status_code == 200
        assert result.json
        assert 'Hash' in result.json
        assert len(result.json['Hash']) == 40
