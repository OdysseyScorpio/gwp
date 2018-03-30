from flask import Blueprint, Response, request
from lib import consts
from lib.things import stock, utils
from lib import colony

import json, gzip

'''This module is to provide backwards compatibility with API versions < 2.1'''
'''Support for this is no longer provided'''

market_module = Blueprint('prime_market', __name__, url_prefix='/market')

@market_module.route('/get_items', methods = ['POST'])
def market_get_items():

    if 'things' not in request.files:
        requestedItems = request.json
    else:
        gfile = request.files['things']
        thingFile = gzip.GzipFile(fileobj = gfile, mode = 'r')
        requestedItems = json.loads(thingFile.read().decode('UTF8'))

    itemsToReturn = []

    for item in requestedItems:
        redisResult = utils.try_get_thing('ThingDef:' + item)
        if redisResult:
            itemsToReturn.append(redisResult)

    return Response(json.dumps(itemsToReturn), mimetype = 'application/json')


@market_module.route('/sell_items', methods = ['POST'])
def market_sell_items():

    soldItems = request.json

    colonyId = colony.manage.get_colony_id_from_uuid(soldItems['ColonyID'])

    # For each item sent in the JSON payload
    for item in soldItems['Things']:

        # Add namespace to item name to form Key
        itemKey = 'ThingDef:' + item['Name']

        # Add Stuff
        if('StuffType' in item and item['StuffType'] != ''):
            itemKey = itemKey + ":" + item['StuffType']

        # Then quality
        if('Quality' in item and item['Quality'] != ''):
            itemKey = itemKey + ":" + item['Quality']

        wasOK = stock.sell_item_from_stock(itemKey, item)
        
        if(not wasOK):
            Response(consts.ERROR_INVALID, status = 400)
        
        colony.manage.update_colony_sell_stats(colonyId, item['ThingID'], item['Quantity'])
        
    colony.manage.set_colony_login_flag(colonyId)

    return Response(json.dumps("OK"))


@market_module.route('/buy_items', methods = ['POST'])
def market_buy_items():

    boughtItems = request.json

    colonyId = colony.manage.get_colony_id_from_uuid(boughtItems['ColonyID'])

    # For each item sent in the JSON payload
    for item in boughtItems['Things']:

        if(not utils.validate_item_schema(item)):
            return Response(consts.ERROR_INVALID, status = 400)

        # Add namespace to item name to form Key
        itemKey = 'ThingDef:' + item['Name']

        # Add Stuff
        if('StuffType' in item and item['StuffType'] != ''):
            itemKey = itemKey + ":" + item['StuffType']

        # Then quality
        if('Quality' in item and item['Quality'] != ''):
            itemKey = itemKey + ":" + item['Quality']

        itemData = stock.add_item_to_stock(itemKey, item)

        colony.manage.update_colony_purchase_stats(colonyId, itemData['ThingID'], itemData['Quantity'])

    colony.manage.set_colony_login_flag(colonyId)

    return Response(json.dumps("OK"))