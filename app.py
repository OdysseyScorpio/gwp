from flask import Flask, Response, g, request
from flask_compress import Compress
import json, redis, gzip
import uuid
import datetime

app = Flask(__name__)

app.config.update(
        DEBUG=False,
        PROPAGATE_EXCEPTIONS=True
        )

# Turn on HTTP Compression
Compress(app)

# Returns a valid, connected Redis object 
def get_db():
    # Check to see if we've already opened a database
    db = getattr(g, '_database', None)
    if db is None:
        # If not, open and connect to the database, Decode responses in UTF-8 (default)
        db = g._database = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    return db

def key_is_in_item(item, value):
    
    return (value in item)

def validate_item_schema(item):
    objectSchema = ['Name', 'BaseMarketValue', 'CurrentPrice', 'Quantity', 'StuffType', 'MinifiedContainer']
    for schemaValue in objectSchema:
        if not key_is_in_item(item, schemaValue):
            print('Item {0} is broken!'.format(json.dumps(item)))
            return False
    
    return True

@app.route('/market/get_items', methods=['POST'])
def market_get_items():
    
    if 'things' not in request.files:
        requestedItems = request.json    
    else:
        gfile = request.files['things']
        thingFile = gzip.GzipFile(fileobj=gfile, mode='r')
        requestedItems = json.loads(thingFile.read().decode('UTF8'))
        
    itemsToReturn = []
    
    for item in requestedItems:
        redisResult = try_get_thing('ThingDef:' + item)
        if redisResult:
            itemsToReturn.append(redisResult)
            
    return Response(json.dumps(itemsToReturn), mimetype='application/json')

@app.route('/market/sell_items', methods=['POST'])
def market_sell_items():
    
    db = get_db()
    
    soldItems = request.json    

    colonyID = get_colony_id_from_uuid(soldItems['ColonyID'])

    colonyCounterKey = 'Colony:' + colonyID + ':ThingsSold' 

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
            
        # Request Key from Redis
        itemData = try_get_thing(itemKey)
        
        # Did we find the Key?
        if not itemData is None:
            
            # Add thing ID if there isn't one.
            if not 'ThingID' in itemData:
                itemData['ThingID'] = thing_generate_id(itemKey)
                db.hset(itemKey, "ThingID", itemData['ThingID'])
                
            # Decrement the quantity that was bought from stock
            db.hincrby(itemKey, 'Quantity', -item['Quantity'])
            
            # Update individual colony purchase stats
            db.hincrby(colonyCounterKey, itemData['ThingID'], item['Quantity'])
                              
            # Update ThingStats
            things_update_stats(itemData['ThingID'], item['Quantity'], True)
        else:
            
            # Couldn't locate Key in DB, something is wrong...
            print("We sold something we never had in the first place: Item was " + itemKey)
            return Response("ThingDef was not found", status=500)
    
    return Response(json.dumps("OK"))

@app.route('/market/buy_items', methods=['POST'])
def market_buy_items():
    
    db = get_db()
    
    boughtItems = request.json
    
    colonyID = get_colony_id_from_uuid(boughtItems['ColonyID'])

    colonyCounterKey = 'Colony:' + colonyID + ':ThingsBought' 

    # For each item sent in the JSON payload
    for item in boughtItems['Things']:
        
        if(not validate_item_schema(item)):
            return Response("Item schema is invalid", status=500)
        
        # Add namespace to item name to form Key
        itemKey = 'ThingDef:' + item['Name']
        
        # Add Stuff
        if('StuffType' in item and item['StuffType'] != ''):
            itemKey = itemKey + ":" + item['StuffType']
         
        # Then quality
        if('Quality' in item and item['Quality'] != ''):
            itemKey = itemKey + ":" + item['Quality']
                
        # Request Key from Redis
        itemData = try_get_thing(itemKey)
        
        newItem = dict(item)
        
        # Did we find the Key?
        if itemData is not None:

            # Add thing ID if there isn't one.
            if not 'ThingID' in itemData:
                newItem['ThingID'] = thing_generate_id(itemKey)
            else:
                newItem['ThingID'] = db.hget(itemKey, 'ThingID')
            
            # Increment the quantity in stock
            db.hincrby(itemKey, 'Quantity', item['Quantity'])
            
            # Increment individual colony purchase stats
            db.hincrby(colonyCounterKey, newItem['ThingID'], item['Quantity'])
            
            # Remove quantity from Dict so we don't overwrite it in the next step
            if 'Quantity' in newItem:
                del newItem['Quantity']
           
        else: 
            # This is a new Thing so get an ID.
            newItem['ThingID'] = thing_generate_id(itemKey)
            
            # Increment individual colony purchase stats
            db.hincrby(colonyCounterKey, newItem['ThingID'], item['Quantity'])  
        
        if 'UseServerPrice' in newItem:
            del newItem['UseServerPrice']
        
        # Set the Values of the Key
        db.hmset(itemKey, newItem)
        
        # Update Price History
        things_update_price_history(newItem['ThingID'], newItem['BaseMarketValue'])
        
        # Update ThingStats
        things_update_stats(newItem['ThingID'], item['Quantity'], False)

    return Response(json.dumps("OK"))

