from flask import Blueprint, Response, request
from lib import consts, db

import lib.colony.manage as colonymanage
import lib.things.utils as thingutils
import lib.orders.utils as orderutils

import json
import uuid

order_module = Blueprint('prime_orders', __name__, url_prefix='/orders')

@order_module.route('/<string:colony_uuid>', methods = ['GET'])
def get_orders(colony_uuid):
    
    rdbi = db.get_db()
    response = dict()
    
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)

    # Check the Colony exists
    colonyId = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyId is None:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)
    
    tick = request.args.get('tick')
    
    if(tick is None):
        return Response(consts.ERROR_INVALID, status = consts.HTTP_INVALID)
    
    tick = int(tick)
    
    # Prevent market manipulation.
    orderutils.anti_timewarp_check(colonyId, tick)
    
    # Construct dict of orders.
    
    orders = rdbi.smembers(consts.KEY_COLONY_NEW_ORDERS % colonyId)
    
    orderData = []
    
    for order in orders:
        data = rdbi.hgetall(consts.KEY_ORDER_DATA % order)
        if (data['Status'] in {consts.ORDER_STATUS_NEW, consts.ORDER_STATUS_PROCESSED}):
            data['OrderId'] = order  
            orderData.append(data)
    
    response['Orders'] = orderData
    
    colonymanage.set_colony_login_flag(colonyId)
    
    return Response(json.dumps(response), status = consts.HTTP_OK , mimetype = consts.MIME_JSON)

@order_module.route('/<string:colony_uuid>', methods = ['PUT'])
def place_order(colony_uuid):
    
    rdbi = db.get_db()
    
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)

    # Check the Colony exists
    colonyId = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyId is None:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)
    
    orderKey = orderutils.create_order_key()
    
    requestData = request.json
    
    # Validate the schema of the incoming items.
    for thing in requestData['ThingsSoldToGwp']:
        itemOK = thingutils.validate_item_schema(thing)
        if(not itemOK):
            return Response(json.dumps("Invalid item schema"), status = consts.HTTP_INVALID)
        
    for thing in requestData['ThingsBoughtFromGwp']:
        itemOK = thingutils.validate_item_schema(thing)
        if(not itemOK):
            return Response(json.dumps("Invalid item schema"), status = consts.HTTP_INVALID)
        
    structure = dict()
    
    structure['ThingsSoldToGwp'] = json.dumps(requestData['ThingsSoldToGwp'])
    structure['ThingsBoughtFromGwp'] = json.dumps(requestData['ThingsBoughtFromGwp'])
    structure['OrderedTick'] = int(requestData['CurrentGameTick'])
    structure['Status'] = consts.ORDER_STATUS_NEW
    
    # Calcuate the tick that it's supposed to be delivered.
    
    structure['DeliveryTick'] = int(structure['OrderedTick']) + orderutils.get_ticks_needed_for_delivery()
        
    rdbi.hmset(consts.KEY_ORDER_DATA % orderKey, structure)
    
    rdbi.sadd(consts.KEY_COLONY_NEW_ORDERS % colonyId, orderKey)
    rdbi.sadd(consts.KEY_COLONY_ALL_ORDERS % colonyId, orderKey)
    
    return Response(json.dumps("OK"), status = consts.HTTP_OK , mimetype = consts.MIME_JSON)

@order_module.route('/<string:colony_uuid>/<string:order_uuid>', methods = ['POST'])
def update_order(colony_uuid, order_uuid):
    
    rdbi = db.get_db()
    
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)

    # Check the Colony exists
    colonyId = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyId is None:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)
     
    # Check the order UUID provided is real
    try:
        orderSafeUUID = uuid.UUID(order_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)

    # Check the order exists
    orderExists = rdbi.exists(consts.KEY_ORDER_DATA % orderSafeUUID)
    if orderExists is None:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)
    
    status = request.json['Status']
    
    # Update the state of the order.
    rdbi.hset(consts.KEY_ORDER_DATA % orderSafeUUID, 'Status', status)
    
    if (status == consts.ORDER_STATUS_FAIL):
        #Remove order from list of new orders.
        rdbi.srem(consts.KEY_COLONY_NEW_ORDERS % colonyId, orderSafeUUID)
        
        
    if (status == consts.ORDER_STATUS_DONE):
        #Remove order from list of new orders.
        rdbi.srem(consts.KEY_COLONY_NEW_ORDERS % colonyId, orderSafeUUID)
        
        # Update the statistics and stock counts.
        # Deserialize JSON
        thingsSoldToGwp = json.loads(rdbi.hget(consts.KEY_ORDER_DATA % orderSafeUUID, 'ThingsSoldToGwp'))
        thingsBoughtFromGwp = json.loads(rdbi.hget(consts.KEY_ORDER_DATA % orderSafeUUID, 'ThingsBoughtFromGwp'))
        
        thingutils.sell_things_from_colony(colonyId, thingsSoldToGwp)
        thingutils.give_things_to_colony(colonyId, thingsBoughtFromGwp)
        
    return Response(json.dumps("OK"), status = consts.HTTP_OK , mimetype = consts.MIME_JSON)
    
@order_module.route('/<string:colony_uuid>/<string:order_uuid>', methods = ['GET'])
def get_order(colony_uuid, order_uuid):
    
    rdbi = db.get_db()
    
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)

    # Check the Colony exists
    colonyID = rdbi.hget(consts.KEY_COLONY_MAP, colonySafeUUID)
    if colonyID is None:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)
    
    # Check the order UUID provided is real
    try:
        orderSafeUUID = uuid.UUID(order_uuid)
    except Exception:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)

    # Check the order exists
    orderExists = rdbi.exists(consts.KEY_ORDER_DATA % orderSafeUUID)
    if orderExists is None:
        return Response(consts.ERROR_NOT_FOUND, status = consts.HTTP_NOT_FOUND)
        
    structure = rdbi.hgetall(consts.KEY_ORDER_DATA % orderSafeUUID)
    
    # Deserialize the Things Sold/Bought.
    structure['ThingsSoldToGwp'] = json.loads(structure['ThingsSoldToGwp'])
    structure['ThingsBoughtFromGwp'] = json.loads(structure['ThingsBoughtFromGwp'])
    structure['OrderId'] = str(orderSafeUUID)
    
    return Response(json.dumps(structure), status = consts.HTTP_OK , mimetype = consts.MIME_JSON)
    
