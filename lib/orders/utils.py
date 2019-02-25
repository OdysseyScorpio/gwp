import lib.things.stock
from lib import db, consts
from lib.colonies.colony import Colony
from lib.consts import KEY_CONFIGURATION_ORDERS, HASH_KEY_ORDER_TICK_DELAY
from lib.orders.order import Order
from lib.things.order_thing import OrderThing


def get_ticks_needed_for_delivery():
    db_connection = db.get_redis_db_from_context()

    value = int(db_connection.hget(KEY_CONFIGURATION_ORDERS, HASH_KEY_ORDER_TICK_DELAY))

    return value


def anti_time_warp_check(colony, current_game_tick):
    # Test to see if the current tick is EARLIER than the last time we received a game tick.
    # This usually means they warped back in time due to an earlier game save.  
    if current_game_tick < colony.LastGameTick:
        # We need to undo any orders pending or delivered since the "new" game tick.
        colony.Timewarps += 1

        # Undo all the items added to the market by transactions made after this tick.
        rollback_orders_since_tick(colony, current_game_tick)

    colony.LastGameTick = current_game_tick


def rollback_orders_since_tick(colony: Colony, tick):
    db_connection = db.get_redis_db_from_context()

    pipe = db_connection.pipeline()

    # Get all orders in the list.
    orders_hashes = db_connection.lrange(consts.KEY_COLONY_ALL_ORDERS.format(colony.Hash), 0, -1)

    orders = Order.get_many_from_database(orders_hashes)

    for order in orders.values():

        if order.OrderedTick > tick:

            # If the transaction completed, we need to undo it.
            # if order.Status == consts.ORDER_STATUS_DONE:
                # Get things to add/remove from GWP.
                # things_to_remove_from_gwp = OrderThing.from_dict_and_check_exists(json.loads(order.ThingsSoldToGwp))

            # Always re-add stock that was bought.
            things_bought_from_gwp = [OrderThing.from_dict(saved_thing) for saved_thing in
                                      order.ThingsBoughtFromGwp]
            lib.things.stock.receive_things_from_colony(colony.Hash, things_bought_from_gwp)

            # We don't remove things from GWP anymore if they time warp, we'll just keep hold of them.
            # for thing in things_to_remove_from_gwp:
            #     # Add namespace to item name to form Key

            things_sold_to_gwp = [OrderThing.from_dict(saved_thing) for saved_thing in
                                  order.ThingsSoldToGwp]

            lib.things.stock.give_things_to_colony(colony.Hash, things_sold_to_gwp)

            # Mark it reversed
            order.Status = consts.ORDER_STATUS_REVERSE

            # Remove it from the colonies processing list.
            pipe.lrem(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), 0, order.Hash)

            order.save_to_database(pipe)

    pipe.execute()
