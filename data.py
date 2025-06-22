# data.py
from math import floor
from typing import Dict

STATS = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
DEFENCES = {'AC': ["DEX", "CON", "WIS"], 'PD': ["STR", "DEX", "CON"], 'MD': ["INT", "WIS", "CHA"]}

class User:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.stats = kwargs.get("stats", STATS)
        # sheets is now a dict: name -> Character
        self.sheets: Dict[str, Character] = kwargs.get("sheets", {})

    def __str__(self):
        return f"{self.__class__}: {self.__dict__}"

    def to_dict(self):
        # serialize each Character to its dict form
        return {
            'name': self.name,
            'stats': self.stats,
            'sheets': {name: char.to_dict() for name, char in self.sheets.items()}
        }

    @staticmethod
    def from_dict(d):
        user = User(name=d.get('name', ''), stats=d.get('stats', STATS))
        raw_sheets = d.get('sheets', {})
        # rebuild Character objects
        user.sheets = {
            name: Character.from_dict(char_dict)
            for name, char_dict in raw_sheets.items()
        }
        return user

class Character:
    def __init__(self, name, **kwargs):
        self.name = name
        self.stats: Dict[str, int] = kwargs.get("stats", {stat: 10 for stat in STATS})
        self.bonuses = kwargs.get("bonuses", {})
        self.defences: Dict[str, Defence] = kwargs.get(
            "defences",
            {d: Defence(d, 11) for d in DEFENCES}
        )

    def __str__(self):
        return f"{self.__class__}: {self.__dict__}"

    def modifier(self, stat):
        mod = (self.stats.get(stat, 10) - 10) // 2
        mod += self.bonuses.get(stat, 0)
        return f"+{mod}" if mod > 0 else mod

    def get_defence(self, defence: str):
        return (
            self.get_defence_base(defence)
            + self.get_defence_bonus(defence)
            + self.get_defence_mod(defence)
        )

    def get_defence_mod(self, defence: str):
        defence = defence.upper()
        return self.defences[defence].get_mod(self)

    def get_defence_base(self, defence: str):
        return self.defences[defence].base

    def get_defence_bonus(self, defence: str):
        return self.bonuses.get(defence.upper(), 0)

    def get_defence_stat(self, defence: str):
        # updates last_used_stat internally
        self.get_defence(defence)
        return self.defences[defence.upper()].get_value_stat()

    def to_dict(self):
        # keep name & stats at minimum; add more if you like
        return {'name': self.name, 'stats': self.stats}

    @staticmethod
    def from_dict(d):
        return Character(name=d['name'], stats=d.get('stats'))

class Defence:
    def __init__(self, name, base=10, defence_calc_stat=None):
        self.name = name
        self.base = base
        if defence_calc_stat is not None:
            self.defence_calc_stats = (
                defence_calc_stat
                if isinstance(defence_calc_stat, list)
                else [defence_calc_stat]
            )
        else:
            self.defence_calc_stats = DEFENCES[name]
        self.last_used_stat = self.defence_calc_stats[0]

    def __str__(self):
        return f"{self.__class__}: {self.__dict__}"

    def get_mod(self, character):
        values = {s: character.stats[s] for s in self.defence_calc_stats}
        # pick the lower‐median stat
        sorted_vals = sorted(values.items(), key=lambda item: item[1])
        midpoint = len(sorted_vals) // 2
        chosen_stat, chosen_val = sorted_vals[midpoint]
        self.last_used_stat = chosen_stat
        return (chosen_val - 10) // 2

    def get_value_stat(self):
        return self.last_used_stat
