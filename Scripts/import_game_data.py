import json

import config
from lib.db import get_redis_database_connection
from lib.things.thing import Thing

ok = False
version = None

while not ok:
    version = input('Which version? ')
    if version in config.API_DB_CONFIG:
        ok = True

db = get_redis_database_connection(config.API_DB_CONFIG[version])

pipe = db.pipeline()

with open('{}_base_game_data.json'.format(version), 'r') as json_file:
    json_data = json.load(json_file)

    for thing_data in json_data:

        # Don't add poor quality stuff to DB
        if 'Quality' in thing_data and thing_data['Quality'] == "Poor":
            continue

        thing = Thing.from_dict(
            {
                'Name': thing_data['Name'],
                'Quality': thing_data['Quality'] if thing_data['Quality'] is not None else "",
                'StuffType': thing_data['StuffType'] if thing_data['StuffType'] is not None else "",
                'BaseMarketValue': thing_data['BaseMarketValue'],
                'MinifiedContainer': thing_data['MinifiedContainer'],
                'UseServerPrice': True,
                'CurrentBuyPrice': thing_data['BaseMarketValue'],
                'CurrentSellPrice': thing_data['BaseMarketValue']
            })
        thing.save_to_database(pipe)

count = pipe.execute()
print('Wrote {} items'.format(count))
