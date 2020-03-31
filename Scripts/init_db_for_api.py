import config
import lib.gwpcc.consts as const
from lib.db import get_redis_database_connection

ok = False
version = None

while not ok:
    version = input('Which version? ')
    if version in config.API_DB_CONFIG:
        ok = True

# Create all needed keys
print('Creating {} configuration data'.format(version))

db = get_redis_database_connection(config.API_DB_CONFIG[version])

pipe = db.pipeline()

# Set version keys
pipe.setnx(const.KEY_API_VERSION, 1.1)

# Build maintenance keys
#pipe.setnx(const.KEY_API_MAINTENANCE_MODE, False)
pipe.hsetnx(const.KEY_API_MAINTENANCE_WINDOW, const.HASH_KEY_API_MAINTENANCE_WINDOW_START, int(0))
pipe.hsetnx(const.KEY_API_MAINTENANCE_WINDOW, const.HASH_KEY_API_MAINTENANCE_WINDOW_STOP, int(0))

# Default 1 day delivery for orders.
pipe.hsetnx(const.KEY_CONFIGURATION_ORDERS, const.HASH_KEY_ORDER_TICK_DELAY, 60000)

# 300 silver per interval
pipe.setnx(const.KEY_CONFIGURATION_PRIME_COST, 300)

pipe.execute()
