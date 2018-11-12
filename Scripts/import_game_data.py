import json

import config
import lib.consts
from lib.db import get_redis_database_connection
from lib.things.thing import Thing

ok = False
version = None
language_added = False
language = ''
translate_only = False

while not ok:
    version = input('Which version? ')
    language = input('Language: ')
    translate_only = bool(input('Translate only (0/1)? '))
    if version in config.API_DB_CONFIG:
        ok = True

db = get_redis_database_connection(config.API_DB_CONFIG[version])

pipe = db.pipeline()

with open('{}_base_game_data_{}.json'.format(version, language), 'r', encoding='utf-8') as json_file:
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

        if not translate_only:
            thing.save_to_database(pipe)

        if not language_added:
            pipe.sadd(lib.consts.KEY_THING_LOCALE_KNOWN_LANGUAGES, thing_data['LanguageCode'])
            language_added = True

        # Set full name for Thing, Ours is the version of truth, give it a high score.
        pipe.zadd(lib.consts.KEY_THING_LOCALE_THING_NAMES.format(thing_data['LanguageCode'], thing.Hash),
                  thing_data['LocalizedName'], 1000)

count = len(pipe.execute())
print('Wrote {} items'.format(count))
