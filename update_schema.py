import json
import redis
import pprint

def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    
    return db

def thing_generate_id(thingName):
    
    db = get_db()  

    # Increment the Thing Counter
    thingID = db.incr("Things:Counter")
    
    # Add thing entry to thing map.
    db.hset('Things:Mapping', thingID, thingName)
    
    return thingID

if __name__ == '__main__':
    
    db = get_db()
            
    for item in db.scan_iter(match="ThingDef:*"):
        
        if(item == "ThingDef:Silver"):
            print("Got Silver")
        
        oldName = item
        
        stuffType = None
        
        itemData = db.hgetall(item)
        
        if ('Thing_ID' in itemData):        
            oldThingID = itemData['Thing_ID']
        else:
            oldThingID = None
        
        # Essentially copy all fields to new Key
                
        # If this item key contains #, it must be stuffType Thing
        if('#' in item):
            parts = item.split('#')
            thingDef = parts[0]
            stuffType = parts[1]
        else:
            thingDef = item
        
        # There was no # in the name but a stuff type was set?? -_-
        if('StuffType' in itemData and itemData['StuffType'] != ''):
            stuffType = itemData['StuffType']
                
        # Remove keyspace from key name
        if(':' in thingDef):
            parts = thingDef.split(':')
            thingDef = parts[1]
            
        newItem = dict(itemData)
        
        newItem['Name'] = thingDef
        
        newItemKeyName = 'ThingDef:' + newItem['Name']
        
        if (stuffType is not None):
            newItem['StuffType'] = stuffType
            newItemKeyName = newItemKeyName + ":" + newItem['StuffType']
                
        newItem['ThingID'] = thing_generate_id(newItemKeyName)
        
        if(oldThingID is not None):
            del newItem["Thing_ID"]
        
        pprint.pprint(newItem)
        
        db.hmset(newItemKeyName, newItem)
        
        # If the keys match don't delete them.
        if(oldName != newItemKeyName):
            db.delete(oldName)
        
        if(oldThingID is not None):
            db.hdel('Things:Mapping', oldThingID)