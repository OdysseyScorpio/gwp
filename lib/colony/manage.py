from lib import db, utils
from datetime import datetime

def get_colony_id_from_uuid(colonyId):

    rdbi = db.get_db()

    return rdbi.hget("ColonyData:Mapping", colonyId)

def set_colony_login_flag(colonyId):

    rdbi = db.get_db()

    colonyKey = 'Colony:' + colonyId + ':Data'

    rdbi.hset(colonyKey, 'LastLogin', datetime.utcnow().timestamp())

    # Build cache key string.
    usageBitKey = "ColonyUsage:" + utils.get_today_date_string()

    # Set the bit at the offset ColonyID to 1
    rdbi.setbit(usageBitKey, colonyId, 1)
    
def update_colony_purchase_stats(colonyId, thingId, quantity):
    
    rdbi = db.get_db()
    
    colonyCounterKey = 'Colony:' + colonyId + ':ThingsBought'
    
    # Update individual colony purchase stats
    rdbi.hincrby(colonyCounterKey, thingId, quantity)
    
def update_colony_sell_stats(colonyId, thingId, quantity):
    
    rdbi = db.get_db()
    
    colonyCounterKey = 'Colony:' + colonyId + ':ThingsSold'
    
    # Increment individual colony purchase stats
    rdbi.hincrby(colonyCounterKey, thingId, quantity)
    