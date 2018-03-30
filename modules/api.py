from flask import Blueprint, Response
from lib import  db
import json

api_module = Blueprint('api_module', __name__, url_prefix='/server')

@api_module.route('/maintenance/mode', methods = ['GET'])
def server_status():

    rdbi = db.get_db()

    mode = rdbi.get('API:Maintenance:Mode')

    # True if in Maintenance mode.
    if(bool(int(mode))):
        return Response(json.dumps("Gone"), status = 410, mimetype = 'application/json')
    else:
        return Response(json.dumps("OK"), status = 200, mimetype = 'application/json')


@api_module.route('/maintenance/window', methods = ['GET'])
def server_maintenance_window():

    rdbi = db.get_db()

    # Returns tuple, {Start: epoch, Stop: epoch}
    window = rdbi.hgetall('API:Maintenance:Window')

    return Response(json.dumps(window), status = 200, mimetype = 'application/json')


@api_module.route('/version/api', methods = ['GET'])
def api_version_get():

    rdbi = db.get_db()

    version = rdbi.get('API:Version')

    versionData = {'Version': version}

    return Response(json.dumps(versionData), status = 200, mimetype = 'application/json')