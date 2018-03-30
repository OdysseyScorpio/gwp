import uuid, json
from lib import db, consts, things

def create_order_key():

    rdbi = db.get_db()
    
    orderId = rdbi.incr("Orders:Counter")
    
    while True:

        # Generate a UUID
        orderKey = str(uuid.uuid4())
        
        # Check to see if the Colony UUID is in use (Highly Doubtful)
        if not (rdbi.hexists(consts.KEY_ORDER_MAP, orderKey)):
            rdbi.hset(consts.KEY_ORDER_MAP, orderKey, orderId)
            break
    
    return orderKey

def resolve_key_to_id(orderKey):
    
    rdbi = db.get_db()
    
    return rdbi.hget(consts.KEY_ORDER_MAP, orderKey)

def get_ticks_needed_for_delivery():
    
    rdbi = db.get_db()
    
    value = int(rdbi.hget('Orders:Configuration', 'TicksNeededForDelivery'))
    
    return value

def anti_timewarp_check(colonyId, currentGameTick):
    
    rdbi = db.get_db()
    
    redisKey = consts.KEY_COLONY_DATA % colonyId
    
    lastGameTick = rdbi.hget(redisKey, 'LastGameTick')
    
    if(lastGameTick is None):
        lastGameTick = 0
    else:
        lastGameTick = int(lastGameTick)
    
    # Test to see if the current tick is EARLIER than the last time we received a game tick.
    # This usually means they warped back in time due to an earlier game save.  
    if(currentGameTick < lastGameTick):
        
        # We need to undo any orders pending or delivered since the "new" game tick.
        rdbi.hincrby(redisKey, 'Timewarps', 1)
        
        # Undo all the items added to the market by transactions made after this tick.
        rollback_orders_since_tick(colonyId, currentGameTick)
        
    rdbi.hset(redisKey, 'LastGameTick', currentGameTick)
    
def rollback_orders_since_tick(colonyId, tick):
    
    rdbi = db.get_db()
    
    # Get all orders (members) in the set.
    allOrders = rdbi.smembers(consts.KEY_COLONY_ALL_ORDERS % colonyId)

    for orderKey in allOrders:
        
        order = rdbi.hgetall(consts.KEY_ORDER_DATA % orderKey)

        if(int(order['OrderedTick']) > tick):
            
            # If the transaction completed, we need to undo it.
            if order['Status'] == consts.ORDER_STATUS_DONE:
               
                # Deserialize JSON
                thingsToRemoveFromGwp = json.loads(order['ThingsSoldToGwp'])
                thingsToAddToGwp = json.loads(order['ThingsBoughtFromGwp'])

                for thing in thingsToRemoveFromGwp:
                    # Add namespace to item name to form Key
                    thingKey = things.utils.build_key_from_thing(thing)
                    things.stock.sell_item_from_stock(thingKey, thing, updateStats=False)
                    
                for thing in thingsToAddToGwp:
                    thingKey = things.utils.build_key_from_thing(thing)
                    things.stock.add_item_to_stock(thingKey, thing, updateStats=False)

            # Mark it reversed             
            rdbi.hset(consts.KEY_ORDER_DATA % orderKey, 'Status', consts.ORDER_STATUS_REVERSE)
            
            # Remove it from the colonies processing list.
            rdbi.srem(consts.KEY_COLONY_NEW_ORDERS % colonyId, orderKey)