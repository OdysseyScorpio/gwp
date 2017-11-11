from flask import Flask, Response, g, request
from flask_compress import Compress
import json, redis, pprint
import uuid
import datetime



app = Flask(__name__)

app.config.update(
        DEBUG=False,
        PROPAGATE_EXCEPTIONS=True
        )

# Turn on HTTP Compression
# Compress(app)

# Returns a valid, connected Redis object 
def get_db():
    # Check to see if we've already opened a database
    db = getattr(g, '_database', None)
    if db is None:
        # If not, open and connect to the database, Decode responses in UTF-8 (default)
        db = g._database = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    return db

@app.route('/market/get_items', methods=['POST'])
def market_get_items():
    
    db = get_db()
    
    r = request.json    

    itemsToReturn = []

    for item in r:
        marketItem = { 'Name' : item}
        redisResult = db.hgetall('ThingDef:' + item)
        if redisResult:
            marketItem.update(redisResult)
            itemsToReturn.append(marketItem)
            
    return Response(json.dumps(itemsToReturn), mimetype='application/json')

@app.route('/market/sell_items', methods=['POST'])
def market_sell_items():
    
    db = get_db()
    
    r = request.json    

    # For each item sent in the JSON payload
    for item in r:
        
        # Add namespace to item name to form Key
        itemKey = 'ThingDef:' + item['Name']
         
        # Request Key from Redis
        itemData = db.hgetall(itemKey)
        
        # Did we find the Key?
        if not itemData is None:
            
            # Decrement the quantity that was bought from stock
            db.hincrby(itemKey, 'Quantity', -item['Quantity'])
            
            # Add thing ID if there isn't one.
            if not 'Thing_ID' in itemData:
                itemData['Thing_ID'] = thing_generate_id(item['Name'])
                db.hset(itemKey, "Thing_ID", itemData['Thing_ID'])
 
            # Update ThingStats
            things_update_stats(itemData['Thing_ID'], item['Quantity'], True)
        else:
            
            # Couldn't locate Key in DB, something is wrong...
            print("We sold something we never had in the first place: Item was " + itemKey)
            return Response("ThingDef was not found", status=500)
    
    return Response(json.dumps("OK"))

@app.route('/market/buy_items', methods=['POST'])
def market_buy_items():
    
    db = get_db()
    
    r = request.json    
    
    # For each item sent in the JSON payload
    for item in r:
        
        # Add namespace to item name to form Key
        itemKey = 'ThingDef:' + item['Name']
        
        # Request Key from Redis
        itemData = db.hgetall(itemKey)
        
        # Did we find the Key?
        if not itemData is None:
            
            # Increment the quantity in stock
            db.hincrby(itemKey, 'Quantity', item['Quantity'])
            
            newItem = dict(itemData)
            
            # Add thing ID if there isn't one.
            if not 'Thing_ID' in itemData:
                newItem['Thing_ID'] = thing_generate_id(item['Name'])
            
            # Remove quantity from Dict so we don't overwrite it in the next step
            del newItem['Quantity']
        else:          
            newItem = dict(item)
            
            # This is a new Thing so get an ID.
            newItem['Thing_ID'] = thing_generate_id(item['Name'])
            
            # Remove name from Dict so it doesn't get added to Key Values
            del newItem['Name']
            
        # TODO: Calculate price
        
        # Set the Values of the Key
        db.hmset(itemKey, newItem)
        
        # Update ThingStats
        things_update_stats(newItem['Thing_ID'], item['Quantity'], False)

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
        print(uuidExists)
        if not (uuidExists):
            db.hset('ColonyData:Mapping', colonyUUID, colonyID)
            break
      
    return Response(json.dumps(colonyUUID), status=200)

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
       
    redisKey = 'Colony:' + colonyID + ':Data'
    db.hmset(redisKey, colony_data)
    
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
    
    return Response(json.dumps(colony_data), status=200)

@app.route('/things', methods=['GET'])
def things_get_count():
    db = get_db()
    
    thingCount = db.get("Things:Counter")
    
    return Response(json.dumps(thingCount))

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
    current_ts = datetime.datetime.today().strftime('%Y-%m-%d')
    
    # Update the ThingStats for this Thing.
    db.hincrby("Things:Stats:" + current_ts, str(thingID) + mode, quantity)
    
    # Expire the stats one week after last write.
    db.expire("Things:Stats:" + current_ts, 604800) 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
