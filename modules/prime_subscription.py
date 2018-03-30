from flask import Blueprint, Response, request
from lib import consts, db
import json
import uuid

prime_module = Blueprint('prime_subscription', __name__, url_prefix='/prime_subscription')

@prime_module.route('/check/<string:colony_uuid>', methods = ['GET'])
def subscription_check(colony_uuid):

    rdbi = db.get_db()
    response = dict()
    
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    # Check the Colony exists
    colonyID = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyID is None:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    redisKey = 'Prime_Subscriptions:Cost'
    response['SubscriptionCost'] = int(rdbi.get(redisKey))
    response['TickSubscriptionExpires'] = 0

    # Get the in-game Tick that Colonies subscription expires.
    redisKey = 'Prime_Subscriptions:List'
    
    tickSubExpires = rdbi.hget(redisKey, colonyID)
    
    if(tickSubExpires is not None):
        response['TickSubscriptionExpires'] = int(tickSubExpires)

    return Response(json.dumps(response), status = 200, mimetype = 'application/json')

@prime_module.route('/subscribe/<string:colony_uuid>', methods = ['PUT'])
def subscription_update(colony_uuid):
    
    rdbi = db.get_db()

    subData = request.json

    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    # Check the Colony exists
    colonyID = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyID is None:
        return Response(consts.ERROR_NOT_FOUND, status = 404)

    # Update subscription tick for Colony.
    redisKey = 'Prime_Subscriptions:List'
    rdbi.hset(redisKey, colonyID, int(subData['TickSubscriptionExpires']))
    
    # Update Silver acquired.
    itemKey = "ThingDef:Silver"
    rdbi.hincrby(itemKey, 'Quantity', subData['SubscriptionCost'])
    
    return Response("OK", status = 200)
        