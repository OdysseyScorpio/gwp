import hashlib

from lib import db, consts, date_utils


class Order(object):

    def __init__(self, owner_hash: str, **kwargs):

        required = [
            'OrderedTick',
            'ThingsBoughtFromGwp',
            'ThingsSoldToGwp',
            'DeliveryTick'
        ]

        if not owner_hash:
            raise ValueError('Must specify the colony to deliver to!')

        for key in required:
            if key not in kwargs:
                raise ValueError('Missing required kwarg {}'.format(key))

        self._owner_id = owner_hash
        self._ordered_tick = int(kwargs['OrderedTick'])
        self._delivery_tick = int(kwargs['DeliveryTick'])
        self._things_bought = kwargs.get('ThingsBoughtFromGwp')
        self._things_sold = kwargs.get('ThingsSoldToGwp')
        self._date_created = int(kwargs.get('DateCreated', date_utils.get_current_unix_time()))
        self._status = kwargs.get('Status', consts.ORDER_STATUS_NEW)

        self._hash = kwargs.get('Hash', self.generate_hash(owner_hash, self.OrderedTick))
        self._from_database = bool(kwargs.get('FromDatabase', False))
        self.__changes = {}

    @property
    def DateCreated(self):
        return self._date_created

    @DateCreated.setter
    def DateCreated(self, value):
        self.__changes['DateCreated'] = True
        self._date_created = value

    @property
    def DeliveryTick(self):
        return self._delivery_tick

    @DeliveryTick.setter
    def DeliveryTick(self, value):
        self.__changes['DeliveryTick'] = True
        self._delivery_tick = value

    @property
    def OrderedTick(self):
        return self._ordered_tick

    @OrderedTick.setter
    def OrderedTick(self, value):
        self.__changes['OrderedTick'] = True
        self._ordered_tick = value

    # def ping(self):
    #     self.LastAction = utils.get_current_unix_time()

    @property
    def ThingsBoughtFromGwp(self):
        return self._things_bought

    @ThingsBoughtFromGwp.setter
    def ThingsBoughtFromGwp(self, value):
        self.__changes['ThingsBoughtFromGwp'] = True
        self._things_bought = value

    @property
    def ThingsSoldToGwp(self):
        return self._things_sold

    @ThingsSoldToGwp.setter
    def ThingsSoldToGwp(self, value):
        self.__changes['ThingsSoldToGwp'] = True
        self._things_sold = value

    @property
    def Status(self):
        return self._status

    @Status.setter
    def Status(self, value):
        self.__changes['Status'] = True
        self._status = value

    @property
    def OwnerID(self):
        return self._owner_id

    @OwnerID.setter
    def OwnerID(self, value):
        self.__changes['OwnerID'] = True
        self._owner_id = value

    @property
    def Hash(self):
        return self._hash

    @Hash.setter
    def Hash(self, value):
        self.__changes['Hash'] = True
        self._hash = value

    @property
    def FromDatabase(self):
        return self._from_database

    @classmethod
    def iter_properties(cls):
        for var_name in dir(cls):
            value = getattr(cls, var_name)
            if isinstance(value, property):
                yield var_name

    def to_dict(self, delta=False, just_headers=False):
        to_save = {}

        if self.FromDatabase and delta:
            for key in self.__changes.keys():
                to_save[key] = getattr(self, key)
        else:
            for prop in self.iter_properties():
                to_save[prop] = getattr(self, prop)
            del to_save['FromDatabase']

        if just_headers:
            if 'ThingsBoughtFromGwp' in to_save:
                del to_save['ThingsBoughtFromGwp']
            if 'ThingsSoldToGwp' in to_save:
                del to_save['ThingsSoldToGwp']

        # del to_save['Hash']  # Should it store the hash? I can think of a few reasons why it could be useful.
        return to_save

    def save_to_database(self, connection=None):
        """
        Save this Order to the database using the provided connection.
        The connection can be direct or a pipeline object.
        If None is provided, a connection will be created.
        :param connection: Can be a None, a Redis connection or a pipeline.
        :return:
        """
        if not connection:
            connection = db.get_redis_db_from_context()

        # If this is a new order, add it to the relevant indices.
        if not self.FromDatabase:
            # We need to add the hash to the Thing Index
            connection.rpush(consts.KEY_COLONY_ALL_ORDERS.format(self.OwnerID), self.Hash)
            connection.rpush(consts.KEY_COLONY_NEW_ORDERS.format(self.OwnerID), self.Hash)

        connection.hmset(consts.KEY_ORDER_MANIFEST.format(self.Hash), self.to_dict(delta=True))

    @staticmethod
    def generate_hash(colony_hash: str, ordered_tick):
        return hashlib.sha1(
            (
                    colony_hash +
                    str(ordered_tick)
            ).encode('UTF8')
        ).hexdigest()

    @classmethod
    def get_many_from_database(cls, list_of_order_hash) -> dict:
        db_connection = db.get_redis_db_from_context()
        pipe = db_connection.pipeline()

        orders_to_find = {}

        # Iterate of the list of orders and build hash keys
        for order_hash in list_of_order_hash:
            orders_to_find[order_hash] = None
            pipe.hgetall(consts.KEY_ORDER_MANIFEST.format(order_hash))

        # Combine the list of hashes and list of results into a dictionary of Key(Hash), Value(Data)
        results = dict(zip(orders_to_find.keys(), pipe.execute()))

        for hash_key, data in results.items():
            if len(data) > 0:
                data['FromDatabase'] = True
                results[hash_key] = cls.from_order_data_dict(data)
            else:
                results[hash_key] = None

        return results

    @classmethod
    def from_order_data_dict(cls, order_data: dict) -> "Order":
        return cls(order_data['OwnerID'], **order_data)

    @classmethod
    def get_from_database_by_hash(cls, order_hash):
        db_connection = db.get_redis_db_from_context()

        data = db_connection.hgetall(consts.KEY_ORDER_MANIFEST.format(order_hash))

        if len(data) > 0:
            data['FromDatabase'] = True
            return cls.from_order_data_dict(data)

        return None
