from flask import Flask, Response, g, request
from flask_compress import Compress
import json, redis, pprint

app = Flask(__name__)

app.config.update(
        DEBUG=True,
        PROPAGATE_EXCEPTIONS=True
        )

# Turn on HTTP Compression
# Compress(app)

# Returns a valid, connected Redis object 
def get_db():
    # Check to see if we've already opened a database
    db = getattr(g, '_database', None)
    if db is None:
        # If not, open and connect to the database
        db = g._database = redis.Redis('127.0.0.1','6379',decode_responses = True)
    return db


# POST Market Get Items
# Input: 
# Returns a Dict<String,Tuple<Price,Qty>>
@app.route('/market/get_items', methods=['POST'])
def get_market_item():
    
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
def post_market_sell():
    
    db = get_db()
    
    r = request.json    

    for item in r:

        redisKey = 'ThingDef:' + item['Name']
        if db.hexists(redisKey, 'Quantity'):
            db.hincrbyfloat(redisKey, 'Quantity', -item['Quantity'])
        else:    
            print("We sold something we never had in the first place: Item was " + redisKey)
            
    return Response(json.dumps("OK"))

@app.route('/market/buy_items', methods=['POST'])
def post_market_buy():
    
    db = get_db()
    
    r = request.json    

    for item in r:

        redisKey = 'ThingDef:' + item['Name']
        if db.hexists(redisKey, 'Quantity'):
            db.hincrbyfloat(redisKey, 'Quantity', item['Quantity'])
            newItem = dict(item)
            del newItem['Quantity']
            del newItem['Name']
        else:
            newItem = dict(item)
            del newItem['Name']
            
            # TODO: Calculate price
        db.hmset(redisKey, newItem)
            
    return Response(json.dumps("OK"))

#Start the app/webserver
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080,debug=True)
