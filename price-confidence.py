import redis
import statistics
from collections import Counter
from itertools import groupby


def invert_dict_fast(d):
    return dict({v: k for k, v in d.items()})


def get_db():

    # If not, open and connect to the database, Decode responses in UTF-8 (default)
    db = redis.Redis('127.0.0.1', '6379', decode_responses=True)
    
    return db


if __name__ == '__main__':
    
    db = get_db()
    
    thingDefsFetched = []
    
    for thingDef in db.scan_iter(match="ThingDef:*"):
        if(thingDef != "ThingDef:Silver"):
            thingDefsFetched.append(thingDef)
    
    thingMap = invert_dict_fast(dict(db.hgetall('Things:Mapping')))
    
    pipe = db.pipeline()
    
    for thingDef in thingDefsFetched:
        thingID = thingMap[thingDef]
        pipe.lrange('Things:PriceHistory:%s' % thingID, 0, -1)
        
    prices = pipe.execute()
    
    thingDefWithPrices = dict(zip(thingDefsFetched, prices))
    
    for thingDef, prices in thingDefWithPrices.items():
        
        if (len(prices) >= 10):
            floatPrice = list(map(float, prices))
            mean = statistics.mean(floatPrice)
            variance = statistics.pvariance(floatPrice, mean)
            samples = len(floatPrice)
            maxPrice = max(floatPrice)
            minPrice = min(floatPrice)
            range = maxPrice - minPrice
            
            try:
                mode = statistics.mode(floatPrice)
            except:
                # If we can't find the mode, return most common group.
                mode = Counter(floatPrice).most_common(1)
                if (mode[0][1] < 2):
                    # Every single value was different. Set mode to average instead.
                    mode = 0
                else:
                    mode = mode[0][1]       
                
            # Calculate how confident we are that the price is accurate reflects the true Base Market Value.
            confidence = 0
                        
            # If the variance is 0, we should be very confident
            if(variance == 0 and samples >= 10):
                confidence += 1     
            
            # If the mode is less than 25% different from average
            modeMeanDiff = abs(mode / mean)
            if(modeMeanDiff > 0.75 and modeMeanDiff < 1.25):
                confidence += 0.50
                
            if(samples >= 20):
                confidence += 0.25
                
            if(range == 0):
                confidence += 0.25
            
            newPrice = float("{:,.2}".format(mean))
            
            if(confidence > 1.50):
                print('{0} Confidence: {5}, New Price: {9} Mean: {1}, Mode: {3}, Range: {6}, Min: {7}, Max: {8}, Samples: {4}'.format(thingDef, mean, variance, mode, len(floatPrice), confidence, range, minPrice, maxPrice, newPrice))
                        
        else:
            continue
            # print('Not enough Sample for {0}, Currently have {1}'.format(thingDef, len(prices)))
                  
    print('Done')
