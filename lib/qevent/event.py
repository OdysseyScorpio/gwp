import json

from lib import db
from lib.qevent.basemessage import BaseMessage


def send(message: BaseMessage):
    rdb = db.get_redis_db_from_context()
    rdb.publish('market', json.dumps(message.to_dict()))
