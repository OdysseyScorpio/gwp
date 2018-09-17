# def things_update_price_history(thing_id, price):
#     db_connection = db.get_redis_db_from_context()
#
#     key_name = 'Things:PriceHistory:' + str(thing_id)
#
#     db_connection.rpush(key_name, price)


# def get_colony_price_overrides(colony_id):
#     db_connection = db.get_redis_db_from_context()
#
#     json_data = db_connection.get(consts.KEY_COLONY_PRICE_PENALTIES % colony_id)
#
#     if json_data == '':
#         return None
