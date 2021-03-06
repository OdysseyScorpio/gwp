import gzip
import io
import json

import pytest
from flask import Flask

from config import API_DB_CONFIG
from tests.modules.v4.helpers import make_user, make_colony

versions = ['v4']
markets = API_DB_CONFIG


class TestColoniesPutModMeta:
    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_put_colony_mod_list(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)

        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/colonies/{}/mod_metadata'.format(version, market, colony_id)

        colony_metadata = {
            'ModList': ["Core", "GlitterWorldPrime [R1]"]
        }

        payload = io.BytesIO(gzip.compress(json.dumps(colony_metadata).encode('utf-8')))

        result = client.put(url, data={'mods': (payload, 'mods')})
        assert result.status_code == 200
