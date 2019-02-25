import json

from flask import g
from pytest import fixture

import app
from lib import consts
from lib.db import get_redis_database_connection
from lib.things.thing import Thing


@fixture(scope='session')
def test_app_context():
    a = app.make_app()
    a.config['TESTING'] = True
    a.app_context().push()
    g._database = get_redis_database_connection(db_number=15)

    pipe = get_redis_database_connection(db_number=15).pipeline()

    pipe.set(consts.KEY_CONFIGURATION_PRIME_COST, 300, nx=True)
    pipe.set(consts.KEY_API_VERSION, '1.0', nx=True)
    pipe.hset(consts.KEY_CONFIGURATION_ORDERS, consts.HASH_KEY_ORDER_TICK_DELAY, '60000')
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_MTIME_START, 23)
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_MTIME_LENGTH, 3600)
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_MTIME_PREABMLE, 7200)
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_MTIME_NEXT, 0)
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_MTIME_SET, "false")
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_BUY_PRICE_MULTIPLIER, "0.20")
    pipe.hmset(consts.KEY_API_MAINTENANCE_WINDOW, {"Start": "1551049200", "Stop": "1551052800"})

    pipe.hset(consts.KEY_GLITTERBOT_DATA,
              consts.KEY_GLITTERBOT_IGNORE_THINGS, json.dumps(
            ['8697f432058b914ba2b20c5bd6f0678548126e21', 'cdf9187a28bcb1b219a3a4aeaf3c99a65e7eb882'])
              )
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_SELL_PRICE_MULTIPLIER, "0.75")
    pipe.hsetnx(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_MIN_SELL_PRICE_MULTIPLIER, "0.2")
    breakpoints = [
        {'PriceStart': 0, 'PriceStop': 5, 'StockMin': 1000, 'StockMax': 100000, 'CapBuyPrice': 2.5},
        {'PriceStart': 5, 'PriceStop': 25, 'StockMin': 200, 'StockMax': 250, 'CapBuyPrice': 2.75},
        {'PriceStart': 25, 'PriceStop': 50, 'StockMin': 100, 'StockMax': 150, 'CapBuyPrice': 3.0},
        {'PriceStart': 50, 'PriceStop': 100, 'StockMin': 10, 'StockMax': 15, 'CapBuyPrice': 3.5},
        {'PriceStart': 100, 'PriceStop': 100000, 'StockMin': 1, 'StockMax': 15, 'CapBuyPrice': 4.0},
        {'PriceStart': 100000, 'PriceStop': 200000, 'StockMin': 1, 'StockMax': 5, 'CapBuyPrice': 4.5}
    ]
    pipe.hset(consts.KEY_GLITTERBOT_DATA, consts.KEY_GLITTERBOT_PRICEBREAKS, json.dumps(breakpoints))

    thing = Thing("Silver")
    thing.save_to_database(pipe)

    pipe.execute()

    yield a


@fixture(scope='function')
def test_app_context_no_database_set():
    a = app.make_app()
    a.config['TESTING'] = True
    a.app_context().push()
    yield a
