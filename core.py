import tools
import player

import threading
import time


class Client(object):

    def __init__(self, steamid, userid=None, gold=0, heroes=None,
                 current_hero=None):
        self.steamid = steamid  # Mainly for database handling
        self.userid = userid  # Events, etc.
        self._gold = gold
        self.heroes = tools.UniqueList(heroes, type_filter=(Hero,))
        self._current_hero = current_hero

        self.e_gold_change = tools.Event()
        self.e_current_hero_change = tools.Event()

    def _get_gold(self):
        return self._gold

    def _set_gold(self, gold):
        if gold != self._gold:
            previous_gold = self._gold
            self._gold = gold
            self.e_gold_change.fire(sender=self,
                                    new_gold=gold,
                                    previous_gold=previous_gold)

    gold = property(_get_gold, _set_gold)

    def _get_current_hero(self):
        return self._current_hero

    def _set_current_hero(self, hero):
        if hero not in self.heroes:
            raise ValueError("Client '%s': Attempt to switch to an \
unowned hero: '%s'" % (str(self), hero.name))
        if hero != self.current_hero:
            previous_hero = self._current_hero
            self._current_hero = hero
            self.e_current_hero_change.fire(sender=self,
                                            new_hero=hero,
                                            previous_hero=previous_hero)

    current_hero = property(_get_current_hero, _set_current_hero)

    def get_player(self):
        return player.Player(self.userid)

    def _get_total_level(self):
        return sum([hero.level for hero in self.heroes])

    total_level = property(_get_total_level)


class Entity(object):

    def __init__(self, name, description='', author='', cost=0, level=0,
                 required_level=0, max_level=-1, allowed_users=None):
        self.name = name
        self.description = description
        self.author = author
        self.cost = cost
        self._level = level
        self.required_level = required_level
        self.max_level = max_level
        self.allowed_users = allowed_users or []
        self.e_level_change = tools.Event()

    def _get_level(self):
        return self._level

    def _set_level(self, level):
        if 0 <= self.max_level < level:
            level = self.max_level
        if level != self._level:
            previous_level = self._level
            self._level = level
            self.e_level_change.fire(sender=self,
                                     new_level=level,
                                     previous_level=previous_level)

    level = property(_get_level, _set_level)

    @classmethod
    def get_subclasses(cls):
        subclasses = tools.UniqueList()
        for entity_cls in cls.__subclasses__():
            subclasses.append(entity_cls)
            subclasses.extend(entity_cls.get_subclasses())
        return subclasses


class Hero(Entity):

    @staticmethod
    def evaluate_required_exp(level):
        return 100 + level * 25

    def __init__(self, name, description='', author='', cost=0, level=0,
                 required_level=0, max_level=-1, exp=0, skills=None, items=None,
                 restricted_items=None):
        super(Hero, self).__init__(name, description, author, cost, level,
                                   required_level, max_level)
        self._exp = exp
        self.skills = skills or []
        self.items = items or []
        self.restricted_items = restricted_items or []
        self.e_exp_change = tools.Event()

    _get_level = Entity._get_level

    #TODO: External cmd "hw_givelevel <userid> <amount>
    #TODO: External cmd "hw_givexp <userid> <amount>
    def _set_level(self, level):
        self._exp = 0
        super(Hero, self)._set_level(level)

    level = property(_get_level, _set_level)

    def _get_exp(self):
        return self._exp

    def _set_exp(self, exp):
        if exp != self._exp:
            previous_exp = self._exp
            exp_change = exp - self._exp
            self._exp = exp
            level_change = 0
            required_exp = Hero.evaluate_required_exp(self._level)
            while self._exp >= required_exp:  # Level up
                self._exp -= required_exp
                level_change += 1
                required_exp = Hero.evaluate_required_exp(
                    self._level + level_change)
            while self._exp < 0:  # Level down
                self._exp += Hero.evaluate_required_exp(
                    self._level - 1 + level_change)
                level_change -= 1
            self.e_exp_change.fire(sender=self,
                                   exp=exp,
                                   previous_exp=previous_exp,
                                   exp_change=exp_change,
                                   level_change=level_change)
            # Prevents call to 'self._exp = 0'
            super(Hero, self)._set_level(self._level + level_change)

    exp = property(_get_exp, _set_exp)

    def _get_skill_points(self):
        used_skill_points = sum([skill.level for skill in self.skills])
        return self._level - used_skill_points

    skill_points = property(_get_skill_points)

    def execute_skills(self, **eargs):
        for skill in self.skills:
            skill.execute(eargs)


class Skill(Entity):

    def __init__(self, name, description='', author='', cost=1, level=0,
                 required_level=0, max_level=-1, cooldown=0):
        super(Skill, self).__init__(name, description, author, cost, level,
                                    required_level, max_level)
        self.cooldown = cooldown
        self.remaining_cooldown = cooldown
        self.e_execute = tools.Event()
        self.e_cooldown_reset = tools.Event()

    def execute(self, eargs):
        if self.level > 0 and 'game_event' in eargs \
                and hasattr(self, eargs['game_event']):
            if self.cooldown and self.remaining_cooldown <= 0:
                threading.Thread(target=self.start_cooldown, args=(self,))
            getattr(self, eargs['game_event'])(eargs)
            self.e_execute.fire(sender=self, eargs=eargs)

    def start_cooldown(self):
        self.remaining_cooldown = self.cooldown
        while self.remaining_cooldown > 0:
            time.sleep(1)
            self.remaining_cooldown -= 1
        self.remaining_cooldown = 0
        self.e_cooldown_reset.fire(sender=self)