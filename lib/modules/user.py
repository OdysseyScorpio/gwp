import hashlib
import json
from datetime import datetime

from flask import Blueprint, Response

from lib import consts, db

user_module = Blueprint('v3_user_module', __name__, url_prefix='/v3/user')


@user_module.route('/create', methods=['GET'])
def user_generate_id():
    db_connection = db.get_redis_db_from_context()

    # Generate a hash for the user.
    user_hash = hashlib.sha1(str(datetime.utcnow().timestamp()).encode('UTF8')).hexdigest()

    db_connection.set(consts.KEY_USER_NORMAL, user_hash)

    # Add the UUID to the UUID to ID map
    db_connection.rpush(consts.KEY_USER_INDEX_BY_ID, user_hash)

    return Response(json.dumps({'Hash': user_hash}), status=200, mimetype='application/json')
