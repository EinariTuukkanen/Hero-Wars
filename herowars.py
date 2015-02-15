# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero Wars
from herowars.player import get_player
from herowars.player import create_player
from herowars.player import remove_player

from herowars.database import setup_database
from herowars.database import save_player_data

from herowars.heroes import *

from herowars.entities import Hero

from herowars.configs import database_path

import herowars.menus as menus

# Source.Python 
from events import Event


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def load():
    """Setups the database upon Hero Wars loading.

    Also makes sure there are heroes on the server.
    
    Raises:
        NotImplementedError: When there are no heroes
    """

    if not Hero.get_subclasses():
        raise NotImplementedError('No heroes on the server.')
    setup_database(database_path)


# ======================================================================
# >> GAME EVENTS
# ======================================================================

@Event
def player_disconnect(game_event):
    """Removes a player and saves his data upon disconnection."""

    userid = game_event.get_int('userid')
    remove_player(userid)


@Event
def player_spawn(game_event):
    """Creates new players and saves existing players' data.

    Also executes spawn skills.
    """

    userid = game_event.get_int('userid')
    player = get_player(userid)
    if player:
        save_player_data(database_path, player)
    else:
        player = create_player(userid)
    if game_event.get_int('teamnum') > 0:
        player.hero.execute_skills('on_spawn', game_event)


@Event
def player_death(game_event):
    """Executes kill, assist and death skills."""

    game_event.set_int('defender', game_event.get_int('userid'))
    game_event.set_int('userid', 0)
    defender = get_player(game_event.get_int('defender'))
    attacker = get_player(game_event.get_int('attacker'))
    assister = get_player(game_event.get_int('assister'))
    if defender:
        if attacker:
            attacker.hero.execute_skills('on_kill', game_event)
            defender.hero.execute_skills('on_death', game_event)
        else:
            defender.hero.execute_skills('on_suicide', game_event)
        if assister:
            assister.hero.execute_skills('on_assist', game_event)


@Event
def player_hurt(game_event):
    """Executes attack and defend skills."""

    game_event.set_int('defender', game_event.get_int('userid'))
    game_event.set_int('userid', 0)
    defender = get_player(game_event.get_int('defender'))
    attacker = get_player(game_event.get_int('attacker'))
    if defender and attacker:
        attacker.hero.execute_skills('on_attack', game_event)
        defender.hero.execute_skills('on_defend', game_event)


@Event
def player_jump(game_event):
    """Executes jump skills."""

    player = get_player(game_event.get_int('userid'))
    if player:
        player.hero.execute_skills('on_jump', game_event)


@Event
def player_say(game_event):
    """Executes ultimate skills."""

    player = get_player(game_event.get_int('userid'))
    if player:
        text = game_event.get_string('text')
        if text == '!ultimate':
            player.hero.execute_skills('on_ultimate', game_event)