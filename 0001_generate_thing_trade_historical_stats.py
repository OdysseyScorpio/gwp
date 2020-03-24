import config
from lib.db import get_redis_database_connection
from lib.gwpcc.consts import KEY_COUNTERS_HISTORICAL_THING_VOLUME_TRADED_BY_DATE_AND_ACTION

for version in config.API_DB_CONFIG.keys():

    db = get_redis_database_connection(config.API_DB_CONFIG[version])

    pipe = db.pipeline()

    # We need to scan for all historical keys
    pattern = 'Statistics:Counters:Historical:Things:VolumeTradedByDate:*'
    # "Statistics:Counters:Historical:Things:VolumeTradedByDate:3dbddc20498b66a80ef15ad0ad5bdedfbb5a5020:2018-10-20

    keys = db.keys(pattern)

    for key in keys:
        # Load all trade data
        pipe.hgetall(key)
    results = pipe.execute()
    trade_data = dict(zip(keys, results))

    for key in keys:
        components = key.split(':')
        date = components[-1]
        thing_hash = components[-2]

        for action in ['Bought', 'Sold']:
            if trade_data[key].get(action):
                pipe.zincrby(KEY_COUNTERS_HISTORICAL_THING_VOLUME_TRADED_BY_DATE_AND_ACTION.format(date, action),
                             thing_hash, trade_data[key][action])

    pipe.execute()
