'''
Created on 16 Jan 2018

@author: aleyshon
'''

import redis
import config
from flask import g

# Returns a valid, connected Redis object
def get_db():
    # Check to see if we've already opened a database
    db = getattr(g, '_database', None)
    if db is None:
        # If not, open and connect to the database, Decode responses in UTF-8 (default)
        db = g._database = redis.Redis(config.DATABASE_IP, config.DATABASE_PORT, decode_responses = True)
    return db