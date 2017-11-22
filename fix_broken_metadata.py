import redis

def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    
    return db

def key_is_in_item(item, value):
    
    return (value in item)

if __name__ == '__main__':
    
    db = get_db()
        
    objectSchema = ['BaseMarketValue', 'CurrentPrice', 'Quantity', 'StuffType', 'MinifiedContainer']    
    
    for item in db.scan_iter(match="ThingDef:*"):
        if(item != "ThingDef:Silver"):
            db.hsetnx(item, 'MinifiedContainer', 'False')
            itemData = db.hgetall(item)
            for schemaValue in objectSchema:
                if not key_is_in_item(itemData, schemaValue):
                    print('Item {0} is broken! Removing'.format(item))
                    db.delete(item)
                    break