import json, redis

def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    
    return db

if __name__ == '__main__':
    
    db = get_db()
    
    quantity = 0
    
    for item in db.scan_iter(match="ThingDef:*"):
        if(item != "ThingDef:Silver"):
            quantity += int(db.hget(item, "Quantity"))
    
    print("Total Items in Stock {0}".format(quantity))
    
    print("Silver: {0}".format(int(db.hget("ThingDef:Silver", "Quantity"))))