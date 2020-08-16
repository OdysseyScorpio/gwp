import json
import logging

from flask import Blueprint, Response

from lib import db
from lib.gwpcc.consts import KEY_API_MAINTENANCE_MODE, \
    KEY_API_MAINTENANCE_WINDOW, KEY_API_VERSION, KEY_API_VERSION_SUPPORTED

api_module = Blueprint('v4_api_module', __name__, url_prefix='/application')


@api_module.route('/maintenance/mode', methods=['GET'])
def server_status():
    db_connection = db.get_redis_db_from_context()

    mode = db_connection.get(KEY_API_MAINTENANCE_MODE)
    print("Maintenance Mode is {}".format(mode))
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
    print("Maintenance Window is {}".format(json.dumps(window)))
    return Response(json.dumps(window), status=200, mimetype='application/json')


@api_module.route('/version', methods=['GET'])
def api_version_get():
    db_connection = db.get_redis_db_from_context()

    version = db_connection.get(KEY_API_VERSION)
    versionSupported = db_connection.get(KEY_API_VERSION_SUPPORTED)

    print("Main Version is {} Supported Version is {}".format(
        version, versionSupported))
    version_data = {'Version': version, 'Supported': versionSupported}

    return Response(json.dumps(version_data), status=200, mimetype='application/json')
