import gzip
from flask import Blueprint, Response, request, current_app,  make_response, json

import lib.gwpcc.orders.stats as order_stats
import lib.gwpcc.orders.utils as order_utils
import lib.gwpcc.things.stats as thing_stats
import lib.gwpcc.things.stock as stock_control
from lib import db
from lib.gwpcc import consts
from lib.gwpcc.colonies.colony import Colony
from lib.gwpcc.orders.order import Order
from lib.gwpcc.qevent.event import send
from lib.gwpcc.qevent.messages.order import OrderMessage
from lib.gwpcc.things.order_thing import OrderThing
from lib.gwpcc.things.thing import Thing

order_module = Blueprint('v4_prime_orders', __name__, url_prefix='/v4/orders')


@order_module.route('/<string:colony_hash>', methods=['GET'])
def get_orders(colony_hash):
    print("Sending orders for colony to colony")
    connection = db.get_redis_db_from_context()
    response = dict()

    colony = Colony.get_from_database_by_hash(colony_hash, db.get_redis_db_from_context())

    ####
    # WE DON'T NEED A SUBSCRIPTION TO GET THE ORDER LIST
    ####

    if colony is None:
        print("Colony does not exist in db")
        return Response(consts.ERROR_NOT_FOUND, status=consts.ERROR_NOT_FOUND)

    if colony.IsBanned():
        print("Colony is banned in db")
        return Response(consts.ERROR_BANNED, status=consts.HTTP_FORBIDDEN)

    current_tick = request.args.get('tick')

    if current_tick is None:
        print("Colony tick is not present in request")
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    current_tick = int(current_tick)

    # Prevent market manipulation.
    order_utils.anti_time_warp_check(colony, current_tick, connection)

    # Construct dict of orders.

    orders = list(connection.lrange(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), 0, -1))

    order_data = Order.get_many_from_database(orders, connection)

    return_list = [order.to_dict(just_headers=True) for order in order_data.values() if
                   order.Status in [consts.ORDER_STATUS_NEW, consts.ORDER_STATUS_PROCESSED]]

    response['Orders'] = return_list

    colony.ping()

    colony.save_to_database()
    print("Orders sent")
    return Response(json.dumps(response), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)


@order_module.route('/<string:colony_hash>', methods=['PUT'])
def place_order(colony_hash):
    print("Received order request from colony")
    connection = db.get_redis_db_from_context()

    colony = Colony.get_from_database_by_hash(colony_hash, db.get_redis_db_from_context())

    if colony is None:
        print("Colony does not exist in db")
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    if colony.IsBanned():
        print("Colony is banned in db")
        return Response(consts.ERROR_BANNED, status=consts.HTTP_FORBIDDEN)

    ####
    # WE MUST HAVE A SUBSCRIPTION TO PLACE AN ORDER
    ####

    if not colony.HasActiveSubscription():
        print("Colony does not have activ subscription")
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    gz_post_data = request.files['order']

    # Decompress payload
    compressed_order = gzip.GzipFile(fileobj=gz_post_data, mode='r')

    # Deserialize JSON
    payload = json.loads(compressed_order.read().decode('UTF8'))

    # Check if these OrderThings exist in database.
    things_sold_to_gwp = OrderThing.many_from_dict_and_check_exists(payload['ThingsSoldToGwp'], connection)
    things_bought_from_gwp = OrderThing.many_from_dict_and_check_exists(payload['ThingsBoughtFromGwp'], connection)

    # We need to create any Things that don't exist so they can be updated later.
    # Things are created with zero quantity and will be updated when the order is done.
    create_missing_things = connection.pipeline()
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

    json_thing_bought = [order_thing.to_dict(keep_quantity=True) for order_thing in things_bought_from_gwp.values()]
    json_thing_sold = [order_thing.to_dict(keep_quantity=True) for order_thing in things_sold_to_gwp.values()]

    order = Order(colony.Hash,
                  connection=connection,
                  OrderedTick=int(payload['CurrentGameTick']),
                  ThingsBoughtFromGwp=json.dumps(json_thing_bought),
                  ThingsSoldToGwp=json.dumps(json_thing_sold),
                  DeliveryTick=int(
                      int(payload['CurrentGameTick']) + order_utils.get_ticks_needed_for_delivery(connection)))

    pipe = connection.pipeline()
    stock_control.give_things_to_colony(colony.Hash, things_bought_from_gwp.values(), pipe)
    stock_control.receive_things_from_colony(colony.Hash, things_sold_to_gwp.values(), pipe)
    pipe.execute()

    # Update database
    order.save_to_database(connection)
    order_stats.increment_order_counter(connection)
    order_stats.update_orders_placed_by_hour(connection)
    colony.ping()

    # Try to send message to queue.
    try:
        message = OrderMessage.prepare(db.get_market_name(), things_bought_from_gwp, things_sold_to_gwp, colony)
        send(message, connection)
        print("Message sent to queue")
    except Exception:
        print("An error in sending to message to queue")
        print(Exception)
        pass  # IDGAF
    
    print("Order created")
    return Response(json.dumps("OK"), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)


