import gzip
import json

from flask import Blueprint, Response, request

from lib.things.thing import Thing

market_module = Blueprint('v3_prime_market', __name__, url_prefix='/v3/market')


@market_module.route('/process_item_list_request', methods=['POST'])
def market_get_items():
    if 'things' not in request.files:
        requested_items = request.json
    else:
        gz_post_data = request.files['things']
        thing_file = gzip.GzipFile(fileobj=gz_post_data, mode='r')
        requested_items = json.loads(thing_file.read().decode('UTF8'))

    things = Thing.get_many_from_database(requested_items)

    thing_data = [thing.to_dict() for thing in things.values()]

    return Response(json.dumps(thing_data), mimetype='application/json')
