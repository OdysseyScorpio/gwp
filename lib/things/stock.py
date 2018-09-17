from lib import consts
from lib import db


def update_thing_stock(thing_hash, quantity):
    """
    Immediately updates item stock, No pipelining.
    :param thing_hash: Hash of the Thing to update.
    :param quantity: Positive increases stock, negative subtracts.
    """

    db_connection = db.get_redis_db_from_context()

    db_connection.hincrby(consts.KEY_THING_META.format(thing_hash), 'Quantity', quantity)


def receive_things_from_colony(colony_hash, list_of_things: list):
    # For each item sent in the JSON payload
    for thing in list_of_things:
        update_thing_stock(thing.Hash, thing.Quantity)


def give_things_to_colony(colony_hash, list_of_things: list):
    # For each item sent in the JSON payload
    for thing in list_of_things:
        update_thing_stock(thing.Hash, (0 - thing.Quantity))
