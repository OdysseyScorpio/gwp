from lib import db, consts

def things_update_price_history(thingID, price):

    rdbi = db.get_db()

    keyName = 'Things:PriceHistory:' + str(thingID)

    rdbi.rpush(keyName, price)
    
def get_colony_price_overrides(colonyID):
    
    rdbi = db.get_db()

    jsonData = rdbi.get(consts.KEY_COLONY_PRICE_PENALTIES % colonyID)
    
    if(jsonData == ''):
        return None
    