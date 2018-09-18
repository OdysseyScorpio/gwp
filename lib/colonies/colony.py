import hashlib
from collections import OrderedDict

from lib import db, consts, date_utils


class Colony(object):

    def __init__(self, base_name: str, faction_name: str, planet: str, **kwargs):
        if not base_name:
            raise ValueError('Must specify a Base name!')

        if not faction_name:
            raise ValueError('Must specify a Faction name!')

        if not planet:
            raise ValueError('Must specify a Planet name!')

        self._base_name = base_name
        self._faction_name = faction_name
        self._planet = planet

        self._date_created = int(kwargs.get('DateCreated', date_utils.get_current_unix_time()))
        self._last_action = int(kwargs.get('LastAction', self._date_created))
        self._last_game_tick = int(kwargs.get('LastGameTick', 0))
        self._timewarps = int(kwargs.get('Timewarps', 0))
        self._owner_type = kwargs.get('OwnerType', None)
        self._owner_id = str(kwargs.get('OwnerID', None))

        self._hash = kwargs.get('Hash', self.generate_hash(base_name, faction_name, planet, self._date_created))

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
    def LastAction(self):
        return self._last_action

    @LastAction.setter
    def LastAction(self, value):
        self.__changes['LastAction'] = True
        self._last_action = value

    @property
    def LastGameTick(self):
        return self._last_game_tick

    @LastGameTick.setter
    def LastGameTick(self, value):
        self.__changes['LastGameTick'] = True
        self._last_game_tick = value

    @property
    def Timewarps(self):
        return self._timewarps

    @Timewarps.setter
    def Timewarps(self, value):
        self.__changes['Timewarps'] = True
        self._timewarps = value

    @property
    def BaseName(self):
        return self._base_name

    @BaseName.setter
    def BaseName(self, value):
        self.__changes['BaseName'] = True
        self._base_name = value

    @property
    def Planet(self):
        return self._planet

    @Planet.setter
    def Planet(self, value):
        self.__changes['Planet'] = True
        self._planet = value

    @property
    def FactionName(self):
        return self._faction_name

    @FactionName.setter
    def FactionName(self, value):
        self.__changes['FactionName'] = True
        self._faction_name = value

    @property
    def OwnerType(self):
        return self._owner_type

    @OwnerType.setter
    def OwnerType(self, value):
        self.__changes['OwnerType'] = True
        self._owner_type = value

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
        for varname in vars(cls):
            value = getattr(cls, varname)
            if isinstance(value, property):
                yield varname

    def to_dict(self, delta=False):
        to_save = {}

        if self.FromDatabase and delta:
            for key in self.__changes.keys():
                to_save[key] = getattr(self, key)
        else:
            for prop in self.iter_properties():
                to_save[prop] = getattr(self, prop)
            del to_save['FromDatabase']

        # del to_save['Hash']  # Should it store the hash? I can think of a few reasons why it could be useful.
        return to_save

    def save_to_database(self, connection=None):
        """
        Save this Colony to the database using the provided connection.
        The connection can be direct or a pipeline object.
        If None is provided, a connection will be created.
        :param connection: Can be a None, a Redis connection or a pipeline.
        :return:
        """
        if not connection:
            connection = db.get_redis_db_from_context()

        if not self.FromDatabase:
            # We need to add the hash to the Thing Index
            connection.rpush(consts.KEY_COLONY_INDEX_BY_ID, self.Hash)

            if self.OwnerType == 'Steam':
                connection.rpush(
                    consts.KEY_COLONY_INDEX_BY_STEAM_ID.format(self.OwnerID),
                    self.Hash
                )

        connection.hmset(consts.KEY_COLONY_METADATA.format(self.Hash), self.to_dict(delta=True))

    @classmethod
    def from_dict(cls, colony: dict):
        return cls(colony['BaseName'], colony['FactionName'], colony['Planet'], **colony)

    @staticmethod
    def generate_hash(base_name, faction_name, planet, date_created):
        return hashlib.sha1(
            (
                    base_name +
                    faction_name +
                    planet +
                    str(date_created)
            ).encode('UTF8')
        ).hexdigest()

    @classmethod
    def get_many_from_database(cls, list_of_colony_dict):
        db_connection = db.get_redis_db_from_context()
        pipe = db_connection.pipeline()

        colonies_to_find = OrderedDict()

        # Iterate of the list of Thing data structures and build hash keys
        for colony_data in list_of_colony_dict:
            if ('Hash' not in colony_data or not colony_data['Hash']) \
                    and ('DateCreated' not in colony_data or not colony_data['DateCreated']):
                raise ValueError('You must supply the Hash or the exact Date Created to perform Colony lookups')
            colony_obj = cls.from_dict(colony_data)
            colonies_to_find[colony_obj.Hash] = colony_obj
            pipe.hgetall(consts.KEY_COLONY_METADATA.format(colony_obj.Hash))

        # Combine the list of hashes and list of results into a dictionary of Key(Hash), Value(Data)
        results = dict(zip(colonies_to_find.keys(), pipe.execute()))

        for hash_key, data in results.items():
            if len(data) > 0:
                data['FromDatabase'] = True
                results[hash_key] = cls.from_dict(data)
            else:
                # Use the generated object, Caller should test FromDatabase
                results[hash_key] = colonies_to_find[hash_key]

        return results

    @classmethod
    def get_from_database(cls, colony_dict: dict):
        db_connection = db.get_redis_db_from_context()

        colony_obj = cls.from_dict(colony_dict)

        data = db_connection.hgetall(consts.KEY_COLONY_METADATA.format(colony_obj.Hash))

        if len(data) > 0:
            data['FromDatabase'] = True
            return cls.from_dict(data)

        # Caller should test FromDatabase
        return colony_obj

    @classmethod
    def get_from_database_by_hash(cls, colony_hash: str):
        db_connection = db.get_redis_db_from_context()

        data = db_connection.hgetall(consts.KEY_COLONY_METADATA.format(colony_hash))

        if len(data) > 0:
            data['FromDatabase'] = True
            return cls.from_dict(data)

        # If looked up by hash, it's almost guaranteed to exist.
        return None

    def ping(self):
        current_hour = date_utils.get_current_hour()
        current_epoch = date_utils.get_current_unix_time()
        current_date = date_utils.get_today_date_string()
        connection = db.get_redis_db_from_context()

        # Calculate start/end epoch times for this hour
        epoch_start, epoch_stop = date_utils.get_unix_time_range_for_hour()

        # Get the item at the top of the set with the highest score (0,0).
        old_colony = connection.zrange(consts.KEY_BUCKET_COLONIES_ACTIVE, 0, 0, withscores=True)

        # Start transaction
        pipe = connection.pipeline()

        # If the lowest score item in the set is less than the start of the hour,
        # We need to trim the set as we've probably transitioned into a new hour.
        if len(old_colony) > 0 and old_colony[0][1] < epoch_start:
            # Remove all colonies that haven't been active in this current hour.
            pipe.zremrangebyscore(consts.KEY_BUCKET_COLONIES_ACTIVE, '-inf', '(' + str(epoch_start))

        # Add this colony to the set or update the score if it's already in it.
        pipe.zadd(consts.KEY_BUCKET_COLONIES_ACTIVE, self.Hash, current_epoch)

        # Add this colony to set for current day if it's not already in it.
        pipe.sadd(consts.KEY_TRENDS_HISTORICAL_COLONIES_ACTIVE_BY_DATE.format(current_date), self.Hash)

        # Update last colony action
        pipe.hset(consts.KEY_COLONY_METADATA.format(self.Hash), 'LastAction', current_epoch)

        # Finish transaction
        pipe.execute()

        # Count members in set for the current hour
        count = connection.zcount(consts.KEY_BUCKET_COLONIES_ACTIVE, epoch_start, epoch_stop)

        # Update stats counter
        connection.set(consts.KEY_COUNTERS_HOURLY_COLONIES_ACTIVE.format(current_hour), count)
