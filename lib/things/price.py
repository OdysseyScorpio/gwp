from lib import db

def things_update_price_history(thingID, price):

    rdbi = db.get_db()

    keyName = 'Things:PriceHistory:' + str(thingID)

    rdbi.rpush(keyName, price)