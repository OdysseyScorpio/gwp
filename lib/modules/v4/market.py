import json

from flask import Blueprint, Response

from lib import consts
from lib.colonies.colony import Colony
from lib.things.thing import Thing

market_module = Blueprint('v4_prime_market', __name__, url_prefix='/v4/market')


@market_module.route('/get_data/<string:colony_hash>', methods=['GET'])
def market_get_items(colony_hash):
    colony = Colony.get_from_database_by_hash(colony_hash)
    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    things = Thing.get_many_from_database(colony.SupportedThings)

    thing_data = [thing.to_dict() for thing in things.values()]

    return Response(json.dumps(thing_data), mimetype='application/json')