@app.route('/colony/generate_id', methods=['GET'])
def colony_generate_id():
    
    db = get_db()  

    # Increment the Colony Counter
    colonyID = db.incr("ColonyData:Counter")
    
    while True:
    
        # Generate a UUID
        newuuid = uuid.uuid4()
        colonyUUID = str(newuuid)
    
        # Check to see if the Colony UUID is in use (Highly Doubtful)
        uuidExists = db.hexists('ColonyData:Mapping', colonyUUID)
        colonyData = {"UUID": colonyUUID}
        print(uuidExists)
        if not (uuidExists):
            db.hset('ColonyData:Mapping', colonyUUID, colonyID)
            break
       
    return Response(json.dumps(colonyData), status=200, mimetype='application/json')

@app.route('/colonies/<string:colony_uuid>', methods=['PUT'])
def colony_set_data(colony_uuid):
    
    db = get_db()
    
    colony_data = request.json
    
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response("Invalid Colony UUID", status=404)
    
    # Check the Colony exists
    colonyID = db.hget('ColonyData:Mapping', colonySafeUUID)
    if colonyID is None:
        return Response("Colony does not exist", status=404)
    
    # Set all the values passed in the payload to Redis. 
    # Maybe I should change this... Seems a little dangerous.
    redisKey = 'Colony:' + colonyID + ':Data'
    
    colony_data['LastLogin'] = datetime.datetime.utcnow().timestamp()
    
    db.hmset(redisKey, colony_data)
    
    # Build cache key string.
    usageBitKey = "ColonyUsage:" + get_today_date_string()
    
    # Set the bit at the offset ColonyID to 1
    db.setbit(usageBitKey, colonyID, 1)
    
    return Response("OK", status=200)

@app.route('/colonies/<string:colony_uuid>', methods=['GET'])
def colony_get_data(colony_uuid):
    
    db = get_db()
        
    # Check the colony UUID provided is real
    try:
        colonySafeUUID = uuid.UUID(colony_uuid)
    except Exception:
        return Response("Invalid Colony UUID", status=404)
    
    # Check the Colony exists
    colonyID = db.hget('ColonyData:Mapping', colonySafeUUID)
    if colonyID is None:
        return Response("Colony does not exist", status=404)
       
    redisKey = 'Colony:' + colonyID + ':Data'
    colony_data = db.hgetall(redisKey)
    
    return Response(json.dumps(colony_data), status=200, mimetype='application/json')

@app.route('/server/maintenance/mode', methods=['GET'])
def server_status():
    
    db = get_db()
    
    mode = db.get('API:Maintenance:Mode')
    
    # True if in Maintenance mode.
    if(bool(int(mode))):
        return Response(json.dumps("Gone"), status=410, mimetype='application/json')
    else:
        return Response(json.dumps("OK"), status=200, mimetype='application/json')  

@app.route('/server/maintenance/window', methods=['GET'])
def server_maintenance_window():
    
    db = get_db()
    
    # Returns tuple, {Start: epoch, Stop: epoch}
    window = db.hgetall('API:Maintenance:Window')
        
    return Response(json.dumps(window), status=200, mimetype='application/json')

@app.route('/server/version/api', methods=['GET'])
def api_version_get():
    
    db = get_db()
    
    version = db.get('API:Version')
    
    versionData = {'Version': version}
    
    return Response(json.dumps(versionData), status=200, mimetype='application/json')

@app.route('/things', methods=['GET'])
def things_get_count():
    db = get_db()
    
    thingCount = db.get("Things:Counter")
    
    return Response(json.dumps(thingCount))

def try_get_thing(itemKey):
    
    db = get_db()
    
    # Try looking up by full name first,    
    if(db.exists(itemKey)):
        return db.hgetall(itemKey)
    
    # Try removing Normal from the key and check again.
    if(':Normal' in itemKey):
        itemKeyNoNormal = itemKey[:-7]
        
        #Now does the key exist?
        if(db.exists(itemKeyNoNormal)):
            itemData = db.hgetall(itemKeyNoNormal)
            
            # Set normal quality
            itemData['Quality'] = 'Normal'
            
            # Copy to expected key.
            db.hmset(itemKey, itemData)
            
            # Update Item Map
            db.hset('Things:Mapping', itemData['ThingID'], itemKey)
            
            # Delete old item
            db.delete(itemKeyNoNormal)
            
            return itemData
        
    # If we didn't find it return None.
    return None
            
def thing_generate_id(thingName):
    
    db = get_db()  

    # Increment the Thing Counter
    thingID = db.incr("Things:Counter")
    
    # Add thing entry to thing map.
    db.hset('Things:Mapping', thingID, thingName)
    
    return thingID

def things_update_stats(thingID, quantity, selling=False):
   
    db = get_db()
    
    # Did we buy or sell items?
    if(selling):
        mode = "_sold"
    else:
        mode = "_bought"
    
    # Get the current date in yyyy-mm-dd format.    
    current_ts = get_today_date_string()
    
    # Update the ThingStats for this Thing.
    db.hincrby("Things:Stats:" + current_ts, str(thingID) + mode, quantity)
    
    # Expire the stats 8 days after last write.
    db.expire("Things:Stats:" + current_ts, 691200) 

def get_today_date_string():
        # Get the current date in yyyy-mm-dd format.    
    return datetime.datetime.today().strftime('%Y-%m-%d')

def things_update_price_history(thingID, price):
    
    db = get_db()
    
    keyName = 'Things:PriceHistory:' + str(thingID)
    
    db.lpush(keyName, price)

def get_colony_id_from_uuid(colonyUUID):
    
    db = get_db()
    
    return db.hget("ColonyData:Mapping", colonyUUID)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)
