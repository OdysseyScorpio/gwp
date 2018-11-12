from typing import Dict

from lib.colonies.colony import Colony
from lib.qevent.basemessage import BaseMessage
from lib.things.order_thing import OrderThing


class OrderMessage(BaseMessage):

    def __init__(self, market, order, colony):
        self.order = order
        self.colony = colony
        super().__init__(market, 'order', {
            'order': order,
            'colony': colony
        })

    @staticmethod
    def prepare(market, bought: Dict[str, OrderThing], sold: Dict[str, OrderThing], colony: Colony):

        # Start building data to send to Message Queue
        queue_data = {'buy': [], 'sell': []}

        for order_thing in bought.values():
            queue_data['buy'].append((order_thing.FullName, order_thing.Quantity))
        for order_thing in sold.values():
            queue_data['sell'].append((order_thing.FullName, order_thing.Quantity))

        return OrderMessage(market, queue_data, colony.FullName)

    @staticmethod
    def parse(message: BaseMessage):
        if message.action != 'order':
            raise Exception('Wrong action type')

        order = message.data['order']
        colony = message.data['colony']

        return OrderMessage(message.market, order, colony)

    def __str__(self):
        string = '{0}'.format(self.colony)

        did_buy = False
        did_sell = False

        if len(self.order['buy']) > 0:
            string += ' just bought '
            items = []
            for name, qty in self.order['buy']:
                items.append('{0} of {1} '.format(qty, name))
            string += ', '.join(items)
            did_buy = True

        if len(self.order['sell']) > 0:
            if did_buy:
                string += ' and'
            string += ' just sold '
            items = []
            for name, qty in self.order['sell']:
                items.append('{0} of {1} '.format(qty, name))
                did_sell = True
            string += ', '.join(items)
        return string
