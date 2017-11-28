import json, redis

def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    
    return db

if __name__ == '__main__':
    
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    
    print("Deleting ThingDef Thing IDs")
    for item in db.scan_iter(match="ThingDef:*"):
        itemName = item.split(':')[1]
        print("Deleting Thing ID from {0}".format(item))
        db.hdel(item, 'Thing_ID')
        print("Deleting ThingID from {0}".format(item))
        db.hdel(item, 'ThingID')
        
    print("Deleting Thing Map key")
    db.delete('Things:Mapping')
    
    print("Resetting Thing Counter")
    db.set("Things:Counter", 0)
    
    print("Deleting Stats:")
    
    for stat in db.scan_iter(match="Things:Stats:*"):
        print("Deleting {0}".format(stat))
        db.delete(stat)