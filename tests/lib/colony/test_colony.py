import redis
from pytest import fixture

from lib import date_utils, consts
from lib.colonies.colony import Colony
from lib.db import get_redis_db_from_context


class TestColonyClass:

    @staticmethod
    @fixture()
    def fixture_colony_a() -> Colony:
        a: Colony = Colony.from_dict(
            {
                'BaseName': 'TestColonyA',
                'FactionName': 'TestFactionA',
                'Planet': 'TestPlanetA',
                'DateCreated': 1,
                'OwnerType': 'Normal',
                'OwnerID': 1
            }
        )
        return a

    @staticmethod
    @fixture()
    def fixture_colony_b() -> Colony:
        b: Colony = Colony.from_dict(
            {
                'BaseName': 'TestColonyB',
                'FactionName': 'TestFactionB',
                'Planet': 'TestPlanetB',
                'Hash': 'ABCD',
                'OwnerType': 'Normal',
                'OwnerID': 1
            }
        )
        return b

    @staticmethod
    @fixture()
    def fixture_colony_steam() -> Colony:
        s: Colony = Colony.from_dict(
            {
                'BaseName': 'TestColonyS',
                'FactionName': 'TestFactionS',
                'Planet': 'TestPlanetS',
                'DateCreated': 100,
                'OwnerType': 'Steam',
                'OwnerID': '76561198275909496'
            }
        )
        return s

    @staticmethod
    def setup_data_in_db(colony: Colony, connection):

        do_exec = False

        if not isinstance(connection, redis.client.Pipeline):
            connection = connection.pipeline()
            do_exec = True

        connection.delete(consts.KEY_COLONY_METADATA.format(colony.Hash))

        # Remove the key from the index if it already exists
        connection.lrem(consts.KEY_COLONY_INDEX_BY_ID, 0, colony.Hash)

        # Remove key from Steam User keys
        if colony.OwnerType == 'Steam':
            connection.lrem(
                consts.KEY_COLONY_INDEX_BY_STEAM_ID.format(colony.OwnerID),
                0,
                colony.Hash
            )

        # Write the Colony to the database.
        colony.save_to_database(connection)

        if do_exec:
            connection.execute()

    def test_get_colony_by_hash(self, test_app_context, fixture_colony_steam):
        connection = get_redis_db_from_context()
        self.setup_data_in_db(fixture_colony_steam, connection)

        result = Colony.get_from_database_by_hash(fixture_colony_steam.Hash)

        assert result.FromDatabase

    def test_update_stats_for_colony_action(self, test_app_context, fixture_colony_a, fixture_colony_b):

        connection = get_redis_db_from_context()

        self.setup_data_in_db(fixture_colony_a, connection)
        self.setup_data_in_db(fixture_colony_b, connection)

        date = date_utils.get_today_date_string()
        hour = date_utils.get_current_hour()

        with connection.pipeline() as pipe:
            pipe.delete(consts.KEY_BUCKET_COLONIES_ACTIVE)
            pipe.delete(consts.KEY_COUNTERS_HOURLY_COLONIES_ACTIVE.format(hour))
            pipe.execute()

        fixture_colony_a.ping()
        fixture_colony_b.ping()

        colony_set = connection.smembers(consts.KEY_TRENDS_HISTORICAL_COLONIES_ACTIVE_BY_DATE.format(date))
        assert fixture_colony_a.Hash in colony_set
        assert fixture_colony_b.Hash in colony_set

        colony_set = connection.zrange(consts.KEY_BUCKET_COLONIES_ACTIVE, 0, -1)
        assert fixture_colony_a.Hash in colony_set
        assert fixture_colony_b.Hash in colony_set

        colony_count = connection.get(consts.KEY_COUNTERS_HOURLY_COLONIES_ACTIVE.format(hour))
        assert colony_count >= 2

    def test_all_exist(self, test_app_context, fixture_colony_a, fixture_colony_b, fixture_colony_steam):

        connection = get_redis_db_from_context()

        a = fixture_colony_a
        b = fixture_colony_b
        c = fixture_colony_steam

        self.setup_data_in_db(a, connection)
        self.setup_data_in_db(b, connection)
        self.setup_data_in_db(c, connection)

        colony_data = [a.to_dict(), b.to_dict(), c.to_dict()]

        result = Colony.get_many_from_database(colony_data)

        s = zip(colony_data, result.values())

        for a, b in s:
            assert a['BaseName'] == b.BaseName and b.FromDatabase

    def test_one_doesnt_exist(self, test_app_context, fixture_colony_a, fixture_colony_b):
        connection = get_redis_db_from_context()

        a = fixture_colony_a
        b = fixture_colony_b

        self.setup_data_in_db(a, connection)
        self.setup_data_in_db(b, connection)

        c = Colony.from_dict(
            {
                'BaseName': 'TestColonyC',
                'FactionName': 'TestFactionC',
                'Planet': 'TestPlanetC',
                'Hash': 'EFGH',
                'OwnerType': 'Normal',
                'OwnerID': 1
            }
        )
        colony_data = [a.to_dict(), b.to_dict(), c.to_dict()]

        result = list(Colony.get_many_from_database(colony_data).values())

        assert len(result) == 3
        assert result[0].BaseName == a.BaseName and result[0].FromDatabase
        assert result[1].BaseName == b.BaseName and result[1].FromDatabase
        assert result[2].BaseName == c.BaseName and not result[2].FromDatabase

    def test_all_none(self, test_app_context):
        """
        Test that none of these entries exist in the DB,
        Assert that all results have FromDatabase == False
        :param test_app_context:
        :return:
        """
        a = Colony.from_dict(
            {
                'BaseName': 'TestColonyA',
                'FactionName': 'TestFactionA',
                'Planet': 'TestPlanetA',
                'Hash': '1234',
                'OwnerType': 'Normal',
                'OwnerID': 1
            }
        )
        b = Colony.from_dict(
            {
                'BaseName': 'TestColonyB',
                'FactionName': 'TestFactionB',
                'Planet': 'TestPlanetB',
                'Hash': '5678',
                'OwnerType': 'Normal',
                'OwnerID': 1
            }
        )
        c = Colony.from_dict(
            {
                'BaseName': 'TestColonyC',
                'FactionName': 'TestFactionC',
                'Planet': 'TestPlanetC',
                'Hash': 'EFGH',
                'OwnerType': 'Normal',
                'OwnerID': 1
            }
        )
        colony_data = [a.to_dict(), b.to_dict(), c.to_dict()]
        result = Colony.get_many_from_database(colony_data)
        s = list(zip(colony_data, result.values()))

        assert len(s) == 3
        for a, b in s:
            assert not b.FromDatabase

    def test_class_init_from_dict_to_dict(self, test_app_context, fixture_colony_a):

        a_dict = fixture_colony_a.to_dict()
        b = Colony.from_dict(a_dict).to_dict()

        for k, v in b.items():
            assert a_dict[k] == v

    def test_class_init_from_dict_hash(self, test_app_context, fixture_colony_a):

        o = Colony.from_dict(fixture_colony_a.to_dict())

        assert "87a41f64617b379cb80c7123351b35db356c97c8" == o.Hash

    def test_save_and_load(self, test_app_context, fixture_colony_a):

        connection = get_redis_db_from_context()

        self.setup_data_in_db(fixture_colony_a, connection)

        # It should be near the end of the list.
        index = connection.lrange(consts.KEY_COLONY_INDEX_BY_ID, -5, -1)

        assert fixture_colony_a.Hash in index

        # Reload it as a new object
        o_loaded = Colony.get_from_database(fixture_colony_a.to_dict())

        assert o_loaded.FromDatabase
        assert o_loaded.Hash == fixture_colony_a.Hash

        od = fixture_colony_a.to_dict()

        for k, v in o_loaded.to_dict().items():
            assert od[k] == v

    def test_save_and_load_steam(self, test_app_context, fixture_colony_steam):

        connection = get_redis_db_from_context()

        self.setup_data_in_db(fixture_colony_steam, connection)

        # It should be near the end of the list.
        index = connection.lrange(consts.KEY_COLONY_INDEX_BY_ID, -5, -1)

        steam_index = connection.lrange(
            consts.KEY_COLONY_INDEX_BY_STEAM_ID.format(fixture_colony_steam.OwnerID),
            -5,
            -1
        )

        assert fixture_colony_steam.Hash in index
        assert fixture_colony_steam.Hash in steam_index

        # Reload it as a new object
        o_loaded = Colony.get_from_database(fixture_colony_steam.to_dict())

        assert o_loaded.FromDatabase
        assert o_loaded.Hash == fixture_colony_steam.Hash

        od = fixture_colony_steam.to_dict()

        for k, v in o_loaded.to_dict().items():
            assert od[k] == v

    def test_load_modify_save(self, test_app_context, fixture_colony_a):

        ad = fixture_colony_a.to_dict()

        connection = get_redis_db_from_context()

        # It should be near the end of the list.
        index = connection.lrange(consts.KEY_COLONY_INDEX_BY_ID, -5, -1)

        assert fixture_colony_a.Hash in index

        # Reload it as a new object
        b = Colony.get_from_database(ad)

        assert b.Hash == fixture_colony_a.Hash

        for k, v in b.to_dict().items():
            assert ad[k] == v

        b.LastAction = 2

        b.save_to_database(connection)

        c = Colony.get_from_database(ad)

        assert c.LastAction == b.LastAction
