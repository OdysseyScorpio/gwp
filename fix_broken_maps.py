import json, redis, pprint, collections
from texttable import Texttable

def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)

    return db

if __name__ == '__main__':

    db = get_db()

    quantity = 0

    statKey = 'Things:Stats:2017-11-21'
    thingMapKey = 'Things:Mapping'

    thingMap = db.hgetall(thingMapKey)

    pipe = db.pipeline()

    for thingMapID, thingDef in thingMap.items():
        pipe.hmget(thingDef, 'Name', 'ThingID')

    itemNames = pipe.execute()
    
    itemKeys = []
    
    for item in db.scan_iter(match="ThingDef:*"):
        itemKeys.append(item)
        pipe.hgetall(item)
        
    allItemData = pipe.execute()

    allItemsAndKeys = list(zip(itemKeys, allItemData))

    deletes = 0
    updates = 0
    
    for thingMapItem, itemNameA in zip(thingMap, itemNames):
        if(itemNameA[0]) is None:
            print('Could not find {0} {1}, trying Normal Quality'.format(thingMap[thingMapItem],thingMapItem))
            tryNormal = db.hmget(thingMap[thingMapItem]+":Normal", 'Name', 'ThingID')
            if(tryNormal[0] is None):
                found = False
                # Try revese mapping from ThingDef to Mapping table. Slow as shit but required.
                for itemKey, itemData in allItemsAndKeys:
                    if(int(itemData['ThingID']) == int(thingMapItem)):
                        found = True
                        break
                        pipe.hset(thingMapKey, thingMapItem, itemKey)
                if (found):
                    print('Found Item by reverse mapping. Setting {0} to {1}'.format(thingMapItem, item))
                    pipe.hset(thingMapKey, thingMapItem, item)
                    updates += 1
                    print('Fixed item {0} from {1}'.format(thingMapItem, item))
                else:
                    print('Item not found at all {0}, Deleting..'.format(thingMapItem))
                    pipe.hdel(thingMapKey, thingMapItem)
                    deletes +=1
                    print('Deleted Hash Value {0}'.format(thingMapItem))
            else:
                print('Found item with Normal Quality {0}'.format(tryNormal))
                pipe.hset(thingMapKey, thingMapItem, thingMap[thingMapItem]+":Normal")
                updates += 1
                print('Fixed item {0} from {1}'.format(thingMap[thingMapItem],thingMap[thingMapItem]+":Normal"))
    
    print('Will make {0} updates and {1} deletions'.format(updates, deletes))
    
    print('Executing commands')
    
    pipe.execute()
    
    print('Done')