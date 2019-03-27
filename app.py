from flask import Flask
from flask import current_app
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix

import config
from lib.api import set_database_connection
from lib.modules.v4 import make_routes as make_routes_v4


def before_send(event, hint):
    a = current_app
    if a and a.config.get('TESTING', False):
        return None

    return event


def make_app():
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn="https://6d5e55bd65094408b11d053eb3ab7328@sentry.thecodecache.net/3",
        integrations=[FlaskIntegration()],
        before_send=before_send
    )

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_host=2, x_port=2, x_prefix=2, x_proto=2)

    app.config.update(
        DEBUG=config.DEBUG_MODE,
        PROPAGATE_EXCEPTIONS=True
    )

    for version in config.API_DB_CONFIG:
        make_routes_v4.register(app, 'v4/{}'.format(version))

    # Install a hooks to setup the database connection
    # according to the API version requested and log request/response.
    app.before_request(set_database_connection)
    # app.before_request(log_request_info)
    # app.after_request(log_response)

    # Install HTTP compression hooks
    Compress(app)
    print(app.url_map)
    return app


if __name__ == "__main__":
    app = make_app()
    app.run(host=config.LISTEN_ON_IP, port=config.LISTEN_ON_PORT, debug=config.DEBUG_MODE, threaded=True)
