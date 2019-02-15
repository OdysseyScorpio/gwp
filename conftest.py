from flask import g
from pytest import fixture

import app
from lib.db import get_redis_database_connection


@fixture(scope='session')
def test_app_context():
    a = app.make_app()
    a.config['TESTING'] = True
    a.app_context().push()
    g._database = get_redis_database_connection(db_number=15)
    yield a


@fixture(scope='function')
def test_app_context_no_database_set():
    a = app.make_app()
    a.config['TESTING'] = True
    a.app_context().push()
    yield a
