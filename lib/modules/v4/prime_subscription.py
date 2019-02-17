import hashlib
import json

from flask import Blueprint, Response, request

from lib import consts, db
from lib import date_utils
from lib.colonies.colony import Colony
from lib.things.thing import Thing

prime_module = Blueprint('v4_prime_subscription', __name__, url_prefix='/v4/prime_subscription')

TicksPerDay = 60000
DaysPerQuadrum = 15


@prime_module.route('/check/<string:colony_hash>', methods=['GET'])
def subscription_check(colony_hash):
    db_connection = db.get_redis_db_from_context()
    response = dict()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    response['SubscriptionCost'] = int(db_connection.get(consts.KEY_CONFIGURATION_PRIME_COST))

    # 0 ticks left unless we get a score back from the sorted set.
    response['TickSubscriptionExpires'] = 0

    ticks_remaining = db_connection.get(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash))

    if ticks_remaining is not None:
        response['TickSubscriptionExpires'] = int(ticks_remaining)
    else:
        # Generate a random token only valid for 30 seconds.
        token = make_token(colony.Hash)
        pipe = db_connection.pipeline()
        pipe.set(consts.KEY_PRIME_TOKEN_DATA.format(colony.Hash), token)
        pipe.expire(consts.KEY_PRIME_TOKEN_DATA.format(colony.Hash), 30)
        pipe.execute()
        response['Token'] = token

    return Response(json.dumps(response), status=200, mimetype='application/json')


def make_token(colony_id):
    return hashlib.sha1(
        ("{}{}".format(colony_id, date_utils.get_current_unix_time())).encode('UTF8')
    ).hexdigest()


@prime_module.route('/subscribe/<string:colony_hash>', methods=['PUT'])
def subscription_update(colony_hash):
    db_connection = db.get_redis_db_from_context()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_INVALID)

    sub_data = request.json

    # Validate token
    if 'Token' not in sub_data:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    # Fetch our token from DB
    token_in_db = db_connection.get(consts.KEY_PRIME_TOKEN_DATA.format(colony.Hash))

    # Has it expired or ever existed?
    if token_in_db is None:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    # They should match
    if token_in_db != sub_data['Token']:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    expiryTick = DaysPerQuadrum * TicksPerDay + colony.LastGameTick

    pipe = db_connection.pipeline()
    # Update subscription tick for Colony.
    pipe.set(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash), int(expiryTick))

    # Remove the token to prevent reuse.
    pipe.delete(consts.KEY_PRIME_TOKEN_DATA.format(colony_hash))

    # Subscriptions expire after 42 days in real life.
    pipe.expireat(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash),
                  date_utils.add_days_to_current_time(30))

    # Update Silver acquired.
    thing = Thing("Silver")
    subscriptionCost = int(db_connection.get(consts.KEY_CONFIGURATION_PRIME_COST))
    pipe.hincrby(consts.KEY_THING_META.format(thing.Hash), 'Quantity', subscriptionCost)
    pipe.execute()
    return Response("OK", status=consts.HTTP_OK)
