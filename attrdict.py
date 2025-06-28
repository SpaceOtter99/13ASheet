# attrdict.py

from collections import UserDict

class AttrDict(UserDict):
    """
    A dictionary that also allows attribute access:
      d.foo  <==>  d['foo']
    And will auto‐wrap any nested dict into an AttrDict as well.
    """
    def __getattr__(self, key):
        try:
            val = self.data[key]
        except KeyError as e:
            raise AttributeError(key) from e

        # auto‐wrap nested dicts
        if isinstance(val, dict) and not isinstance(val, AttrDict):
            val = AttrDict(val)
            self.data[key] = val
        return val

    def __setattr__(self, key, value):
        # store everything under .data except 'data' itself
        if key == "data":
            super().__setattr__(key, value)
        else:
            self.data[key] = value

    def __getitem__(self, key):
        val = self.data[key]
        if isinstance(val, dict) and not isinstance(val, AttrDict):
            val = AttrDict(val)
            self.data[key] = val
        return val

    def update(self, *args, **kwargs):
        # override to auto‐wrap nested dicts on update
        for k, v in dict(*args, **kwargs).items():
            if isinstance(v, dict) and not isinstance(v, AttrDict):
                v = AttrDict(v)
            self.data[k] = v

    def to_dict(self):
        result = {}
        for k, v in self.data.items():
            if isinstance(v, AttrDict):
                result[k] = v.to_dict()
            else:
                result[k] = v
        return result
