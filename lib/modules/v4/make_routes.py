from lib.modules.v4.api import api_module

from lib.modules.v4.colony import colony_module
from lib.modules.v4.market import market_module
from lib.modules.v4.orders import order_module
from lib.modules.v4.prime_subscription import prime_module
from lib.modules.v4.user import user_module


def register(app, version):
    app.register_blueprint(user_module, url_prefix='/{}/user'.format(version))
    app.register_blueprint(prime_module, url_prefix='/{}/prime_subscription'.format(version))
    app.register_blueprint(order_module, url_prefix='/{}/orders'.format(version))
    app.register_blueprint(market_module, url_prefix='/{}/market'.format(version))
    app.register_blueprint(colony_module, url_prefix='/{}/colonies'.format(version))
    app.register_blueprint(api_module, url_prefix='/{}/application'.format(version))
