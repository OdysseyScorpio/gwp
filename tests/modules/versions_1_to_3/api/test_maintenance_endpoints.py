import pytest
from flask import Flask

from config import OLD_API_DB_CONFIG

versions = OLD_API_DB_CONFIG


class TestMode:

    @pytest.mark.parametrize("version", versions)
    def test_get_mode(self, version, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '/{}/application/maintenance/mode'.format(version)
        result = client.get(url)

        assert result.status_code == 200

    @pytest.mark.parametrize("version", versions)
    def test_get_window(self, version, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '/{}/application/maintenance/window'.format(version)
        result = client.get(url)

        assert result.status_code == 200
        assert all(key in result.json for key in ['Start', 'Stop'])

    @pytest.mark.parametrize("version", versions)
    def test_get_window(self, version, test_app_context: Flask):
        client = test_app_context.test_client()
        url = '/{}/application/version'.format(version)
        result = client.get(url)

        assert result.status_code == 200
        assert result.json
        assert 'Version' in result.json
        assert result.json['Version']
