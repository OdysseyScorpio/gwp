import hashlib
from abc import ABC


class BaseThing(ABC):

    def __init__(self, name: str, **kwargs):
        if name is None or name == '':
            raise ValueError('Must specify a name!')
        self._name = name
        self._quality = kwargs.get('Quality', "")
        self._stuff_type = kwargs.get('StuffType', "")
        self._base_market_value = float(kwargs.get('BaseMarketValue', 0))
        self._current_buy_price = float(kwargs.get('CurrentBuyPrice', -1))
        self._quantity = int(kwargs.get('Quantity', 0))
        self._minified_container = bool(kwargs.get('MinifiedContainer', False))
        self._hash = kwargs.get('Hash', self.calculate_hash(self.Name, self.Quality, self.StuffType))
        self._changes = {}

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        self._changes['Name'] = True
        self._name = value

    @property
    def Quality(self):
        return self._quality

    @Quality.setter
    def Quality(self, value):
        self._changes['Quality'] = True
        self._quality = value

    @property
    def StuffType(self):
        return self._stuff_type

    @StuffType.setter
    def StuffType(self, value):
        self._changes['StuffType'] = True
        self._stuff_type = value

    @property
    def CurrentBuyPrice(self):
        return self._current_buy_price

    @CurrentBuyPrice.setter
    def CurrentBuyPrice(self, value):
        self._changes['CurrentBuyPrice'] = True
        self._current_buy_price = value

    @property
    def BaseMarketValue(self):
        return self._base_market_value

    @BaseMarketValue.setter
    def BaseMarketValue(self, value):
        self._changes['BaseMarketValue'] = True
        self._base_market_value = value

    @property
    def Quantity(self):
        return self._quantity

    @Quantity.setter
    def Quantity(self, value):
        self._changes['Quantity'] = True
        self._quantity = value

    @property
    def MinifiedContainer(self):
        return self._minified_container

    @MinifiedContainer.setter
    def MinifiedContainer(self, value):
        self._changes['MinifiedContainer'] = True
        self._minified_container = value

    @property
    def Hash(self):
        return self._hash

    @Hash.setter
    def Hash(self, value):
        self._changes['Hash'] = True
        self._hash = value

    @classmethod
    def _iter_properties(cls):
        for var_name in dir(cls):
            value = getattr(cls, var_name)
            if isinstance(value, property):
                yield var_name

    @classmethod
    def from_dict(cls, thing: dict):
        return cls(thing['Name'], **thing)

    @classmethod
    def calculate_hash(cls, name: str, quality=None, stuff_type=None) -> str:
        if not quality:
            quality = ''
        if not stuff_type:
            stuff_type = ''
        return hashlib.sha1('{}{}{}'.format(name, stuff_type, quality).encode('UTF8')).hexdigest()

    @classmethod
    def calculate_hash_from_dict(cls, dict_of_thing: dict) -> str:
        return cls.calculate_hash(dict_of_thing['Name'], dict_of_thing.get('Quality'), dict_of_thing.get('StuffType'))

    @property
    def FullName(self):
        full_name = self._name
        if self._quality:
            full_name += ':{}'.format(self._quality)
        if self._stuff_type:
            full_name += ':{}'.format(self._stuff_type)
        return full_name

    def __str__(self):
        return '{} ({})'.format(self.FullName, self.Hash)
