from flask import Blueprint, Response, request
from lib import consts
from lib import colony
import lib.colony.manage as colonymanage
import lib.things.utils as thingutils
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

    itemsToReturn = thingutils.mass_try_get_things(requestedItems)    

#     for item in requestedItems:
#         redisResult = thingutils.try_get_thing('ThingDef:' + item)
#         if redisResult:
#             itemsToReturn.append(redisResult)

    return Response(json.dumps(itemsToReturn), mimetype = 'application/json')


@market_module.route('/sell_items', methods = ['POST'])
def market_sell_items():

    soldItems = request.json

    colonyId = colony.manage.get_colony_id_from_uuid(soldItems['ColonyID'])

    # For each item sent in the JSON payload
    for item in soldItems['Things']:
        if(not thingutils.validate_item_schema(item)):
            return Response(consts.ERROR_INVALID, status = 400)

    thingutils.give_things_to_colony(colonyId, soldItems['Things'])
        
    colonymanage.set_colony_login_flag(colonyId)

    return Response(json.dumps("OK"))


@market_module.route('/buy_items', methods = ['POST'])
def market_buy_items():

    boughtItems = request.json

    colonyId = colony.manage.get_colony_id_from_uuid(boughtItems['ColonyID'])

    # For each item sent in the JSON payload
    for item in boughtItems['Things']:
        if(not thingutils.validate_item_schema(item)):
            return Response(consts.ERROR_INVALID, status = 400)

    thingutils.sell_things_from_colony(colonyId, boughtItems['Things'])

    colonymanage.set_colony_login_flag(colonyId)

    return Response(json.dumps("OK"))