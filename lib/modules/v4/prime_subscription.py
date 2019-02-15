import json

from flask import Blueprint, Response, request

from lib import consts, db
from lib import date_utils
from lib.colonies.colony import Colony
from lib.things.thing import Thing

prime_module = Blueprint('v4_prime_subscription', __name__, url_prefix='/v4/prime_subscription')


@prime_module.route('/check/<string:colony_hash>', methods=['GET'])
def subscription_check(colony_hash):
    db_connection = db.get_redis_db_from_context()
    response = dict()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    response['SubscriptionCost'] = int(db_connection.get(consts.KEY_CONFIGURATION_PRIME_COST))

    # 0 ticks left unless we get a score back from the sorted set.
    response['TickSubscriptionExpires'] = 0

    ticks_remaining = db_connection.get(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash))

    if ticks_remaining is not None:
        response['TickSubscriptionExpires'] = int(ticks_remaining)

    return Response(json.dumps(response), status=200, mimetype='application/json')


@prime_module.route('/subscribe/<string:colony_hash>', methods=['PUT'])
def subscription_update(colony_hash):
    db_connection = db.get_redis_db_from_context()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    sub_data = request.json

    # Update subscription tick for Colony.
    db_connection.set(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash), int(sub_data['TickSubscriptionExpires']))

    # Subscriptions expire after 42 days in real life.
    db_connection.expireat(consts.KEY_PRIME_SUBSCRIPTION_DATA.format(colony.Hash),
                           date_utils.add_days_to_current_time(42))

    # Update Silver acquired.
    thing = Thing("Silver")
    db_connection.hincrby(consts.KEY_THING_META.format(thing.Hash), 'Quantity', sub_data['SubscriptionCost'])

    return Response("OK", status=200)
