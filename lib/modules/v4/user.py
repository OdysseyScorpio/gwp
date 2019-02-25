import hashlib
import json
from datetime import datetime

from flask import Blueprint, Response, request, escape, current_app

from lib import db
from lib.gwpcc import consts

user_module = Blueprint('v4_user_module', __name__, url_prefix='/v4/user')


@user_module.route('/create', methods=['GET'])
def user_generate_id():
    db_connection = db.get_redis_db_from_context()

    # Generate a hash for the user.
    ts = datetime.utcnow().timestamp()
    user_hash = hashlib.sha1(str(ts).encode('UTF8')).hexdigest()
    db_connection.hset(consts.KEY_USER_NORMAL.format(user_hash), 'DateCreated', ts)

    # Add to index
    db_connection.sadd(consts.KEY_USER_INDEX_BY_NORMAL_ID, user_hash)

    return Response(json.dumps({'Hash': user_hash}), status=200, mimetype='application/json')


@user_module.route('/reactivate', methods=['POST'])
def reactivate():
    try:
        incoming_data = request.json
        token = escape(incoming_data['Token'])
        user_id = escape(incoming_data['UserId'])
        user_type = escape(incoming_data['UserType'])
    except KeyError:
        return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

    current_app.logger.info('{}:{} is trying to use activation token {}'.format(user_type, user_id, token))

    db_connection = db.get_redis_db_from_context()

    # Fetch our token from DB
    token_in_db = db_connection.get(consts.KEY_USER_ACTIVATION_REQUEST_TOKEN.format(user_id))

    accept = False
    # Has it expired or ever existed?
    if token_in_db is None:
        current_app.logger.error('{} activation token was not in database or has expired.'.format(token))
    else:
        # They should match
        if token_in_db != token:
            current_app.logger.error(
                '{}:{} activation tokens did not match {} != {}.'.format(user_type, user_id, token, token_in_db))
        else:
            accept = True
            if user_type == 'Steam':
                ban_key = consts.KEY_USER_STEAM_ID_BANNED_SET
            elif user_type == 'Normal':
                ban_key = consts.KEY_USER_NORMAL_ID_BANNED_SET
            else:
                return Response(consts.ERROR_INVALID, status=consts.HTTP_INVALID)

            db_connection.srem(ban_key, user_id)
            db_connection.delete(consts.KEY_USER_ACTIVATION_REQUEST_TOKEN.format(user_id))
            current_app.logger.info('{}:{} removed from ban list'.format(user_type, user_id))

    return Response(json.dumps({'Accepted': accept}), status=200, mimetype=consts.MIME_JSON)
