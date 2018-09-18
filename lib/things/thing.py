from collections import OrderedDict

from lib import db, consts
from lib.things.base_thing import BaseThing


class Thing(BaseThing):

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)

        self._current_sell_price = float(kwargs.get('CurrentSellPrice', -1))
        self._use_server_price = kwargs.get('UseServerPrice', False)
        self._buy_price_override = float(kwargs.get('BuyPriceOverride', 0))
        self._sell_price_override = float(kwargs.get('SellPriceOverride', 0))
        self._from_database = False

    @property
    def CurrentSellPrice(self):
        return self._current_sell_price

    @CurrentSellPrice.setter
    def CurrentSellPrice(self, value):
        self._changes['CurrentSellPrice'] = True
        self._current_sell_price = value

    @property
    def BuyPriceOverride(self):
        return self._buy_price_override

    @BuyPriceOverride.setter
    def BuyPriceOverride(self, value):
        self._changes['BuyPriceOverride'] = True
        self._buy_price_override = value

    @property
    def SellPriceOverride(self):
        return self._sell_price_override

    @SellPriceOverride.setter
    def SellPriceOverride(self, value):
        self._changes['SellPriceOverride'] = True
        self._sell_price_override = value

    @property
    def UseServerPrice(self):
        return self._use_server_price

    @UseServerPrice.setter
    def UseServerPrice(self, value):
        self._changes['UseServerPrice'] = True
        self._use_server_price = value

    @property
    def FromDatabase(self):
        return self._from_database

    def to_dict(self, delta=False):
        to_save = {}

        if self.FromDatabase and delta:
            for key in self._changes.keys():
                to_save[key] = getattr(self, key)
        else:
            for prop in self._iter_properties():
                to_save[prop] = getattr(self, prop)
            del to_save['FromDatabase']

        # del to_save['Hash']  # Should it store the hash? I can think of a few reasons why it could be useful.
        return to_save

    def save_to_database(self, connection=None):
        """
        Save this Thing to the database using the provided connection.
        The connection can be direct or a pipeline object.
        If None is provided, a connection will be created.
        :param connection: Can be a None, a Redis connection or a pipeline.
        :return:
        """
        if connection is None:
            connection = db.get_redis_db_from_context()

        if not self.FromDatabase:
            # We need to add the hash to the Thing Index
            connection.sadd(consts.KEY_THING_INDEX, self.Hash)

        # Do a Delta update if we can (Only if FromDatabase is True)
        connection.hmset(consts.KEY_THING_META.format(self.Hash), self.to_dict(delta=True))

    @classmethod
    def get_many_from_database(cls, list_of_thing_dict):
        db_connection = db.get_redis_db_from_context()
        pipe = db_connection.pipeline()

        things_to_find = OrderedDict()

        # Iterate of the list of Thing data structures and build hash keys
        for thing_data in list_of_thing_dict:
            thing_obj = cls.from_dict(thing_data)
            things_to_find[thing_obj.Hash] = thing_obj
            pipe.hgetall(consts.KEY_THING_META.format(thing_obj.Hash))

        # Combine the list of hashes and list of results into a dictionary of Key(Hash), Value(Data)
        results = dict(zip(things_to_find.keys(), pipe.execute()))

        for hash_key, data in results.items():
            if len(data) > 0:
                new_thing = cls.from_dict(data)
                new_thing._from_database = True
                results[hash_key] = new_thing
            else:
                # Use the generated object, Caller should test FromDatabase
                results[hash_key] = things_to_find[hash_key]

        return results

    @classmethod
    def get_from_database(cls, thing_dict):
        db_connection = db.get_redis_db_from_context()

        thing_obj = cls.from_dict(thing_dict)

        data = db_connection.hgetall(consts.KEY_THING_META.format(thing_obj.Hash))

        if len(data) > 0:
            new_thing = cls.from_dict(data)
            new_thing._from_database = True
            return new_thing

        # Caller should test FromDatabase
        return thing_obj
