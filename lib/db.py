"""
Created on 16 Jan 2018

@author: aleyshon
"""
import ast

import redis
from flask import g

import config


def try_auto_parse(val):
    try:
        val = ast.literal_eval(val)
    except Exception:
        pass
    return val


def parse_boolean_responses_hgetall(response, **options):
    if not response:
        return {}

    for index in range(1, len(response), 2):
        response[index] = try_auto_parse(response[index])

        # if response[index] == "True":
        #     response[index] = True
        # if response[index] == "False":
        #     response[index] = False

    it = iter(response)
    return dict(zip(it, it))


def parse_boolean_responses_get(response, **options):
    if not response:
        return None

    return try_auto_parse(response)


def get_redis_database_connection(db_number=0):
    """
    Create a new Redis database connection.
    :return:
    """

    db = redis.Redis(config.DATABASE_IP, config.DATABASE_PORT, decode_responses=True, db=db_number)

    db.set_response_callback('GET', parse_boolean_responses_get)
    db.set_response_callback('HGET', parse_boolean_responses_get)
    db.set_response_callback('HGETALL', parse_boolean_responses_hgetall)
    db.set_response_callback('HMGET', parse_boolean_responses_hgetall)

    return db


# Returns an valid, connected Redis object either from the cache or it creates one.
def get_redis_db_from_context(db_number=0):
    # Check to see if we've already opened a database
    db = getattr(g, '_database', None)
    if db is None:
        # If not, open and connect to the database, Decode responses in UTF-8 (default)
        db = g._database = get_redis_database_connection(db_number)
    return db