@order_module.route('/<string:colony_hash>/<string:order_hash>', methods=['POST'])
def update_order(colony_hash, order_hash):
    print("Received update order request")
    connection = db.get_redis_db_from_context()

    ####
    # WE DON'T NEED A SUBSCRIPTION TO UPDATE THE ORDER STATUS
    ####

    pipe = connection.pipeline()

    colony = Colony.get_from_database_by_hash(colony_hash, connection)

    if not colony:
        print("Colony does not exist in db")
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    if colony.IsBanned():
        print("Colony is banned in db")
        return Response(consts.ERROR_BANNED, status=consts.HTTP_FORBIDDEN)

    order = Order.get_from_database_by_hash(order_hash, connection)

    if not order:
        print("Order not found in db")
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    if (request.json('Status')):
        new_status = request.json['Status']

        # Check that the state is not going backwards or is invalid.
        if new_status in consts.ORDER_VALID_STATES:
            if check_order_state_is_valid(order, new_status):
                order.Status = new_status
            else:
                return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)
        else:
            print("Order invalid")
<<<<<<< HEAD
            return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)
    elif (request.json('DeliveryTick')):
        try:
            update_DeliveryTick = int(request.json['DeliveryTick'])
            order.DeliveryTick = update_DeliveryTick
        except:
=======
>>>>>>> 5ac3457 (Added logging)
            return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)
    else:
        print("Order invalid")
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    if order.Status == consts.ORDER_STATUS_FAIL:
        # Remove order from list of new orders.
        pipe.lrem(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), 0, order.Hash)

    elif order.Status == consts.ORDER_STATUS_DONE:
        # Remove order from list of new orders.
        pipe.lrem(consts.KEY_COLONY_NEW_ORDERS.format(colony.Hash), 0, order.Hash)

        # Deserialize JSON back into OrderThings
        things_sold_to_gwp = [OrderThing.from_dict(saved_thing) for saved_thing in
                              (order.ThingsSoldToGwp if type(order.ThingsSoldToGwp) == list else '[]')]

        things_bought_from_gwp = [OrderThing.from_dict(saved_thing) for saved_thing in
                                  (order.ThingsBoughtFromGwp if type(order.ThingsBoughtFromGwp) == list else '[]')]

        # Update bucket timestamp and clear if needed.
        thing_stats.reset_thing_traded_stats_bucket(connection)

        # Update statistics for things being sold.
        for order_thing in things_sold_to_gwp:
            thing_stats.update_stats_for_sold_thing(order_thing, order_thing.Quantity, pipe)

        for order_thing in things_bought_from_gwp:
            thing_stats.update_stats_for_bought_thing(order_thing, order_thing.Quantity, pipe)

    order.save_to_database(pipe)

    colony.ping()

    pipe.execute()
    print("Order updated")
    return Response(json.dumps("OK"), status=consts.HTTP_OK, mimetype=consts.MIME_JSON)


@order_module.route('/<string:colony_hash>/<string:order_hash>', methods=['GET'])
def get_order(colony_hash, order_hash):
    print("Getting order for colony")
    connection = db.get_redis_db_from_context()
    colony = Colony.get_from_database_by_hash(colony_hash, connection)

    ####
    # WE DON'T NEED A SUBSCRIPTION TO GET THE ORDER STATUS
    ####

    if not colony:
        print("Colony does not exist in db")
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_INVALID)

    order = Order.get_from_database_by_hash(order_hash, connection)
    if not order:
        print("Order does not exist in db")
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

    # Deserialize the Things Sold/Bought so they can be correctly re-serialized as dicts not JSON strings.
    order.ThingsSoldToGwp = order.ThingsSoldToGwp if type(order.ThingsSoldToGwp) == list else '[]'
    order.ThingsBoughtFromGwp = order.ThingsBoughtFromGwp if type(order.ThingsBoughtFromGwp) == list else '[]'

    colony.ping()

    content = gzip.compress(json.dumps(order.to_dict().encode('utf8'), 5))
    response = make_response(content)
    response.headers['Content-length'] = len(content)
    response.headers['Content-Encoding'] = 'gzip'
    print("Order sent to colony")
    return response

def check_order_state_is_valid(order, new_status):
    if order.Status == 'new':
        allowed_statuses = ['processed', 'failed']
    elif order.Status == 'processed':
        allowed_statuses = ['done', 'failed']
    else:
        return False

    if new_status in allowed_statuses:
        return True
    else:
        return False
