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

        for prop in self._iter_properties():
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

        things_to_find = {}

        # Iterate of the list of Thing data structures and build hash keys
        for thing_data in list_of_order_thing_dict:
            thing_obj = cls.from_dict(thing_data)
            if thing_obj.Hash in things_to_find:
                continue
            things_to_find[thing_obj.Hash] = thing_obj
            pipe.exists(consts.KEY_THING_META.format(thing_obj.Hash))

        # Combine the list of hashes and list of results into a dictionary of Key(Hash), Value(Data)
        results = dict(zip(things_to_find.keys(), pipe.execute()))

        for hash_key, exists in results.items():
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
