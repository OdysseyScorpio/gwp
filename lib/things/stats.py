from lib import db, utils

def things_update_stats(thingID, quantity, selling = False):

    rdbi = db.get_db()

    # Did we buy or sell items?
    if(selling):
        mode = "_sold"
    else:
        mode = "_bought"

    # Get the current date in yyyy-mm-dd format.
    current_ts = utils.get_today_date_string()

    # Update the ThingStats for this Thing.
    rdbi.hincrby("Things:Stats:" + current_ts, str(thingID) + mode, quantity)

    # Expire the stats 8 days after last write.
    rdbi.expire("Things:Stats:" + current_ts, 691200)