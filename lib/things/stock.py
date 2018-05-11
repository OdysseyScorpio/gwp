from lib import db
from lib.things import utils, stats, price

def add_item_to_stock(itemKey, thingData, updateStats = True):
        
        rdbi = db.get_db()
        
        # Request Key from Redis
        itemData = utils.try_get_thing(itemKey)

        # Did we find the Key?
        if itemData is not None:

            # We don't accept all of the client side data anymore.
            # Construct a new item from bits of the Client data
            newItem = dict()

            # Add thing ID if there isn't one.
            if not 'ThingID' in itemData:
                newItem['ThingID'] = utils.thing_generate_id(itemKey)
            else:
                newItem['ThingID'] = rdbi.hget(itemKey, 'ThingID')

            # Increment the quantity in stock
            rdbi.hincrby(itemKey, 'Quantity', thingData['Quantity'])

            # Get client side base market value to add to price history for later average calcs.
            newItem['BaseMarketValue'] = thingData['BaseMarketValue']

        else:

            # Create a new item based on data from Client.
            newItem = dict(thingData)

            # This is a new Thing so get an ID.
            newItem['ThingID'] = utils.thing_generate_id(itemKey)
            
            newItem['UseServerPrice'] = "false"
            
        # Set the Values of the Key
        rdbi.hmset(itemKey, newItem)

        if(updateStats):
            # Update Price History
            price.things_update_price_history(newItem['ThingID'], newItem['BaseMarketValue'])
    
            # Update ThingStats
            stats.things_update_stats(newItem['ThingID'], thingData['Quantity'], False)
        
        return newItem
    
def sell_item_from_stock(itemKey, thingData, updateStats = True):
    
    rdbi = db.get_db()
    
    # Request Key from Redis
    itemData = utils.try_get_thing(itemKey)

    # Did we find the Key?
    if not itemData is None:

        # Add thing ID if there isn't one.
        if not 'ThingID' in itemData:
            itemData['ThingID'] = utils.thing_generate_id(itemKey)
            rdbi.hset(itemKey, "ThingID", itemData['ThingID'])

        # Decrement the quantity that was bought from stock
        rdbi.hincrby(itemKey, 'Quantity', -thingData['Quantity'])

        # Update ThingStats
        if(updateStats):
            stats.things_update_stats(itemData['ThingID'], thingData['Quantity'], True)
        
        return True
    else:
        # Couldn't locate Key in rdbi, something is wrong...
        print("We sold something we never had in the first place: Item was " + itemKey)
        
        return False