import hashlib
import json

from flask import Blueprint, Response, request, current_app

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
        current_app.logger.error('{} colony not found in database'.format(colony.Hash))
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    response['SubscriptionCost'] = int(db_connection.get(consts.KEY_CONFIGURATION_PRIME_COST))

    # 0 ticks left unless we get a score back from the sorted set.
    response['TickSubscriptionExpires'] = 0

    ticks_remaining = db_connection.get(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash))

    if ticks_remaining is not None:
        response['TickSubscriptionExpires'] = int(ticks_remaining)
    else:
        response['TickSubscriptionExpires'] = 0

    current_app.logger.debug('{} is generating a subscription token.'.format(colony.Hash))
    # Generate a random token only valid for 30 seconds.
    token = make_token(colony.Hash)
    pipe = db_connection.pipeline()
    pipe.set(consts.KEY_PRIME_TOKEN_DATA.format(colony.Hash), token)
    pipe.expire(consts.KEY_PRIME_TOKEN_DATA.format(colony.Hash), 30)
    pipe.execute()
    response['Token'] = token
    current_app.logger.debug('{} new token is .'.format(colony.Hash, token))

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
        current_app.logger.error('{} colony not found in database'.format(colony.Hash))
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    sub_data = request.json

    # Validate token
    if 'Token' not in sub_data:
        current_app.logger.error('{} Subscription token was not in payload.'.format(colony.Hash))
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    # Fetch our token from DB
    token_in_db = db_connection.get(consts.KEY_PRIME_TOKEN_DATA.format(colony.Hash))

    # Has it expired or ever existed?
    if token_in_db is None:
        current_app.logger.error('{} Subscription token was not in database or has expired.'.format(colony.Hash))
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    # They should match
    if token_in_db != sub_data['Token']:
        current_app.logger.error(
            '{} Subscription tokens did not match {} != {}.'.format(colony.Hash, sub_data['Token'], token_in_db))
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
    current_app.logger.debug('{} Subscription successful.'.format(colony.Hash))
    return Response("OK", status=consts.HTTP_OK)
