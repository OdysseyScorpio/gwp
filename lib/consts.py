'''
Created on 16 Jan 2018

@author: aleyshon
'''

ERROR_NOT_FOUND = 'Not Found'
ERROR_INTERNAL = 'Internal Server Error'
ERROR_INVALID = 'Invalid Request'

MIME_JSON = 'application/json'

HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_INVALID = 400

# Database keys
KEY_COLONY_MAP = 'ColonyData:Mapping'
KEY_COLONY_DATA = 'Colony:%s:Data'

KEY_ORDER_DATA = 'Orders:Data:%s'
KEY_ORDER_MAP = 'Orders:Mapping'

KEY_COLONY_NEW_ORDERS = 'Orders:Colony:New:%s'
KEY_COLONY_ALL_ORDERS = 'Orders:Colony:All:%s'

ORDER_STATUS_NEW = 'new'
ORDER_STATUS_PROCESSED = 'processed'
ORDER_STATUS_DONE = 'done'
ORDER_STATUS_FAIL = 'failed'
ORDER_STATUS_REVERSE = 'reversed'

# Price override keys

# JSON Dict of ThingID and Sell Price
KEY_COLONY_PRICE_PENALTIES = 'Colony:%s:PricingPenalties'

KEY_ORDER_CONFIG = 'Orders:Configuration'
KEY_ORDER_TICKDELAY = 'TicksNeededForDelivery'
