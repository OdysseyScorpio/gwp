import pytest
from flask import Flask

from config import API_DB_CONFIG

versions = ['v4']
markets = API_DB_CONFIG

class TestAPI:

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_get_mode(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '/{}/{}/application/maintenance/mode'.format(version, market)
        result = client.get(url)

        assert result.status_code == 200

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_get_window(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '/{}/{}/application/maintenance/window'.format(version, market)
        result = client.get(url)

        assert result.status_code == 200
        assert all(key in result.json for key in ['Start', 'Stop'])

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_get_version(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '/{}/{}/application/version'.format(version, market)
        result = client.get(url)

        assert result.status_code == 200
        assert result.json
        assert 'Version' in result.json
        assert result.json['Version']
