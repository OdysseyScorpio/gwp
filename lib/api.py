from flask import request, Response, current_app, g
#from sentry_sdk import configure_scope

from config import API_DB_CONFIG
from lib.db import get_redis_db_from_context
from lib.gwpcc import consts


def set_database_connection():
    """
    This function setups up a database connection depending on the version of the API being requested.
    And is called before each request.
    :return:
    """

    try:
        groups = request.path.split('/')
        if groups is None or len(groups) < 1:
            return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)

        version = groups[1]

        # Check if it's a new style URL
        if version.startswith('v'):
            if len(groups) > 2:
                version = groups[2]

                # New versions: m1, m2, m3 etc.
                if version in API_DB_CONFIG:
                    db_number = API_DB_CONFIG[version]
                else:
                    return Response('Unknown API Version', status=consts.HTTP_NOT_FOUND)

            else:
                return Response('Unknown API Version', status=consts.HTTP_NOT_FOUND)

        else:
            return Response('Unknown API Version', status=consts.HTTP_NOT_FOUND)

        g.gwp_market = version
        get_redis_db_from_context(db_number)

    except Exception as e:
        return Response(consts.ERROR_NOT_FOUND, status=consts.HTTP_NOT_FOUND)


# def collect_sentry_tags():
#     with configure_scope() as scope:
#         if g.gwp_market:
#             scope.set_tag('market', g.gwp_market)

#         if request.view_args and 'colony_hash' in request.view_args:
#             scope.set_tag('colony_id', request.view_args['colony_hash'])

#         if request.data and request.json and isinstance(request.json, dict):
#             data = request.json
#             if 'OwnerType' in data:
#                 scope.set_tag('Owner Type', data['OwnerType'])
#             if 'OwnerID' in data:
#                 scope.set_tag('Owner ID', data['OwnerID'])


def log_request_info():
    current_app.logger.debug('=' * 50)
    current_app.logger.debug('Request')
    current_app.logger.debug('Headers: %s', request.headers)
    current_app.logger.debug('=' * 50)


def log_response(resp):
    current_app.logger.debug('-' * 50)
    current_app.logger.debug('Response')
    current_app.logger.debug('Headers: {}'.format(resp.headers))
    current_app.logger.debug('-' * 50)
    return resp
