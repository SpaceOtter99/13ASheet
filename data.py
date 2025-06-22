
STATS = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']

class User:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.stats = kwargs.get("stats", STATS)
        self.sheets = kwargs.get("sheets", [])

    def to_dict(self):
        return {'name': self.name, 'stats': self.stats, 'sheets': self.sheets}

    @staticmethod
    def from_dict(d):
        return Character(name=d['name'], stats=d.get('stats'))


class Character:
    def __init__(self, name, stats=None):
        self.name = name
        self.stats = stats or {stat: 10 for stat in STATS}

    def modifier(self, stat):
        mod = (self.stats.get(stat, 10) - 10) // 2
        return f"+{mod}" if mod > 0 else mod

    def to_dict(self):
        return {'name': self.name, 'stats': self.stats}

    @staticmethod
    def from_dict(d):
        return Character(name=d['name'], stats=d.get('stats'))