from lib import db
import lib.things.stock as thingstock
import lib.colony.manage as colonymanage
import json

def build_key_from_thing(thing):
    
    # Add namespace to item name to form Key
    itemKey = 'ThingDef:' + thing['Name']

    # Add Stuff
    if('StuffType' in thing and thing['StuffType'] != ''):
        itemKey = itemKey + ":" + thing['StuffType']

    # Then quality
    if('Quality' in thing and thing['Quality'] != ''):
        itemKey = itemKey + ":" + thing['Quality']

    return itemKey

def get_thing_id_from_key(thingKey):
    
    rdbi = db.get_db()
    
    thingId = rdbi.hget(thingKey, 'ThingID') 
    
    if(thingId is not None):
        thingId = int(thingId)    
        
    return thingId

def mass_try_get_things(listOfThingDef):
    
    rdbi = db.get_db()
    pipe = rdbi.pipeline()
    
    for thingDef in listOfThingDef:
        pipe.hgetall('ThingDef:{}'.format(thingDef))
    
    results = pipe.execute()
    
    toReturn = []
    
    for thingData in results:
        if(len(thingData) > 0):
            toReturn.append(thingData)
        
    return toReturn
        
def try_get_thing(itemKey):

    rdbi = db.get_db()

    # Try looking up by full name first,
    if(rdbi.exists(itemKey)):
        return rdbi.hgetall(itemKey)

    # Try removing Normal from the key and check again.
    if(':Normal' in itemKey):
        itemKeyNoNormal = itemKey[:-7]

        # Now does the key exist?
        if(rdbi.exists(itemKeyNoNormal)):
            itemData = rdbi.hgetall(itemKeyNoNormal)

            # Set normal quality
            itemData['Quality'] = 'Normal'

            # Copy to expected key.
            rdbi.hmset(itemKey, itemData)

            # Update Item Map
            rdbi.hset('Things:Mapping', itemData['ThingID'], itemKey)

            # Delete old item
            rdbi.delete(itemKeyNoNormal)

            return itemData

    # If we didn't find it return None.
    return None

def thing_generate_id(thingName):

    rdbi = db.get_db()

    # Increment the Thing Counter
    thingID = rdbi.incr("Things:Counter")

    # Add thing entry to thing map.
    rdbi.hset('Things:Mapping', thingID, thingName)

    return thingID

def validate_item_schema(item):
    objectSchema = ['Name', 'BaseMarketValue', 'CurrentPrice', 'Quantity', 'StuffType', 'MinifiedContainer']
    for schemaValue in objectSchema:
        if not (schemaValue in item):
            print('Item {0} is broken!'.format(json.dumps(item)))
            return False

    return True

def sell_things_from_colony(colonyId, listOfThings):
    
    # For each item sent in the JSON payload
    for thing in listOfThings:

        # Add namespace to item name to form Key
        thingKey = build_key_from_thing(thing)
                
        wasOK = thingstock.add_item_to_stock(thingKey, thing) 
        
        # We get the ThingID after because the Thing may not have existed until we ad
        thingID = get_thing_id_from_key(thingKey)
        
        if not wasOK:
            return False
        
        colonymanage.update_colony_sell_stats(colonyId, thingID, thing['Quantity'])
    
    return True

def give_things_to_colony(colonyId, listOfThings):
    
    # For each item sent in the JSON payload
    for thing in listOfThings:
        
        thingKey = build_key_from_thing(thing)

        wasOK = thingstock.sell_item_from_stock(thingKey, thing)

        # We get the ThingID after because the Thing may not have existed until we ad
        thingID = get_thing_id_from_key(thingKey)

        if not wasOK:
            return False
        
        colonymanage.update_colony_purchase_stats(colonyId, thingID, thing['Quantity'])

    return True