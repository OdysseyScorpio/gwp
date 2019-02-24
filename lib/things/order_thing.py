from collections import OrderedDict

from flask import current_app

from lib import db, consts
from lib.things.base_thing import BaseThing


class OrderThing(BaseThing):

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._thing_exists = False

    @property
    def ThingExists(self):
        return self._thing_exists

    @ThingExists.setter
    def ThingExists(self, value):
        self._thing_exists = value

    def to_dict(self, keep_quantity: bool = False) -> dict:
        to_save = {}

        for prop in self.get_props():
            to_save[prop] = getattr(self, prop)

        # Remove the flag.
        del to_save['ThingExists']

        if not keep_quantity:
            # Make sure we don't export the quantity.
            del to_save['Quantity']

        return to_save

    @classmethod
    def many_from_dict_and_check_exists(cls, list_of_order_thing_dict):
        db_connection = db.get_redis_db_from_context()
        pipe = db_connection.pipeline()

        things_to_find = OrderedDict()

        # Iterate of the list of Thing data structures and build hash keys
        for thing_data in list_of_order_thing_dict:
            thing_obj = cls.from_dict(thing_data)

            # Do we already have this item? If so compress the stacks into a single line.
            if thing_obj.Hash in things_to_find:
                things_to_find[thing_obj.Hash].Quantity += thing_obj.Quantity
            else:
                things_to_find[thing_obj.Hash] = thing_obj
                pipe.exists(consts.KEY_THING_META.format(thing_obj.Hash))

        # Combine the list of hashes and list of results into a dictionary of Key(Hash), Value(Data)
        results = dict(zip(things_to_find.keys(), pipe.execute()))

        # # DEBUG ONLY!
        # pipe = db_connection.pipeline()
        # hashes = []
        # for thing_data in list_of_order_thing_dict:
        #     thing_obj = cls.from_dict(thing_data)
        #     hashes.append(thing_obj.Hash)
        #     pipe.hgetall(consts.KEY_THING_META.format(thing_obj.Hash))
        #
        # pipe.execute()
        #
        # debug = dict(zip(hashes, pipe.execute()))
        #
        # for hash_key, entry in debug.values():
        #     current_app.logger.debug('Found {}, {}'.format(hash_key, entry))
        # # END DEBUG

        for hash_key, exists in results.items():
            current_app.logger.debug('{} exists: {}'.format(hash_key, exists))
            things_to_find[hash_key].ThingExists = exists
            results[hash_key] = things_to_find[hash_key]

        return results

    @classmethod
    def from_dict_and_check_exists(cls, order_thing_dict):
        db_connection = db.get_redis_db_from_context()

        # Iterate of the list of Thing data structures and build hash keys
        thing_obj = cls.from_dict(order_thing_dict)
        result = db_connection.exists(consts.KEY_THING_META.format(thing_obj.Hash))

        if result is True:
            thing_obj.ThingExists = True

        return thing_obj
