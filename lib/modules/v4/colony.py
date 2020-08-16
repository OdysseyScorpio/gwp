import gzip
import json

from flask import Blueprint, Response, request, escape

from lib import db
from lib.gwpcc import consts
from lib.gwpcc.colonies.colony import Colony
from lib.gwpcc.consts import KEY_THING_LOCALE_THING_NAMES, USER_TYPES
from lib.gwpcc.things.thing import Thing

colony_module = Blueprint('v4_colony_module', __name__, url_prefix='/v4/colonies')


@colony_module.route('/create', methods=['PUT'])
def colony_create():
    incoming_data = request.json
    connection = db.get_redis_db_from_context()
    colony = new_colony_from_request(incoming_data, connection)
    print("Saving new colony to db")
    if not any(allowed_type == colony.OwnerType for allowed_type in USER_TYPES):
        print("Not allowed - not saving - sending error")
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)
    
    colony.save_to_database(connection)

    colony.ping()
    print("Colony Saved")
    return Response(json.dumps({'Hash': colony.Hash}), status=201, mimetype='application/json')


def new_colony_from_request(incoming_data, connection):
    new_colony = {'BaseName': escape(incoming_data['BaseName']),
                  'FactionName': escape(incoming_data['FactionName']),
                  'Planet': escape(incoming_data['Planet']),
                  'OwnerType': escape(incoming_data['OwnerType']),
                  'OwnerID': escape(incoming_data['OwnerID']),
                  'LastGameTick': escape(incoming_data['LastGameTick'])}

    return Colony.from_dict(new_colony, connection=connection)


@colony_module.route('/<string:colony_hash>', methods=['PUT'])
def colony_update_data(colony_hash):
    connection = db.get_redis_db_from_context()
    colony = Colony.get_from_database_by_hash(colony_hash, connection)

    print("Saving colony data")
    incoming_data = request.json

    created = False

    if not colony or colony.OwnerID != incoming_data['OwnerID']:
        # If the Owner ID's don't match. Create a new colony.
        # And assign it a new ID. Might have happened if save sharing.
        colony = new_colony_from_request(incoming_data, connection)
        created = True
    else:
        colony.BaseName = escape(incoming_data['BaseName'])
        colony.FactionName = escape(incoming_data['FactionName'])
        colony.Planet = escape(incoming_data['Planet'])
        colony.LastGameTick = escape(incoming_data['LastGameTick'])
        if incoming_data['HasSpawned']:
            colony.Ban()

    pipe = connection.pipeline()

    if colony.IsBanned():
        return Response(consts.ERROR_BANNED, status=consts.HTTP_FORBIDDEN)

    # Make sure add the owners to the correct sets.
    if colony.OwnerType == 'Steam':
        key = consts.KEY_USER_INDEX_BY_STEAM_ID
    elif colony.OwnerType == 'Normal':
        key = consts.KEY_USER_INDEX_BY_NORMAL_ID
    else:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    pipe.sadd(key, colony.OwnerID)

    colony.save_to_database(pipe)

    pipe.execute()

    colony.ping()
    print("Sending colony hash")
    return Response(json.dumps({'Hash': colony.Hash}), status=201 if created else 200, mimetype='application/json')


@colony_module.route('/<string:colony_hash>', methods=['GET'])
def colony_get_data(colony_hash):
    print("Getting colony data")
    colony = Colony.get_from_database_by_hash(colony_hash, db.get_redis_db_from_context())

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)
    print("Sending colony data")
    return Response(json.dumps(colony.to_dict()), status=200, mimetype='application/json')


@colony_module.route('/<string:colony_hash>/thing_metadata', methods=['PUT'])
def colony_set_supported_things(colony_hash: str):
    print("Received Supported things list from colony")

    colony = Colony.get_from_database_by_hash(colony_hash, db.get_redis_db_from_context())
    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    try:
        gz_post_data = request.files['things']

        # Decompress payload
        thing_file = gzip.GzipFile(fileobj=gz_post_data, mode='r')

        # Deserialize JSON back in to {'Locale': str, 'Things': List[Dict[str, str]]}
        payload = json.loads(thing_file.read().decode('UTF8'))

        # Set locale
        locale = payload['Locale'].lower()

        # This is a List[Dict[str, str]]
        supported_things_json = payload['Things']

        print("Supported things parsed")

    except json.JSONDecodeError:
        print("Error in things list found")
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    # Need to construct things then add Localized name to index
    pipe = db.get_redis_db_from_context().pipeline()

    pipe.sadd(consts.KEY_THING_LOCALE_KNOWN_LANGUAGES, locale)


    for thing_json in supported_things_json:
        thing = Thing.from_dict(thing_json)
        pipe.zincrby(KEY_THING_LOCALE_THING_NAMES.format(locale, thing.Hash), 1, thing.LocalizedName)
    pipe.execute()

    # This is immediately saved.
    colony.SupportedThings = supported_things_json
    print("Supported things saved")
    return Response('OK', status=200, mimetype='application/json')


@colony_module.route('/<string:colony_hash>/mod_metadata', methods=['PUT'])
def colony_set_mods(colony_hash: str):
    print("Received List of Mods from colony")
    colony = Colony.get_from_database_by_hash(colony_hash, db.get_redis_db_from_context())
    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    try:
        gz_post_data = request.files['mods']
        mod_file = gzip.GzipFile(fileobj=gz_post_data, mode='r')
        payload = json.loads(mod_file.read().decode('UTF8'))
        mod_list = payload['ModList']

    except json.JSONDecodeError:
        print("Error in mod list found")
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    # This is immediately saved.
    colony.ModList = mod_list
    print("List of Mods Saved")
    return Response('OK', status=200, mimetype='application/json')
