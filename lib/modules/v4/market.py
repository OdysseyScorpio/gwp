import json

from flask import Blueprint, Response

from lib import db
from lib.gwpcc import consts
from lib.gwpcc.colonies.colony import Colony
from lib.gwpcc.things.thing import Thing

market_module = Blueprint('v4_prime_market', __name__, url_prefix='/v4/market')


@market_module.route('/get_data/<string:colony_hash>', methods=['GET'])
def market_get_items(colony_hash):
    print("Sending Market items to Colony")
    connection = db.get_redis_db_from_context()
    colony = Colony.get_from_database_by_hash(colony_hash, db.get_redis_db_from_context())
    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    things = Thing.get_many_from_database(colony.SupportedThings, connection)

    #thing_data = [thing.to_dict() for thing in things.values()]
    thing_data = [thing.to_dict() for thing in things.values() if thing.Quantity > 0 ]
    print("Market items sent")
    return Response(json.dumps(thing_data), mimetype='application/json')
