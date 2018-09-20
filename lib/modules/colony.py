import json

from flask import Blueprint, Response, request, escape

from lib import consts, db
from lib.colonies.colony import Colony

colony_module = Blueprint('v3_colony_module', __name__, url_prefix='/v3/colonies')


@colony_module.route('/create', methods=['PUT'])
def colony_create():
    incoming_data = request.json

    colony = new_colony_from_request(incoming_data)

    colony.save_to_database(db.get_redis_db_from_context())

    colony.ping()

    return Response(json.dumps({'Hash': colony.Hash}), status=201, mimetype='application/json')


def new_colony_from_request(incoming_data):
    new_colony = {'BaseName': escape(incoming_data['BaseName']),
                  'FactionName': escape(incoming_data['FactionName']),
                  'Planet': escape(incoming_data['Planet']),
                  'OwnerType': escape(incoming_data['OwnerType']),
                  'OwnerID': escape(incoming_data['OwnerID'])}

    return Colony.from_dict(new_colony)


@colony_module.route('/<string:colony_hash>', methods=['PUT'])
def colony_update_data(colony_hash):
    colony = Colony.get_from_database_by_hash(colony_hash)

    incoming_data = request.json

    created = False

    if not colony or colony.OwnerID != incoming_data['OwnerID']:
        # If the Owner ID's don't match. Create a new colony.
        # And assign it a new ID. Might have happened if save sharing.
        colony = new_colony_from_request(incoming_data)
        created = True
    else:
        colony.BaseName = escape(incoming_data['BaseName'])
        colony.FactionName = escape(incoming_data['FactionName'])
        colony.Planet = escape(incoming_data['Planet'])

    colony.save_to_database(db.get_redis_db_from_context())

    colony.ping()

    return Response(json.dumps({'Hash': colony.Hash}), status=201 if created else 200, mimetype='application/json')


@colony_module.route('/<string:colony_hash>', methods=['GET'])
def colony_get_data(colony_hash):
    colony = Colony.get_from_database_by_hash(colony_hash)

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    return Response(json.dumps(colony.to_dict()), status=200, mimetype='application/json')