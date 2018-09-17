from lib.modules.api import api_module

from lib.modules.colony import colony_module
from lib.modules.market import market_module
from lib.modules.orders import order_module
from lib.modules.prime_subscription import prime_module
from lib.modules.user import user_module


def register(app, version):
    app.register_blueprint(user_module, url_prefix='/{}/user'.format(version))
    app.register_blueprint(prime_module, url_prefix='/{}/prime_subscription'.format(version))
    app.register_blueprint(order_module, url_prefix='/{}/orders'.format(version))
    app.register_blueprint(market_module, url_prefix='/{}/market'.format(version))
    app.register_blueprint(colony_module, url_prefix='/{}/colonies'.format(version))
    app.register_blueprint(api_module, url_prefix='/{}/application'.format(version))
