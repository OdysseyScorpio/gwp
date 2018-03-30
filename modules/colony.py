from flask import Blueprint, Response, request
from datetime import datetime
from lib import consts, db
import json
import uuid

colony_module = Blueprint('colony_module', __name__, url_prefix='/colony')

@colony_module.route('/generate_id', methods = ['GET'])
def colony_generate_id():

    rdbi = db.get_db()

    # Increment the Colony Counter
    colonyID = rdbi.incr("ColonyData:Counter")

    while True:

        # Generate a UUID
        colonyUUID = str(uuid.uuid4())
        
        # Check to see if the Colony UUID is in use (Highly Doubtful)
        if not (rdbi.hexists(consts.KEY_COLONY_MAP, colonyUUID)):
            rdbi.hset(consts.KEY_COLONY_MAP, colonyUUID, colonyID)
            break
    
    colonyData = {"UUID": colonyUUID}
        
    return Response(json.dumps(colonyData), status = 200, mimetype = 'application/json')

@colony_module.route('/<string:colony_uuid>', methods = ['PUT'])
def colony_set_data(colony_uuid):

    rdbi = db.get_db()

    colony_data = request.json

    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    # Check the Colony exists
    colonyID = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyID is None:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    # Set all the values passed in the payload to Redis.
    # Maybe I should change this... Seems a little dangerous.

    colony_data['LastLogin'] = datetime.utcnow().timestamp()

    rdbi.hmset(consts.KEY_COLONY_DATA % colonyID, colony_data)

    return Response("OK", status = 200)

@colony_module.route('/<string:colony_uuid>', methods = ['GET'])
def colony_get_data(colony_uuid):

    rdbi = db.get_db()

    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    # Check the Colony exists
    colonyID = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyID is None:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    colony_data = rdbi.hgetall(consts.KEY_COLONY_DATA % colonyID)

    return Response(json.dumps(colony_data), status = 200, mimetype = 'application/json')