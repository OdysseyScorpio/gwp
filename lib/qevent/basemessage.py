class BaseMessage:

    def __init__(self, market, action, data):
        self.market = market
        self.action = action
        self.data = data

    def to_dict(self):
        return {'market': self.market,
                'action': self.action,
                'data': self.data
                }

    @staticmethod
    def from_dict(message):
        return BaseMessage(message['market'], message['action'], message['data'])

    def __str__(self):
        return ''
