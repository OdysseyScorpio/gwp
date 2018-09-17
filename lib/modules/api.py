import json

from flask import Blueprint, Response

from lib import db
from lib.consts import KEY_API_MAINTENANCE_MODE, \
    KEY_API_MAINTENANCE_WINDOW, KEY_API_VERSION

api_module = Blueprint('v3_api_module', __name__, url_prefix='/v3/application')


@api_module.route('/maintenance/mode', methods=['GET'])
def server_status():
    db_connection = db.get_redis_db_from_context()

    mode = db_connection.get(KEY_API_MAINTENANCE_MODE)

    # True if in Maintenance mode.
    if mode:
        return Response(json.dumps("Gone"), status=410, mimetype='application/json')
    else:
        return Response(json.dumps("OK"), status=200, mimetype='application/json')


@api_module.route('/maintenance/window', methods=['GET'])
def server_maintenance_window():
    db_connection = db.get_redis_db_from_context()

    # Returns tuple, {Start: epoch, Stop: epoch}
    window = db_connection.hgetall(KEY_API_MAINTENANCE_WINDOW)

    return Response(json.dumps(window), status=200, mimetype='application/json')


@api_module.route('/version', methods=['GET'])
def api_version_get():
    db_connection = db.get_redis_db_from_context()

    version = db_connection.get(KEY_API_VERSION)

    version_data = {'Version': version}

    return Response(json.dumps(version_data), status=200, mimetype='application/json')
