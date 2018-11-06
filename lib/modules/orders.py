import json

from flask import Blueprint, Response, request, current_app

import lib.orders.stats as order_stats
import lib.orders.utils as order_utils
import lib.things.stats as thing_stats
import lib.things.stock as stock_control
from lib import consts, db
from lib.colonies.colony import Colony
from lib.orders.order import Order
from lib.qevent.event import send
from lib.qevent.messages.order import OrderMessage
from lib.things.order_thing import OrderThing
from lib.things.thing import Thing

order_module = Blueprint('v3_prime_orders', __name__, url_prefix='/v3/orders')


@order_module.route('/<string:colony_hash>', methods=['GET'])
def get_orders(colony_hash):
    db_connection = db.get_redis_db_from_context()
    response = dict()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if colony is None:
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    current_tick = request.args.get('tick')

    if current_tick is None:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    current_tick = int(current_tick)

    # Prevent market manipulation.
    order_utils.anti_time_warp_check(colony, current_tick)

    # Construct dict of orders.

    orders = list(db_connection.lrange(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), 0, -1))

    order_data = Order.get_many_from_database(orders)

    return_list = [order.to_dict(just_headers=True) for order in order_data.values() if
                   order.Status in [consts.ORDER_STATUS_NEW, consts.ORDER_STATUS_PROCESSED]]

    response['Orders'] = return_list

    colony.ping()

    colony.save_to_database()

    return Response(json.dumps(response), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)


@order_module.route('/<string:colony_hash>', methods=['PUT'])
def place_order(colony_hash):
    db_connection = db.get_redis_db_from_context()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if colony is None:
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    request_data = request.json

    # Check if these OrderThings exist in database.
    things_sold_to_gwp = OrderThing.many_from_dict_and_check_exists(request_data['ThingsSoldToGwp'])
    things_bought_from_gwp = OrderThing.many_from_dict_and_check_exists(request_data['ThingsBoughtFromGwp'])

    # We need to create any Things that don't exist so they can be updated later.
    # Things are created with zero quantity and will be updated when the order is done.
    create_missing_things = db_connection.pipeline()
    for thing_hash, order_thing in things_sold_to_gwp.items():
        if not order_thing.ThingExists:
            thing = Thing.from_dict(order_thing.to_dict())
            current_app.logger.warning('Seen {} for the first time, Saving to database'.format(thing))
            thing.save_to_database(create_missing_things)

    for thing_hash, order_thing in things_bought_from_gwp.items():
        if not order_thing.ThingExists:
            # This should never happen, they wouldn't be able to buy it since the Quantity would be zero.
            # But still just to be safe.
            thing = Thing.from_dict(order_thing.to_dict())
            current_app.logger.warning('User bought {} that was not in the database'.format(thing))
            thing.save_to_database(create_missing_things)

    create_missing_things.execute()

    order = Order(
        colony.Hash,
        OrderedTick=int(request_data['CurrentGameTick']),
        ThingsBoughtFromGwp=json.dumps(
            [order_thing.to_dict(keep_quantity=True) for order_thing in things_bought_from_gwp.values()]),
        ThingsSoldToGwp=json.dumps(
            [order_thing.to_dict(keep_quantity=True) for order_thing in things_sold_to_gwp.values()]),
        DeliveryTick=int(int(request_data['CurrentGameTick']) + order_utils.get_ticks_needed_for_delivery())
    )

    # Update database
    order.save_to_database(db_connection)
    order_stats.increment_order_counter()
    order_stats.update_orders_placed_by_hour()
    colony.ping()

    # Try to send message to queue.
    try:
        message = OrderMessage.prepare(db.get_market_name(), things_bought_from_gwp, things_sold_to_gwp, colony)
        send(message)
    except Exception:
        pass  # IDGAF

    return Response(json.dumps("OK"), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)


@order_module.route('/<string:colony_hash>/<string:order_hash>', methods=['POST'])
def update_order(colony_hash, order_hash):
    db_connection = db.get_redis_db_from_context()

    pipe = db_connection.pipeline()

    colony = Colony.get_from_database_by_hash(colony_hash)

    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    order = Order.get_from_database_by_hash(order_hash)

    if not order:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    status = request.json['Status']

    if status in consts.ORDER_VALID_STATES:
        order.Status = status
    else:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    if status == consts.ORDER_STATUS_FAIL:
        # Remove order from list of new orders.
        pipe.lrem(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), order.Hash, 0)

    elif status == consts.ORDER_STATUS_DONE:
        # Remove order from list of new orders.
        pipe.lrem(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), order.Hash, 0)

        # Deserialize JSON back into OrderThings
        things_sold_to_gwp = [OrderThing.from_dict(saved_thing) for saved_thing in
                              json.loads(order.ThingsSoldToGwp)]
        things_bought_from_gwp = [OrderThing.from_dict(saved_thing) for saved_thing in
                                  json.loads(order.ThingsBoughtFromGwp)]

        stock_control.receive_things_from_colony(colony.Hash, things_sold_to_gwp, pipe)
        stock_control.give_things_to_colony(colony.Hash, things_bought_from_gwp, pipe)

        # Update statistics for things being sold.
        for order_thing in things_sold_to_gwp:
            thing_stats.update_stats_for_sold_thing(order_thing, order_thing.Quantity, pipe)

        for order_thing in things_bought_from_gwp:
            thing_stats.update_stats_for_bought_thing(order_thing, order_thing.Quantity, pipe)

    order.save_to_database(pipe)

    colony.ping()

    pipe.execute()

    return Response(json.dumps("OK"), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)


@order_module.route('/<string:colony_hash>/<string:order_hash>', methods=['GET'])
def get_order(colony_hash, order_hash):
    colony = Colony.get_from_database_by_hash(colony_hash)
    if not colony:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_INVALID)

    order = Order.get_from_database_by_hash(order_hash)
    if not order:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    # Deserialize the Things Sold/Bought so they can be correctly re-serialized as dicts not JSON strings.
    order.ThingsSoldToGwp = json.loads(order.ThingsSoldToGwp)
    order.ThingsBoughtFromGwp = json.loads(order.ThingsBoughtFromGwp)

    colony.ping()

    return Response(json.dumps(order.to_dict()), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)
