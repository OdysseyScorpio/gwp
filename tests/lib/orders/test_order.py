import json

import redis
from pytest import fixture

from lib import consts
from lib.colonies.colony import Colony
from lib.db import get_redis_db_from_context
from lib.orders.order import Order
from lib.things.order_thing import OrderThing
from lib.things.thing import Thing


class TestOrderClass:
    @staticmethod
    @fixture
    def thing_a_bought():
        return {'Name': 'OrderedThing1',
                'Quality': 'Good',
                'StuffType': 'Silver',
                'CurrentBuyPrice': 19.99,
                'BaseMarketValue': 15.99,
                'MinifiedContainer': True,
                'Quantity': 100
                }

    @staticmethod
    @fixture
    def thing_a_sold():
        return {'Name': 'OrderedThing1',
                'Quality': 'Good',
                'StuffType': 'Silver',
                'CurrentBuyPrice': 19.99,
                'BaseMarketValue': 15.99,
                'MinifiedContainer': True,
                'Quantity': 23
                }

    @staticmethod
    @fixture
    def thing_c_not_exist_sold():
        return {'Name': 'OrderedThing2',
                'Quality': 'Good',
                'StuffType': 'Silver',
                'CurrentBuyPrice': 19.99,
                'BaseMarketValue': 15.99,
                'MinifiedContainer': True,
                'Quantity': 100
                }

    @staticmethod
    @fixture()
    def fixture_colony_a() -> Colony:
        a: Colony = Colony.from_dict(
            {
                'BaseName': 'TestColonyA',
                'FactionName': 'TestFactionA',
                'Planet': 'TestPlanetA',
                'DateCreated': 1
            }
        )
        return a

    @classmethod
    @fixture
    def order_a(cls) -> Order:
        colony = cls.fixture_colony_a()

        order: Order = Order.from_order_data_dict(
            {
                'OwnerID': colony.Hash,
                'OrderedTick': 1000,
                'ThingsBoughtFromGwp': json.dumps(
                    [OrderThing.from_dict(cls.thing_a_bought()).to_dict(keep_quantity=True)]),
                'ThingsSoldToGwp': json.dumps([OrderThing.from_dict(cls.thing_a_sold()).to_dict(keep_quantity=True)]),
                'DeliveryTick': 10000
            }
        )
        return order

    @staticmethod
    def setup_order_data_in_db(order: Order, connection):

        do_exec = False

        if not isinstance(connection, redis.client.BasePipeline):
            connection = connection.pipeline()
            do_exec = True

        connection.delete(consts.KEY_ORDER_MANIFEST.format(order.Hash))

        # Remove the key from the index if it already exists
        connection.lrem(consts.KEY_COLONY_NEW_ORDERS.format(order.OwnerID), order.Hash, 0)
        connection.lrem(consts.KEY_COLONY_ALL_ORDERS.format(order.OwnerID), order.Hash, 0)

        # Write the Colony to the database.
        order.save_to_database(connection)

        if do_exec:
            connection.execute()

    @staticmethod
    def setup_data_in_db(thing: Thing, connection):

        do_exec = False

        if not isinstance(connection, redis.client.BasePipeline):
            connection = connection.pipeline()
            do_exec = True

        connection.delete(consts.KEY_THING_META.format(thing.Hash))

        # Remove the key from the index if it already exists
        connection.srem(consts.KEY_THING_INDEX, thing.Hash)

        # Write the Thing to the database.
        thing.save_to_database(connection)

        if do_exec:
            connection.execute()

    def test_init(self, test_app_context, order_a):
        assert True

    def test_to_dict(self, test_app_context, order_a):

        output = order_a.to_dict(delta=False)

        for k, v in order_a.to_dict().items():
            assert output[k] == v

    def test_not_from_database(self, test_app_context, order_a):
        assert order_a.FromDatabase is False

    def test_is_from_database(self, test_app_context, order_a):
        db = get_redis_db_from_context()

        self.setup_order_data_in_db(order_a, db)

        order_hash = order_a.Hash

        order_a = Order.get_from_database_by_hash(order_hash)

        assert order_a.FromDatabase

    def test_is_from_database_many(self, test_app_context, order_a):
        db = get_redis_db_from_context()

        self.setup_order_data_in_db(order_a, db)

        order_hash = [order_a.Hash]

        orders = Order.get_many_from_database(order_hash)

        result = list(orders.values())[0]

        assert result.Hash == order_a.Hash

    def test_can_deserialize_into_order_thing(self, test_app_context, order_a, thing_a_bought):
        db = get_redis_db_from_context()

        self.setup_order_data_in_db(order_a, db)
        self.setup_data_in_db(Thing.from_dict(self.thing_a_bought()), db)

        order_a = Order.get_from_database_by_hash(order_a.Hash)

        things_bought_from_gwp = OrderThing.many_from_dict_and_check_exists(order_a.ThingsBoughtFromGwp)

        first_item = list(things_bought_from_gwp.values())[0].to_dict(keep_quantity=True)

        for k, v in thing_a_bought.items():
            assert first_item[k] == v

    def test_can_deserialize_into_thing(self, test_app_context, order_a, thing_a_bought):
        db = get_redis_db_from_context()

        self.setup_order_data_in_db(order_a, db)
        self.setup_data_in_db(Thing.from_dict(self.thing_a_bought()), db)

        order_a = Order.get_from_database_by_hash(order_a.Hash)

        things_bought_from_gwp = Thing.get_many_from_database(order_a.ThingsBoughtFromGwp)

        first_item = list(things_bought_from_gwp.values())[0].to_dict()

        for k, v in thing_a_bought.items():
            assert first_item[k] == v

        thing = Thing.get_from_database(thing_a_bought)

        assert thing.FromDatabase
        assert thing.Quantity == thing_a_bought['Quantity']
