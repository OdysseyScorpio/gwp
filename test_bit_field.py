import redis, bitarray
from datetime import datetime

db = redis.Redis('127.0.0.1', '6380', decode_responses=True)

key = "ColonyUsage:2017-11-30"

bitstring = db.get(key)
ba = bitarray.bitarray()
ba.frombytes(bitstring)

arrayLength = len(ba)
i= 0
while i < arrayLength:
    if(ba[i]):
        colonyKey = "Colony:%s:Data" % i
        ts = db.hget(colonyKey, 'LastLogin')
        d = datetime.utcfromtimestamp(float(ts))
        print ("Colony %s logged in @ " % i + (d.strftime('%Y-%m-%d %H:%M:%S')))
    i += 1

print('Done, Seen %s Colonies today, Data stored in %s bits (%s bytes)' % (db.bitcount(key), arrayLength, (arrayLength/8)))

