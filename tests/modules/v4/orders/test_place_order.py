import gzip
import io
import json

import pytest
from flask import Flask

from config import API_DB_CONFIG
from lib.gwpcc import consts
from tests.modules.v4.helpers import make_user, make_colony, make_prime

versions = ['v4']
markets = API_DB_CONFIG


class TestOrder:
    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_place_order_small_correctly(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)
        make_prime(client, version, market, colony_id)

        ####
        # Place the order
        ####
        url = '/{}/{}/orders/{}'.format(version, market, colony_id)

        tick = 1

        order = {"ThingsSoldToGwp": [
            {"BaseMarketValue": 1.2, "CurrentBuyPrice": 9.36, "HitPoints": 140, "MinifiedContainer": False,
             "Name": "WoodLog", "Quality": "", "Quantity": 1, "StuffType": ""},
            {"BaseMarketValue": 1, "CurrentBuyPrice": 1, "HitPoints": -1, "MinifiedContainer": False, "Name": "Silver",
             "Quality": "", "Quantity": 14, "StuffType": ""}], "ThingsBoughtFromGwp": [
            {"BaseMarketValue": 1.9, "CurrentBuyPrice": 14.82, "HitPoints": -1, "MinifiedContainer": False,
             "Name": "Steel", "Quality": "", "Quantity": 1, "StuffType": ""}], "CurrentGameTick": tick}

        payload = io.BytesIO(gzip.compress(json.dumps(order).encode('utf-8')))

        result = client.put(url, data={'order': (payload, 'order')})
        assert result.status_code == 200

        ####
        # Get a list of orders
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        assert result.status_code == 200
        assert result.json
        assert 'Orders' in result.json
        assert type(result.json['Orders']) == list and len(result.json) == 1

        ####
        # Get the order metadata
        ####
        hash_id = result.json['Orders'][0]['Hash']
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.get(url)

        assert result.status_code == 200
        assert result.json
        assert 'Hash' in result.json
        assert result.json['Hash'] == hash_id
        assert result.json['ThingsSoldToGwp']
        assert result.json['ThingsBoughtFromGwp']

        ####
        # Update the order status to Processed
        ####

        order_status = {'Status': 'processed'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

        ####
        # Update the order status to Done
        ####

        order_status = {'Status': 'done'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_place_order_small_cheat_reset_to_new(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)
        make_prime(client, version, market, colony_id)

        ####
        # Place the order
        ####
        url = '/{}/{}/orders/{}'.format(version, market, colony_id)

        tick = 1

        order = {"ThingsSoldToGwp": [
            {"BaseMarketValue": 1.2, "CurrentBuyPrice": 9.36, "HitPoints": 140, "MinifiedContainer": False,
             "Name": "WoodLog", "Quality": "", "Quantity": 1, "StuffType": ""},
            {"BaseMarketValue": 1, "CurrentBuyPrice": 1, "HitPoints": -1, "MinifiedContainer": False, "Name": "Silver",
             "Quality": "", "Quantity": 14, "StuffType": ""}], "ThingsBoughtFromGwp": [
            {"BaseMarketValue": 1.9, "CurrentBuyPrice": 14.82, "HitPoints": -1, "MinifiedContainer": False,
             "Name": "Steel", "Quality": "", "Quantity": 1, "StuffType": ""}], "CurrentGameTick": tick}

        payload = io.BytesIO(gzip.compress(json.dumps(order).encode('utf-8')))

        result = client.put(url, data={'order': (payload, 'order')})
        assert result.status_code == 200

        ####
        # Get a list of orders
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        ####
        # Get the order metadata
        ####
        hash_id = result.json['Orders'][0]['Hash']
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.get(url)

        ####
        # Update the order status to Processed
        ####

        order_status = {'Status': 'processed'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

        ####
        # Try cheating to new
        ####

        order_status = {'Status': 'new'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Update the order status to Done
        ####

        order_status = {'Status': 'done'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

        ####
        # Try cheating to new
        ####

        order_status = {'Status': 'new'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_place_order_small_cheat_reset_failed(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)
        make_prime(client, version, market, colony_id)

        ####
        # Place the order
        ####
        url = '/{}/{}/orders/{}'.format(version, market, colony_id)

        tick = 1

        order = {"ThingsSoldToGwp": [
            {"BaseMarketValue": 1.2, "CurrentBuyPrice": 9.36, "HitPoints": 140, "MinifiedContainer": False,
             "Name": "WoodLog", "Quality": "", "Quantity": 1, "StuffType": ""},
            {"BaseMarketValue": 1, "CurrentBuyPrice": 1, "HitPoints": -1, "MinifiedContainer": False, "Name": "Silver",
             "Quality": "", "Quantity": 14, "StuffType": ""}], "ThingsBoughtFromGwp": [
            {"BaseMarketValue": 1.9, "CurrentBuyPrice": 14.82, "HitPoints": -1, "MinifiedContainer": False,
             "Name": "Steel", "Quality": "", "Quantity": 1, "StuffType": ""}], "CurrentGameTick": tick}

        payload = io.BytesIO(gzip.compress(json.dumps(order).encode('utf-8')))

        result = client.put(url, data={'order': (payload, 'order')})
        assert result.status_code == 200

        ####
        # Get a list of orders
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        ####
        # Get the order metadata
        ####
        hash_id = result.json['Orders'][0]['Hash']
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.get(url)

        assert result.status_code == 200

        ####
        # Update the order status to Processed
        ####

        order_status = {'Status': 'failed'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

        ####
        # Try cheating to new
        ####

        order_status = {'Status': 'new'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Update the order status to Done
        ####

        order_status = {'Status': 'done'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Try cheating to new
        ####

        order_status = {'Status': 'new'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_place_order_small_timewarp_cheat(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)
        make_prime(client, version, market, colony_id)

        ####
        # Place the order
        ####
        url = '/{}/{}/orders/{}'.format(version, market, colony_id)

        tick = 1000

        order = {"ThingsSoldToGwp": [
            {"BaseMarketValue": 1.2, "CurrentBuyPrice": 9.36, "HitPoints": 140, "MinifiedContainer": False,
             "Name": "WoodLog", "Quality": "", "Quantity": 1, "StuffType": ""},
            {"BaseMarketValue": 1, "CurrentBuyPrice": 1, "HitPoints": -1, "MinifiedContainer": False, "Name": "Silver",
             "Quality": "", "Quantity": 14, "StuffType": ""}], "ThingsBoughtFromGwp": [
            {"BaseMarketValue": 1.9, "CurrentBuyPrice": 14.82, "HitPoints": -1, "MinifiedContainer": False,
             "Name": "Steel", "Quality": "", "Quantity": 1, "StuffType": ""}], "CurrentGameTick": tick}

        payload = io.BytesIO(gzip.compress(json.dumps(order).encode('utf-8')))

        result = client.put(url, data={'order': (payload, 'order')})
        assert result.status_code == 200

        ####
        # Get a list of orders
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        ####
        # Get the order metadata
        ####
        hash_id = result.json['Orders'][0]['Hash']
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.get(url)

        assert result.status_code == 200

        tick = 100

        ####
        # Get a list of orders again with a lower tick number, this triggers the time warp detection
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        ####
        # Try cheating to Processed
        ####

        order_status = {'Status': 'failed'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Try cheating to new
        ####

        order_status = {'Status': 'new'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Try cheating to Done
        ####

        order_status = {'Status': 'done'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

    @pytest.mark.parametrize("version", versions)
    @pytest.mark.parametrize("market", markets)
    def test_place_order_small_timewarp_cheat_after_done(self, version, market, test_app_context: Flask):
        client = test_app_context.test_client()

        user_id = make_user(client, version, market)
        colony_id = make_colony(client, version, market, user_id)
        make_prime(client, version, market, colony_id)

        ####
        # Place the order
        ####
        url = '/{}/{}/orders/{}'.format(version, market, colony_id)

        tick = 1000

        order = {"ThingsSoldToGwp": [
            {"BaseMarketValue": 1.2, "CurrentBuyPrice": 9.36, "HitPoints": 140, "MinifiedContainer": False,
             "Name": "WoodLog", "Quality": "", "Quantity": 1, "StuffType": ""},
            {"BaseMarketValue": 1, "CurrentBuyPrice": 1, "HitPoints": -1, "MinifiedContainer": False, "Name": "Silver",
             "Quality": "", "Quantity": 14, "StuffType": ""}], "ThingsBoughtFromGwp": [
            {"BaseMarketValue": 1.9, "CurrentBuyPrice": 14.82, "HitPoints": -1, "MinifiedContainer": False,
             "Name": "Steel", "Quality": "", "Quantity": 1, "StuffType": ""}], "CurrentGameTick": tick}

        payload = io.BytesIO(gzip.compress(json.dumps(order).encode('utf-8')))

        result = client.put(url, data={'order': (payload, 'order')})
        assert result.status_code == 200

        ####
        # Get a list of orders
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        ####
        # Get the order metadata
        ####
        hash_id = result.json['Orders'][0]['Hash']
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.get(url)

        assert result.status_code == 200

        ####
        # Update to processed
        ####

        order_status = {'Status': 'processed'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

        ####
        # Update to done
        ####

        order_status = {'Status': 'done'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 200

        tick = 100

        ####
        # Get a list of orders again with a lower tick number, this triggers the time warp detection
        ####

        url = '/{}/{}/orders/{}?tick={}'.format(version, market, colony_id, tick)
        result = client.get(url)

        ####
        # Try cheating to Processed
        ####

        order_status = {'Status': 'failed'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Try cheating to new
        ####

        order_status = {'Status': 'new'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400

        ####
        # Try cheating to Done
        ####

        order_status = {'Status': 'done'}
        url = '/{}/{}/orders/{}/{}'.format(version, market, colony_id, hash_id)
        result = client.post(url, data=json.dumps(order_status), content_type=consts.MIME_JSON)

        assert result.status_code == 400
