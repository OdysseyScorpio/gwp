import redis
from pytest import fixture

import lib.gwpcc.consts as consts
from lib.db import get_redis_database_connection, get_redis_db_from_context
from lib.gwpcc.things.thing import Thing


class TestThingClass:

    @fixture
    def a(self):
        return {'Name': 'TestQS', 'Quality': 'Good', 'StuffType': 'WoodenLog'}

    @fixture
    def b(self):
        return {'Name': 'TestQ', 'Quality': 'Good'}

    @fixture
    def c(self):
        return {'Name': 'TestS', 'StuffType': 'WoodenLog'}

    def test_all_exist(self, test_app_context, a, b, c):

        thing_data = [a, b, c]

        self.setup_data_in_db(Thing.from_dict(a), get_redis_db_from_context())
        self.setup_data_in_db(Thing.from_dict(b), get_redis_db_from_context())
        self.setup_data_in_db(Thing.from_dict(c), get_redis_db_from_context())

        result = Thing.get_many_from_database(thing_data).values()

        s = zip(thing_data, result)

        for a, b in s:
            assert a['Name'] == b.Name and b.FromDatabase

    def test_one_doesnt_exist(self, test_app_context, a, c):
        b = {'Name': 'Nonexistent', 'StuffType': 'WoodenLog'}
        thing_data = [a, b, c]

        self.setup_data_in_db(Thing.from_dict(a), get_redis_db_from_context())
        self.setup_data_in_db(Thing.from_dict(c), get_redis_db_from_context())

        result = list(Thing.get_many_from_database(thing_data).values())

        assert len(result) == 3
        assert result[0].Name == a['Name'] and result[0].FromDatabase
        assert result[1].Name == b['Name'] and not result[1].FromDatabase
        assert result[2].Name == c['Name'] and result[2].FromDatabase

    def test_all_none(self, test_app_context):
        a = {'Name': 'Nonexistent1', 'Quality': 'Good'}
        b = {'Name': 'Nonexistent2', 'StuffType': 'WoodenLog'}
        c = {'Name': 'Nonexistent3', 'Quality': 'Good', 'StuffType': 'WoodenLog'}
        thing_data = [a, b, c]
        result = Thing.get_many_from_database(thing_data).values()
        s = list(zip(thing_data, result))

        assert len(s) == 3
        for a, b in s:
            assert not b.FromDatabase

    def test_nonexistent(self, test_app_context):
        thing_data = {'Name': 'Doesn\'t_exist'}
        assert not Thing.get_from_database(thing_data).FromDatabase

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

    def test_name_with_quality_and_stuff(self, test_app_context, a):
        thing_data = a
        a = Thing.from_dict(thing_data)
        self.setup_data_in_db(a, get_redis_db_from_context())
        b = Thing.get_from_database(thing_data)
        assert b.Hash == '4f57967468deccdb718432a13fdd55eef9f8bd4f'

    def test_name_with_quality(self, test_app_context, b):
        a = Thing.from_dict(b)
        self.setup_data_in_db(a, get_redis_db_from_context())
        b = Thing.get_from_database(b)
        assert b.Hash == 'aafd448dfc6644cd92bdab58470a5f52d56677ec'

    def test_name_with_stuff(self, test_app_context, c):
        a = Thing.from_dict(c)
        self.setup_data_in_db(a, get_redis_db_from_context())
        b = Thing.get_from_database(c)
        assert b.Hash == 'f1987009817fdc766c908591571982ace2f211d0'

    def test_class_init(self):
        o = Thing('Test')
        assert o.Name == 'Test'

    def test_class_init_from_dict(self, a):

        o = Thing.from_dict(a)

        assert o.Name == a['Name']
        assert o.Quality == a['Quality']
        assert o.StuffType == a['StuffType']

    def test_class_init_from_dict_to_dict(self, a):

        o = Thing.from_dict(a)
        r = o.to_dict()

        for k, v in a.items():
            assert r[k] == v

    def test_class_init_from_dict_hash(self, a):

        o = Thing.from_dict(a)

        assert '4f57967468deccdb718432a13fdd55eef9f8bd4f' == o.Hash

    def test_save_and_load(self, test_app_context):

        d = {'Name': 'TestSaveAndLoad',
             'Quality': 'Good',
             'StuffType': 'Silver',
             'UseServerPrice': True,
             'CurrentBuyPrice': 19.99,
             'CurrentSellPrice': 13.99,
             'BaseMarketValue': 15.99,
             'Quantity': 100
             }

        o_save = Thing.from_dict(d)
        od = o_save.to_dict()

        db = get_redis_database_connection(db_number=15)

        # Remove the key from the index if it already exists
        db.srem(consts.KEY_THING_INDEX, o_save.Hash)

        # Write the Thing to the database.
        o_save.save_to_database(db)

        # It should be near the end of the list.
        is_member = db.sismember(consts.KEY_THING_INDEX, o_save.Hash)

        assert is_member

        # Reload it as a new object
        o_loaded = Thing.get_from_database(o_save.to_dict())

        assert o_loaded.FromDatabase
        assert o_loaded.Hash == o_save.Hash

        for k, v in o_loaded.to_dict().items():
            assert od[k] == v

    def test_load_modify_save(self, test_app_context):
        d = {'Name': 'TestSaveAndLoadDifference',
             'Quality': 'Good',
             'StuffType': 'Silver',
             'UseServerPrice': True,
             'CurrentBuyPrice': 19.99,
             'CurrentSellPrice': 13.99,
             'BaseMarketValue': 15.99,
             'Quantity': 100
             }

        a = Thing.from_dict(d)
        ad = a.to_dict()

        db = get_redis_database_connection(db_number=15)

        # Remove the key from the index if it already exists
        db.srem(consts.KEY_THING_INDEX, a.Hash)

        # Write the Thing to the database.
        a.save_to_database(db)

        # It should be near the end of the list.
        is_member = db.sismember(consts.KEY_THING_INDEX, a.Hash)

        assert is_member

        # Reload it as a new object
        b = Thing.get_from_database(a.to_dict())

        assert b.Hash == a.Hash

        for k, v in b.to_dict().items():
            assert ad[k] == v

        b.Quantity = 50

        b.save_to_database(db)

        c = Thing.from_dict(db.hgetall(consts.KEY_THING_META.format(a.Hash)))

        assert c.Quantity == 50
