from flask import Flask
from flask_compress import Compress

from modules.prime_subscription import prime_module
from modules.orders import order_module
from modules.market import market_module
from modules.colony import colony_module
from modules.api import api_module

app = Flask(__name__)

app.config.update(
        DEBUG = False,
        PROPAGATE_EXCEPTIONS = True
        )

app.register_blueprint(prime_module)
app.register_blueprint(order_module)
app.register_blueprint(market_module)
app.register_blueprint(colony_module)
app.register_blueprint(colony_module, url_prefix="/colonies")
app.register_blueprint(api_module)

# Turn on HTTP Compression
Compress(app)

if __name__ == "__main__":
    print (app.url_map)
    app.run(host = '0.0.0.0', port = 8080, debug = False)