import redis

def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)

    return db

def remap_thing_ID_colony_stats(pipe, OldThingID, NewThingID):
    
    itemKeys = []
    
    for colony in db.scan_iter(match="Colony:*:Data"):
        itemKeys.append(colony)
    
    for colony in itemKeys:
        splitData = colony.split(":")
        colonyID = splitData[1]
        
        keyColonyBought = "Colony:%s:ThingsBought" % colonyID
        keyColonySold = "Colony:%s:ThingsSold" % colonyID
        
        oldThingQuantity = db.hget(keyColonySold, OldThingID)
        
        if(not oldThingQuantity is None):
            pipe.hset(keyColonySold,  NewThingID, oldThingQuantity)
            pipe.hdel(keyColonySold, OldThingID)
            
        oldThingQuantity = db.hget(keyColonyBought, OldThingID)
        
        if(not oldThingQuantity is None):
            pipe.hset(keyColonyBought, NewThingID, oldThingQuantity)
            pipe.hdel(keyColonySold, OldThingID)
    
def remap_thing_ID_trading_statistics(pipe, OldThingID, NewThingID):
    
    itemKeys = []

    for item in db.scan_iter(match="Things:Stats:*"):
        itemKeys.append(item)
            
    for stat_entry in itemKeys:
        oldThingQuantity = db.hget(stat_entry, "%s_sold" % OldThingID)
        
        if(not oldThingQuantity is None):
            pipe.hset(stat_entry, "%s_sold" % NewThingID, oldThingQuantity)
            pipe.hdel(stat_entry, "%s_sold" % OldThingID)
            
        oldThingQuantity = db.hget(stat_entry, "%s_bought" % OldThingID)
        
        if(not oldThingQuantity is None):
            pipe.hset(stat_entry, "%s_bought" % NewThingID, oldThingQuantity)
            pipe.hdel(stat_entry, "%s_bought" % OldThingID)
            
if __name__ == '__main__':

    db = get_db()

    quantity = 0

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
    
    itemNoQuality = {}
    itemWithQuality = {}
    
    thingMapWithThingData = list(zip(thingMap, itemNames))
    
    #pipe.delete(thingMap)

    print('Scanning for Things with no quality and quality entries.')
    
    for thingMapItem, itemNameA in allItemsAndKeys:
        tryNormal = db.hgetall(thingMapItem+":Normal")
        if(len(tryNormal) != 0):
            print('Duplicate Found, Merging item without Quality into %s ' % thingMapItem+":Normal")
            
            itemNoQuality['KeyName'] = thingMapItem
            itemWithQuality['KeyName'] = thingMapItem + ":Normal"
            itemWithQuality.update(tryNormal)
            
            # Get Thing Data from key with no quality.
            itemNoQuality.update(db.hgetall(itemNoQuality['KeyName']))
            
            # Add the Non-Quality count to Quality amount.
            pipe.hincrby(itemWithQuality['KeyName'], 'Quantity', itemNoQuality['Quantity'])
        
            # Update the statistics to reflect NEW Thing ID for Thing with Quality.
            remap_thing_ID_colony_stats(pipe, itemNoQuality['ThingID'],itemWithQuality['ThingID'])
            remap_thing_ID_trading_statistics(pipe, itemNoQuality['ThingID'],itemWithQuality['ThingID'])
            
            # Delete item without quality for good.
            pipe.hdel(thingMapKey,itemNoQuality['ThingID'])
            pipe.delete(itemNoQuality['KeyName'])
        
    print('Scanning Things:Mapping for inconsistencies')
    for thingMapItem, itemNameA in thingMapWithThingData:
        if(itemNameA[0]) is None:
            print('Could not find ThingDef Entry for {0} {1}, trying Normal Quality'.format(thingMap[thingMapItem],thingMapItem))
            tryNormal = db.hmget(thingMap[thingMapItem]+":Normal", 'Name', 'ThingID')
            if(tryNormal[0] is None):
                found = False
                print('Scanning all ThingDefs for Matching ThingID')
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
                    print('ThingDef with Thing ID {0} was not found, Deleting from Things:Mapping..'.format(thingMapItem))
                    pipe.hdel(thingMapKey, thingMapItem)
                    deletes +=1
                    print('Deleted Things:Mapping entry for {0}'.format(thingMapItem))
            else:
                
                if(int(tryNormal[1]) == int(thingMapItem)):
                    print('Thing with Quality has same Thing ID')
                    print('Updating Thing Map with new ThingDef')
                    pipe.hset(thingMapKey, thingMapItem, thingMap[thingMapItem]+":Normal")
                    updates +=1 
                else:
                    print('Thing with Normal Quality {0} has different Thing ID'.format(tryNormal))
                    print('Remapping Stats to Thing ID {0} from {1}'.format(tryNormal[1], thingMapItem))
                    remap_thing_ID_colony_stats(pipe, thingMapItem, tryNormal[1])
                    remap_thing_ID_trading_statistics(pipe, thingMapItem, tryNormal[1])
                
                    print('Deleting orphaned thing from Mapping Table')
                    pipe.hdel(thingMapKey, thingMapItem)
                    deletes += 1
                
    print('Will make {0} updates and {1} deletions'.format(updates, deletes))
    
    print('Total commands to execute: %s' % len(pipe))
    
    print('Executing commands')
    
    pipe.execute()
    
    print('Done')