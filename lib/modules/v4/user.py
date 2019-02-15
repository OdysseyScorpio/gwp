import hashlib
import json
from datetime import datetime

from flask import Blueprint, Response

from lib import consts, db

user_module = Blueprint('v4_user_module', __name__, url_prefix='/v4/user')


@user_module.route('/create', methods=['GET'])
def user_generate_id():
    db_connection = db.get_redis_db_from_context()

    # Generate a hash for the user.
    user_hash = hashlib.sha1(str(datetime.utcnow().timestamp()).encode('UTF8')).hexdigest()
    db_connection.hset(consts.KEY_USER_NORMAL.format(user_hash), 'DateCreated', int(datetime.utcnow().timestamp()))

    # Add to index
    db_connection.sadd(consts.KEY_USER_INDEX_BY_NORMAL_ID, user_hash)

    return Response(json.dumps({'Hash': user_hash}), status=200, mimetype='application/json')
