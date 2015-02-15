# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.tools import get_subclasses
from herowars.tools import classproperty

# Source.Python
from listeners.tick.repeat import TickRepeat


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all___ = (
    'Entity',
    'Hero',
    'Skill',
    'Passive',
    'Item'
)


# ======================================================================
# >> CLASSES
# ======================================================================

class Entity(object):
    """The base element of Hero Wars.

    Entity is a base class for most of the Hero Wars classes.
    It implements common properties like name and description, as well
    as common behavior and methods for most objects in Hero Wars.

    Attributes:
        level: Entity's Hero Wars level

    Class Attributes:
        name: Entity's name
        description: Short description of the entity
        author: Creator/Designer of the entity
        cost: How much does the entity cost
        max_level: Maximum level the entity can be leveled to
        enabled: Is the entity enabled on the server
        required_level: Required level before the entity can be used
        allowed_users: A private set of users who can use the entity 
    """

    # Defaults
    name = 'Unnamed Entity'
    description = 'This is an entity.'
    author = 'Unknown'
    cost = 0
    max_level = -1  # Negative value for unlimited
    enabled = True
    required_level = 0
    allowed_users = tuple()

    @classproperty
    def cls_id(cls):
        """Gets the class' id.

        Returns the name of the class or instance's class.
        Can be called from the class or one of its instances.

        Returns:
            The class id
        """

        return cls.__name__

    def __init__(self, level=0):
        """Initializes a new Hero Wars entity.

        Args:
            level: Entity's starting level
        """

        self._level = level

    @property
    def level(self):
        """Getter for entity's level.

        Returns:
            Entity's level
        """

        return self._level

    @level.setter
    def level(self, level):
        """Setter for entity's level.

        Raises:
            ValueError: If the level is set to a negative value or
                to a value higher than max_level
        """

        if level < 0:
            raise ValueError('Attempt to set negative level for an entity.')
        elif level > self.max_level and self.max_level > 0:
            raise ValueError('Attempt to set an entity over it\'s max level.')
        self._level = level

    @classmethod
    def get_subclasses(cls):
        """Gets a list of the enabled subclasses.

        Loops through all the subclasses of an entity class, adding the
        ones that have 'enabled' set to True to a list and returns
        the list of all the subclasses, sorted by the class's name.

        Returns:
            List of enabled entity class' subclasses
        """

        return sorted(
            (subcls for subcls in get_subclasses(cls) if subcls.enabled),
            key=lambda subcls: subcls.name
        )


class Hero(Entity):
    """Heroes strenghten players, giving them a set of powerful skills.

    Each hero has its own unique skill set (see herowars.core.Skill) to
    spice up the game.
    Clients attempt to level up their heroes by gaining enough
    experience points (exp) until the hero levels up.
    Experience points are gained from in-game tasks, such as killing
    enemies and planting bombs.
    After leveling up, player can upgrade the hero's skills a little.

    Attributes:
        skills: List of hero object's skills
        exp: Hero's experience points for gradually leveling up
        required_exp: Experience points required for hero to level up

    Class Attributes:
        skill_set (cls var): List of skill classes the hero will use
    """

    # Defaults
    name = 'Unnamed Hero'
    description = 'This is a hero.'
    skill_set = tuple()
    passive_set = tuple()
    cost = 100
    max_level = 70

    def __init__(self, level=0, exp=0):
        """Initializes a new Hero Wars hero.

        Args:
            level: Hero's current level
            exp: Hero's experience points
        """

        super().__init__(level)
        self._exp = exp
        self.skills = [
            skill() for skill in self.skill_set if skill.enabled
        ]
        self.passives = [
            passive() for passive in self.passive_set if passive.enabled
        ]
        self.items = []

    @property
    def required_exp(self):
        """Calculate required experience points for a hero to level up.
        
        Returns:
            Required experience points for leveling up
        """
        
        return 100 + self.level * 25

    @Entity.level.setter
    def level(self, level):
        """Level setter for hero.

        Sets hero's level to an absolute value, and manages setting
        his experience points to zero in case the level was decreased.
        This is mostly used only by admins.

        Args:
            level: Level to set the hero to
        """

        self._exp = 0
        Entity.level.fset(self, level)  # Call to Entity's level setter

    @property
    def exp(self):
        """Getter for hero's experience points.

        Returns:
            Hero's experience points
        """

        return self._exp

    @exp.setter
    def exp(self, exp):
        """Setter for hero's experience points.

        Sets hero's exp, increases hero's level as his experience points
        reach their maximum.

        Raises:
            ValueError: If attempting to set exp to a negative value
        """

        if exp < 0:
            raise ValueError('Attempt to set negative exp for a hero.')
        if exp != self._exp:
            # Increase levels if necessary
            while self.exp >= self.required_exp:
                self._exp -= self.required_exp
                self._level += 1

    @property
    def skill_points(self):
        """Gets the amount of hero's unused skill points.

        Returns:
            Unused skill points
        """

        used_skill_points = sum(skill.level for skill in self.skills)
        return self._level - used_skill_points

    def execute_skills(self, method_name, game_event):
        """Executes hero's skills and passives.

        Calls each of hero's skills' and passives' execute() method with
        the given game_event.

        Args:
            method_name: Name of the method to execute
            game_event: Game event object containing event information
        """

        for passive in self.passives:
            passive.execute_method(method_name, game_event)
        for skill in self.skills:
            if skill.level:
                skill.execute_method(method_name, game_event)
        for item in self.items:
            item.execute_method(method_name, game_event)

    @classmethod
    def skill(cls, skill_class):
        """Decorator for adding skills to a hero's skill set.

        Decorator that allows easily adding skills into hero's skill set
        upon the definition of the skill class. The decorated skill
        class will get appended to the end of the skill set.

        Args:
            skill_class: Skill class to add into hero's skill set

        Returns:
            The skill without any modifications, simply appended to
            the hero's skill set.
        """

        cls.skill_set += (skill_class, )
        return skill_class

    @classmethod
    def passive(cls, skill_class):
        """Decorator for adding passive skills to a hero's skill set.

        Read Hero.skill for more info.

        Args:
            skill_class: Skill class to add into hero's skill set

        Returns:
            The passive skill without any modifications, simply appended
            to the hero's passive skill set.
        """

        cls.passive_set += (skill_class, )
        return skill_class


class Skill(Entity):
    """Skills give custom powers and effects for heroes.

    Skills are what heroes use to become strong an dunique; they allow
    more versatile gameplay for Hero Wars. Each hero has a certain skill
    set, and each skill gets used during a certain event or action to
    create a bonus effect, such as damaging the enemy.
    """

    # Defaults
    name = 'Unnamed Skill'
    description = 'This is a skill.'
    cost = 1
    max_level = 8

    def execute_method(self, method_name, game_event):
        """Executes skill's method.

        Executes the skill's method with matching name to the
        method_name with provided event arguments.

        Args:
            method_name: Name of the method to execute
            game_event: Game event object containing event information
        """

        method = getattr(self.__class__, method_name, None)
        if method:
            method(self, game_event)


class Item(Skill):
    """Items are kind of temporary skills that can be bought on heroes.

    Each hero can equip 6 items at once, they can be bought and sold
    and some can be upgraded.
    
    Class Attributes:
        permanent: Does the item stay when the hero dies
    """

    # Defaults
    name = 'Unnamed Item'
    description = 'This is an item.'
    cost = 10
    permanent = False  # Stays after death?
    limit = 0