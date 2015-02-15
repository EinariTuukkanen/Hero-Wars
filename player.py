# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.database import load_player_data
from herowars.database import save_player_data
from herowars.database import load_hero_data
from herowars.database import save_hero_data

from herowars.entities import Hero

from herowars.tools import find_element

from herowars.configs import database_path

# Source.Python
from players.entity import PlayerEntity
from players.helpers import index_from_userid


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all___ = (
    'player',
    'get_player',
    'create_player',
    'remove_player'
)


# ======================================================================
# >> GLOBALS
# ======================================================================

players = []


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def get_player(userid):
    """Gets a player with matching userid.

    Loops through the players list and returns a player with matching
    userid to the provided parameter value.

    Args:
        userid: Userid of the player to find

    Returns:
        Player with matching userid
    """

    return find_element(players, 'userid', userid)


def create_player(userid):
    """Creates a new player, fetching his data from the database.

    Args:
        userid: Userid of the player to create

    Returns:
        New player who's been added to the players list
    """

    player = _Player(index_from_userid(userid))
    load_player_data(database_path, player)
    if not player.heroes:
        first_hero_cls = Hero.get_subclasses()[0]
        player.heroes.append(first_hero_cls())
    if not player.hero:
        player._hero = player.heroes[0]
    players.append(player)
    return player


def remove_player(userid):
    """Removes a player, inserting his data into the database.

    Args:
        userid: Userid of the player to remove
    """

    player = get_player(userid)
    if player:
        save_player_data(database_path, player)
        players.remove(player)


# ======================================================================
# >> CLASSES
# ======================================================================

class _Player(PlayerEntity):
    """Player class for Hero Wars related activity.

    Player extends Source.Python's PlayerEntity, implementing player
    sided properties for Hero Wars related information.
    Adds methods such as burn, freeze and push.

    Attributes:
        gold: Player's Hero Wars gold, used to purchase heroes and items
        hero: Player's hero currently in use
        heroes: List of owned heroes
    """

    def __new__(cls, index, gold=0):
        """Creates a new Hero Wars player.

        Args:
            index: Player's index
            gold: Player's Hero Wars gold
        """

        self = super().__new__(cls, index)
        self._gold = gold
        self._hero = None
        self.heroes = []
        return self

    @property
    def gold(self):
        """Getter for player's Hero Wars gold.

        Returns:
            Player's gold
        """

        return self._gold

    @gold.setter
    def gold(self, gold):
        """Setter for player's Hero Wars gold.

        Raises:
            ValueError: If gold is set to a negative value
        """

        if gold < 0:
            raise ValueError('Attempt to set negative gold for a player.')
        self._gold = gold

    @property
    def hero(self):
        """Getter for player's current hero.

        Returns:
            Player's hero
        """

        return self._hero

    @hero.setter
    def hero(self, hero):
        """Setter for player's current hero.

        Makes sure player owns the hero and saves his current hero to
        the database before switching to the new one.

        Args:
            hero: Hero to switch to
        
        Raises:
            ValueError: Hero not owned by the player
        """

        if hero not in self.heroes:
            raise ValueError('Hero {cls_id} not owned by {steamid}.'.format(
                cls_id=hero.cls_id, steamid=self.steamid
            ))
        save_hero_data(database_path, self.steamid, self.hero)
        self._hero = hero