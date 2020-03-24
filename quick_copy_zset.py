import config
from lib.db import get_redis_database_connection
from lib.gwpcc.consts import KEY_COUNTERS_HISTORICAL_THING_VOLUME_TRADED_BY_DATE_AND_ACTION

db = get_redis_database_connection(config.API_DB_CONFIG['u1'])
pipe = db.pipeline()
for action in ['Bought', 'Sold']:
    results = db.zrange(KEY_COUNTERS_HISTORICAL_THING_VOLUME_TRADED_BY_DATE_AND_ACTION.format('2018-11-09', action),
                        0,
                        -1,
                        withscores=True)

    for result in results:
        pipe.zincrby(KEY_COUNTERS_HISTORICAL_THING_VOLUME_TRADED_BY_DATE_AND_ACTION.format('2018-11-11', action),
                     result[0], result[1])

pipe.execute()
