from lib import db, date_utils, consts
from lib.things.thing import BaseThing


def update_stats_for_sold_thing(thing: BaseThing, quantity, connection=None):
    __update_stats_for_thing(False, thing, quantity, connection)


def update_stats_for_bought_thing(thing: BaseThing, quantity, connection=None):
    __update_stats_for_thing(True, thing, quantity, connection)


def __update_stats_for_thing(buy, thing, quantity, connection):
    current_hour = date_utils.get_current_hour()
    current_day = date_utils.get_today_date_string()

    action = 'Bought' if buy else 'Sold'

    do_exec = False

    if not connection:
        connection = db.get_redis_db_from_context().pipeline()
        do_exec = True

    # Update Base Market Value
    connection.zincrby(consts.KEY_THING_BASE_MARKET_VALUE_DATA.format(thing.Hash), thing.BaseMarketValue, 1)

    # Hourly
    connection.hincrby(consts.KEY_COUNTERS_HOURLY_VOLUME_TRADED.format(current_hour), action, quantity)
    connection.hincrby(consts.KEY_COUNTERS_HOURLY_THINGS.format(thing.Hash, current_hour), action, quantity)

    # Daily
    connection.hincrby(consts.KEY_COUNTERS_HISTORICAL_VOLUME_TRADED.format(current_day), action, quantity)
    connection.hincrby(consts.KEY_COUNTERS_HISTORICAL_THINGS.format(thing.Hash, current_day), action, quantity)

    # Trends
    connection.hincrby(consts.KEY_TRENDS_VOLUME_TRADED_BY_HOUR.format(current_hour), action, quantity)

    # Totals
    connection.incrby(consts.KEY_TOTAL_BUY_OR_SELL.format(action), quantity)

    if do_exec:
        connection.execute()
