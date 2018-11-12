"""
Created on 16 Jan 2018

@author: aleyshon
"""

# HTTP Related constants
ERROR_NOT_FOUND = 'Not Found'
ERROR_INTERNAL = 'Internal Server Error'
ERROR_INVALID = 'Invalid Request'
MIME_JSON = 'application/json'
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_INVALID = 400

# Thing keys
KEY_THING_META = 'Things:Metadata:{}'
KEY_THING_LOCALE = 'Things:Locale:{}:{}'
KEY_THING_INDEX = 'Things:Index'
KEY_THING_BASE_MARKET_VALUE_DATA = 'Things:BaseMarketValueData:{}'
KEY_THING_LOCALE_FULL_TEXT_INDEX = 'Things:Locale:FTI:{}'
KEY_THING_LOCALE_THING_NAME = 'Things:Locale:Name:{}:{}'
KEY_THING_LOCALE_THING_NAMES = 'Things:Locale:Names:{}:{}'
KEY_THING_LOCALE_KNOWN_LANGUAGES = 'Things:Locale:Known'


# User keys
KEY_USER_INDEX_BY_ID = 'Users:Indices:ByID'
KEY_USER_INDEX_BY_STEAM_ID = 'Users:Indices:BySteamID'
KEY_USER_INDEX_BY_NORMAL_ID = 'Users:Indices:ByNormalID'
KEY_USER_STEAM = 'Users:Steam:{}'
KEY_USER_NORMAL = 'Users:Normal:{}'

# Colony keys
KEY_COLONY_INDEX_BY_ID = 'Colonies:Indices:ByColonyID'
KEY_COLONY_INDEX_BY_STEAM_ID = 'Colonies:Indices:BySteamID:{}'
KEY_COLONY_INDEX_BY_NORMAL_ID = 'Colonies:Indices:ByNormalID:{}'

KEY_COLONY_METADATA = 'Colonies:Metadata:{}'

# API Status Keys
KEY_API_VERSION = 'Configuration:API:Version'
KEY_API_MAINTENANCE_MODE = 'Configuration:API:Maintenance:Mode'
KEY_API_MAINTENANCE_WINDOW = 'Configuration:API:Maintenance:Window'
HASH_KEY_API_MAINTENANCE_WINDOW_START = 'Start'
HASH_KEY_API_MAINTENANCE_WINDOW_STOP = 'Stop'

# Order keys
KEY_ORDER_INDEX = 'Orders:Index'
KEY_ORDER_MANIFEST = 'Orders:Manifest:{}'
KEY_COLONY_NEW_ORDERS = 'Orders:Colony:{}:Outstanding'
KEY_COLONY_ALL_ORDERS = 'Orders:Colony:{}:All'

# Order Status Constants
ORDER_STATUS_NEW = 'new'
ORDER_STATUS_PROCESSED = 'processed'
ORDER_STATUS_DONE = 'done'
ORDER_STATUS_FAIL = 'failed'
ORDER_STATUS_REVERSE = 'reversed'
ORDER_VALID_STATES = [
    ORDER_STATUS_NEW,
    ORDER_STATUS_PROCESSED,
    ORDER_STATUS_DONE,
    ORDER_STATUS_FAIL
]

# Hourly Counters
KEY_COUNTERS_HOURLY_VOLUME_TRADED = 'Statistics:Counters:Hourly:VolumeTraded:{}'
KEY_COUNTERS_HOURLY_ORDERS = 'Statistics:Counters:Hourly:Orders:{}'
KEY_COUNTERS_HOURLY_COLONIES_ACTIVE = 'Statistics:Counters:Hourly:ColoniesActive:{}'
KEY_COUNTERS_HOURLY_THINGS = 'Statistics:Counters:Hourly:Things:{}:{}'

# Historical Counters
KEY_COUNTERS_HISTORICAL_VOLUME_TRADED = 'Statistics:Counters:Historical:VolumeTraded:{}'
KEY_COUNTERS_HISTORICAL_THING_VOLUME_TRADED_BY_DATE_AND_ACTION = \
    'Statistics:Counters:Historical:Things:VolumeTradedByDateAndAction:{}:{}'
KEY_COUNTERS_HISTORICAL_ORDERS = 'Statistics:Counters:Historical:Orders:{}'

# This key is updated by GlitterBot during maintenance.
# If you really need to know the count do SCARD with KEY_TRENDS_HISTORICAL_COLONIES_ACTIVE_BY_DATE
KEY_COUNTERS_HISTORICAL_COLONIES_ACTIVE = 'Statistics:Counters:Historical:ColoniesActive:{}'

