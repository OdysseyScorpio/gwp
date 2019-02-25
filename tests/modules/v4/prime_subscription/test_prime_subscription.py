import json

import pytest
from flask import Flask

from config import API_DB_CONFIG
from tests.modules.v4.helpers import make_user, make_colony

versions = ['v4']
markets = API_DB_CONFIG


class TestColoniesPut:

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_not_subscribed(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/prime_subscription/check/{}'.format(version, market, colony_id)

        result = client.get(url, mimetype='application/json')

        assert result.status_code == 200
        assert "TickSubscriptionExpires" in result.json
        assert result.json['TickSubscriptionExpires'] == 0

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_subscribe(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)

        # Get token
        url = '/{}/{}/prime_subscription/check/{}'.format(version, market, colony_id)
        result = client.get(url, mimetype='application/json')
        assert result.status_code == 200
        assert 'Token' in result.json

        url = '/{}/{}/prime_subscription/subscribe/{}'.format(version, market, colony_id)

        post = {'Token': result.json['Token']}

        result = client.put(url, data=json.dumps(post), mimetype='application/json')

        assert result.status_code == 200

        url = '/{}/{}/prime_subscription/check/{}'.format(version, market, colony_id)

        result = client.get(url, mimetype='application/json')

        assert result.status_code == 200
        assert result.json
        assert "TickSubscriptionExpires" in result.json
        assert "SubscriptionCost" in result.json
        assert 'Token' in result.json

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_subscribe_no_token(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)

        url = '/{}/{}/prime_subscription/subscribe/{}'.format(version, market, colony_id)

        result = client.put(url, data='{}', mimetype='application/json')

        assert result.status_code == 400

        result = client.put(url, data=json.dumps({'Token': ''}), mimetype='application/json')

        assert result.status_code == 400

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_subscribe_wrong_token(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)

        # Get token
        url = '/{}/{}/prime_subscription/check/{}'.format(version, market, colony_id)
        result = client.get(url, mimetype='application/json')
        assert result.status_code == 200
        assert 'Token' in result.json

        url = '/{}/{}/prime_subscription/subscribe/{}'.format(version, market, colony_id)
        post = {'Token': '1234'}
        result = client.put(url, data=json.dumps(post), mimetype='application/json')

        assert result.status_code == 400
