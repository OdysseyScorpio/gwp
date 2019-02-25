import redis
from pytest import fixture

import lib.consts as consts
from lib.db import get_redis_db_from_context
from lib.things.order_thing import OrderThing
from lib.things.thing import Thing


class TestOrderThingClass:

    @fixture
    def a(self):
        return {'Name': 'TestQS', 'Quality': 'Good', 'StuffType': 'WoodenLog'}

    @fixture
    def b(self):
        return {'Name': 'TestQ', 'Quality': 'Good'}

    @fixture
    def c(self):
        return {'Name': 'TestS', 'StuffType': 'WoodenLog'}

    @staticmethod
    def setup_data_in_db(thing: Thing, connection):

        do_exec = False

        if not isinstance(connection, redis.client.Pipeline):
            connection = connection.pipeline()
            do_exec = True

        connection.delete(consts.KEY_THING_META.format(thing.Hash))

        # Remove the key from the index if it already exists
        connection.srem(consts.KEY_THING_INDEX, thing.Hash)

        # Write the Thing to the database.
        thing.save_to_database(connection)

        if do_exec:
            connection.execute()

    def test_all_exist(self, test_app_context, a, b, c):

        thing_data = [a, b, c]

        self.setup_data_in_db(Thing.from_dict(a), get_redis_db_from_context())
        self.setup_data_in_db(Thing.from_dict(b), get_redis_db_from_context())
        self.setup_data_in_db(Thing.from_dict(c), get_redis_db_from_context())

        result = OrderThing.many_from_dict_and_check_exists(thing_data).values()

        s = zip(thing_data, result)

        for a, b in s:
            assert a['Name'] == b.Name and b.ThingExists

    def test_one_exists(self, test_app_context, a):

        self.setup_data_in_db(Thing.from_dict(a), get_redis_db_from_context())

        result = OrderThing.from_dict_and_check_exists(a)

        assert a['Name'] == result.Name
        assert result.ThingExists

    def test_one_not_exists(self, test_app_context):

        thing_data = {'Name': 'Non-existent thing'}

        result = OrderThing.from_dict_and_check_exists(thing_data)

        assert thing_data['Name'] == result.Name
        assert not result.ThingExists

    def test_one_in_many_not_exist(self, test_app_context, a, c):
        b = {'Name': 'Nonexistent', 'StuffType': 'WoodenLog'}
        thing_data = [a, b, c]

        self.setup_data_in_db(Thing.from_dict(a), get_redis_db_from_context())
        self.setup_data_in_db(Thing.from_dict(c), get_redis_db_from_context())

        result = list(OrderThing.many_from_dict_and_check_exists(thing_data).values())

        assert len(result) == 3
        assert result[0].Name == a['Name'] and result[0].ThingExists
        assert result[1].Name == b['Name'] and not result[1].ThingExists
        assert result[2].Name == c['Name'] and result[2].ThingExists
