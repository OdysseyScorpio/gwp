from flask import Flask
from flask_compress import Compress

import config
from lib.api import set_database_connection
from lib.modules import make_routes


def make_app():
    app = Flask(__name__)

    app.config.update(
        DEBUG=config.DEBUG_MODE,
        PROPAGATE_EXCEPTIONS=True
    )

    # Iterate over supported versions and generate urls for each blueprint
    for version in config.API_DB_CONFIG:
        make_routes.register(app, version)

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
    print(app.url_map)
    app.run(host=config.LISTEN_ON_IP, port=config.LISTEN_ON_PORT, debug=config.DEBUG_MODE, threaded=True)