KEY_COUNTERS_HISTORICAL_THINGS_TRADED_BY_DATE = 'Statistics:Counters:Historical:Things:VolumeTradedByDate:{}:{}'

# Trend historical hashes/sets
KEY_TRENDS_HISTORICAL_THING_PRICE_BY_DAY = 'Statistics:Trends:Historical:Things:PriceByDate:{}:{}'
KEY_TRENDS_HISTORICAL_THING_PRICE_BY_WEEK = 'Statistics:Trends:Historical:Things:PriceByWeek:{}:{}:{}'
KEY_TRENDS_HISTORICAL_COLONIES_ACTIVE_BY_DATE = 'Statistics:Trends:Historical:Colonies:Active:ByDate:{}'

# Trend counters

# These are updated nightly.
KEY_TRENDS_COLONIES_BY_TYPE = 'Statistics:Trends:ColoniesByUserType'
KEY_TRENDS_COLONIES_BY_HOUR = 'Statistics:Trends:ColoniesActiveByHour:{}'
KEY_TRENDS_COLONIES_BY_WEEKDAY = 'Statistics:Trends:ColoniesActiveByWeekday:{}'

# These are updated adhoc
KEY_TRENDS_VOLUME_TRADED_BY_HOUR = 'Statistics:Trends:VolumeTradedByHour:{}'
KEY_TRENDS_ORDERS_BY_HOUR = 'Statistics:Trends:OrdersPlacedByHour:{}'

# Total Counters
KEY_TOTAL_ORDERS = 'Statistics:Totals:Orders'
KEY_TOTAL_BUY_OR_SELL = 'Statistics:Totals:{}'
KEY_TOTAL_BOUGHT = 'Statistics:Totals:Bought'
KEY_TOTAL_SOLD = 'Statistics:Totals:Sold'

# Bucket Keys
KEY_BUCKET_COLONIES_ACTIVE = 'Statistics:Bucket:ColoniesActive'

# Cache keys

# ZSET of Hash: Qty
KEY_BUCKET_MOST_TRADED_CURRENT_HOUR = 'Statistics:Bucket:VolumeTradedThisHourByAction:{}'
KEY_BUCKET_MOST_TRADED_CURRENT_LAST_UPDATED = 'Statistics:Bucket:VolumeTradedThisHourByAction:{}:LastUpdated'


# Prime configuration data
KEY_CONFIGURATION_PRIME_COST = 'Configuration:Prime:CostPerInterval'
KEY_CONFIGURATION_PRIME_INTERVAL = 'Configuration:Prime:Interval'
KEY_PRIME_SUBSCRIPTION_DATA = 'Prime:Subscribed:{}'
KEY_CONFIGURATION_ORDERS = 'Configuration:Orders'
HASH_KEY_ORDER_TICK_DELAY = 'TicksNeededForDelivery'

# Glitterbot Specific
KEY_GLITTERBOT_DATA = "Configuration:GlitterBot"
KEY_GLITTERBOT_PRICEBREAKS = "PriceBreaks"
KEY_GLITTERBOT_MTIME_START = "Maintenance_Window_Start_Hour"
KEY_GLITTERBOT_MTIME_LENGTH = "Maintenance_Window_Length"
KEY_GLITTERBOT_MTIME_NEXT = "Maintenance_Next_Run"
KEY_GLITTERBOT_MTIME_PREABMLE = "Maintenance_Window_Preamble"
KEY_GLITTERBOT_MTIME_SET = "Maintenance_Window_Set"
KEY_GLITTERBOT_HAS_RUN = "Maintenance_Has_Run"
KEY_GLITTERBOT_BUY_PRICE_MULTIPLIER = "BuyPriceMultiplier"
KEY_GLITTERBOT_SELL_PRICE_MULTIPLIER = 'SellPriceReductionMultiplier'
KEY_GLITTERBOT_MIN_SELL_PRICE_MULTIPLIER = 'MinPriceReductionMultiplier'
KEY_GLITTERBOT_SALE_DATA = 'Configuration:GlitterBot:Sales:{}'
KEY_GLITTERBOT_IGNORE_THINGS = 'IgnoredThingIDs'

# Handy shortcuts
WELLKNOWN_THINGS_SILVER = '8697f432058b914ba2b20c5bd6f0678548126e21'
