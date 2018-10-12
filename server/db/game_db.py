""" Contains DB helpers for game actions.
"""

from sqlalchemy import func, and_

from db.models import Base, Game, Action, Player
from db.session import session_wrapper
from defs import Action as ActionCodes


def reset_db():
    """ Re-applies DB schema.
    """
    Base.metadata.drop_all()
    Base.metadata.create_all()


@session_wrapper
def truncate_tables(session=None):
    """ Truncates all game-related tables.
    """
    tables = [Action.__table__, Player.__table__, Game.__table__]
    for table in tables:
        session.execute(table.delete())


@session_wrapper
def add_game(name, map_idx, num_players=1, session=None):
    """ Creates a new Game in DB.
    """
    new_game = Game(name=name, map_id=map_idx, num_players=num_players)
    session.add(new_game)
    session.commit()  # Commit to get game's id.
    return new_game.id


@session_wrapper
def add_action(game_idx, action, message=None, player_idx=None, session=None):
    """ Creates a new Action in DB.
    """
    message = {} if message is None else message
    new_action = Action(game_id=game_idx, code=action.value, message=message, player_id=player_idx)
    session.add(new_action)


@session_wrapper
def add_player(idx, name, password=None, session=None):
    """ Creates a new Player in DB.
    """
    new_player = Player(id=idx, name=name, password=password)
    session.add(new_player)


@session_wrapper
def get_player_by_name(name, session=None):
    """ Retrieves a Player from DB.
    """
    return session.query(Player).filter(Player.name == name).first()


@session_wrapper
def get_all_games(session=None):
    """ Retrieves all games with their length.
    """
    return session.query(Game, func.count(Action.id)).outerjoin(
        Action, and_(Game.id == Action.game_id, Action.code == ActionCodes.TURN.value)).group_by(
            Game.id).order_by(Game.id).all()


@session_wrapper
def get_game(game_idx, session=None):
    """ Retrieves specified game with it's length.
    """
    return session.query(Game, func.count(Action.id)).filter(Game.id == game_idx).outerjoin(
        Action, and_(Game.id == Action.game_id, Action.code == ActionCodes.TURN.value)).group_by(
            Game.id).first()


@session_wrapper
def get_all_actions(game_idx, session=None):
    """ Retrieves all actions for the game.
    """
    return session.query(Action).filter(
        Action.game_id == game_idx).order_by(Action.created_at, Action.id).all()
