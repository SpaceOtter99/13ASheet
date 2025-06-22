# data.py
import operator
from typing import Dict, List, Any

STATS = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
DEFENCES = {
    'AC': ["DEX", "CON", "WIS"],
    'PD': ["STR", "DEX", "CON"],
    'MD': ["INT", "WIS", "CHA"],
}


class Condition:
    """
    A single condition of the form:
      left (stat or attr)  operand  right (stat or attr * multiplier)
    e.g.  ('hp', '>', 'max_hp', 0.5)
    """
    OPS = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne,
    }

    def __init__(self,
                 left: str,
                 operand: str,
                 right: str,
                 multiplier: float = 1.0):
        self.left = left
        self.operand = operand
        self.right = right
        self.multiplier = multiplier

    def evaluate(self, character: "Character") -> bool:
        # fetch left value
        if self.left in ('base_hp', 'current_hp', 'temp_hp', 'max_hp', 'level'):
            val1 = getattr(character, self.left)
        else:
            val1 = character.stats.get(self.left, 0)

        # fetch right value
        if self.right in ('base_hp', 'current_hp', 'temp_hp', 'max_hp', 'level'):
            val2 = getattr(character, self.right) * self.multiplier
        else:
            val2 = character.stats.get(self.right, 0) * self.multiplier

        op_func = self.OPS[self.operand]
        return op_func(val1, val2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'left': self.left,
            'operand': self.operand,
            'right': self.right,
            'multiplier': self.multiplier,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Condition":
        return Condition(
            left=d['left'],
            operand=d['operand'],
            right=d['right'],
            multiplier=d.get('multiplier', 1.0),
        )


class Bonus:
    """
    A bonus to either a stat-mod or a defence-mod.
    target_type: 'stat' or 'defence'
    target_name: e.g. 'STR' or 'AC'
    value: integer bonus
    conditions: list of Condition that must all pass
    """
    def __init__(self,
                 target_type: str,
                 target_name: str,
                 value: int,
                 conditions: List[Condition] = None):
        self.target_type = target_type
        self.target_name = target_name
        self.value = value
        self.conditions = conditions or []

    def applies_to(self,
                   character: "Character",
                   target_type: str,
                   target_name: str) -> bool:
        if self.target_type != target_type or self.target_name != target_name:
            return False
        return all(cond.evaluate(character) for cond in self.conditions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'target_type': self.target_type,
            'target_name': self.target_name,
            'value': self.value,
            'conditions': [c.to_dict() for c in self.conditions],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Bonus":
        conds = [Condition.from_dict(cd) for cd in d.get('conditions', [])]
        return Bonus(
            target_type=d['target_type'],
            target_name=d['target_name'],
            value=d['value'],
            conditions=conds,
        )


class MagicItem:
    """
    A magic item with a level and a list of bonuses.
    """
    def __init__(self,
                 name: str,
                 level: int,
                 bonuses: List[Bonus] = None):
        self.name = name
        self.level = level
        self.bonuses = bonuses or []

    def get_bonus_for(self,
                      character: "Character",
                      target_type: str,
                      target_name: str) -> int:
        return sum(
            b.value
            for b in self.bonuses
            if b.applies_to(character, target_type, target_name)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'level': self.level,
            'bonuses': [b.to_dict() for b in self.bonuses],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "MagicItem":
        bonuses = [Bonus.from_dict(bd) for bd in d.get('bonuses', [])]
        return MagicItem(name=d['name'], level=d['level'], bonuses=bonuses)


class Defence:
    def __init__(self,
                 name: str,
                 base: int = 10,
                 defence_calc_stat=None):
        self.name = name.upper()
        self.base = base
        if defence_calc_stat is not None:
            self.defence_calc_stats = (
                defence_calc_stat
                if isinstance(defence_calc_stat, list)
                else [defence_calc_stat]
            )
        else:
            self.defence_calc_stats = DEFENCES[self.name]
        self.last_used_stat = self.defence_calc_stats[0]

    def get_mod(self, character: "Character") -> int:
        pairs = [(s, character.stats[s]) for s in self.defence_calc_stats]
        pairs.sort(key=lambda x: x[1])
        mid_stat, mid_val = pairs[len(pairs)//2]
        self.last_used_stat = mid_stat
        return (mid_val - 10) // 2

    def get_value_stat(self) -> str:
        return self.last_used_stat

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'base': self.base,
            'defence_calc_stats': self.defence_calc_stats,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Defence":
        return Defence(
            name=d['name'],
            base=d['base'],
            defence_calc_stat=d.get('defence_calc_stats'),
        )


class Character:
    def __init__(self,
                 name: str,
                 **kwargs):
        self.name = name
        self.stats: Dict[str, int] = kwargs.get(
            "stats", {s: 10 for s in STATS}
        )
        self.bonuses: Dict[str, int] = kwargs.get("bonuses", {})

        raw_defs = kwargs.get("defences", None)
        if raw_defs:
            self.defences = {
                d: Defence.from_dict(dd) for d, dd in raw_defs.items()
            }
        else:
            self.defences: Dict[str, Defence] = {
                d: Defence(d) for d in DEFENCES
            }

        self.level: int = kwargs.get("level", 1)
        self.race: str = kwargs.get("race", "Human")
        self.classname: str = kwargs.get("class", "Fighter")
        self.base_hp: int = kwargs.get("base_hp", 10)
        self.temp_hp: int = kwargs.get("temp_hp", 0)
        self.current_hp: int = kwargs.get("current_hp", self.max_hp)

        raw_items = kwargs.get("magic_items", [])
        self.magic_items: List[MagicItem] = [
            MagicItem.from_dict(mi) for mi in raw_items
        ]

    def __str__(self):
        return f"{self.__class__}: {self.__dict__}"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def max_hp(self) -> int:
        # (Base HP + CON raw mod) * level
        return (self.base_hp + self.get_raw_modifier('CON')) * self.level

    def get_raw_modifier(self, stat: str) -> int:
        # classic (stat – 10)//2 plus any static bonuses
        return ((self.stats.get(stat, 10) - 10) // 2
                + self.bonuses.get(stat, 0))

    def get_magic_bonus(self, target_type: str, target_name: str) -> int:
        # sum of all item bonuses that apply
        return sum(
            mi.get_bonus_for(self, target_type, target_name)
            for mi in self.magic_items
        )

    def modifier(self, stat: str) -> str:
        """
        Full stat-modifier = raw + any magic-item bonus.
        Returns '+n' if positive, '0' for 0, else '-n'.
        """
        raw = self.get_raw_modifier(stat)
        magic = self.get_magic_bonus('stat', stat)
        total = raw + magic
        return f"+{total}" if total > 0 else str(total)

    def get_defence(self, defence: str) -> int:
        d = defence.upper()
        base = self.defences[d].base
        bonus = self.get_defence_bonus(d)
        mod   = self.get_defence_mod(d)
        return base + bonus + mod

    def get_defence_mod(self, defence: str) -> int:
        d = defence.upper()
        raw_mod = self.defences[d].get_mod(self)
        magic   = self.get_magic_bonus('defence', d)
        return raw_mod + magic

    def get_defence_base(self, defence: str) -> int:
        return self.defences[defence.upper()].base

    def get_defence_bonus(self, defence: str) -> int:
        return self.bonuses.get(defence.upper(), 0)

    def get_defence_stat(self, defence: str) -> str:
        """
        Return the name of the stat used for this defence
        (i.e. the median stat value).
        """
        d = defence.upper()
        self.get_defence(d)
        return self.defences[d].get_value_stat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'stats': self.stats,
            'bonuses': self.bonuses,
            'defences': {d: self.defences[d].to_dict()
                         for d in self.defences},
            'race': self.race,
            'level': self.level,
            'classname': self.classname,
            'base_hp': self.base_hp,
            'current_hp': self.current_hp,
            'temp_hp': self.temp_hp,
            'magic_items': [mi.to_dict() for mi in self.magic_items],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Character":
        return Character(
            name=d['name'],
            stats=d.get('stats'),
            bonuses=d.get('bonuses', {}),
            defences=d.get('defences'),
            level=d.get('level', 1),
            race=d.get('race', 'Human'),
            classname=d.get('classnmae', 'Fighter'),
            base_hp=d.get('base_hp', 10),
            current_hp=d.get('current_hp'),
            temp_hp=d.get('temp_hp', 0),
            magic_items=d.get('magic_items', []),
        )


class User:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.stats = kwargs.get("stats", STATS)
        self.sheets: Dict[str, Character] = kwargs.get("sheets", {})

    def __str__(self):
        return f"{self.__class__}: {self.__dict__}"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'stats': self.stats,
            'sheets': {
                n: char.to_dict()
                for n, char in self.sheets.items()
            }
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "User":
        user = User(name=d.get('name', ''), stats=d.get('stats', STATS))
        raw = d.get('sheets', {})
        user.sheets = {
            n: Character.from_dict(cd)
            for n, cd in raw.items()
        }
        return user
